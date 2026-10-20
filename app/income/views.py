# Import necessary modules and classes
import logging
from datetime import datetime
import re
from django.db import transaction
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font
from authentication.middleware import Role
from organization.models import BankAccount, LocalChurch, Region
from organization.utils import get_user_local_church
from utils.helpers import get_user_regions, get_filtered_context
from .forms import DonationInKindForm
from .models import Source, Income, DonationInKind
from .selectors import looks_like_contribution_source, selectable_sources
from django.core.paginator import Paginator
from django.template import loader
from django.views import View
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import json
from django.http import JsonResponse, HttpResponse
from openpyxl import load_workbook, Workbook
from contributor.helper import validate_date, check_amount

logger = logging.getLogger(__name__)

# Function to calculate the total income for the current month
def current_month_income(user=None, region=None, local_church=None):
    current_year = datetime.now().year
    current_month = datetime.now().month
    # Filter incomes for the current month and year
    total_income_current_month = Income.objects.filter(
        date__month=current_month, date__year=current_year
    )
    if region:
        total_income_current_month = total_income_current_month.filter(local_church__region_id=region)
    if local_church:
        total_income_current_month = total_income_current_month.filter(local_church_id=local_church)
    # Aggregate the total amount
    total_income_current_month = total_income_current_month.aggregate(total=Sum('amount'))['total'] or 0.0
    return total_income_current_month

# Function to calculate the total income for the current year
def current_year_income(user=None, region=None, local_church=None):
    current_year = datetime.now().year
    # Filter incomes for the current year
    total_income_current_year = Income.objects.filter(
        date__year=current_year
    )
    if region:
        total_income_current_year = total_income_current_year.filter(local_church__region_id=region)
    if local_church:
        total_income_current_year = total_income_current_year.filter(local_church_id=local_church)
    # Aggregate the total amount
    total_income_current_year = total_income_current_year.aggregate(total=Sum('amount'))['total'] or 0.0
    return total_income_current_year

# Function to search incomes based on the search string
def search_income(request):
    if request.method == "POST":
        search_str = json.loads(request.body).get("searchText")
        # Filter incomes based on the search string
        income = (
            Income.objects.filter(amount__istartswith=search_str, owner=request.user)
            | Income.objects.filter(date__istartswith=search_str, owner=request.user)
            | Income.objects.filter(description__icontains=search_str, owner=request.user)
            | Income.objects.filter(source__icontains=search_str, owner=request.user)
        )
        data = income.values()
        return JsonResponse(list(data), safe=False)

# View to display the list of incomes
@login_required(login_url="/authentication/login")
def index(request):
    start_date = request.GET.get('start_date', None)
    end_date = request.GET.get('end_date', None)

    user = request.user
    local_churches = get_user_local_church(user)
    region_income = Income.objects.filter(region__isnull=False)

    region = request.GET.get("region", None)
    regions = get_user_regions(user)

    if region:
        region_list = regions.filter(name__iexact=region)
        local_churches = local_churches.filter(region__in=region_list)

    if user.role == 4:
        # Assuming user.region is a string representing the region name
        try:
            region_obj = Region.objects.get(id=user.local_church.region.id)
            region_income = region_income.filter(region=region_obj)
        except Region.DoesNotExist:
            logger.error(f"Region does not exist for user.")
            messages.error(request, "Your region is not configured properly.")
            return redirect('income')

    # Filter incomes based on the date range
    # if start_date and end_date:
    #     if isinstance(start_date, str):
    #         start_date = datetime.strptime(start_date, "%d-%m-%Y").date()
    #     if isinstance(end_date, str):
    #         end_date = datetime.strptime(end_date, "%d-%m-%Y").date()
    #     income = income.filter(date__range=[start_date, end_date], deleted=False)
    # else:
    #     income = income

    # income_this_month = current_month_income(user=request.user)
    # income_this_year = current_year_income(user=request.user)
    income = Income.objects.filter(local_church__in=local_churches)
    income, filter_context = get_filtered_context(
        request,
        income,
        model_field_map={
            "region": "local_church__region__name",
            "local_church": "local_church_id"
        }
    )

    context = {
        "income": income,
        "region_income": region_income,
        "page_obj": income,
        # "current_month_income": income_this_month,
        # "current_year_income": income_this_year,
        "regions": regions,
        "churches": local_churches,
        **filter_context
    }
    return render(request, "income/index.html", context)

# View to add a new income
@login_required(login_url="/authentication/login")
def add_income(request):
    sources = selectable_sources()
    accounts = BankAccount.objects.all()
    user = request.user
    local_churches = get_user_local_church(user)
    context = {
        "sources": sources,
        "local_churches": local_churches,
        "accounts": accounts,
        "values": request.POST,
        "current_user": int(request.user.id)
    }
    if request.method == "GET":
        return render(request, "income/add_income.html", context)

    if request.method == "POST":
        local_church = request.POST.get("local_church")
        account = request.POST.get("account")
        amount = request.POST.get("amount")
        description = request.POST.get("description")
        date = request.POST.get("income_date")
        source = request.POST.get("source")

        # Validate the form data
        if not local_church:
            messages.error(request, "Income Church required")
            return render(request, "income/add_income.html", context)

        if not amount:
            messages.error(request, "Amount is required")
            return render(request, "income/add_income.html", context)

        if not description:
            messages.error(request, "Description is required")
            return render(request, "income/add_income.html", context)

        if not date:
            messages.error(request, "Date is required")
            return render(request, "income/add_income.html", context)

        if not source:
            messages.error(request, "Source is required")
            return render(request, "income/add_income.html", context)

        try:
            # Create the income
            Income.objects.create(
                local_church_id=local_church,
                account_id=account,
                amount=amount,
                date=date,
                source_id=source,
                description=description,
            )
            messages.success(request, "Income saved successfully")
            return redirect("income")

        except Exception as e:
            print(f"Error saving income: {e}")
        messages.error(request, "An unexpected error")
        return render(request, "income/add_income.html", context)


@login_required(login_url="/authentication/login")
def income_edit(request, id):
    income = Income.objects.get(pk=id)
    sources = selectable_sources(current_source_id=income.source_id)
    user = request.user
    local_churches = get_user_local_church(user)
    context = {"income": income, "values": income, "sources": sources, "local_churches": local_churches}

    if request.method == "GET":
        return render(request, "income/edit_income.html", context)
    if request.method == "POST":
        local_church = request.POST.get("local_church")
        amount = request.POST.get("amount")
        description = request.POST.get("description")
        date = request.POST.get("income_date")
        source = request.POST.get("source")

        # Validate the form data
        if not amount:
            messages.error(request, "Amount is required")
            return render(request, "income/edit_income.html", context)

        if not description:
            messages.error(request, "Description is required")
            return render(request, "income/edit_income.html", context)

        try:
            date_object = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            # Handle invalid date
            messages.error(request, "Please enter a valid date in the format YYYY-MM-DD.")
            return render(request, "income/edit_income.html", context)

        # Update the income
        income.amount = amount
        income.description = description
        income.date = date_object
        income.source_id = source
        income.local_church_id = local_church
        income.save()
        messages.success(request, "Record updated successfully")

        return redirect("income")


def delete_income(request, id):
    income = Income.objects.get(pk=id)
    income.delete()
    messages.success(request, "Record was removed")
    return redirect("income")


class SourceListView(LoginRequiredMixin, ListView):
    model = Source
    template_name = 'source_list.html'
    context_object_name = 'sources'

    def get_queryset(self):
        return Source.objects.select_related('entry_by').order_by('id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        types = [
            {
                "id": "Income",
                "name": "Income"
            },
            {
                "id": "Expense",
                "name": "Expense"
            },
        ]
        context['current_user'] = self.request.user.id
        context['types'] = types
        return context

# View to create or edit a source
class SourceView(View):
    def get(self, request):
        types = [
            {
                "id": "Income",
                "name": "Income"
            },
            {
                "id": "Expense",
                "name": "Expense"
            },
        ]
        html_render = loader.get_template("income/components/source-create-edit-form.html")
        html_render = html_render.render({'types': types})
        return JsonResponse({
            'status': 'success',
            'html_render': html_render
        })

    def post(self, request):
        try:
            name = request.POST.get('name')
            description = request.POST.get('description')
            source = {
                'name': name,
                'type': 'Income',
                'description': description,
                'entry_by': request.user,
                # A source named for tithe, offering or special contribution
                # money is flagged on creation. That money is recorded on the
                # Contributions screens and summed from there by the financial
                # report, so Income rows against it would be counted twice.
                # An administrator can untick this if the name is misleading.
                'counted_via_contributions': looks_like_contribution_source(name),
            }
            Source.objects.create(**source)
            return JsonResponse({
                'status': 'success',
                'message': 'Source created successfully'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'failed',
                'message': 'Something went wrong'
            })

# View to delete or edit a source
class SourceEditDeleteView(View):
    def get(self, request, id):
        try:
            Source.objects.get(id=id).delete()
            return JsonResponse({
                'status': 'success',
                'message': 'Deleted successfully'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'failed',
                'message': 'Something went wrong'
            })

    def post(self, request, id):
        try:
            source = Source.objects.get(id=id)
            data = request.POST
            source.name = data['name']
            source.description = data['description']
            source.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Updated successfully'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'failed',
                'message': 'Something went wrong'
            })

# Helper class for income uploader
class IncomeUploaderHelper:
    @staticmethod
    def validate_headers(worksheet):
        headers = [cell.value.strip() if cell.value else None for cell in worksheet[1]]
        return headers == ['Amount', 'Description', 'Date', 'Source']

    @staticmethod
    def process_and_save(worksheet, local_church_id):
        with transaction.atomic():
            for row_number, row in enumerate(worksheet.iter_rows(min_row=2, values_only=True, max_row=8), start=2):
                amount, description, date, source_name = row[0], row[1], row[2], row[3]

                if not amount and not description and not date and not source_name:
                    continue

                local_church = LocalChurch.objects.get(id=local_church_id)
                source = Source.objects.filter(name=source_name).first()
                if not source:
                    source = None

                # Create the income
                Income.objects.create(
                    local_church=local_church,
                    amount=amount,
                    description=description,
                    date=date,
                    source=source,
                )

# View for uploading incomes from a file
class IncomeUploadView(View):
    @staticmethod
    def validate_income_uploader(file, local_church_id):
        income_upload_helper = IncomeUploaderHelper()
        try:
            workbook = load_workbook(file, read_only=True)
            worksheet = workbook.active

            # Validate the headers of the worksheet
            if not income_upload_helper.validate_headers(worksheet):
                return {'error': 'Invalid headers'}

            for row_number, row in enumerate(worksheet.iter_rows(min_row=2, values_only=True, max_row=8), start=2):
                amount, description, date, source_name = row[0], row[1], row[2], row[3]

                if not amount and not description and not date and not source_name:
                    continue

                if date and not validate_date(date):
                    return {'error': f'Invalid date format: "{date}" in Row: {row_number}'}

                if amount and not check_amount(amount):
                    return {'error': f'Invalid amount format: "{amount}" in Row: {row_number}'}

                if not amount or not date or not source_name:
                    data = 'amount' if not amount else 'date' if not date else 'source_name'
                    return {'error': f'Required field missing in Row {row_number}. Please provide {data}.'}

            income_upload_helper.process_and_save(worksheet, local_church_id)

        except Exception as e:
            return {'error': f'Error processing the file: {str(e)}'}

    def get(self, request):
        local_churches = []
        if request.user.is_staff or request.user.role == 3:
            local_churches = LocalChurch.objects.all().order_by('local_church_name__title')
        if request.user.role == 2:
            local_churches = LocalChurch.objects.filter(local_church_pastor=request.user).order_by('local_church_name__title')
        if request.user.role == 4:
            local_churches = LocalChurch.objects.filter(region__region_overseer=request.user).order_by('local_church_name__title')
        return render(request, 'income/income_uploader.html', {'local_churches': local_churches})

    def post(self, request):
        errors = self.validate_income_uploader(request.FILES['file'], request.POST.get('local_church'))
        if errors:
            local_church = LocalChurch.objects.all()
            return render(request, 'income/income_uploader.html', {'errors': errors, 'local_churches': local_church})
        messages.success(request, 'Income records uploaded and processed successfully!')
        return redirect('income')

# Function to download a sample income uploader file
def download_income_uploader_sample(request):
    # Create a new workbook and add a worksheet
    workbook = Workbook()
    worksheet = workbook.active

    # Add headers to the worksheet
    headers = ['Amount', 'Description', 'Date', 'Source']
    worksheet.append(headers)

    header_row = worksheet[1]
    for cell in header_row:
        cell.font = Font(bold=True)

    # Add sample data to the worksheet
    data = [
        ['1500.75', 'Monthly Donation', '2024-08-01', 'Sales'],
        ['250.00', 'Fundraiser', '2024-07-12', 'Charity Donations'],
        ['250.00', 'Fundraiser', '2024-07-13', 'Other Donations'],
        ['2250.00', 'Fundraiser', '2024-07-14', 'Material Sales'],
    ]
    for sample_data in data:
        worksheet.append(sample_data)

    # Set column widths for better readability
    for col_num, column_letter in enumerate(get_column_letter(len(headers)), start=1):
        worksheet.column_dimensions[column_letter].width = 15

    # Create a response object with the XLSX content
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=sample_income_uploader_file.xlsx'
    workbook.save(response)

    return response


class DonationInKindListView(LoginRequiredMixin, ListView):
    model = DonationInKind
    template_name = 'income/donation_in_kind_list.html'
    context_object_name = 'donations'
    ordering = ['-donation_date']

    def __init__(self):
        super().__init__()
        self.filter_context = None

    def get_queryset(self):
        user = self.request.user
        queryset = DonationInKind.objects.all()

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


class DonationInKindCreateView(LoginRequiredMixin, CreateView):
    model = DonationInKind
    form_class = DonationInKindForm
    template_name = 'income/donation_in_kind_form.html'
    success_url = reverse_lazy('donation-list')

    def form_valid(self, form):
        messages.success(self.request, "Donation successfully created.")
        return super().form_valid(form)


class DonationInKindUpdateView(LoginRequiredMixin, UpdateView):
    model = DonationInKind
    form_class = DonationInKindForm
    template_name = 'income/donation_in_kind_form.html'
    success_url = reverse_lazy('donation-list')

    def form_valid(self, form):
        messages.success(self.request, "Donation successfully updated.")
        return super().form_valid(form)


@login_required(login_url='/authentication/login')
def delete_donation(request, pk):
    # Get the attendance record to delete
    instance = get_object_or_404(DonationInKind, pk=pk)
    instance.delete()
    messages.success(request, "Donation deleted successfully")
    return redirect('donation-list')


@login_required(login_url="/authentication/login")
def add_region_income(request):
    sources = selectable_sources()
    accounts = BankAccount.objects.all()
    user = request.user
    regions = Region.objects.all()

    if request.user.role == 4:
        regions = regions.filter(region_overseer=user)

    context = {
        "sources": sources,
        "regions": regions,
        "accounts": accounts,
        "values": request.POST,
        "current_user": int(request.user.id)
    }
    if request.method == "GET":
        return render(request, "income/add_region_income.html", context)

    if request.method == "POST":
        region = request.POST.get("region")
        account = request.POST.get("account")
        amount = request.POST.get("amount")
        description = request.POST.get("description")
        date = request.POST.get("income_date")
        source = request.POST.get("source")

        # Validate the form data
        if not region:
            messages.error(request, "Income Region required")
            return render(request, "income/add_region_income.html", context)

        if not amount:
            messages.error(request, "Amount is required")
            return render(request, "income/add_region_income.html", context)

        if not date:
            messages.error(request, "Date is required")
            return render(request, "income/add_region_income.html", context)

        if not source:
            messages.error(request, "Source is required")
            return render(request, "income/add_region_income.html", context)

        try:
            # Create the Region income
            Income.objects.create(
                region_id=region,
                account_id=account,
                amount=amount,
                date=date,
                source_id=source,
                description=description,
            )
            messages.success(request, "Region income saved successfully")
            return redirect("income")

        except Exception as e:
            print(f"Error saving Regin income: {e}")
        messages.error(request, "An unexpected error")
        return render(request, "income/add_income.html", context)


@login_required(login_url="/authentication/login")
def region_income_edit(request, id):
    income = Income.objects.get(pk=id, region__isnull=False)
    sources = selectable_sources(current_source_id=income.source_id)
    user = request.user
    regions = Region.objects.all()

    if request.user.role == 4:
        regions = regions.filter(region_overseer=user)

    context = {"income": income, "values": income, "sources": sources, "regions": regions}

    if request.method == "GET":
        return render(request, "income/edit_region_income.html", context)

    if request.method == "POST":
        region = request.POST.get("region")
        amount = request.POST.get("amount")
        description = request.POST.get("description")
        date = request.POST.get("income_date")
        source = request.POST.get("source")

        # Validate the form data
        if not amount:
            messages.error(request, "Amount is required")
            return render(request, "income/edit_income.html", context)
        try:
            date_object = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            # Handle invalid date
            messages.error(request, "Please enter a valid date in the format YYYY-MM-DD.")
            return render(request, "income/edit_region_income.html", context)

        # Update the income
        income.amount = amount
        income.description = description
        income.date = date_object
        income.source_id = source
        income.region_id = region
        income.save()
        messages.success(request, "Record updated successfully")
        return redirect("income")


def delete_region_income(request, id):
    income = Income.objects.get(pk=id, region__isnull=False)
    income.delete()
    messages.success(request, "Region income record was removed")
    return redirect("income")
