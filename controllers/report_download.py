import json
import logging

from odoo import http
from odoo.http import request, content_disposition
from odoo.tools.safe_eval import safe_eval, time

from odoo.addons.web.controllers.report import ReportController


_logger = logging.getLogger(__name__)


class BirReportController(ReportController):

    # =========================================================
    # THIS IS THE ONLY REPORT WE CUSTOMIZE
    # =========================================================

    DELIVERY_REPORT_NAME = (
        "l10n_ph_bir_forms.delivery_receipt"
    )

    @http.route(
        "/report/download",
        type="http",
        auth="user",
    )
    def report_download(
        self,
        data,
        context=None,
        token=None,
        readonly=True,
    ):
        # =====================================================
        # FIRST: LET STANDARD ODOO GENERATE THE REPORT
        # =====================================================

        response = super().report_download(
            data,
            context=context,
            token=token,
            readonly=readonly,
        )

        # =====================================================
        # EVERYTHING BELOW IS ONLY FOR OUR DELIVERY RECEIPT
        # =====================================================

        try:
            request_data = json.loads(data)

            if not request_data:
                return response

            url = request_data[0]

            # -------------------------------------------------
            # STRICT REPORT CHECK
            # -------------------------------------------------

            if self.DELIVERY_REPORT_NAME not in url:
                return response

            # -------------------------------------------------
            # ONLY PDF
            # -------------------------------------------------

            if len(request_data) > 1:
                report_type = request_data[1]

                if report_type != "qweb-pdf":
                    return response

            # -------------------------------------------------
            # READ URL OPTIONS
            # -------------------------------------------------

            from werkzeug.urls import url_parse

            query_data = url_parse(url).decode_query(
                cls=dict
            )

            options = query_data.get("options")

            if not options:
                return response

            if isinstance(options, str):
                options = json.loads(options)

            if not isinstance(options, dict):
                return response

            # -------------------------------------------------
            # GET PICKING ID
            # -------------------------------------------------

            picking_id = options.get("picking_id")

            if not picking_id:
                _logger.info(
                    "BIR DR: no picking_id in report options."
                )
                return response

            try:
                picking_id = int(picking_id)
            except (TypeError, ValueError):
                return response

            # -------------------------------------------------
            # GET STOCK PICKING
            # -------------------------------------------------

            picking = (
                request.env["stock.picking"]
                .browse(picking_id)
                .exists()
            )

            if not picking:
                return response

            # -------------------------------------------------
            # VERIFY REPORT
            # -------------------------------------------------

            report = (
                request.env["ir.actions.report"]
                ._get_report_from_name(
                    self.DELIVERY_REPORT_NAME
                )
            )

            if not report:
                return response

            if report.model != "stock.picking":
                return response

            # -------------------------------------------------
            # BUILD FILENAME
            # -------------------------------------------------

            filename = None

            if report.print_report_name:

                filename = safe_eval(
                    report.print_report_name,
                    {
                        "object": picking,
                        "time": time,
                    },
                )

            # -------------------------------------------------
            # FALLBACK
            # -------------------------------------------------

            if not filename:

                number = (
                    picking.name.split("/")[-1]
                    if picking.name
                    else str(picking.id)
                )

                filename = (
                    "Delivery Receipt - %s"
                    % number
                )

            # -------------------------------------------------
            # ENSURE .PDF
            # -------------------------------------------------

            filename = str(filename)

            if not filename.lower().endswith(".pdf"):
                filename += ".pdf"

            # -------------------------------------------------
            # CHANGE ONLY THE DOWNLOAD FILENAME
            # -------------------------------------------------

            response.headers["Content-Disposition"] = (
                content_disposition(filename)
            )

            _logger.info(
                "BIR DELIVERY RECEIPT filename: %s",
                filename,
            )

        except Exception:
            # =================================================
            # NEVER BREAK REPORT GENERATION
            # =================================================

            _logger.exception(
                "Error customizing BIR Delivery Receipt filename"
            )

        return response