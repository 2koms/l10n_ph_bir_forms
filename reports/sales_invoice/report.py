from odoo import models


class SalesInvoiceYaletrakReport(models.AbstractModel):
    _name = 'report.l10n_ph_bir_forms.sales_invoice'
    _description = 'Sales Invoice Report (Yaletrak format)'

    def _num_to_words(self, amount, currency_name):
        # Best-effort amount-in-words.
        # Falls back to blank if num2words is unavailable.
        try:
            from num2words import num2words

            words = num2words(int(amount), lang='en').title()
            cents = round((amount - int(amount)) * 100)

            if cents:
                words += f' and {cents:02d}/100'

            return f'{words} {currency_name} Only'

        except Exception:
            return ''

    def _safe_phone(self, partner):
        # Some Odoo 19 setups may not expose a mobile field.
        mobile = (
            partner.mobile
            if 'mobile' in partner._fields
            else ''
        )

        return partner.phone or mobile or ''

    def _get_report_values(self, docids, data=None):

        # Recover invoice id from wizard
        if (not docids) and data and data.get('invoice_id'):
            docids = [data['invoice_id']]

        invoices = self.env['account.move'].browse(docids)

        docs_data = []

        for inv in invoices:

            partner = inv.partner_id
            company = inv.company_id
            company_partner = company.partner_id

            # ======================================================
            # COMPANY ADDRESS
            # ======================================================

            company_address = ', '.join(filter(None, [
                company.street,
                company.street2,
                company.city,
                company.state_id.name if company.state_id else '',
                company.country_id.name if company.country_id else '',
            ]))

            # ======================================================
            # CUSTOMER / SALES ORDER
            # ======================================================

            sale_order = (
                self.env['sale.order'].search(
                    [('name', '=', inv.invoice_origin)],
                    limit=1
                )
                if inv.invoice_origin
                else self.env['sale.order']
            )

            customer_po = sale_order.client_order_ref or ''

            # ======================================================
            # CUSTOMER ADDRESS
            # ======================================================

            addr_parts = [
                partner.street or '',
                partner.street2 or '',
                ', '.join(filter(None, [
                    partner.city,
                    partner.state_id.name if partner.state_id else '',
                    partner.zip,
                ])),
            ]

            # ======================================================
            # VEHICLE INFORMATION
            # ======================================================

            vehicle = inv.infi_vehicle_id

            make = (
                vehicle.model_id.brand_id.name
                if vehicle
                else ''
            )

            model = (
                vehicle.model_id.name
                if vehicle
                else ''
            )

            serial_no = (
                vehicle.vin_sn
                if vehicle
                else ''
            )

            rental_no = (
                vehicle.license_plate
                if vehicle
                else ''
            )

            # ======================================================
            # INVOICE LINES
            # ======================================================

            product_lines = inv.invoice_line_ids.filtered(
                lambda l: l.display_type in (False, 'product')
            )

            lines = [{
                'qty': line.quantity,
                'part_no': line.product_id.default_code or '',
                'uom': line.product_uom_id.name or '',
                'particulars': (
                    line.name
                    or line.product_id.name
                    or ''
                ),
                'unit_cost': line.price_unit,
                'amount': line.price_subtotal,
            } for line in product_lines]

            # ======================================================
            # MATERIALS / LABOR
            # ======================================================

            total_materials = sum(
                line.price_subtotal
                for line in product_lines
                if 'material' in (
                    line.product_id.categ_id.name or ''
                ).lower()
            )

            total_labor = sum(
                line.price_subtotal
                for line in product_lines
                if (
                    'labor' in (
                        line.product_id.categ_id.name or ''
                    ).lower()
                    or
                    'labour' in (
                        line.product_id.categ_id.name or ''
                    ).lower()
                )
            )

            # ======================================================
            # SALES TOTALS
            # ======================================================

            gross_sales = sum(
                line.quantity * line.price_unit
                for line in product_lines
            )

            net_sales = inv.amount_untaxed
            discount_total = gross_sales - net_sales
            vat_amount = inv.amount_tax
            total_amount = inv.amount_total

            # ======================================================
            # WITHHOLDING TAX
            # ======================================================

            wht_lines = inv.line_ids.filtered(
                lambda l:
                    l.display_type == 'tax'
                    and l.tax_line_id
                    and l.tax_line_id.amount < 0
            )

            withholding_amount = abs(
                sum(wht_lines.mapped('balance'))
            )

            total_amount_due = (
                total_amount - withholding_amount
            )

            # ======================================================
            # REPORT DATA
            # ======================================================

            docs_data.append({

                # ==================================================
                # MAIN RECORDS
                # ==================================================

                'invoice': inv,
                'company': company,

                # ==================================================
                # COMPANY
                # ==================================================

                'company_mobile': (
                    company_partner.mobile
                    if 'mobile' in company_partner._fields
                    else ''
                ) or '',

                'company_address': company_address,

                # ==================================================
                # CUSTOMER
                # ==================================================

                'customer_name': partner.name or '',
                'tin_no': partner.vat or '',

                'addr_lines': [
                    address
                    for address in addr_parts
                    if address
                ],

                'contact_no': self._safe_phone(partner),

                # ==================================================
                # INVOICE INFORMATION
                # ==================================================

                'term': (
                    inv.invoice_payment_term_id.name
                    or ''
                ),

                'invoice_date': inv.invoice_date,

                'customer_po': customer_po,

                # ==================================================
                # DYNAMIC SALES INVOICE FIELDS
                # ==================================================

                # Actual account.move field:
                # infi_period_covered
                #
                # Report/QWeb dictionary key:
                # period_covered
                'period_covered': (
                    inv.infi_period_covered
                    or ''
                ),

                # Actual account.move field:
                # infi_remarks
                #
                # Report/QWeb dictionary key:
                # invoice_remarks
                'invoice_remarks': (
                    inv.infi_remarks
                    or ''
                ),

                # ==================================================
                # VEHICLE
                # ==================================================

                'make': make,
                'model': model,
                'rental_no': rental_no,
                'serial_no': serial_no,

                # ==================================================
                # INVOICE LINES
                # ==================================================

                'lines': lines,

                # ==================================================
                # SUMMARY
                # ==================================================

                'total_materials': total_materials,
                'total_labor': total_labor,
                'tax': vat_amount,

                'total_amount': total_amount,

                'gross_sales': gross_sales,
                'discount_total': discount_total,
                'net_sales': net_sales,

                'vatable_sales': net_sales,
                'vat_exempt_sales': 0.0,
                'vat_zero_rated_sales': 0.0,

                'vat_amount': vat_amount,

                # ==================================================
                # WITHHOLDING TAX
                # ==================================================

                'withholding_amount': withholding_amount,

                'total_amount_due': total_amount_due,

                # ==================================================
                # AMOUNT IN WORDS
                # ==================================================

                'total_in_words': self._num_to_words(
                    total_amount,
                    inv.currency_id.name
                ),
            })

        return {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'docs': invoices,
            'docs_data': docs_data,
            'data': data or {},
        }