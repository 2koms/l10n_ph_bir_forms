from odoo import models


class StatementOfAccountService(models.AbstractModel):
    _name = "statement.of.account.service"
    _description = "Statement of Account Service"

    def get_partner_move_lines(
        self,
        partner,
        date_from,
        statement_date,
        statement_type,
        include_credit_notes=True,
    ):
        """
        Return Statement of Account data.

        Accounting calculations remain in this service layer.
        The QWeb report only consumes the prepared report data.
        """

        opening_balance = self._get_opening_balance(
            partner,
            date_from,
            include_credit_notes,
        )

        move_lines = self._get_move_lines(
            partner,
            date_from,
            statement_date,
            statement_type,
            include_credit_notes,
        )

        return self._build_report_data(
            opening_balance,
            move_lines,
        )

    # ==========================================================
    # Private Methods
    # ==========================================================

    def _get_opening_balance(
        self,
        partner,
        date_from,
        include_credit_notes,
    ):
        domain = [
            ("partner_id", "=", partner.id),
            ("parent_state", "=", "posted"),
            ("date", "<", date_from),
            ("account_id.account_type", "=", "asset_receivable"),
        ]

        if not include_credit_notes:
            domain.append(
                ("move_id.move_type", "!=", "out_refund")
            )

        opening_lines = self.env["account.move.line"].search(
            domain,
            order="date,id",
        )

        return sum(
            opening_lines.mapped(
                lambda line: line.debit - line.credit
            )
        )

    def _get_move_lines(
        self,
        partner,
        date_from,
        statement_date,
        statement_type,
        include_credit_notes,
    ):
        domain = [
            ("partner_id", "=", partner.id),
            ("parent_state", "=", "posted"),
            ("date", ">=", date_from),
            ("date", "<=", statement_date),
            ("account_id.account_type", "=", "asset_receivable"),
        ]

        if statement_type == "outstanding":
            domain.append(
                ("move_id.payment_state", "!=", "paid")
            )

        if not include_credit_notes:
            domain.append(
                ("move_id.move_type", "!=", "out_refund")
            )

        return self.env["account.move.line"].search(
            domain,
            order="date,id",
        )

    # ==========================================================
    # Payment / Invoice Helpers
    # ==========================================================

    def _get_payments_by_move(self, move_lines):
        """
        Build a map of account.move IDs to account.payment records.

        Payments in Odoo are represented by an account.move and linked
        through account.payment.move_id.

        This avoids performing a payment search for every SOA line.
        """

        move_ids = move_lines.mapped("move_id").ids

        if not move_ids:
            return {}

        payments = self.env["account.payment"].search(
            [
                ("move_id", "in", move_ids),
            ]
        )

        return {
            payment.move_id.id: payment
            for payment in payments
            if payment.move_id
        }

    def _get_reconciled_invoices(self, payment):
        """
        Return customer invoices / credit notes reconciled with a payment.

        Uses Odoo's native reconciliation relationship rather than
        relying on the payment memo/reference text.
        """

        if not payment:
            return self.env["account.move"]

        invoices = payment.reconciled_invoice_ids

        if not invoices:
            return self.env["account.move"]

        return invoices.filtered(
            lambda move: move.move_type in (
                "out_invoice",
                "out_refund",
            )
        )

    def _get_sales_orders(self, invoice):
        """
        Get Sales Orders related to an invoice through invoice lines.

        This uses the native sale order relationship:

            Invoice
                -> Invoice Lines
                    -> Sale Order Lines
                        -> Sale Order
        """

        if not invoice:
            return self.env["sale.order"]

        sale_lines = invoice.invoice_line_ids.mapped(
            "sale_line_ids"
        )

        return sale_lines.mapped(
            "order_id"
        )

    def _get_sales_order_reference(self, move):
        """
        Return the Sales Order number associated with an invoice.

        The first related Sales Order is used for the report.
        """

        if not move or move.move_type not in (
            "out_invoice",
            "out_refund",
        ):
            return ""

        sale_orders = self._get_sales_orders(move)

        return sale_orders[:1].name if sale_orders else ""

    # ==========================================================
    # Report Data
    # ==========================================================

    def _build_report_data(
        self,
        opening_balance,
        move_lines,
    ):
        total_debit = sum(
            move_lines.mapped("debit")
        )

        total_credit = sum(
            move_lines.mapped("credit")
        )

        running_balance = opening_balance

        lines = []

        # ------------------------------------------------------
        # Prepare payment lookup once.
        # ------------------------------------------------------

        payments_by_move = self._get_payments_by_move(
            move_lines
        )

        # ------------------------------------------------------
        # Build report lines.
        # ------------------------------------------------------

        for line in move_lines:

            move = line.move_id

            payment = payments_by_move.get(
                move.id
            )

            # --------------------------------------------------
            # Invoice information
            # --------------------------------------------------

            invoice_number = ""

            sales_order_number = ""

            if move.move_type in (
                "out_invoice",
                "out_refund",
            ):
                invoice_number = (
                    move.name
                    or line.move_name
                    or ""
                )

                sales_order_number = (
                    self._get_sales_order_reference(move)
                )

            # --------------------------------------------------
            # Payment information
            # --------------------------------------------------

            official_receipt_no = ""

            payment_date = False

            if payment:

                official_receipt_no = (
                    payment.official_receipt_no
                    or ""
                )

                # Native Odoo payment date.
                payment_date = payment.date

                # If the payment is reconciled with an invoice,
                # use that invoice as the document represented
                # by the payment.
                reconciled_invoices = (
                    self._get_reconciled_invoices(payment)
                )

                if reconciled_invoices:
                    invoice = reconciled_invoices[:1]

                    invoice_number = (
                        invoice.name
                        or invoice.ref
                        or ""
                    )

                    sales_order_number = (
                        self._get_sales_order_reference(
                            invoice
                        )
                    )

            # --------------------------------------------------
            # Date
            # --------------------------------------------------

            report_date = (
                payment_date
                if payment
                else line.date
            )

            # --------------------------------------------------
            # Existing description is intentionally preserved.
            #
            # IMPORTANT:
            # The revision requested changing the COLUMN HEADER
            # to "PO", not changing the actual PO/description
            # content.
            # --------------------------------------------------

            description = line.name or ""

            # --------------------------------------------------
            # Running balance
            # --------------------------------------------------

            running_balance += (
                line.debit - line.credit
            )

            lines.append({

                # ----------------------------------------------
                # Existing report fields
                # ----------------------------------------------

                "date": report_date,

                "document": (
                    invoice_number
                    or line.move_name
                    or move.name
                    or ""
                ),

                "reference": (
                    sales_order_number
                    or line.ref
                    or ""
                ),

                # KEEP ORIGINAL CONTENT.
                # QWeb will display this under "PO".
                "description": description,

                "journal": (
                    line.journal_id.code
                    or ""
                ),

                "move_type": move.move_type,

                "payment_state": (
                    move.payment_state
                    if move
                    else ""
                ),

                "debit": line.debit,

                "credit": line.credit,

                "balance": running_balance,

                "move": move,

                "line": line,

                # ----------------------------------------------
                # New SOA fields
                # ----------------------------------------------

                "invoice_number": invoice_number,

                "sales_order_number": sales_order_number,

                "official_receipt_no": (
                    official_receipt_no
                ),

                "payment_date": payment_date,

                "payment": payment,

            })

        return {
            "opening_balance": opening_balance,
            "lines": lines,
            "total_debit": total_debit,
            "total_credit": total_credit,
            "closing_balance": running_balance,
        }