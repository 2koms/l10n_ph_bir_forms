from odoo import models


class CollectionReceiptReport(models.AbstractModel):
    _name = "report.l10n_ph_bir_forms.collection_receipt"
    _description = "Collection Receipt Report"

    def _safe_phone(self, partner):
        mobile = partner.mobile if "mobile" in partner._fields else ""
        return partner.phone or mobile or ""

    def _get_report_values(self, docids, data=None):

        # Recover payment id from wizard
        if (not docids) and data and data.get("payment_id"):
            docids = [data["payment_id"]]

        payments = self.env["account.payment"].browse(docids)

        docs_data = []

        for payment in payments:

            partner = payment.partner_id
            company = payment.company_id
            company_partner = company.partner_id

            # ======================================================
            # Company Address
            # ======================================================

            company_address = ", ".join(filter(None, [
                company_partner.street,
                company_partner.street2,
                company_partner.city,
                company_partner.state_id.name if company_partner.state_id else "",
                company_partner.country_id.name if company_partner.country_id else "",
            ]))

            # ======================================================
            # Customer Address
            # ======================================================

            customer_address = ", ".join(filter(None, [
                partner.street,
                partner.street2,
                partner.city,
                partner.state_id.name if partner.state_id else "",
                partner.country_id.name if partner.country_id else "",
            ]))

            # ======================================================
            # Invoice Distribution
            # ======================================================

            invoice_lines = []

            invoices = payment.reconciled_invoice_ids

            withholding_tax = (
                getattr(payment, "withholding_tax_amount", 0.0)
                or getattr(payment, "x_withholding_tax", 0.0)
                or 0.0
            )

            for inv in invoices:
                invoice_lines.append({
                    "invoice_no": inv.name,
                    "invoice_date": inv.invoice_date,
                    "amount": inv.amount_total,
                    "withholding_tax": withholding_tax,
                })

            # ======================================================
            # Payment Method
            # ======================================================

            payment_method_name = (
                payment.payment_method_line_id.name
                if payment.payment_method_line_id
                else ""
            )

            payment_method = payment_method_name.lower()

            is_cash = "cash" in payment_method
            is_check = (
                "check" in payment_method
                or "cheque" in payment_method
            )

            is_bank_transfer = (
                "bank" in payment_method
                or "transfer" in payment_method
            )

            # ======================================================
            # Check Number
            # ======================================================

            check_number = (
                getattr(payment, "check_number", "")
                or getattr(payment, "x_check_number", "")
                or ""
            )

            # ======================================================
            # Totals
            # ======================================================

            total_amount_payable = payment.amount
            collectible_amount = total_amount_payable - withholding_tax

            # ======================================================
            # Amount in Words
            # ======================================================

            try:
                amount_in_words = payment.currency_id.amount_to_text(
                    payment.amount
                )
            except Exception:
                amount_in_words = ""

            # ======================================================
            # Authorized Representative
            # ======================================================

            authorized_representative = (
                getattr(company, "authorized_representative", "")
                or getattr(company, "x_authorized_representative", "")
                or self.env.user.name
            )

            # ======================================================
            # Report Data
            # ======================================================

            docs_data.append({

                # Main Records
                "payment": payment,
                "company": company,
                "partner": partner,

                # ==================================================
                # Company
                # ==================================================

                "company_name": company.name,
                "company_logo": company.logo,
                "company_address": company_address,
                "company_phone": company.phone or "",
                "company_mobile": (
                    company_partner.mobile
                    if "mobile" in company_partner._fields
                    else ""
                ) or "",
                "company_vat": company.vat or "",

                # ==================================================
                # Customer
                # ==================================================

                "customer_name": partner.name or "",
                "customer_address": customer_address,
                "customer_tin": partner.vat or "",
                "customer_phone": self._safe_phone(partner),

                "customer_business_style": (
                    getattr(partner, "x_business_style", "")
                    or getattr(partner, "business_style", "")
                    or ""
                ),

                # ==================================================
                # Receipt
                # ==================================================

                "receipt_no": payment.name,
                "receipt_date": payment.date,
                "payment_reference": (
                    getattr(payment, "payment_reference", "")
                    or getattr(payment, "ref", "")
                    or getattr(payment, "communication", "")
                    or ""
                ),

                "amount": payment.amount,
                "currency": payment.currency_id,

                # ==================================================
                # Payment
                # ==================================================

                "payment_method": payment_method_name,
                "is_cash": is_cash,
                "is_check": is_check,
                "is_bank_transfer": is_bank_transfer,
                "check_number": check_number,

                # ==================================================
                # Totals
                # ==================================================

                "total_amount_payable": total_amount_payable,
                "withholding_tax": withholding_tax,
                "collectible_amount": collectible_amount,

                # ==================================================
                # Amount in Words
                # ==================================================

                "amount_in_words": amount_in_words,

                # ==================================================
                # Signature
                # ==================================================

                "authorized_representative": authorized_representative,

                # ==================================================
                # Invoice Distribution
                # ==================================================

                "invoice_lines": invoice_lines,

            })

        return {
            "doc_ids": docids,
            "doc_model": "account.payment",
            "docs": payments,
            "docs_data": docs_data,
            "data": data or {},
        }