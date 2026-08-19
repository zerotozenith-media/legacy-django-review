from django.urls import path

from authentication.views import user_delete
from . import views
from .views import GCKEventListView, GCKEventCreateView, GCKEventUpdateView, delete_gckevent

urlpatterns = [
    path('', views.attendance_list, name='attendance_list'),
    path('add/', views.add, name='add_attendance'),
    path('<int:pk>/edit/', views.edit_attendance, name='edit_attendance'),
    path('<int:pk>/delete/', views.delete_attendance, name='delete_attendance'),
    path('church_services/', views.ChurchServiceView.as_view(), name='church_service_view'),
    path("upload/", views.AttendanceUploadView.as_view(), name="attendance_uploader"),
    path('attendance-uploader-sample/', views.download_attendance_uploader_sample,
         name='download_attendance_uploader_sample'),
    path('gck/', views.gck_attendance_list, name='gck_attendance_list'),
    path('gck/add', views.GCKAttendanceCreateView.as_view(), name='gck_attendance_add'),
    path('gck/edit/<int:pk>/', views.GCKAttendanceEditView.as_view(), name='edit_gck_attendance'),
    path('gck/<int:pk>/delete/', views.delete_gck_attendance, name='delete_gck_attendance'),
    path('gck_coverts/follow_up/', views.gck_converts_follow_up_table, name='gck_converts_follow_up'),
    path('gck/ministers_workers/', views.gck_ministers_workers_list, name='gck_ministers_workers_list'),
    path('gck/ministers_workers/add/', views.GCKWorkersAttendanceCreateView.as_view(),
         name='gck_workers_attendance_add'),
    path('gck/ministers_workers/edit/<int:pk>/', views.GCKWorkersAttendanceEditView.as_view(),
         name='edit_gck_workers_attendance'),
    path('gck/ministers_workers/<int:pk>/delete/', views.delete_gck_workers_attendance,
         name='delete_gck_workers_attendance'),
    path('gck/projections/', views.gck_projections, name='gck_projections'),

    path("events/", GCKEventListView.as_view(), name="event_list"),
    path("events/add/", GCKEventCreateView.as_view(), name="event_add"),
    path('event/delete/<int:event_id>/', delete_gckevent, name='event_delete'),
    path("events/<int:pk>/edit/", GCKEventUpdateView.as_view(), name="event_edit"),
]
