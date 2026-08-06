from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    infi_vehicle_id = fields.Many2one(
        "fleet.vehicle",
        string="Vehicle",
        help="Used by the Sales Invoice report.",
    )