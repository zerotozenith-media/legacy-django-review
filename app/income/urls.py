from django.urls import path
from . import views

from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path("", views.index, name="income"),
    path("add-income", views.add_income, name="add-income"),
    path("edit-income/<int:id>", views.income_edit, name="income-edit"),
    path("income-delete/<int:id>", views.delete_income, name="income-delete"),
    path("search-income", csrf_exempt(views.search_income), name="search_income"),
    path("source-list/", views.SourceListView.as_view(), name="source-list"),
    path("source-income/", views.SourceView.as_view(), name="source-income"),
    path("source-update-delete/<int:id>/", views.SourceEditDeleteView.as_view(), name="source-income-update-delete"),
    path("upload/", views.IncomeUploadView.as_view(), name="income_uploader"),
    path('income-uploader-sample/', views.download_income_uploader_sample, name='download_income_uploader_sample'),

    path("donations/", views.DonationInKindListView.as_view(), name="donation-list"),
    path('donations/add/', views.DonationInKindCreateView.as_view(), name='donation-add'),
    path('donations/<int:pk>/edit/', views.DonationInKindUpdateView.as_view(), name='donation-edit'),
    path('donations/<int:pk>/delete/', views.delete_donation, name='donation-delete'),

    path("add-region-income", views.add_region_income, name="add-region-income"),
    path("edit-region-income/<int:id>", views.region_income_edit, name="region-income-edit"),
    path("income-region-delete/<int:id>", views.delete_region_income, name="region-income-delete"),
]
