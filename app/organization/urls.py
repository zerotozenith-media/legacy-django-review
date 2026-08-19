from django.urls import path
from . import views

from django.views.decorators.csrf import csrf_exempt


urlpatterns = [
    path("", views.index, name="dashboard"),
    path('ajax/local_churcheses/', views.get_local_churches_by_region, name='get_local_churches_by_region'),
    path('ajax/regions/', views.get_regions_by_local_church, name='get_regions_by_local_church'),
    path('detail_reports/', views.report_management, name='detail_report_view'),
    path('reconciliation_n_allocation/', views.reconciliation_and_allocation, name='reconciliation_n_allocation'),
    path('reconciliation/export/', views.download_sample_reconciliation, name='export_reconciliation'),
    path('payment_allocation/<int:id>/', views.get_payment_allocation, name='get_payment_allocation')
]
