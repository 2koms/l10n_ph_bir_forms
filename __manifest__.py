{
    "name": "Philippines BIR Forms",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "author": "2Koms Business Solutions Philippines Inc.",
    "license": "LGPL-3",

    "depends": [
        "account",
        "stock",
        "purchase",
        "sale_management",
        "fleet",
    ],

    "data": [

        "security/ir.model.access.csv",

        "views/account_move_views.xml",
        "views/account_payment_views.xml",
        "views/bir_forms_wizard_views.xml",
        "views/stock_picking_views.xml",
        "views/statement_of_account_wizard_views.xml",
        "views/statement_of_account_menu.xml",
        "views/bir_forms_menu.xml",

        # ----------------------------
        # Sales Invoice
        # ----------------------------
        "reports/sales_invoice/report_action.xml",
        "reports/sales_invoice/computerized.xml",
        "reports/sales_invoice/preprinted.xml",
        "reports/sales_invoice/report_template.xml",

        # ----------------------------
        # Delivery Receipt
        # ----------------------------
        "reports/delivery_receipt/report_action.xml",
        "reports/delivery_receipt/computerized.xml",
        "reports/delivery_receipt/preprinted.xml",
        "reports/delivery_receipt/report_template.xml",

        # ----------------------------
        # Collection Receipt
        # ----------------------------
        "reports/collection_receipt/report_action.xml",
        "reports/collection_receipt/computerized.xml",
        "reports/collection_receipt/preprinted.xml",
        "reports/collection_receipt/report_template.xml",

        # ----------------------------
        # Statement of Account
        # ----------------------------
        "reports/statement_of_account/report_action.xml",
        "reports/statement_of_account/report_template.xml",
        "reports/statement_of_account/soa.xml",
    ],

    "installable": True,
    "application": True,
}