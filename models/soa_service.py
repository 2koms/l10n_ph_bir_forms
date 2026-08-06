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

        The report layer should only consume the returned dictionary
        and should not contain accounting logic.
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
                lambda l: l.debit - l.credit
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

    def _build_report_data(
        self,
        opening_balance,
        move_lines,
    ):
        total_debit = sum(move_lines.mapped("debit"))
        total_credit = sum(move_lines.mapped("credit"))

        running_balance = opening_balance

        lines = []

        for line in move_lines:

            running_balance += line.debit - line.credit

            lines.append({
                "date": line.date,
                "document": line.move_name or line.move_id.name or "",
                "reference": line.ref or "",
                "journal": line.journal_id.code,
                "description": line.name,
                "move_type": line.move_id.move_type,
                "payment_state": line.move_id.payment_state,
                "debit": line.debit,
                "credit": line.credit,
                "balance": running_balance,
                "move": line.move_id,
                "line": line,
            })

        return {
            "opening_balance": opening_balance,
            "lines": lines,
            "total_debit": total_debit,
            "total_credit": total_credit,
            "closing_balance": running_balance,
        }