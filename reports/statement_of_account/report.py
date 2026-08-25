from odoo import api, fields, models


class StatementOfAccountReport(models.AbstractModel):
    _name = "report.l10n_ph_bir_forms.statement_of_account"
    _description = "Statement of Account Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}

        # ==========================================================
        # Partner
        # ==========================================================

        partner = self.env["res.partner"].browse(
            data.get("partner_id")
        )

        company = self.env.company

        # ==========================================================
        # Statement Dates
        # ==========================================================

        statement_date = fields.Date.to_date(
            data.get("statement_date")
        )

        date_from = (
            fields.Date.to_date(data.get("date_from"))
            if data.get("date_from")
            else statement_date
        )

        # ==========================================================
        # Statement Options
        # ==========================================================

        statement_type = data.get(
            "statement_type"
        )

        include_credit_notes = data.get(
            "include_credit_notes",
            True,
        )

        # ==========================================================
        # Print Header Option
        #
        # The wizard sends either:
        #
        #     with_header
        #     without_header
        #
        # Default is with_header for safety.
        # ==========================================================

        print_header = data.get(
            "print_header",
            "with_header",
        )

        if print_header not in (
            "with_header",
            "without_header",
        ):
            print_header = "with_header"

        # ==========================================================
        # Statement Service
        # ==========================================================

        service = self.env[
            "statement.of.account.service"
        ]

        report_data = service.get_partner_move_lines(
            partner=partner,
            date_from=date_from,
            statement_date=statement_date,
            statement_type=statement_type,
            include_credit_notes=include_credit_notes,
        )

        # ==========================================================
        # Report Values
        # ==========================================================

        return {
            "doc_ids": [partner.id],
            "doc_model": "res.partner",
            "docs": partner,

            "company": company,
            "partner": partner,

            "date_from": date_from,
            "statement_date": statement_date,

            "statement_type": statement_type,
            "include_credit_notes": include_credit_notes,

            # IMPORTANT:
            # This is consumed by soa.xml.
            "print_header": print_header,

            **report_data,
        }