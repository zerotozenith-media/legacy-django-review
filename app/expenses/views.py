# Import necessary modules and classes
import logging

from django.db.models import Sum
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from authentication.middleware import Role
from organization.models import BankAccount, LocalChurch, Region
from organization.utils import get_user_local_church
from utils.helpers import get_filtered_context, get_user_regions
from .models import Category, Expense, SubCategory
from django.contrib import messages
from django.core.paginator import Paginator
import json
from django.http import JsonResponse
from datetime import datetime, timedelta
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font
import re
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from openpyxl import load_workbook, Workbook
from contributor.helper import validate_date, check_amount, parse_date
from django.views import View

logger = logging.getLogger(__name__)

# Function to calculate the total expense for the current month
def current_month_expense(user=None, region=None, local_church=None):
    current_year = datetime.now().year
    current_month = datetime.now().month
    # Filter expenses for the current month and year
    total_expense_current_month = Expense.objects.filter(
        date__month=current_month, date__year=current_year
    )
    if region:
        total_expense_current_month = total_expense_current_month.filter(local_church__region_id=region)
    if local_church:
        total_expense_current_month = total_expense_current_month.filter(local_church_id=local_church)
    # Aggregate the total amount
    total_expense_current_month = total_expense_current_month.aggregate(total=Sum('amount'))['total'] or 0.0
    return total_expense_current_month

# Function to calculate the total expense for the current year
def current_year_expense(user=None, region=None, local_church=None):
    current_year = datetime.now().year
    # Filter expenses for the current year
    total_expense_current_year = Expense.objects.filter(
        date__year=current_year
    )
    if region:
        total_expense_current_year = total_expense_current_year.filter(local_church__region_id=region)
    if local_church:
        total_expense_current_year = total_expense_current_year.filter(local_church_id=local_church)
    # Aggregate the total amount
    total_expense_current_year = total_expense_current_year.aggregate(total=Sum('amount'))['total'] or 0.0
    return total_expense_current_year

# Function to search expenses based on the search string
def search_expenses(request):
    if request.method == "POST":
        search_str = json.loads(request.body).get("searchText")
        # Filter expenses based on the search string
        expenses = (
            Expense.objects.filter(amount__istartswith=search_str, owner=request.user)
            | Expense.objects.filter(date__istartswith=search_str, owner=request.user)
            | Expense.objects.filter(description__icontains=search_str, owner=request.user)
            | Expense.objects.filter(category__icontains=search_str, owner=request.user)
        )
        data = expenses.values()
        return JsonResponse(list(data), safe=False)


# View to display the list of expenses
@login_required(login_url="/authentication/login")
def index(request):
    try:
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        user = request.user
        local_churches = get_user_local_church(user)

        region = request.GET.get("region", None)
        regions = get_user_regions(user)

        if region:
            region_list = regions.filter(name__iexact=region)
            local_churches = local_churches.filter(region__in=region_list)

        region_expenses = Expense.objects.filter(region__isnull=False)

        if user.role == 4:
            # Assuming user.region is a string representing the region name
            try:
                region_obj = Region.objects.get(id=user.local_church.region.id)
                region_expenses = region_expenses.filter(region=region_obj)
            except Region.DoesNotExist:
                logger.error(f"Region does not exist for user.")
                messages.error(request, "Your region is not configured properly.")
                return redirect('expenses')

        # Filter expenses based on the date range or category
        expenses = Expense.objects.filter(local_church__in=local_churches)
        expenses, filter_context = get_filtered_context(
            request,
            expenses,
            model_field_map={
                "region": "local_church__region__name",
                "local_church": "local_church_id"
            }
        )

        if start_date and end_date:
            try:
                start_date_parsed = datetime.strptime(start_date, "%d-%m-%Y").date()
                end_date_parsed = datetime.strptime(end_date, "%d-%m-%Y").date()
            except ValueError as ve:
                logger.error(f"Date parsing error: {ve}")
                messages.error(request, "Invalid date format. Please use DD-MM-YYYY.")
                return redirect('expenses')
            expenses = expenses.filter(date__range=[start_date_parsed, end_date_parsed], deleted=False)

        context = {
            "expenses": expenses,
            "region_expenses": region_expenses,
            "page_obj": expenses,
            "categories": [],
            "selected_category": "",
            # "current_month_expense": current_month_expense(user=user),
            # "current_year_expense": current_year_expense(user=user),
            "regions": regions,
            "churches": local_churches,
            **filter_context
        }

        return render(request, "expenses/index.html", context)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        messages.error(request, "Something went wrong")
        return redirect('expenses')

# View to add a new expense
@login_required(login_url="/authentication/login")
def add_expense(request):
    expense = Expense()
    categories = Category.objects.all()
    sub_categories = SubCategory.objects.all()
    user = request.user
    local_churches = get_user_local_church(user)

    context = {
        "categories": categories,
        "sub_categories": sub_categories,
        "local_churches": local_churches,
        "values": request.POST,
        "expense": expense,
    }
    if request.method == "GET":
        return render(request, "expenses/add-expense.html", context)

    if request.method == "POST":
        local_church = request.POST["local_church"]
        amount = request.POST["amount"]
        description = request.POST["description"]
        date = request.POST["expense_date"]
        category = request.POST["category"]
        tax_amount = request.POST["tax_amount"]
        tax_category = request.POST["tax_category"]
        sub_category = request.POST.get("sub_category", None)

        # Validate the form data
        if not local_church:
            messages.error(request, "Expense local_church required")
            return render(request, "expenses/add-expense.html", context)

        if not amount:
            messages.error(request, "Amount is required")
            return render(request, "expenses/add-expense.html", context)

        if not description:
            messages.error(request, "Description is required")
            return render(request, "expenses/add-expense.html", context)

        if not date:
            messages.error(request, "Date is required")
            return render(request, "expenses/add-expense.html", context)

        if not tax_amount:
            messages.error(request, "Tax amount required")
            return render(request, "expenses/add-expense.html", context)

        if not sub_category:
            messages.error(request, "Sub category required")
            return render(request, "expenses/add-expense.html", context)

        # Create the expense
        Expense.objects.create(
            local_church_id=local_church,
            amount=amount,
            date=date,
            category_id=category,
            sub_category_id=sub_category,
            description=description,
            tax_amount=tax_amount,
            tax_category=tax_category,
        )
        messages.success(request, "Expense saved successfully")

        return redirect("expenses")

# View to edit an existing expense
@login_required(login_url="/authentication/login")
def expense_edit(request, id):
    expense = Expense.objects.get(pk=id)
    categories = Category.objects.all()
    sub_categories = SubCategory.objects.all()
    user = request.user
    local_churches = get_user_local_church(user)
    context = {
        "expense": expense,
        "values": expense,
        "categories": categories,
        "sub_categories": sub_categories,
        "local_churches": local_churches,
    }
    if request.method == "GET":
        return render(request, "expenses/edit-expense.html", context)
    if request.method == "POST":
        amount = request.POST["amount"]

        if not amount:
            messages.error(request, "Amount is required")
            return render(request, "expenses/edit-expense.html", context)
        description = request.POST["description"]
        date = request.POST["expense_date"]
        category_id = request.POST["category"]
        local_church_id = request.POST["local_church"]
        tax_amount = request.POST["tax_amount"]
        tax_category = request.POST["tax_category"]
        sub_category_id = request.POST["sub_category"]

        if not description:
            messages.error(request, "Description is required")
            return render(request, "expenses/edit-expense.html", context)

        try:
            local_church_instance = LocalChurch.objects.get(pk=int(local_church_id))
            expense.local_church = local_church_instance
        except (LocalChurch.DoesNotExist, ValueError):
            messages.error(request, "Invalid or non-existent church selected.")
            return render(request, "expenses/edit-expense.html", context)

        try:
            category_instance = Category.objects.get(pk=int(category_id))
            expense.category = category_instance
        except (Category.DoesNotExist, ValueError):
            messages.error(request, "Invalid or non-existent category selected.")
            return render(request, "expenses/edit-expense.html", context)
        
        try:
            sub_category_instance = SubCategory.objects.get(pk=int(sub_category_id))
            expense.sub_category = sub_category_instance 
        except (SubCategory.DoesNotExist, ValueError):
            messages.error(request, "Invalid or non-existent sub-category selected.")
            return render(request, "expenses/edit-expense.html", context)

        # Update the expense
        expense.amount = amount
        expense.date = date
        expense.tax_amount = tax_amount
        expense.tax_category = tax_category
        expense.description = description

        expense.save()
        messages.success(request, "Expense updated successfully")

        return redirect("expenses")


# Function to delete an expense
def delete_expense(request, id):
    expense = Expense.objects.get(pk=id)
    expense.delete()
    messages.success(request, "Expense removed")
    return redirect("expenses")

# Function to get subcategories based on the selected category
def get_subcategories(request):
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if is_ajax:
        if request.method == "GET":
            category_id = request.GET.get("category_id")
            if category_id:
                subcategories = SubCategory.objects.filter(
                    parent_id=category_id
                ).values("id", "name")
                subcategories_list = list(subcategories)
                return JsonResponse(subcategories_list, safe=False)
    return JsonResponse([], safe=False)

# Function to get category expense data for the last year
def get_category_expense_data_last_year(region_id=None, local_church=None):
    # Get the start and end dates for the last 1 year
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    # Filter expenses for the last 1 year
    expenses_last_year = Expense.objects.filter(
        date__range=[start_date, end_date], category__name__isnull=False
    )
    if region_id:
        expenses_last_year = expenses_last_year.filter(local_church__region_id=region_id)
    if local_church:
        expenses_last_year = expenses_last_year.filter(local_church_id=local_church)
    # Aggregate the total amount for each category
    category_expense_data = expenses_last_year.values('category__name').annotate(
        total_expense=Sum('amount')
    )

    # Extract category names and expense amounts from the query results
    category_names = [entry['category__name'] for entry in category_expense_data]
    expense_amounts = [float(entry['total_expense']) for entry in category_expense_data]

    return category_names, expense_amounts

# Helper class for expense uploader
class ExpenseUploaderHelper:
    @staticmethod
    def validate_headers(worksheet):
        headers = [cell.value.strip() if cell.value else None for cell in worksheet[1]]
        return headers == ['Amount', 'Tax Amount', 'Description', 'Date', 'Category', 'Sub Category', 'Tax Category']

    @staticmethod
    def process_and_save(worksheet, local_church_id):
        with transaction.atomic():
            for row_number, row in enumerate(worksheet.iter_rows(min_row=2, values_only=True), start=2):
                amount, tax_amount, description, date, category_name, sub_category_name, tax_category = row

                if not amount and not tax_amount and not description and not date and not category_name and not sub_category_name and not tax_category:
                    continue
                print(category_name)
                local_church = LocalChurch.objects.get(id=local_church_id)
                try:
                    category = Category.objects.get(name=str(category_name))
                except Exception as e:
                    print(e)
                    category = None
                try:
                    sub_category = SubCategory.objects.get(name=str(sub_category_name))
                except Exception as e:
                    print(e)
                    sub_category = None

                # Create the expense
                Expense.objects.create(
                    local_church=local_church,
                    amount=amount,
                    tax_amount=tax_amount or 0,
                    description=description,
                    date=parse_date(date),
                    category=category,
                    sub_category=sub_category,
                    tax_category=tax_category or ''
                )

# View for uploading expenses from a file
class ExpenseUploadView(View):
    @staticmethod
    def validate_expense_uploader(file, local_church_id):
        expense_upload_helper = ExpenseUploaderHelper()
        try:
            workbook = load_workbook(file, read_only=True)
            worksheet = workbook.active

            # Validate the headers of the worksheet
            if not expense_upload_helper.validate_headers(worksheet):
                return {'error': 'Invalid headers'}

            for row_number, row in enumerate(worksheet.iter_rows(min_row=2, values_only=True), start=2):
                amount, tax_amount, description, date, category_name, sub_category_name, tax_category = row

                if isinstance(date, str):
                    date = parse_date(date)

                if not amount and not tax_amount and not description and not date and not category_name and not sub_category_name and not tax_category:
                    continue

                if date and not validate_date(date):
                    return {'error': f'Invalid date format: "{date}" in Row: {row_number}'}

                if amount and not check_amount(amount):
                    return {'error': f'Invalid amount format: "{amount}" in Row: {row_number}'}

                if not amount or not date or not category_name:
                    data = 'amount' if not amount else 'date' if not date else 'category_name'
                    return {'error': f'Required field missing in Row {row_number}. Please provide {data}.'}

            expense_upload_helper.process_and_save(worksheet, local_church_id)

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
        return render(request, 'expenses/expense_uploader.html', {'local_churches': local_churches})

    def post(self, request):
        errors = self.validate_expense_uploader(request.FILES['file'], request.POST.get('local_church'))
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
            return render(request, 'expenses/expense_uploader.html', {'errors': errors, 'local_churches': local_churches})
        messages.success(request, 'Expense records uploaded and processed successfully!')
        return redirect('expenses')

# Function to download a sample expense uploader file
def download_expense_uploader_sample(request):
    # Create a new workbook and add a worksheet
    workbook = Workbook()
    worksheet = workbook.active

    # Add headers to the worksheet
    headers = ['Amount', 'Tax Amount', 'Description', 'Date', 'Category', 'Sub Category', 'Tax Category']
    worksheet.append(headers)

    header_row = worksheet[1]
    for cell in header_row:
        cell.font = Font(bold=True)

    # Add sample data to the worksheet
    data = [
        ['1500.75', '150.00', 'Expense Description', '2024-08-01', 'Advertising and Promotion', 'Promotion / Retreat Expenses', 'HST'],
        ['250.00', '25.00', 'Another Expense Desc', '2024-07-15', 'Travel and Vehicle Expenses', 'Vehicle Registration and Insurance', 'GST'],
        ['250.00', '25.00', 'Another Another Expense Desc', '2024-07-18', 'Licenses, Memberships and Dues', 'Professional License Fees', 'GST'],
    ]
    for sample_data in data:
        worksheet.append(sample_data)

    # Set column widths for better readability
    for col_num, column_letter in enumerate(get_column_letter(len(headers)), start=1):
        worksheet.column_dimensions[column_letter].width = 15

    # Create a response object with the XLSX content
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=sample_expense_uploader_file.xlsx'
    workbook.save(response)

    return response


# View to add a new expense
@login_required(login_url="/authentication/login")
def add_region_expense(request):
    expense = Expense()
    categories = Category.objects.all()
    sub_categories = SubCategory.objects.all()
    user = request.user
    regions = Region.objects.all()

    if request.user.role == 4:
        regions = regions.filter(region_overseer=user)

    context = {
        "categories": categories,
        "sub_categories": sub_categories,
        "regions": regions,
        "values": request.POST,
        "expense": expense,
    }
    if request.method == "GET":
        return render(request, "expenses/add-region-expense.html", context)

    if request.method == "POST":
        region = request.POST["region"]
        amount = request.POST["amount"]
        description = request.POST["description"]
        date = request.POST["expense_date"]
        category = request.POST["category"]
        tax_amount = request.POST["tax_amount"]
        tax_category = request.POST["tax_category"]
        sub_category = request.POST.get("sub_category", None)

        # Validate the form data
        if not region:
            messages.error(request, "Expense region required")
            return render(request, "expenses/add-region-expense.html", context)

        # Create the expense
        Expense.objects.create(
            region_id=region,
            amount=amount,
            date=date,
            category_id=category,
            sub_category_id=sub_category,
            description=description,
            tax_amount=tax_amount,
            tax_category=tax_category,
        )
        messages.success(request, "Region Expense saved successfully")

        return redirect("expenses")


# # View to edit an existing expense
@login_required(login_url="/authentication/login")
def region_expense_edit(request, id):
    expense = Expense.objects.get(pk=id)
    categories = Category.objects.all()
    sub_categories = SubCategory.objects.all()
    user = request.user
    regions = Region.objects.all()

    if request.user.role == 4:
        regions = regions.filter(region_overseer=user)
    context = {
        "expense": expense,
        "values": expense,
        "categories": categories,
        "sub_categories": sub_categories,
        "regions": regions,
    }
    if request.method == "GET":
        return render(request, "expenses/edit-region-expense.html", context)

    if request.method == "POST":
        amount = request.POST["amount"]

        if not amount:
            messages.error(request, "Amount is required")
            return render(request, "expenses/edit-region-expense.html", context)

        description = request.POST["description"]
        date = request.POST["expense_date"]
        category_id = request.POST["category"]
        region_id = request.POST["region"]
        tax_amount = request.POST["tax_amount"]
        tax_category = request.POST["tax_category"]
        sub_category_id = request.POST["sub_category"]

        try:
            region_instance = Region.objects.get(pk=int(region_id))
            expense.region = region_instance
        except (Region.DoesNotExist, ValueError):
            messages.error(request, "Invalid or non-existent region selected.")
            return render(request, "expenses/edit-region-expense.html", context)

        try:
            category_instance = Category.objects.get(pk=int(category_id))
            expense.category = category_instance
        except (Category.DoesNotExist, ValueError):
            messages.error(request, "Invalid or non-existent category selected.")
            return render(request, "expenses/edit-region-expense.html", context)

        try:
            sub_category_instance = SubCategory.objects.get(pk=int(sub_category_id))
            expense.sub_category = sub_category_instance
        except (SubCategory.DoesNotExist, ValueError):
            messages.error(request, "Invalid or non-existent sub-category selected.")
            return render(request, "expenses/edit-region-expense.html", context)

        # Update the expense
        expense.amount = amount
        expense.date = date
        expense.tax_amount = tax_amount
        expense.tax_category = tax_category
        expense.description = description

        expense.save()
        messages.success(request, "Region Expense updated successfully")

        return redirect("expenses")


# Function to delete region expense
def delete_region_expense(request, id):
    expense = Expense.objects.get(pk=id)
    expense.delete()
    messages.success(request, "Region Expense removed")
    return redirect("expenses")
