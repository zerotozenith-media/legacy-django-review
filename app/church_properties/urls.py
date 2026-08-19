from django.urls import path
from church_properties.views import *

urlpatterns = [
    path("", PropertiesListView.as_view(), name="church_properties_list"),
    path("add/", PropertyAddView.as_view(), name="add-property"),
    path("edit/<int:id>/", PropertyEditView.as_view(), name="edit-property"),
    path("delete/<int:id>/", delete_property, name="delete-property"),
    path("upload/", PropertyUploadView.as_view(), name="property_uploader"),
    path('property-uploader-sample/', download_property_uploader_sample, name='download_property_uploader_sample'),
    # path("edit-property/<int:id>", views.income_edit, name="income-edit"),

]
