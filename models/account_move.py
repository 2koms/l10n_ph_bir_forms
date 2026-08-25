from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    # ==========================================================
    # SALES INVOICE DETAILS
    # ==========================================================

    infi_vehicle_id = fields.Many2one(
        "fleet.vehicle",
        string="Vehicle",
        ondelete="restrict",
        index=True,
        help="Vehicle associated with this sales invoice.",
    )

    infi_period_covered = fields.Char(
        string="Period Covered",
        help=(
            "Optional billing or service period. Examples: "
            "'July 2026', 'July 1-31, 2026', 'Q3 2026', or '2026'."
        ),
    )

    infi_remarks = fields.Text(
        string="Notes / Remarks",
        help="Additional notes or remarks to appear on the sales invoice.",
    )

    # ==========================================================
    # VALIDATION
    # ==========================================================

    @api.constrains("infi_period_covered")
    def _check_infi_period_covered(self):
        """
        Validate Period Covered when the user provides a value.

        The field is intentionally optional because not every invoice
        requires a covered period.

        We accept common business formats such as:
            - July 2026
            - July 1-31, 2026
            - August 1–31, 2026
            - Q1 2026
            - Q3 2026
            - 2026

        We reject values that contain no recognizable time information,
        such as:
            - asdad
            - abc
            - xyz
        """

        month_names = {
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
        }

        quarter_names = {
            "q1",
            "q2",
            "q3",
            "q4",
        }

        for move in self:
            period = (move.infi_period_covered or "").strip()

            # Period Covered is optional.
            if not period:
                continue

            period_lower = period.lower()

            # Accept if the value contains a 4-digit year.
            has_year = any(
                str(year) in period
                for year in range(1900, 2200)
            )

            # Accept month names.
            has_month = any(
                month in period_lower
                for month in month_names
            )

            # Accept quarters such as Q1, Q2, Q3, Q4.
            has_quarter = any(
                quarter in period_lower
                for quarter in quarter_names
            )

            if not (has_year or has_month or has_quarter):
                raise ValidationError(
                    "Invalid Period Covered.\n\n"
                    "Please enter a meaningful billing or service period, "
                    "for example:\n"
                    "• July 2026\n"
                    "• July 1-31, 2026\n"
                    "• Q3 2026\n"
                    "• 2026\n\n"
                    "Leave the field blank if Period Covered is not "
                    "applicable to this invoice."
                )