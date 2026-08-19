from django.urls import path
from . import views

from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path("", views.index, name="transfer"),
    path("add-transfer", views.add_transfer, name="add-transfer"),
    path("edit-transfer/<int:id>", views.transfer_edit, name="transfer-edit"),
    path("transfer-delete/<int:id>", views.delete_transfer, name="transfer-delete"),
    path("search-transfer", csrf_exempt(views.search_transfer), name="search_transfer"),
    path("upload/", views.TransferUploadView.as_view(), name="transfer_uploader"),
    path('transfer-uploader-sample/', views.download_transfer_uploader_sample, name='download_transfer_uploader_sample'),
]
