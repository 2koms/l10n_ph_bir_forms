from odoo import api, fields, models


class BirFormsWizard(models.TransientModel):
    _name = "bir.forms.wizard"
    _description = "BIR Forms Wizard"

    # =========================================================
    # GENERAL
    # =========================================================

    form_type = fields.Selection(
        [
            ("sales_invoice", "Sales Invoice"),
            ("delivery_receipt", "Delivery Receipt"),
            ("collection_receipt", "Collection Receipt"),
            ("credit_memo", "Credit Memo"),
            ("debit_memo", "Debit Memo"),
            ("purchase_order", "Purchase Order"),
        ],
        string="Document Type",
        required=True,
    )

    generation_mode = fields.Selection(
        [
            ("single", "Single Document"),
            ("batch", "Batch Generation"),
        ],
        string="Generation Mode",
        default="single",
        required=True,
    )

    print_type = fields.Selection(
        [
            ("preprinted", "Pre-Printed"),
            ("computerized", "Computerized"),
        ],
        string="Print Type",
        required=True,
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )

    # =========================================================
    # BATCH PARAMETERS
    # =========================================================

    date_from = fields.Date(
        string="Date From",
    )

    date_to = fields.Date(
        string="Date To",
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Customer / Vendor",
    )

    # =========================================================
    # SINGLE DOCUMENT PARAMETERS
    # =========================================================

    invoice_id = fields.Many2one(
        "account.move",
        string="Invoice",
        domain="""
        [
            ("move_type", "=", "out_invoice"),
            ("state", "=", "posted"),
            ("company_id", "=", company_id)
        ]
        """,
    )

    picking_id = fields.Many2one(
        "stock.picking",
        string="Delivery Order",
        domain="""
        [
            ("picking_type_code", "=", "outgoing"),
            ("state", "=", "done"),
            ("company_id", "=", company_id)
        ]
        """,
    )

    purchase_order_id = fields.Many2one(
        "purchase.order",
        string="Purchase Order",
        domain="""
        [
            ("company_id", "=", company_id)
        ]
        """,
    )

    credit_memo_id = fields.Many2one(
        "account.move",
        string="Credit Memo",
        domain="""
        [
            ("move_type", "=", "out_refund"),
            ("company_id", "=", company_id)
        ]
        """,
    )

    debit_memo_id = fields.Many2one(
        "account.move",
        string="Debit Memo",
        domain="""
        [
            ("move_type", "=", "out_invoice"),
            ("company_id", "=", company_id)
        ]
        """,
    )

    payment_id = fields.Many2one(
        "account.payment",
        string="Customer Payment",
        domain="""
        [
            ("company_id", "=", company_id),
            ("partner_type", "=", "customer"),
            ("payment_type", "=", "inbound"),
            ("state", "=", "posted")
        ]
        """,
    )

    # =========================================================
    # DEFAULT VALUES
    # =========================================================

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        active_model = self.env.context.get("active_model")
        active_id = self.env.context.get("active_id")

        if not active_model or not active_id:
            return res

        # =====================================================
        # ACCOUNT MOVE
        # =====================================================

        if active_model == "account.move":

            move = self.env["account.move"].browse(active_id)

            if move.exists():

                if move.move_type == "out_invoice":
                    res.update({
                        "form_type": "sales_invoice",
                        "invoice_id": move.id,
                        "company_id": move.company_id.id,
                    })

                elif move.move_type == "out_refund":
                    res.update({
                        "form_type": "credit_memo",
                        "credit_memo_id": move.id,
                        "company_id": move.company_id.id,
                    })

        # =====================================================
        # STOCK PICKING
        # =====================================================

        elif active_model == "stock.picking":

            picking = self.env["stock.picking"].browse(active_id)

            if picking.exists():
                res.update({
                    "form_type": "delivery_receipt",
                    "picking_id": picking.id,
                    "company_id": picking.company_id.id,
                })

        # =====================================================
        # PURCHASE ORDER
        # =====================================================

        elif active_model == "purchase.order":

            po = self.env["purchase.order"].browse(active_id)

            if po.exists():
                res.update({
                    "form_type": "purchase_order",
                    "purchase_order_id": po.id,
                    "company_id": po.company_id.id,
                })

        # =====================================================
        # CUSTOMER PAYMENT
        # =====================================================

        elif active_model == "account.payment":

            payment = self.env["account.payment"].browse(active_id)

            if payment.exists():

                if (
                    payment.partner_type == "customer"
                    and payment.payment_type == "inbound"
                    and payment.state == "posted"
                ):
                    res.update({
                        "form_type": "collection_receipt",
                        "payment_id": payment.id,
                        "company_id": payment.company_id.id,
                    })

        return res

    # =========================================================
    # GENERATE REPORT
    # =========================================================

    def action_generate(self):
        self.ensure_one()

        # =====================================================
        # SALES INVOICE
        # =====================================================

        if self.form_type == "sales_invoice" and self.invoice_id:

            report = self.env.ref(
                "l10n_ph_bir_forms.action_sales_invoice_report"
            )

            return report.report_action(
                self.invoice_id,
                data={
                    "invoice_id": self.invoice_id.id,
                    "print_type": self.print_type,
                },
            )

        # =====================================================
        # DELIVERY RECEIPT
        # =====================================================

        if self.form_type == "delivery_receipt" and self.picking_id:

            report = self.env.ref(
                "l10n_ph_bir_forms.action_delivery_receipt_report"
            )

            picking = self.picking_id

            return report.report_action(
                picking,
                data={
                    "picking_id": picking.id,
                    "print_type": self.print_type,
                },
            )

        # =====================================================
        # COLLECTION RECEIPT
        # =====================================================

        if self.form_type == "collection_receipt" and self.payment_id:

            report = self.env.ref(
                "l10n_ph_bir_forms.action_collection_receipt_report"
            )

            return report.report_action(
                self.payment_id,
                data={
                    "payment_id": self.payment_id.id,
                    "print_type": self.print_type,
                },
            )

        # =====================================================
        # CREDIT MEMO
        # =====================================================

        if self.form_type == "credit_memo" and self.credit_memo_id:

            report = self.env.ref(
                "l10n_ph_bir_forms.action_credit_memo_report"
            )

            return report.report_action(
                self.credit_memo_id,
                data={
                    "credit_memo_id": self.credit_memo_id.id,
                    "print_type": self.print_type,
                },
            )

        # =====================================================
        # DEBIT MEMO
        # =====================================================

        if self.form_type == "debit_memo" and self.debit_memo_id:

            report = self.env.ref(
                "l10n_ph_bir_forms.action_debit_memo_report"
            )

            return report.report_action(
                self.debit_memo_id,
                data={
                    "debit_memo_id": self.debit_memo_id.id,
                    "print_type": self.print_type,
                },
            )

        # =====================================================
        # PURCHASE ORDER
        # =====================================================

        if self.form_type == "purchase_order" and self.purchase_order_id:

            report = self.env.ref(
                "l10n_ph_bir_forms.action_purchase_order_report"
            )

            return report.report_action(
                self.purchase_order_id,
                data={
                    "purchase_order_id": self.purchase_order_id.id,
                    "print_type": self.print_type,
                },
            )

        # =====================================================
        # NOTHING SELECTED
        # =====================================================

        return True