from odoo import fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    official_receipt_no = fields.Char(
        string="Official Receipt No.",
        copy=False,
        index=True,
        tracking=True,
        help="Official Receipt number issued for this payment.",
    )