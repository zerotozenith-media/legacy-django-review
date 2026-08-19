# Import necessary modules and classes
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import JsonResponse
import json
from django.contrib import messages
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.http import HttpResponse
from church_properties.models import ChurchProperties
from contributor.helper import validate_date, check_amount
from organization.models import LocalChurch
from django.views.generic import ListView
import re
from django.db import transaction
from organization.utils import get_user_local_church
from utils.helpers import get_user_regions, get_filtered_context


# Helper class for property uploader
class PropertyUploaderHelper:
    @staticmethod
    def validate_headers(worksheet):
        # Validate the headers of the worksheet
        headers = [cell.value.strip() if cell.value else None for cell in worksheet[1]]
        return headers == ['Name', 'Purchase Date', 'Description', 'Serial No.', 'Amount Paid (Inc. Tax)', 'Disposal Date', 'Mode of Disposal', 'Amount Sold']

    @staticmethod
    def validate_email(email):
        # Validate the email format using regex
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_regex, email) is not None

    @staticmethod
    def process_and_save(worksheet, local_church_id):
        # Process and save the data from the worksheet
        with transaction.atomic():
            for row_number, row in enumerate(worksheet.iter_rows(min_row=2, values_only=True, max_row=8), start=2):
                print(row_number, row, "this")
                name, purchase_date, description, serial_no, amount_paid, disposal_date, mode_of_disposal, amount_sold = row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]

                if not name and not purchase_date and not amount_paid:
                    continue

                data = {
                    "local_church": LocalChurch.objects.get(id=local_church_id),
                    "name": name,
                    "purchase_date": purchase_date,
                    "description": description,
                    "serial_no": serial_no,
                    "amount_paid": amount_paid,
                    "disposal_date": disposal_date or None,
                    "mode_of_disposal": mode_of_disposal,
                    "amount_sold": amount_sold,
                }

                ChurchProperties.objects.create(**data)


# View for adding a new property
class PropertyAddView(View):
    def get(self, request):
        # Get the list of local churches based on user role
        local_churches = []
        if request.user.is_staff or request.user.role == 3:
            local_churches = LocalChurch.objects.all().order_by('local_church_name__title')
        if request.user.role == 2:
            local_churches = LocalChurch.objects.filter(local_church_pastor=request.user).order_by('local_church_name__title')
        if request.user.role == 4:
            local_churches = LocalChurch.objects.filter(region__region_overseer=request.user).order_by('local_church_name__title')

        return render(request, 'church_properties/add_properties.html', {'local_churches': local_churches})

    def post(self, request):
        try:
            with transaction.atomic():
                request_data = request.POST

                # Convert amount_sold and amount_paid to None if they are empty strings
                amount_sold = request_data.get('amount_sold') if request_data.get('amount_sold') != '' else None
                amount_paid = request_data.get('amount_paid') if request_data.get('amount_paid') != '' else None

                # Ensure required fields are present
                # required_fields = ['local_church', 'name', 'purchase_date', 'description', 'serial_no']
                # if not all(field in request_data for field in required_fields):
                #     raise ValueError("Required fields are missing")

                # Convert purchase_date and disposal_date to datetime objects
                # purchase_date = datetime.datetime.strptime(request_data.get('purchase_date'), '%Y-%m-%d').date()
                # disposal_date = datetime.datetime.strptime(request_data.get('disposal_date'), '%Y-%m-%d').date() if request_data.get('disposal_date') else None

                # Create the ChurchProperties object
                disposal_date = request_data.get('disposal_date', None)

                data = {
                    "local_church": LocalChurch.objects.get(id=request_data.get('local_church')),
                    "name": request_data.get('name'),
                    "purchase_date": request_data.get('purchase_date'),
                    "description": request_data.get('description'),
                    "serial_no": request_data.get('serial_no'),
                    "amount_paid": amount_paid,
                    "disposal_date": disposal_date or None,
                    "mode_of_disposal": request_data.get('mode_of_disposal'),
                    "amount_sold": amount_sold,
                }
                ChurchProperties.objects.create(**data)
                messages.success(request, 'Property Added Successfully')
                return redirect('church_properties_list')
        except Exception as e:
            print(e)
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('add-property')
        
# View for updating a property
class PropertyEditView(View):
    def get(self, request, id, *args, **kwargs):
        # Retrieve the church property by ID
        church_property = get_object_or_404(ChurchProperties, id=id)
        local_churches = []

        # Get local churches based on user role
        if request.user.is_staff or request.user.role == 3:
            local_churches = LocalChurch.objects.all().order_by('local_church_name__title')
        elif request.user.role == 2:
            local_churches = LocalChurch.objects.filter(local_church_pastor=request.user).order_by('local_church_name__title')
        elif request.user.role == 4:
            local_churches = LocalChurch.objects.filter(region__region_overseer=request.user).order_by('local_church_name__title')

        context = {
            'church_property': church_property,
            'local_churches': local_churches,
        }
        return render(request, 'church_properties/edit_properties.html', context)

    def post(self, request, id, *args, **kwargs):
        try:
            with transaction.atomic():
                church_property = get_object_or_404(ChurchProperties, id=id)
                request_data = request.POST

                # Convert optional fields
                amount_sold = request_data.get('amount_sold') if request_data.get('amount_sold') != '' else None
                amount_paid = request_data.get('amount_paid') if request_data.get('amount_paid') != '' else None
                disposal_date = request_data.get('disposal_date', None)

                # Update fields
                church_property.local_church = LocalChurch.objects.get(id=request_data.get('local_church'))
                church_property.name = request_data.get('name')
                church_property.purchase_date = request_data.get('purchase_date')
                church_property.description = request_data.get('description')
                church_property.serial_no = request_data.get('serial_no')
                church_property.amount_paid = amount_paid
                church_property.disposal_date = disposal_date or None
                church_property.mode_of_disposal = request_data.get('mode_of_disposal')
                church_property.amount_sold = amount_sold

                church_property.save()
                messages.success(request, 'Property updated successfully')
                return redirect('church_properties_list')
        except Exception as e:
            print(e)
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('edit-property', id=id)
        
# View for deleting a property
def delete_property(request, id):
    transfer = ChurchProperties.objects.get(pk=id)
    transfer.delete()
    messages.success(request, "Record was removed")
    return redirect("church_properties_list")


# View for listing properties
class PropertiesListView(LoginRequiredMixin, ListView):
    template_name = 'church_properties/property_list.html'
    context_object_name = 'properties'

    def __init__(self):
        super().__init__()
        self.filter_context = None

    def get_queryset(self):
        user = self.request.user
        queryset = ChurchProperties.objects.all()

        # Filter donations by user's accessible local churches
        local_churches = get_user_local_church(user)
        region = self.request.GET.get("region", None)
        regions = get_user_regions(user)

        if region:
            region_list = regions.filter(name__iexact=region)
            local_churches = local_churches.filter(region__in=region_list)

        queryset = queryset.filter(local_church__in=local_churches)

        # Use get_filtered_context to apply additional filters
        queryset, self.filter_context = get_filtered_context(
            self.request,
            queryset,
            model_field_map={
                "region": "local_church__region__name",
                "local_church": "local_church_id"
            }
        )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        local_churches = get_user_local_church(user)

        region = self.request.GET.get("region", None)
        regions = get_user_regions(user)

        if region:
            region_list = regions.filter(name__iexact=region)
            local_churches = local_churches.filter(region__in=region_list)

        context.update({
            "regions": regions,
            "churches": local_churches,
            **getattr(self, 'filter_context', {})
        })

        return context

# View for uploading properties from a file
class PropertyUploadView(View):

    @staticmethod
    def validate_property_uploader(file, local_church_id):
        property_upload_helper = PropertyUploaderHelper()
        try:
            workbook = load_workbook(file, read_only=True)
            worksheet = workbook.active

            if not property_upload_helper.validate_headers(worksheet):
                return {'error': 'Invalid headers'}

            for row_number, row in enumerate(worksheet.iter_rows(min_row=2, values_only=True, max_row=8), start=2):
                print(row_number, row, row[0])
                if row[0]:
                    name, purchase_date, description, serial_no, amount_paid, disposal_date, mode_of_disposal, amount_sold = row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]

                    if not name and not purchase_date and not amount_paid:
                        continue

                    if purchase_date and not validate_date(purchase_date):
                        return {'error': f'Invalid date format: "{purchase_date}" in Row: {row_number}'}

                    if disposal_date and not validate_date(disposal_date):
                        return {'error': f'Invalid date format: "{disposal_date}" in Row: {row_number}'}

                    if amount_paid and not check_amount(amount_paid):
                        return {'error': f'Invalid amount format: "{amount_paid}" in Row: {row_number}'}

                    if amount_sold and not check_amount(amount_sold):
                        return {'error': f'Invalid amount format: "{amount_sold}" in Row: {row_number}'}

                    if not purchase_date or not amount_paid:
                        data = 'purchase_date' if not purchase_date else 'amount_paid'
                        return {'error': f'Required field missing in Row {row_number}. Please provide {data}.'}

            property_upload_helper.process_and_save(worksheet, local_church_id)

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
        return render(request, 'church_properties/property_uploader.html', {'local_churches': local_churches})

    def post(self, request):
        errors = self.validate_property_uploader(request.FILES['file'], request.POST.get('local_church'))
        print(errors)
        if errors:
            local_church = LocalChurch.objects.all()
            return render(request, 'church_properties/property_uploader.html', {'errors': errors, 'local_churches': local_church})
        messages.success(request, 'Properties uploaded and processed successfully!')
        return redirect('church_properties_list')

# View for downloading a sample property uploader file
def download_property_uploader_sample(request):
    # Create a new workbook and add a worksheet
    workbook = Workbook()
    worksheet = workbook.active

    # Add headers to the worksheet
    headers = ['Name', 'Purchase Date', 'Description', 'Serial No.', 'Amount Paid (Inc. Tax)', 'Disposal Date', 'Mode of Disposal', 'Amount Sold']
    worksheet.append(headers)

    header_row = worksheet[1]
    for cell in header_row:
        cell.font = Font(bold=True)
    data = [
        ['Chair', '2023-12-20', 'Bought for receptionist', 'Chur-002', '50', '2024-01-31', 'Selling', '20'],
        ['Table', '2018-07-12', 'Bought for office', 'Tbul-003', '75', '2024-01-28', 'Selling', '30'],
        ['Chair', '2023-10-21', 'Bought for hall room', 'Chur-003', '55', '2024-02-22', 'Selling', '25'],
        ['Chair', '2022-02-17', 'Bought for Father', 'Chur-004', '70', '2024-02-21', 'Selling', '32'],
    ]
    for sample_data in data:
        worksheet.append(sample_data)

    # Set column widths for better readability
    for col_num, column_letter in enumerate(get_column_letter(len(headers)), start=1):
        worksheet.column_dimensions[column_letter].width = 15

    # Create a response object with the XLSX content
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=sample_property_uploader_file.xlsx'
    workbook.save(response)

    return response

# Function to get the count of properties
def get_property_count():
    prop_count = ChurchProperties.objects.filter(deleted=False).count()
    return prop_count
