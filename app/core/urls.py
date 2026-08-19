from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("organization.urls")),
    path("", include("financial_reports.urls")),
    path("expense/", include("expenses.urls")),
    path("authentication/", include("authentication.urls")),
    path("income/", include("income.urls")),
    path("transfer/", include("transfer.urls")),
    path("attendance/", include("attendance.urls")),
    path("contributor/", include("contributor.urls")),
    path("properties/", include("church_properties.urls")),
    path("marriage/", include("marriage.urls")),
] + static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
