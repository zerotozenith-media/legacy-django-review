from django.urls import path
from . import views

from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path("", views.index, name="expenses"),
    path("add-expense", views.add_expense, name="add-expenses"),
    path("edit-expense/<int:id>", views.expense_edit, name="expense-edit"),
    path("expense-delete/<int:id>", views.delete_expense, name="expense-delete"),
    path("search-expenses", csrf_exempt(views.search_expenses), name="search-expenses"),
    path("get-subcategories", views.get_subcategories, name="get-subcategories"),
    # path('expense_category_summary', views.expense_category_summary,
    #      name="expense_category_summary"),
    # path('stats', views.stats_view,
    #      name="stats")
    path("upload/", views.ExpenseUploadView.as_view(), name="expense_uploader"),
    path('expense-uploader-sample/', views.download_expense_uploader_sample, name='download_expense_uploader_sample'),
    path("add-region-expense", views.add_region_expense, name="add-region-expenses"),
    path("edit-region-expense/<int:id>", views.region_expense_edit, name="region-expense-edit"),
    path("region-expense-delete/<int:id>", views.delete_region_expense, name="region-expense-delete"),
]
