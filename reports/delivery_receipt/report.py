from odoo import models


class DeliveryReceiptReport(models.AbstractModel):
    _name = "report.l10n_ph_bir_forms.delivery_receipt"
    _description = "Delivery Receipt Report"

    def _safe_phone(self, partner):
        mobile = partner.mobile if "mobile" in partner._fields else ""
        return partner.phone or mobile or ""

    def _get_report_values(self, docids, data=None):
        data = data or {}

        # If called from the wizard, recover the picking from the wizard
        if not docids:
            active_model = self.env.context.get("active_model")
            active_id = self.env.context.get("active_id")

            if active_model == "bir.forms.wizard" and active_id:
                wizard = self.env["bir.forms.wizard"].browse(active_id)
                docids = wizard.picking_id.ids

        pickings = self.env["stock.picking"].browse(docids)
        
        print_type = data.get("print_type", "computerized")

        docs_data = []

        for picking in pickings:
            partner = picking.partner_id
            company = picking.company_id
            company_partner = company.partner_id

            addr_parts = [
                partner.street or "",
                partner.street2 or "",
                ", ".join(filter(None, [
                    partner.city,
                    partner.state_id.name,
                    partner.zip,
                ])),
            ]

            terms = ""
            if "sale_id" in picking._fields and picking.sale_id:
                terms = picking.sale_id.payment_term_id.name or ""

            date = picking.date_done or picking.scheduled_date

            lines = []
            for move in picking.move_ids:
                lines.append({
                    "quantity": move.quantity or 0,
                    "unit": move.product_uom.name or "",
                    "description": move.product_id.display_name or "",
                })

            docs_data.append({
                "picking": picking,
                "company": company,
                "company_mobile": (
                    company_partner.mobile
                    if "mobile" in company_partner._fields
                    else ""
                ) or "",
                "delivered_to": partner.name or "",
                "tin_no": partner.vat or "",
                "addr_lines": [a for a in addr_parts if a],
                "date": date,
                "terms": terms,
                "lines": lines,
            })

        return {
            "doc_ids": docids,
            "doc_model": "stock.picking",
            "docs": pickings,
            "docs_data": docs_data,
            "print_type": print_type,
        }