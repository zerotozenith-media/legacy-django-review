# Import necessary modules and classes
import calendar
import csv
import json
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import CreateView, UpdateView, ListView
from wkhtmltopdf.views import PDFTemplateResponse

from organization.models import LocalChurch, Region
from organization.utils import get_user_local_church
from utils.helpers import get_filtered_context, get_user_regions
from .forms import GCKAttendanceForm, EditGCKAttendanceForm, EditGCKWorkersAttendanceForm, GCKWorkersAttendanceForm, \
    GCKEventForm
from .models import Attendance, ChurchServices, GCKAttendance, GCKConvertsFollowUpReport, GCKProjections, GCKEvent
from django.db.models import F, Sum
import logging
from django.contrib import messages
from django.views import View
from django.template import loader

import calendar
from io import BytesIO
from .models import GCKEvent, GCKAttendance
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font
import re
from django.db import transaction, models
from django.http import JsonResponse, HttpResponse
from openpyxl import load_workbook, Workbook
from contributor.helper import validate_date, check_amount

from .utils import prepare_gck_attendance_context_data, get_all_months, prepare_gck_workers_attendance_context_data

logger = logging.getLogger(__name__)


# View for listing all attendance records
@login_required(login_url='/authentication/login')
def attendance_list(request):
    user = request.user
    local_churches = get_user_local_church(user)
    region = request.GET.get("region", None)
    regions = get_user_regions(user)

    if region:
        region_list = regions.filter(name__iexact=region)
        local_churches = local_churches.filter(region__in=region_list)

    # Filter by common fields
    attendance = Attendance.objects.filter(deleted=False, local_church__in=local_churches)
    attendance, filter_context = get_filtered_context(
        request,
        attendance,
        model_field_map={
            "region": "local_church__region__name",
            "local_church": "local_church_id"
        }
    )

    # Annotate the attendance records with the total count
    attendance = attendance.annotate(
        total=(
                F('adult_male') + F('adult_female') +
                F('youth_male') + F('youth_female') +
                F('children_male') + F('children_female') +
                F('campus_male') + F('campus_female') + F('cau')
        )
    )

    # Prepare the context for rendering the template
    context = {
        "attendance": attendance,
        "church_services": available_church_services(local_churches if local_churches else []),
        "regions": regions,
        "churches": local_churches,
        **filter_context
    }
    return render(request, 'attendance/index.html', context)

# Helper function to get available church services
def available_church_services(local_churches):
    # Get church services with null local church
    church_services_null_local_church = ChurchServices.objects.filter(local_church_id=None)
    # Get church services for the user's local churches
    church_services_user_local_church = ChurchServices.objects.filter(local_church__in=local_churches)
    # Combine both querysets using the union operator |
    church_services = church_services_null_local_church | church_services_user_local_church
    return church_services

# View for adding a new attendance record
@login_required(login_url='/authentication/login')
def add(request):
    if request.method == 'POST':
        try:
            # Prepare the data for creating a new attendance record
            data = {
                'church_service_id': request.POST.get('church_service'),
                'date': request.POST.get('date'),
                'adult_male': request.POST.get('adult_male'),
                'adult_female': request.POST.get('adult_female'),
                'youth_male': request.POST.get('youth_male'),
                'youth_female': request.POST.get('youth_female'),
                'children_male': request.POST.get('children_male'),
                'children_female': request.POST.get('children_female'),
                'campus_male': request.POST.get('campus_male'),
                'campus_female': request.POST.get('campus_female'),
                'cau': request.POST.get('cau'),
                'visitor': request.POST.get('visitor'),
                'conv': request.POST.get('conv'),
                'ypf_male': request.POST.get('ypf_male'),
                'ypf_female': request.POST.get('ypf_female'),
                'zoom': request.POST.get('zoom'),
                'youtube': request.POST.get('youtube'),
                'comment': request.POST.get('comment'),
                'local_church_id': request.POST.get('local_church'),
            }

            # Convert empty numeric fields to 0
            numeric_fields = [
                'adult_male', 'adult_female', 'youth_male', 'youth_female',
                'children_male', 'children_female', 'campus_male', 'campus_female',
                'cau', 'visitor', 'conv','ypf_male','ypf_female','zoom','youtube'
            ]
            for field in numeric_fields:
                if data[field] == '':
                    data[field] = 0
                else:
                    data[field] = int(data[field])

            attendance = Attendance.objects.create(**data)
            messages.success(request, "Attendance created successfully")
            return redirect('attendance_list')
        except Exception as e:
            logger.error(f"An error occurred while creating attendance: {str(e)}")
            messages.error(request, f"Something went wrong: {str(e)}")
            redirect('add_attendance')

    # Prepare the context for rendering the template
    attendance = Attendance()
    if request.user.is_staff or request.user.role == 3:
        local_churches = LocalChurch.objects.all().order_by('local_church_name__title')
    if request.user.role == 2:
        local_churches = LocalChurch.objects.filter(local_church_pastor=request.user).order_by('local_church_name__title')
    if request.user.role == 4:
        local_churches = LocalChurch.objects.filter(region__region_overseer=request.user).order_by('local_church_name__title')
    church_services = available_church_services(local_churches if local_churches else None)

    context = {
        "attendance": attendance,
        "church_services": church_services,
        "local_churches": local_churches,
    }
    return render(request, 'attendance/add.html', context)

# View for editing an existing attendance record
@login_required(login_url='/authentication/login')
def edit_attendance(request, pk):
    # Get the attendance record to edit
    attendance = get_object_or_404(Attendance, pk=pk)

    if request.method == 'POST':
        try:
            # Update the attendance record with the new data
            attendance.church_services = request.POST.get('church_services')
            attendance.date = request.POST.get('date')
            attendance.adult_male = request.POST.get('adult_male')
            attendance.adult_female = request.POST.get('adult_female')
            attendance.youth_male = request.POST.get('youth_male')
            attendance.youth_female = request.POST.get('youth_female')
            attendance.children_male = request.POST.get('children_male')
            attendance.children_female = request.POST.get('children_female')
            attendance.campus_male = request.POST.get('campus_male')
            attendance.campus_female = request.POST.get('campus_female')
            attendance.cau = request.POST.get('cau')
            attendance.visitor = request.POST.get('visitor')
            attendance.conv = request.POST.get('conv')
            attendance.ypf_male = request.POST.get('ypf_male')
            attendance.ypf_female = request.POST.get('ypf_female')
            attendance.zoom = request.POST.get('zoom')
            attendance.youtube = request.POST.get('youtube')
            attendance.comment = request.POST.get('comment')

            attendance.save()
            messages.success(request, "Attendance updated successfully")
            return redirect('attendance_list')
        except Exception as e:
            logger.error(f"An error occurred while updating attendance: {str(e)}")
            messages.error(request, "Something went wrong")
            return redirect('edit_attendance', pk=pk)

    if request.user.is_staff or request.user.role == 3:
        local_churches = LocalChurch.objects.all().order_by('local_church_name__title')
    if request.user.role == 2:
        local_churches = LocalChurch.objects.filter(local_church_pastor=request.user).order_by(
            'local_church_name__title')
    if request.user.role == 4:
        local_churches = LocalChurch.objects.filter(region__region_overseer=request.user).order_by(
            'local_church_name__title')
    church_services = available_church_services(local_churches if local_churches else None)

    return render(request, 'attendance/edit.html', {
        'attendance': attendance,
        'church_services': church_services,
        'local_churches': local_churches
    })


# View for deleting an attendance record
@login_required(login_url='/authentication/login')
def delete_attendance(request, pk):
    # Get the attendance record to delete
    attendance = get_object_or_404(Attendance, pk=pk)
    attendance.deleted = True
    attendance.save()
    messages.success(request, "Attendance deleted successfully")
    return redirect('attendance_list')

# View for listing all church services
@login_required(login_url='/authentication/login')
def church_service_list(request):
    # Get all church services that are not deleted
    church_services = ChurchServices.objects.filter(deleted=False)
    context = {
        "church_services": church_services,
    }
    return render(request, 'attendance/list.html', context)

# View for creating or editing a church service
class ChurchServiceView(View):
    def get(self, request):
        # Prepare the context for rendering the template
        church_service = ChurchServices()
        local_churches = []
        if request.user.is_staff or request.user.role == 3:
            local_churches = LocalChurch.objects.all().order_by('local_church_name__title')
        if request.user.role == 2:
            local_churches = LocalChurch.objects.filter(local_church_pastor=request.user).order_by(
                'local_church_name__title')
        if request.user.role == 4:
            local_churches = LocalChurch.objects.filter(region__region_overseer=request.user).order_by(
                'local_church_name__title')
        html_render = loader.get_template("attendance/church_services-create-edit-form.html")
        html_render = html_render.render({'church_service': church_service, 'local_churches': local_churches, 'request': request})
        return JsonResponse({
            'status': 'success',
            'html_render': html_render
        })

    def post(self, request):
        try:
            # Prepare the data for creating a new church service
            data = {
                'name': request.POST.get('name'),
                'short_name': request.POST.get('short_name'),
                'description': request.POST.get('description'),
                'local_church_id': request.POST.get('local_church'),
            }

            # Create the church service
            ChurchServices.objects.create(**data)

            return JsonResponse({
                'status': 'success',
                'message': 'Church Service created successfully'
            })

        except Exception as e:
            return JsonResponse({
            'status': 'failed',
            'message': 'Something went wrong'
        })

# View for adding a new church service
def church_add(request):
    if request.method == 'POST':
        try:
            # Prepare the data for creating a new church service
            data = {
                'name': request.POST.get('name'),
                'short_name': request.POST.get('short_name'),
                'description': request.POST.get('description'),
                'local_church_id': request.POST.get('local_church'),
            }

            # Create the church service
            ChurchServices.objects.create(**data)
            # messages.success(request, "Church Service created successfully")
            return JsonResponse({
                'status': 'success',
                'message': 'Church Service created successfully'
            })
        except Exception as e:
            logger.error(f"An error occurred while creating the service: {str(e)}")
            messages.error(request, "Something went wrong!")
            return render(request, 'attendance/church-services--modal.html', {'error_message': str(e)})
    church_service = ChurchServices()
    context = {
        "church_service": church_service,
    }
    return render(request, 'attendance/church-services--modal.html', context)


class AttendanceUploaderHelper:
    @staticmethod
    def validate_headers(worksheet):
        # Validate the headers of the worksheet
        headers = [cell.value.strip() if cell.value else None for cell in worksheet[1]]
        return headers == [
            'Church Service', 'Adult Male', 'Adult Female', 'Youth Male', 'Youth Female',
            'Children Male', 'Children Female', 'Campus Male', 'Campus Female', 'Caucasian',
            'Visitor', 'Converts', 'YPF Male', 'YPF Female', 'Zoom', 'YouTube', 'Date', 'Comment'
        ]

    @staticmethod
    def process_and_save(worksheet, local_church_id):
        # Process and save the data from the worksheet
        with transaction.atomic():
            for row_number, row in enumerate(worksheet.iter_rows(min_row=2, values_only=True), start=2):
                church_service_name, adult_male, adult_female, youth_male, youth_female, \
                children_male, children_female, campus_male, campus_female, cau, visitor, \
                conv, ypf_male, ypf_female, zoom, youtube, date, comment = row

                if not church_service_name and not date:
                    continue

                local_church = LocalChurch.objects.get(id=local_church_id)
                church_service = ChurchServices.objects.get(name=church_service_name)

                Attendance.objects.create(
                    church_service=church_service,
                    adult_male=adult_male or 0,
                    adult_female=adult_female or 0,
                    youth_male=youth_male or 0,
                    youth_female=youth_female or 0,
                    children_male=children_male or 0,
                    children_female=children_female or 0,
                    campus_male=campus_male or 0,
                    campus_female=campus_female or 0,
                    cau=cau or 0,
                    visitor=visitor or 0,
                    conv=conv or 0,
                    ypf_male=ypf_male or 0,
                    ypf_female=ypf_female or 0,
                    zoom=zoom or 0,
                    youtube=youtube or 0,
                    date=date,
                    comment=comment or '',
                    local_church=local_church
                )

# View for uploading attendance records from a file
class AttendanceUploadView(View):
    @staticmethod
    def validate_attendance_uploader(file, local_church_id):
        attendance_upload_helper = AttendanceUploaderHelper()
        try:
            workbook = load_workbook(file, read_only=True)
            worksheet = workbook.active

            if not attendance_upload_helper.validate_headers(worksheet):
                return {'error': 'Invalid headers'}

            for row_number, row in enumerate(worksheet.iter_rows(min_row=2, values_only=True), start=2):
                church_service_name, adult_male, adult_female, youth_male, youth_female, \
                children_male, children_female, campus_male, campus_female, cau, visitor, \
                conv, ypf_male, ypf_female, zoom, youtube, date, comment = row

                if not church_service_name and not date:
                    continue

                if date and not validate_date(date):
                    return {'error': f'Invalid date format: "{date}" in Row: {row_number}'}

                if any(v is not None and v < 0 for v in [adult_male, adult_female, youth_male, youth_female,
                                                        children_male, children_female, campus_male, campus_female,
                                                        cau, visitor, conv, ypf_male, ypf_female, zoom, youtube]):
                    return {'error': f'Invalid number format in Row: {row_number}'}

                if not date or not church_service_name:
                    data = 'date' if not date else 'church_service_name'
                    return {'error': f'Required field missing in Row {row_number}. Please provide {data}.'}

            attendance_upload_helper.process_and_save(worksheet, local_church_id)

        except Exception as e:
            return {'error': f'Error processing the file: {str(e)}'}

    def get(self, request):
        # Get the list of local churches based on user role
        local_churches = []
        if request.user.is_staff or request.user.role == 3:
            local_churches = LocalChurch.objects.all().order_by('local_church_name__title')
        if request.user.role == 2:
            local_churches = LocalChurch.objects.filter(local_church_pastor=request.user).order_by('local_church_name__title')
        if request.user.role == 4:
            local_churches = LocalChurch.objects.filter(region__region_overseer=request.user).order_by('local_church_name__title')
        return render(request, 'attendance/attendance_uploader.html', {'local_churches': local_churches})

    def post(self, request):
        errors = self.validate_attendance_uploader(request.FILES['file'], request.POST.get('local_church'))
        if errors:
            local_churches = []
            if request.user.is_staff or request.user.role == 3:
                local_churches = LocalChurch.objects.all().order_by('local_church_name__title')
            if request.user.role == 2:
                local_churches = LocalChurch.objects.filter(local_church_pastor=request.user).order_by(
                    'local_church_name__title')
            if request.user.role == 4:
                local_churches = LocalChurch.objects.filter(region__region_overseer=request.user).order_by(
                    'local_church_name__title')
            return render(request, 'attendance/attendance_uploader.html', {'errors': errors, 'local_churches': local_churches})
        messages.success(request, 'Attendance records uploaded and processed successfully!')
        return redirect('attendance_list')

# View for downloading a sample attendance uploader file
def download_attendance_uploader_sample(request):
    # Create a new workbook and add a worksheet
    workbook = Workbook()
    worksheet = workbook.active

    # Add headers to the worksheet
    headers = [
        'Church Service', 'Adult Male', 'Adult Female', 'Youth Male', 'Youth Female',
        'Children Male', 'Children Female', 'Campus Male', 'Campus Female', 'Caucasian',
        'Visitor', 'Converts', 'YPF Male', 'YPF Female', 'Zoom', 'YouTube', 'Date', 'Comment'
    ]
    worksheet.append(headers)

    header_row = worksheet[1]
    for cell in header_row:
        cell.font = Font(bold=True)

    # Add sample data to the worksheet
    data = [
        ['Sunday Worship Service', 50, 45, 20, 25, 10, 15, 5, 10, 3, 8, 1, 12, 14, 10, 5, '2024-08-01', 'No comment'],
        ['Bible Study', 30, 25, 15, 20, 5, 7, 2, 3, 1, 4, 0, 5, 6, 5, 2, '2024-07-24', 'Good attendance'],
        ['Workers Meeting', 30, 25, 45, 20, 15, 17, 22, 30, 11, 40, 0, 15, 26, 5, 21, '2024-07-24', 'Good attendance']
    ]
    for sample_data in data:
        worksheet.append(sample_data)

    # Set column widths for better readability
    for col_num, column_letter in enumerate(get_column_letter(len(headers)), start=1):
        worksheet.column_dimensions[column_letter].width = 15

    # Create a response object with the XLSX content
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=sample_attendance_uploader_file.xlsx'
    workbook.save(response)

    return response


@login_required(login_url='/authentication/login')
def gck_attendance_list(request):
    region_list = Region.objects.all().order_by('name')
    region_filter = request.GET.get("region")
    church_filter = None
    user = request.user

    current_year = timezone.now().year
    year = request.GET.get("year", current_year)
    event_id = request.GET.get("event")

    try:
        year = int(year)  # Convert to integer
    except ValueError:
        year = current_year

    events = GCKEvent.objects.filter(year_month__startswith=f"{year}-").order_by('-year_month')

    if not event_id and events.exists():
        event_id = events.first().id

    # For role-based filtering
    if user.role in [2, 4]:
        region_filter = user.local_church.region.name
        if user.role == 2:
            church_filter = user

    # Fetch the selected event
    event = None
    can_download = False
    event_name = "No GCK Events Found"

    if event_id:
        try:
            event = GCKEvent.objects.get(id=event_id)
            event_name = event.name
            can_download = True
        except GCKEvent.DoesNotExist:
            event = None

    # Prepare the data
    data = prepare_gck_attendance_context_data(event=event, region=region_filter, pastor=church_filter)

    # Handle downloads
    if request.GET.get("download") == "1" and event:
        return export_table_to_csv(data, event_name, event.year_month.strftime('%Y-%m'))

    if request.GET.get("download") == "2" and event:
        logo_url = f"{request.scheme}://{request.get_host()}/static/img/logo.png"
        context = {
            "data": data,
            "region_list": region_list,
            "selected_event": event,
            "selected_region": region_filter,
            "event_name": event_name,
            "logo_url": logo_url,
        }
        response = PDFTemplateResponse(
            request=request,
            template='attendance/gck_attendance_pdf.html',
            context=context,
            filename=f"GCK_attendance_report_{event_name}.pdf",
            show_content_in_browser=False,
        )
        return response

    years = [current_year - i for i in range(5, -1, -1)]  # Last 5 years + current year

    # Normal render
    context = {
        "data": data,
        "region_list": region_list,
        "events": events,
        "selected_event_id": int(event_id) if event_id else None,
        "selected_region": region_filter,
        "event_name": event_name,
        "selected_year": year,
        "years": years,
        "can_download": can_download,
    }
    return render(request, 'attendance/gck_attendance_list.html', context)


class GCKAttendanceCreateView(LoginRequiredMixin, View):
    """View to handle creating a new GCKAttendance record."""
    template_name = "attendance/gck_attendance_add.html"
    login_url = '/authentication/login'
    redirect_field_name = 'next'

    def get(self, request):
        """Render the GCKAttendance form."""
        form = GCKAttendanceForm(user=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        """Handle form submission."""
        form = GCKAttendanceForm(request.POST, user=request.user)

        if form.is_valid():
            try:
                attendance = form.save()
                messages.success(request, f"Attendance for {attendance.day.name} successfully added!")
                return redirect('gck_attendance_list')
            except Exception as e:
                print(str(e))  # Log the error for debugging
                messages.error(request, "Something went wrong.")
                return redirect('gck_attendance_add')

        messages.error(request, "Please correct the errors below.")
        return render(request, self.template_name, {'form': form})


class GCKAttendanceEditView(LoginRequiredMixin, View):
    """View to handle Edit GCKAttendance record."""
    template_name = "attendance/gck_attendance_edit.html"
    login_url = '/authentication/login'
    redirect_field_name = 'next'

    def get(self, request, pk):
        """Render the GCKAttendance form."""
        form = EditGCKAttendanceForm(user=request.user, attendance_id=pk)
        return render(request, self.template_name, {'form': form, "pk": pk})

    def post(self, request, pk):
        """Handle form submission."""
        form = EditGCKAttendanceForm(data=request.POST, user=request.user, attendance_id=pk)

        if form.is_valid():
            try:
                attendance = form.save()
                messages.success(request, f"GCK Attendance for {attendance.day.name} successfully updated!")
                return redirect('gck_attendance_list')
            except Exception as e:
                print(str(e))  # Log the error for debugging
                messages.error(request, "Something went wrong.")
                return redirect('edit_gck_attendance', pk=pk)

        messages.error(request, "Please correct the errors below.")
        return render(request, self.template_name, {'form': form, "pk": pk})


@login_required(login_url='/authentication/login')
def delete_gck_attendance(request, pk):
    # Get the attendance record to delete
    attendance = get_object_or_404(GCKAttendance, pk=pk, is_workers=False)
    attendance.delete()
    messages.success(request, "GCK Attendance deleted successfully")
    return redirect('gck_attendance_list')


def gck_converts_follow_up_table(request):
    month_filter = request.GET.get("month", None)
    church_filter = request.GET.get("local_church", None)
    local_churches = get_user_local_church(request.user)

    # Get the current month in "YYYY-MM" format
    current_month = timezone.now().strftime("%Y-%m")
    current_month = month_filter or current_month

    if request.method == "POST":
        try:
            data = json.loads(request.body)

            if data.get("action") == "create":
                # add date as the month and year from current month
                date = timezone.datetime.strptime(data.get("month"), "%Y-%m")
                GCKConvertsFollowUpReport.objects.create(
                    local_church_id=data.get("local_church"),
                    month=data.get("month"),
                    date=date,
                )
            elif data.get("action") == "delete":
                converts_details = get_object_or_404(GCKConvertsFollowUpReport, pk=data.get("id"))
                converts_details.delete()
            elif data.get("action") == "update":
                # Extracting values for the update action
                field_name = data.get("field_name")
                updated_value = data.get("updated_value")
                record_id = data.get("id")

                # Fetch the record that needs to be updated
                report = get_object_or_404(GCKConvertsFollowUpReport, pk=record_id)

                # Dynamically update the appropriate field based on field_name
                if hasattr(report, field_name):  # Ensure the field exists on the model
                    if field_name == "date":  # Special handling for date fields
                        from datetime import datetime
                        updated_value = datetime.strptime(updated_value, "%Y-%m-%d")
                    setattr(report, field_name, updated_value)
                    report.save()  # Save the changes
                    return redirect('gck_converts_follow_up')
                else:
                    # Handle cases where the field_name is invalid
                    return JsonResponse({"status": "error", "message": f"Field '{field_name}' does not exist."},
                                        status=400)
            return redirect('gck_converts_follow_up')
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON data"})

    # Get all reports, filtered by the current month and church-filter
    user = request.user
    reports = GCKConvertsFollowUpReport.objects.filter(month=str(current_month)).order_by("-created_date")
    if user.role == 2:
        church_filter = user.local_church.id
        reports = reports.filter(local_church_pastor=user)

    elif user.role == 4:
        reports = reports.filter(local_church__region=user.local_church.region)

    if church_filter:
        reports = reports.filter(local_church_id=int(church_filter))

    # Get all months for display
    months = [
        {"value": f"{timezone.now().year}-{i:02d}", "name": calendar.month_name[i]}
        for i in range(1, 13)
    ]

    context = {
        "reports": reports,
        "months": months,
        "current_month": current_month,
        "selected_church": int(church_filter) if church_filter else church_filter,
        "local_churches": local_churches
    }

    return render(request, "attendance/gck_converts_follow_up.html", context)


def gck_projections(request):
    region_list = Region.objects.all().order_by('name')
    user = request.user

    region_filter = request.GET.get("region", None)
    month_filter = request.GET.get("month", None)

    # Get the current month in "YYYY-MM" format
    current_month = timezone.now().strftime("%Y-%m")
    current_month = month_filter or current_month

    if request.method == "POST":
        try:
            data = json.loads(request.body)

            if data.get("action") == "projections":
                # Extracting values for the update action
                field_name = data.get("field_name")
                updated_value = data.get("updated_value")
                region_id = data.get("id")
                month = data.get("month")

                projection, created = GCKProjections.objects.get_or_create(region_id=int(region_id), month=str(month))

                if hasattr(projection, field_name):  # Ensure the field exists on the model
                    if field_name == "date":  # Special handling for date fields
                        from datetime import datetime
                        updated_value = datetime.strptime(updated_value, "%Y-%m-%d")
                    setattr(projection, field_name, updated_value)
                    projection.save()  # Save the changes
                    return redirect('gck_projections')

        except Exception as e:
            print(str(e))
            return JsonResponse({"success": False, "error": "Invalid JSON data"})

    # Get all projections, filtered by the current month and region-filter
    user = request.user
    projections = GCKProjections.objects.filter(month=str(current_month)).order_by("-created_date")

    if user.role == 4:
        region_list = region_list.filter(id=user.local_church.region.id)
        projections = projections.filter(region__in=region_list)

    else:
        if region_filter:
            projections = projections.filter(region_id=int(region_filter))

    final_data = []
    for region in region_list if not region_filter else region_list.filter(id=int(region_filter)):
        projection = projections.filter(region=region).first()  # Returns None if not found

        if projection:
            data = {
                "region": region,
                "att_by_weeks": projection.att_by_weeks,
                "att_target_for_month": projection.att_target_for_month,
                "att_sunday_crusade": projection.att_sunday_crusade,
            }
        else:
            data = {
                "region": region,
                "att_by_weeks": "",
                "att_target_for_month": "",
                "att_sunday_crusade": "",
            }
        final_data.append(data)

    context = {
        "projections": final_data,
        "region_list": region_list,
        "months": get_all_months(),
        "current_month": month_filter or current_month,
        "selected_region": int(region_filter) if region_filter else region_filter,
        "year": current_month.split("-")[0]
    }

    return render(request, "attendance/gck_projections.html", context)


@login_required(login_url='/authentication/login')
def gck_ministers_workers_list(request):
    region_list = Region.objects.all().order_by('name')
    user = request.user

    region_filter = request.GET.get("region", None)
    month_filter = request.GET.get("month", None)
    church_filter = None
    # Get filters from request parameters
    if user.role == 4 or user.role == 2:
        region_filter = user.local_church.region.name
        if user.role == 2:
            church_filter = user

    # Prepare the data using the filters
    data = prepare_gck_workers_attendance_context_data(region=region_filter,
                                                        month=month_filter,
                                                        pastor=church_filter,
                                                        is_workers=True)

    # Get all months for display
    months = [
        {"value": f"{datetime.now().year}-{i:02d}", "name": calendar.month_name[i]}
        for i in range(1, 13)
    ]

    # Get the current month in "YYYY-MM" format
    current_month = datetime.now().strftime("%Y-%m")

    context = {
        "data": data,
        "region_list": region_list,
        "months": months,
        "current_month": month_filter or current_month,
        "selected_region": region_filter,
    }

    return render(request, 'attendance/gck_ministers_workers_list.html', context)


class GCKWorkersAttendanceCreateView(LoginRequiredMixin, View):
    """View to handle creating a new GCKAttendance record."""
    template_name = "attendance/gck_workers_attendance_add.html"
    login_url = '/authentication/login'
    redirect_field_name = 'next'

    def get(self, request):
        """Render the GCKAttendance form."""
        form = GCKWorkersAttendanceForm(user=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        """Handle form submission."""
        form = GCKWorkersAttendanceForm(request.POST, user=request.user)

        if form.is_valid():
            try:
                attendance = form.save()
                messages.success(request, f"Gck workers attendance for {attendance.day.name} successfully added!")
                return redirect('gck_ministers_workers_list')
            except Exception as e:
                print(str(e))  # Log the error for debugging
                messages.error(request, "Something went wrong.")
                return redirect('gck_workers_attendance_add')

        messages.error(request, "Please correct the errors below.")
        return render(request, self.template_name, {'form': form})


class GCKWorkersAttendanceEditView(LoginRequiredMixin, View):
    """View to handle Edit GCKAttendance record."""
    template_name = "attendance/gck_workers_attendance_edit.html"
    login_url = '/authentication/login'
    redirect_field_name = 'next'

    def get(self, request, pk):
        """Render the GCKAttendance form."""
        form = EditGCKWorkersAttendanceForm(user=request.user, attendance_id=pk)
        return render(request, self.template_name, {'form': form, "pk": pk})

    def post(self, request, pk):
        """Handle form submission."""
        form = EditGCKWorkersAttendanceForm(data=request.POST, user=request.user, attendance_id=pk)

        if form.is_valid():
            try:
                attendance = form.save()
                messages.success(request, f"GCK Workers attendance for {attendance.day.name} successfully updated!")
                return redirect('gck_ministers_workers_list')
            except Exception as e:
                print(str(e))  # Log the error for debugging
                messages.error(request, "Something went wrong.")
                return redirect('edit_gck_workers_attendance', pk=pk)

        messages.error(request, "Please correct the errors below.")
        return render(request, self.template_name, {'form': form, "pk": pk})


@login_required(login_url='/authentication/login')
def delete_gck_workers_attendance(request, pk):
    # Get the attendance record to delete
    attendance = get_object_or_404(GCKAttendance, pk=pk, is_workers=True)
    attendance.delete()
    messages.success(request, "GCK Workers Attendance deleted successfully")
    return redirect('gck_ministers_workers_list')


class GCKEventListView(ListView):
    model = GCKEvent
    template_name = "events/gckevent_list.html"
    context_object_name = "events"
    ordering = ["-year_month"]


class GCKEventCreateView(CreateView):
    model = GCKEvent
    form_class = GCKEventForm
    template_name = "attendance/gckevent_form.html"
    success_url = reverse_lazy("event_list")


class GCKEventUpdateView(UpdateView):
    model = GCKEvent
    form_class = GCKEventForm
    template_name = "attendance/gckevent_form.html"
    success_url = reverse_lazy("event_list")


def delete_gckevent(request, event_id):
    try:
        event = GCKEvent.objects.get(id=event_id)
        event.delete()
        return JsonResponse({'message': 'GCK Event deleted successfully', "ok": True}, status=200)
    except GCKEvent.DoesNotExist:
        return JsonResponse({'message': 'Event not found'}, status=404)


def export_table_to_csv(data, event_name, date):
    headers = [
        "Location", "Day", "Date", "Adult", "Young Prof", "Campus", "Youths", "Children", "Total", "Remarks",
        "Zoom", "YouTube", "Virtual Total", "FB Reached", "FB Likes", "FB Comments",
        "IG Reached", "IG Engagement", "Converts"
    ]

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="GCK_attendance_report_{date}.csv"'

    writer = csv.writer(response)
    writer.writerow([f"GCK Attendance Report: {event_name} - {date}"])
    writer.writerow(headers)

    for region in data:
        for church in region["churches"]:
            if church["days"]:
                for day in church["days"]:
                    writer.writerow([
                        church["name"], day["day"], day["date"], day["adult"], day["young_prf"],
                        day["campus"], day["youths"], day["children"],
                        day["adult"] + day["young_prf"] + day["campus"] + day["youths"] + day["children"],
                        day["remarks"], day["zoom"], day["youtube"],
                        day["zoom"] + day["youtube"], day["fb_reached"],
                        day["fb_likes"], day["fb_comments"], day["ig_reached"],
                        day["ig_engagement"], day["converts"]
                    ])
            else:
                writer.writerow([church["name"], "No records for the selected month"] + ["-"] * 17)

            # Add church total row
            writer.writerow([
                church["name"] + " Total", "-", "-", church["total"]["adult"], church["total"]["young_prf"],
                church["total"]["campus"], church["total"]["youths"], church["total"]["children"],
                church["total"]["adult"] + church["total"]["young_prf"] + church["total"]["campus"] +
                church["total"]["youths"] + church["total"]["children"], "-", church["total"]["zoom"],
                church["total"]["youtube"], church["total"]["zoom"] + church["total"]["youtube"],
                church["total"]["fb_reached"], church["total"]["fb_likes"], church["total"]["fb_comments"],
                church["total"]["ig_reached"], church["total"]["ig_engagement"], church["total"]["converts"]
            ])

            # Add a blank row after each church
            writer.writerow([])

        # Add region total row
        writer.writerow([
            region["name"] + " Total", "-", "-", region["total"]["adult"], region["total"]["young_prf"],
            region["total"]["campus"], region["total"]["youths"], region["total"]["children"],
            region["total"]["adult"] + region["total"]["young_prf"] + region["total"]["campus"] +
            region["total"]["youths"] + region["total"]["children"], "-", region["total"]["zoom"],
            region["total"]["youtube"], region["total"]["zoom"] + region["total"]["youtube"],
            region["total"]["fb_reached"], region["total"]["fb_likes"], region["total"]["fb_comments"],
            region["total"]["ig_reached"], region["total"]["ig_engagement"], region["total"]["converts"]
        ])

        # Add two blank rows after each region
        writer.writerow([])
        writer.writerow([])

    return response

