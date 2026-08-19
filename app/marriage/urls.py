from django.urls import path
from . import views

urlpatterns = [
    path('records/', views.ListMarriageRecordView.as_view(), name='list_marriage_records'),
    path('records/add/', views.CreateMarriageRecordView.as_view(),
         name='add_marriage_record'),
    path('get-regions/', views.get_regions, name='get_regions'),
    path('record/<int:pk>/edit/', views.EditMarriageRecordView.as_view(), name='edit_marriage_record'),
    path('record/<int:pk>/delete/', views.delete_marriage_record, name='delete_marriage_record'),
]
