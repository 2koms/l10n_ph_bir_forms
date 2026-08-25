from odoo import models


class DeliveryReceiptReport(models.AbstractModel):
    _name = "report.l10n_ph_bir_forms.delivery_receipt"
    _description = "Delivery Receipt Report"

    def _get_report_values(self, docids, data=None):
        data = data or {}

        # =====================================================
        # GET PICKINGS
        # =====================================================

        pickings = self.env["stock.picking"].browse(docids)

        if not pickings:
            picking_id = data.get("picking_id")

            if picking_id:
                pickings = self.env["stock.picking"].browse(
                    picking_id
                )

        # =====================================================
        # PRINT TYPE
        # =====================================================

        print_type = data.get(
            "print_type",
            "computerized",
        )

        # =====================================================
        # BUILD REPORT DATA
        # =====================================================

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

            if (
                "sale_id" in picking._fields
                and picking.sale_id
            ):
                terms = (
                    picking.sale_id.payment_term_id.name
                    or ""
                )

            date = (
                picking.date_done
                or picking.scheduled_date
            )

            lines = []

            for move in picking.move_ids:

                lines.append({
                    "quantity": (
                        move.quantity
                        or move.product_uom_qty
                        or 0
                    ),
                    "unit": (
                        move.product_uom.name
                        or ""
                    ),
                    "description": (
                        move.product_id.display_name
                        or ""
                    ),
                })

            docs_data.append({
                "picking": picking,
                "company": company,

                "company_mobile": (
                    company_partner.mobile
                    if "mobile" in company_partner._fields
                    else ""
                ) or "",

                "delivered_to": (
                    partner.name
                    or ""
                ),

                "tin_no": (
                    partner.vat
                    or ""
                ),

                "addr_lines": [
                    value
                    for value in addr_parts
                    if value
                ],

                "date": date,

                "terms": terms,

                "lines": lines,
            })

        # =====================================================
        # FILENAME
        # =====================================================

        report_filename = data.get(
            "bir_report_filename"
        )

        if not report_filename and len(pickings) == 1:

            picking = pickings[0]

            number = (
                picking.name.split("/")[-1]
                if picking.name
                else str(picking.id)
            )

            report_filename = (
                "Delivery Receipt - %s"
                % number
            )

        # =====================================================
        # RETURN REPORT VALUES
        # =====================================================

        return {
            "doc_ids": pickings.ids,
            "doc_model": "stock.picking",
            "docs": pickings,
            "docs_data": docs_data,
            "print_type": print_type,

            # This is now explicitly available to the
            # report rendering layer.
            "report_filename": report_filename,
        }