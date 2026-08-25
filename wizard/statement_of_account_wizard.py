from odoo import fields, models
from odoo.exceptions import UserError


class StatementOfAccountWizard(models.TransientModel):
    _name = "statement.of.account.wizard"
    _description = "Statement of Account Wizard"

    # ==========================================================
    # Customer
    # ==========================================================

    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        domain=[("customer_rank", ">", 0)],
    )

    # ==========================================================
    # Statement Period
    # ==========================================================

    date_from = fields.Date(
        string="Date From",
    )

    statement_date = fields.Date(
        string="Statement Date",
        required=True,
        default=fields.Date.context_today,
    )

    # ==========================================================
    # Statement Options
    # ==========================================================

    statement_type = fields.Selection(
        [
            ("outstanding", "Outstanding Statement"),
            ("full", "Full Statement"),
        ],
        string="Statement Type",
        default="outstanding",
        required=True,
    )

    include_credit_notes = fields.Boolean(
        string="Include Credit Notes",
        default=True,
    )

    # ==========================================================
    # Print Options
    # ==========================================================

    print_header = fields.Selection(
        [
            ("with_header", "With Header"),
            ("without_header", "Without Header"),
        ],
        string="Print Header",
        default="with_header",
        required=True,
    )

    # ==========================================================
    # Print
    # ==========================================================

    def action_print(self):
        self.ensure_one()

        domain = [
            ("partner_id", "=", self.partner_id.id),
            ("state", "=", "posted"),
            ("move_type", "in", ("out_invoice", "out_refund")),
            ("invoice_date", "<=", self.statement_date),
        ]

        if self.date_from:
            domain.append(
                ("invoice_date", ">=", self.date_from)
            )

        # ------------------------------------------------------
        # Outstanding Statement
        # ------------------------------------------------------
        # Show only invoices that still have an outstanding
        # balance.
        if self.statement_type == "outstanding":
            domain.append(
                ("amount_residual", ">", 0)
            )

        # ------------------------------------------------------
        # Credit Notes
        # ------------------------------------------------------
        if not self.include_credit_notes:
            domain.append(
                ("move_type", "=", "out_invoice")
            )

        moves = self.env["account.move"].search(domain)

        if not moves:
            if self.statement_type == "outstanding":
                raise UserError(
                    "No outstanding transactions were found "
                    "for this customer.\n\n"
                    "The customer may have already settled "
                    "all invoices.\n"
                    "Try printing a Full Statement instead."
                )

            raise UserError(
                "No transactions were found for the selected "
                "statement period.\n\n"
                "Please review the customer or the selected dates."
            )

        # ------------------------------------------------------
        # Generate Report
        # ------------------------------------------------------

        return self.env.ref(
            "l10n_ph_bir_forms.action_statement_of_account"
        ).report_action(
            self.partner_id,
            data={
                "partner_id": self.partner_id.id,

                "date_from": (
                    self.date_from.isoformat()
                    if self.date_from
                    else False
                ),

                "statement_date": (
                    self.statement_date.isoformat()
                    if self.statement_date
                    else False
                ),

                "statement_type": self.statement_type,

                "include_credit_notes": (
                    self.include_credit_notes
                ),

                # Print layout option.
                "print_header": self.print_header,
            },
        )