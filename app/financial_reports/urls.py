from django.urls import path
from . import views

app_name = "financial_reports"

urlpatterns = [
    path("financial-reports/summary/", views.summary_income_expenditure,
         name="summary_income_expenditure"),
    path("financial-reports/t3010/", views.t3010_resources,
         name="t3010_resources"),
    path("financial-reports/usd-account/", views.usd_account,
         name="usd_account"),
    path("financial-reports/inter-transfer/", views.inter_transfer_template,
         name="inter_transfer_template"),
    path("financial-reports/asset-liability/", views.asset_liability_statement,
         name="asset_liability_statement"),
    path("financial-reports/assets-bought/", views.assets_bought,
         name="assets_bought"),
    path("financial-reports/bank-stmt-balances/", views.regions_bank_stmt_balances,
         name="regions_bank_stmt_balances"),
]