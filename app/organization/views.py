# Import necessary modules and classes
import csv
import re
from calendar import month_name, calendar
from decimal import Decimal
from urllib.parse import urlencode

from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from attendance.models import Attendance
from authentication.views import get_unique_users_count
from contributor.views import current_months_contribution, current_year_contribution
from expenses.models import Expense
from expenses.views import current_month_expense, current_year_expense, get_category_expense_data_last_year
from income.models import Income
from organization.models import Region, DetailReport, PaymentAllocation, AllocationReconciliation
from income.views import current_year_income, current_month_income
from django.shortcuts import render
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
from django.db.models.functions import ExtractYear
import json
from collections import defaultdict
from contributor.models import *
from church_properties.models import ChurchProperties
from organization.models import LocalChurch
from django.db.models import Sum, F, Func
from django.db.models.functions import TruncMonth
from django.core.files.storage import FileSystemStorage
from .forms import UploadFileForm
from .models import Reconciliation, Region
from openpyxl import load_workbook
from datetime import timedelta

# Helper functions
from organization.utils import get_user_local_church, extract_transactions_from_pdf


# Function to get attendance data for chart
def attendance_donut_chart_data(local_church_id=None, region_id=None, start_date=None, end_date=None):
    attendance_data = Attendance.objects.all()

    if local_church_id:
        attendance_data = attendance_data.filter(local_church_id=local_church_id)
    if region_id:
        attendance_data = attendance_data.filter(local_church__region_id=region_id)
    if start_date and end_date:
        attendance_data = attendance_data.filter(date__range=[start_date, end_date])

    data = defaultdict(int)

    for attendance in attendance_data:
        data['Adult Male'] += attendance.adult_male
        data['Adult Female'] += attendance.adult_female
        data['Youth Male'] += attendance.youth_male
        data['Youth Female'] += attendance.youth_female
        data['Children Male'] += attendance.children_male
        data['Children Female'] += attendance.children_female
        data['Campus Male'] += attendance.campus_male
        data['Campus Female'] += attendance.campus_female
        data['Caucasian'] += attendance.cau
        data['Visitor'] += attendance.visitor
        data['Converts'] += attendance.conv
        data['YPF Male'] += attendance.ypf_male
        data['YPF Female'] += attendance.ypf_female
        data['Zoom'] += attendance.zoom
        data['YouTube'] += attendance.youtube

    labels = list(data.keys())
    values = list(data.values())

    chart_data = {
        'labels': labels,
        'values': values
    }

    return chart_data


# Function to get contributions by local church for chart
def contributions_by_local_church_chart(local_church_id=None, region_id=None, start_date=None, end_date=None):
    user_contributions = Contribution.objects.filter(local_church__isnull=False)
    misc_contributions = MiscellaneousContribution.objects.filter(local_church__isnull=False)
    anon_contributions = AnonymousContribution.objects.filter(local_church__isnull=False)

    if local_church_id:
        user_contributions = user_contributions.filter(local_church_id=local_church_id)
        misc_contributions = misc_contributions.filter(local_church_id=local_church_id)
        anon_contributions = anon_contributions.filter(local_church_id=local_church_id)

    if region_id:
        user_contributions = user_contributions.filter(local_church__region_id=region_id)
        misc_contributions = misc_contributions.filter(local_church__region_id=region_id)
        anon_contributions = anon_contributions.filter(local_church__region_id=region_id)

    if start_date and end_date:
        user_contributions = user_contributions.filter(deposited_date__range=[start_date, end_date])
        misc_contributions = misc_contributions.filter(deposited_date__range=[start_date, end_date])
        anon_contributions = anon_contributions.filter(deposited_date__range=[start_date, end_date])

    user_contributions = user_contributions.values('local_church__local_church_name__title').annotate(
        total_amount=Sum('amount'))
    misc_contributions = misc_contributions.values(
        'local_church__local_church_name__title').annotate(total_amount=Sum('amount'))
    anon_contributions = anon_contributions.values(
        'local_church__local_church_name__title').annotate(total_amount=Sum('amount'))

    data = defaultdict(float)

    for contribution in user_contributions:
        local_church = contribution['local_church__local_church_name__title']
        total_amount = float(contribution['total_amount'])
        data[local_church] += total_amount

    for contribution in misc_contributions:
        local_church = contribution['local_church__local_church_name__title']
        total_amount = float(contribution['total_amount'])
        data[local_church] += total_amount

    for contribution in anon_contributions:
        local_church = contribution['local_church__local_church_name__title']
        total_amount = float(contribution['total_amount'])
        data[local_church] += total_amount

    labels = list(data.keys())
    amounts = list(data.values())

    return {
        'labels': labels,
        'amounts': amounts
    }


# Function to get cumulative income and expense chart data
def cumulative_income_expense_chart(local_church_id=None, region_id=None, start_date=None, end_date=None):
    filter_params = {}
    contrib_filter_params = {}
    if local_church_id:
        filter_params['local_church_id'] = local_church_id
        contrib_filter_params['local_church_id'] = local_church_id
    if region_id:
        filter_params['local_church__region_id'] = region_id
        contrib_filter_params['local_church__region_id'] = region_id
    if start_date:
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        filter_params['date__gte'] = start_date
        contrib_filter_params['deposited_date__gte'] = start_date
    if end_date:
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        filter_params['date__lte'] = end_date
        contrib_filter_params['deposited_date__lte'] = end_date

    # Aggregate income data from each model separately
    income_data = (
        Income.objects.filter(**filter_params)
        .values('date')
        .annotate(total_income=Sum('amount'))
        .values('date', 'total_income')
    )

    contributions_data = (
        Contribution.objects.filter(**contrib_filter_params)
        .values('deposited_date')
        .annotate(total_income=Sum('amount'))
        .values('deposited_date', 'total_income')
    )

    miscellaneous_data = (
        MiscellaneousContribution.objects.filter(**contrib_filter_params)
        .values('deposited_date')
        .annotate(total_income=Sum('amount'))
        .values('deposited_date', 'total_income')
    )

    anonymous_data = (
        AnonymousContribution.objects.filter(**contrib_filter_params)
        .values('deposited_date')
        .annotate(total_income=Sum('amount'))
        .values('deposited_date', 'total_income')
    )

    # Aggregate expense data
    expense_data = (
        Expense.objects.filter(**filter_params)
        .values('date')
        .annotate(total_expense=Sum('amount'))
        .values('date', 'total_expense')
    )

    # Combine all income data
    combined_income = {}
    for item in list(income_data) + list(contributions_data) + list(miscellaneous_data) + list(anonymous_data):
        date = item.get('date') or item.get('deposited_date')
        if isinstance(date, datetime):
            date_str = date.strftime('%Y-%m-%d')
        else:
            date_str = date
        amount = float(item['total_income'])
        if date_str not in combined_income:
            combined_income[date_str] = {'income': amount, 'expense': 0}
        else:
            combined_income[date_str]['income'] += amount

    # Combine all expense data
    for item in expense_data:
        date = item['date']
        if isinstance(date, datetime):
            date_str = date.strftime('%Y-%m-%d')
        else:
            date_str = date
        amount = float(item['total_expense'])
        if date_str not in combined_income:
            combined_income[date_str] = {'income': 0, 'expense': amount}
        else:
            combined_income[date_str]['expense'] += amount

    # Calculate profit or loss (income - expense) for each date
    for date, values in combined_income.items():
        values['profit'] = values['income'] - values['expense']

    # Prepare data for the chart
    sorted_dates = sorted(combined_income.keys())
    sorted_amounts = [combined_income[date]['profit'] for date in sorted_dates]

    # Prepare traces and layout for Plotly
    traces = [
        {
            'type': 'waterfall',
            'name': 'Income vs Expenses',
            'x': [date.strftime('%b %y') for date in sorted_dates],
            'y': sorted_amounts,
            'measure': ['relative'] * len(sorted_amounts),
            'marker': {
                'color': ['rgba(75, 192, 192, 1)' if y >= 0 else 'rgba(255, 99, 132, 1)' for y in sorted_amounts],
            }
        }
    ]

    layout = {
        'title': {
            'text': 'Profit vs Expenses',
            'font': {
                'size': 16,
                'color': '#333',
            },
        },
        'paper_bgcolor': 'rgba(250, 250, 250, 1)',
        'plot_bgcolor': 'rgba(250, 250, 250, 1)',
        'barmode': 'relative',
        'xaxis': {
            'title': 'Month',
            'tickangle': -45,
            'automargin': True
        },
        'yaxis': {
            'title': 'Amount',
            'automargin': True
        },
        'legend': {
            'orientation': 'h',
            'xanchor': 'center',
            'x': 0.5,
            'yanchor': 'bottom',
            'y': -0.3
        }
    }

    chart_data = {
        'traces': traces,
        'layout': layout
    }

    return chart_data


# Function to get properties chart data
def properties_chart(local_church_id=None, region_id=None, start_date=None, end_date=None):
    properties_data = ChurchProperties.objects.all()

    if local_church_id:
        properties_data = properties_data.filter(local_church_id=local_church_id)
    if region_id:
        properties_data = properties_data.filter(local_church__region_id=region_id)
    if start_date:
        properties_data = properties_data.filter(purchase_date__gte=start_date)
    if end_date:
        properties_data = properties_data.filter(purchase_date__lte=end_date)

    assets_acquired_by_year = properties_data.annotate(
        year=ExtractYear('purchase_date')
    ).values(
        'year', 'local_church'
    ).annotate(
        total_assets_acquired=Sum('amount_paid')
    ).order_by('year', 'local_church')

    data = defaultdict(lambda: defaultdict(float))

    for asset in assets_acquired_by_year:
        year = int(asset['year'])  # Ensure the year is cast to an integer
        local_church_id = asset['local_church']
        if local_church_id:
            local_church_name = LocalChurch.objects.get(id=local_church_id).local_church_name.title
            total_amount = float(asset['total_assets_acquired'])
            data[year][local_church_name] += total_amount

    labels = sorted(data.keys())
    local_churches = set()
    for year_data in data.values():
        local_churches.update(year_data.keys())

    traces = []
    for i, local_church in enumerate(sorted(local_churches)):
        trace = {
            'name': local_church,
            'x': [str(label) for label in labels],  # Ensure labels are strings
            'y': [data[year].get(local_church, 0) for year in labels],
            'type': 'bar'
        }
        traces.append(trace)

    chart_data = {
        'traces': traces,
        'layout': {
            'title': 'Assets Acquired by Year',
            'paper_bgcolor': 'rgba(250, 250, 250, 1)',
            'plot_bgcolor': 'rgba(250, 250, 250, 1)',
            'barmode': 'group',
            'xaxis': {'title': 'Year'},
            'yaxis': {'title': 'Amount Paid'}
        }
    }
    return chart_data


# Function to get incoming amount local church chart data
def incoming_amount_local_church_chart(local_church_id=None, region_id=None, start_date=None, end_date=None):
    contributions_data = Contribution.objects.annotate(
        month_annotated=TruncMonth('deposited_date')
    ).values(
        'month_annotated', 'local_church__local_church_name__title'
    ).annotate(
        total_amount=Sum('amount')
    ).order_by('month_annotated', 'local_church__local_church_name__title')

    income_data = Income.objects.annotate(
        month_annotated=TruncMonth('date')
    ).values(
        'month_annotated', 'local_church__local_church_name__title'
    ).annotate(
        total_amount=Sum('amount')
    ).order_by('month_annotated', 'local_church__local_church_name__title')

    data = defaultdict(float)

    # Filter contributions data
    if local_church_id:
        contributions_data = contributions_data.filter(local_church_id=local_church_id)
    if region_id:
        contributions_data = contributions_data.filter(local_church__region_id=region_id)
    if start_date and end_date:
        contributions_data = contributions_data.filter(deposited_date__range=[start_date, end_date])

    # Aggregate contributions data
    for contribution in contributions_data:
        month = contribution['month_annotated'].strftime('%b %y')
        local_church = contribution['local_church__local_church_name__title']
        total_amount = float(contribution['total_amount'])
        data[(month, local_church)] += total_amount

    # Filter income data
    if local_church_id:
        income_data = income_data.filter(local_church_id=local_church_id)
    if region_id:
        income_data = income_data.filter(local_church__region_id=region_id)
    if start_date and end_date:
        income_data = income_data.filter(date__range=[start_date, end_date])

    # Aggregate income data
    for income in income_data:
        month = income['month_annotated'].strftime('%b %y')
        local_church = income['local_church__local_church_name__title']
        total_amount = float(income['total_amount'])
        data[(month, local_church)] += total_amount

    # Prepare chart data
    labels = sorted(set([month for (month, local_church) in data.keys()]))
    local_churches = sorted(
        set([local_church if local_church is not None else 'Unknown' for (month, local_church) in data.keys()]))

    traces = []
    for local_church in local_churches:
        traces.append({
            'name': local_church,
            'x': labels,
            'y': [data.get((month, local_church), 0) for month in labels],
            'type': 'bar'  # Changed from 'scatter' to 'bar' for bar chart
        })

    chart_data = {
        'traces': traces,
        'layout': {
            'title': 'Income by Local Church',
            'paper_bgcolor': 'rgba(250, 250, 250, 1)',
            'plot_bgcolor': 'rgba(250, 250, 250, 1)',
            'barmode': 'group',  # Group bars for each month
            'xaxis': {'title': 'Month'},
            'yaxis': {'title': 'Amount'},
        }
    }

    return chart_data


# Function to get expense amount local church chart data
def expense_amount_local_church_chart(local_church_id=None, region_id=None, start_date=None, end_date=None):
    expenses = Expense.objects.all()

    if local_church_id:
        expenses = expenses.filter(local_church_id=local_church_id)
    if region_id:
        expenses = expenses.filter(local_church__region_id=region_id)
    if start_date:
        expenses = expenses.filter(date__gte=start_date)
    if end_date:
        expenses = expenses.filter(date__lte=end_date)

    expense_by_month = expenses.annotate(
        month_annotated=TruncMonth('date')
    ).values(
        'month_annotated', 'local_church__local_church_name__title'
    ).annotate(
        total_amount=Sum('amount')
    ).order_by('month_annotated', 'local_church__local_church_name__title')

    data = defaultdict(lambda: defaultdict(float))

    for expense in expense_by_month:
        month = expense['month_annotated']
        local_church = expense['local_church__local_church_name__title']
        total_amount = float(expense['total_amount'])

        # Ensure both month and local_church are not None
        if month and local_church:
            month_str = month.strftime('%b %y')
            data[month_str][local_church] += total_amount

    # Filter out None values from labels and local_churches
    labels = sorted([key for key in data.keys() if key is not None])
    local_churches = set()
    for month_data in data.values():
        local_churches.update([church for church in month_data.keys() if church is not None])

    traces = []
    for local_church in sorted(local_churches):
        trace = {
            'name': local_church,
            'x': labels,
            'y': [data[month].get(local_church, 0) for month in labels],
            'type': 'bar'
        }
        traces.append(trace)

    chart_data = {
        'traces': traces,
        'layout': {
            'title': 'Expenses by Local Church',
            'paper_bgcolor': 'rgba(250, 250, 250, 1)',
            'plot_bgcolor': 'rgba(250, 250, 250, 1)',
            'barmode': 'group',
            'xaxis': {'title': 'Month'},
            'yaxis': {'title': 'Amount'}
        }
    }
    return chart_data


# Function to get monthly expense by category chart data
def monthly_expense_by_category_chart(local_church_id=None, region_id=None, start_date=None, end_date=None):
    expenses = Expense.objects.all()

    if local_church_id:
        expenses = expenses.filter(local_church_id=local_church_id)
    if region_id:
        expenses = expenses.filter(local_church__region_id=region_id)
    if start_date:
        expenses = expenses.filter(date__gte=start_date)
    if end_date:
        expenses = expenses.filter(date__lte=end_date)

    expenses_by_month = expenses.annotate(
        month=TruncMonth('date')
    ).values(
        'month', 'category__name'
    ).annotate(
        total_amount=Sum('amount')
    ).order_by('month', 'category__name')

    data = defaultdict(lambda: defaultdict(float))

    for expense in expenses_by_month:
        month = expense['month']
        category = expense['category__name']
        total_amount = float(expense['total_amount'])
        data[month][category] += total_amount

    labels = sorted(data.keys())
    labels = [month.strftime('%b %y') for month in labels]  # Format the month labels as "Aug 2024"
    categories = set()
    for month_data in data.values():
        categories.update(month_data.keys())

    datasets = []

    categories.discard(None)
    for category in sorted(categories):
        if category is not None:
            datasets.append({
                'name': category,
                'x': labels,
                'y': [data[month].get(category, 0) for month in sorted(data.keys())],
                'type': 'bar'
            })

    chart_data = {
        'labels': labels,
        'datasets': datasets
    }

    return chart_data


# Function to get income and expense chart data
def income_expense_chart(request, region_id=None, local_church=None):
    current_date = timezone.now().date()
    current_month = current_date.month
    current_year = current_date.year

    # Generate labels for the last 12 months
    labels = []
    for i in range(12):
        month = current_month - i
        year = current_year
        if month <= 0:
            month += 12
            year -= 1
        label = datetime(year, month, 1).strftime("%b %y")  # Format the label as "MMM YY"
        labels.insert(0, label)

    income_amounts = []
    expense_amounts = []
    balances = []
    current_balance = Decimal(0.0)  # Start with a balance of 0

    for label in labels:
        label_date = datetime.strptime(label, '%b %y')
        month = label_date.month
        year = label_date.year

        # Fetch income data
        income_data = Income.objects.filter(date__month=month, date__year=year)
        if region_id:
            income_data = income_data.filter(local_church__region_id=region_id)
        if local_church:
            income_data = income_data.filter(local_church_id=local_church)
        s_amount_income = income_data.aggregate(Sum('amount'))['amount__sum'] or Decimal(0.0)
        income_amounts.append(float(s_amount_income))

        # Fetch expense data
        expense_data = Expense.objects.filter(date__month=month, date__year=year)
        if region_id:
            expense_data = expense_data.filter(local_church__region_id=region_id)
        if local_church:
            expense_data = expense_data.filter(local_church_id=local_church)
        s_amount_expense = expense_data.aggregate(Sum('amount'))['amount__sum'] or Decimal(0.0)
        expense_amounts.append(float(s_amount_expense))

        # Calculate balance
        current_balance += s_amount_income - s_amount_expense
        if current_balance < 0:
            balances.append(0.00)
        else:
            balances.append(float(current_balance))

    return labels, income_amounts, expense_amounts, balances


# Function to get total attendance for user local church chart data
def total_attendance_for_user_local_church(local_church_id=None, region_id=None, start_date=None, end_date=None):
    attendance_object = Attendance.objects.all()
    if local_church_id:
        attendance_object = attendance_object.filter(local_church_id=local_church_id)
    if region_id:
        attendance_object = attendance_object.filter(local_church__region_id=region_id)
    if start_date:
        attendance_object = attendance_object.filter(date__gte=start_date)
    if end_date:
        attendance_object = attendance_object.filter(date__lte=end_date)

    total = attendance_object.aggregate(
        total_adult_male=Sum('adult_male'),
        total_adult_female=Sum('adult_female'),
        total_youth_male=Sum('youth_male'),
        total_youth_female=Sum('youth_female'),
        total_children_male=Sum('children_male'),
        total_children_female=Sum('children_female'),
        total_campus_male=Sum('campus_male'),
        total_campus_female=Sum('campus_female'),
        total_cau=Sum('cau'),
        total_visitor=Sum('visitor'),
        total_conv=Sum('conv')
    )

    total_count = sum([
        total['total_adult_male'] or 0,
        total['total_adult_female'] or 0,
        total['total_youth_male'] or 0,
        total['total_youth_female'] or 0,
        total['total_children_male'] or 0,
        total['total_children_female'] or 0,
        total['total_campus_male'] or 0,
        total['total_campus_female'] or 0,
        total['total_cau'] or 0,
        total['total_visitor'] or 0,
        total['total_conv'] or 0
    ])

    return total_count


# View to display the dashboard
@login_required(login_url="/authentication/login")
def index(request):
    region = None
    local_church = None
    start_date = None
    end_date = None
    local_church_list = []
    region_list = []
    user = request.user
    year = datetime.now().year
    overall_grand_total = 0.00
    if request.GET:
        region = request.GET.get('region')
        local_church = request.GET.get('local_church')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        year = request.GET.get('year', datetime.now().year)

    if user.role == 3 or user.is_staff:
        region_list = Region.objects.all().order_by('name')
        local_church_list = LocalChurch.objects.all().order_by('local_church_name__title')
    if user.role == 4:
        region_list = Region.objects.filter(region_overseer=user).order_by('name')
        for region in region_list:
            local_church_list += LocalChurch.objects.filter(region=region).order_by('local_church_name__title')
        region = region_list.first().id
    if user.role == 2:
        local_church_list = LocalChurch.objects.filter(local_church_pastor=user).order_by('local_church_name__title')
        local_church = local_church_list.first().id

    labels, income_amounts, expense_amounts, balances = income_expense_chart(request, region_id=region,
                                                                             local_church=local_church)
    expense_categories, expenses_last_year = get_category_expense_data_last_year(region_id=region,
                                                                                 local_church=local_church)
    # for table data
    contrib_totals = Contribution.objects.values('payment_type').annotate(total_amount=Sum('amount')).exclude(
        payment_type__in=['direct', 'online_deposited'])
    income_reconciliation = Reconciliation.objects.filter(recon_type='income')
    online_deposited = income_reconciliation.filter(description__icontains='TFR-FR').aggregate(Sum('amount'))[
        'amount__sum']
    direct_deposit = income_reconciliation.exclude(
        Q(description__icontains='GC') | Q(description__icontains='E-TRANSFER') | Q(
            description__icontains='TFR-FR')).aggregate(Sum('amount'))['amount__sum']
    income_total = Income.objects.all().aggregate(Sum('amount'))['amount__sum']
    grand_total_contrib = Contribution.objects.aggregate(Sum('amount'))['amount__sum']
    grand_total_misc = MiscellaneousContribution.objects.aggregate(Sum('amount'))['amount__sum']
    if grand_total_misc and grand_total_contrib:
        overall_grand_total = grand_total_contrib + grand_total_misc
    if region:
        contrib_totals = Contribution.objects.filter(local_church__region_id=region).values('payment_type').annotate(
            total_amount=Sum('amount')).exclude(
            payment_type__in=['direct', 'online_deposited'])
        income_reconciliation = Reconciliation.objects.filter(recon_type='income', region_id=region)
        online_deposited = income_reconciliation.filter(description__icontains='TFR-FR').aggregate(Sum('amount'))[
            'amount__sum']
        direct_deposit = income_reconciliation.exclude(
            Q(description__icontains='GC') | Q(description__icontains='E-TRANSFER') | Q(
                description__icontains='TFR-FR')).aggregate(Sum('amount'))['amount__sum']
        income_total = Income.objects.filter(local_church__region_id=region).aggregate(Sum('amount'))['amount__sum']
        grand_total_contrib = Contribution.objects.filter(local_church__region_id=region).aggregate(Sum('amount'))[
            'amount__sum']
        grand_total_misc = \
        MiscellaneousContribution.objects.filter(local_church__region_id=region).aggregate(Sum('amount'))['amount__sum']
    if local_church:
        contrib_totals = Contribution.objects.filter(local_church_id=local_church).values('payment_type').annotate(
            total_amount=Sum('amount')).exclude(
            payment_type__in=['direct', 'online_deposited'])
        income_reconciliation = Reconciliation.objects.filter(recon_type='income',
                                                              region__local_churches__in=[local_church])
        online_deposited = income_reconciliation.filter(description__icontains='TFR-FR').aggregate(Sum('amount'))[
            'amount__sum']
        direct_deposit = income_reconciliation.exclude(
            Q(description__icontains='GC') | Q(description__icontains='E-TRANSFER') | Q(
                description__icontains='TFR-FR')).aggregate(Sum('amount'))['amount__sum']
        income_total = Income.objects.filter(local_church_id=local_church).aggregate(Sum('amount'))['amount__sum']
        grand_total_contrib = Contribution.objects.filter(local_church_id=local_church).aggregate(Sum('amount'))[
            'amount__sum']
        grand_total_misc = \
            MiscellaneousContribution.objects.filter(local_church_id=local_church).aggregate(Sum('amount'))[
                'amount__sum']

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if 'payment_type' in request.GET:
            payment_type = request.GET.get('payment_type')
            contrib_details = list(
                Contribution.objects.filter(payment_type=payment_type).values(
                    'contributor__full_name', 'amount', 'deposited_date'
                ))
            return JsonResponse({
                'contrib_details': contrib_details,
            })
        elif 'miscellaneous' in request.GET:
            misc_contrib_details = list(MiscellaneousContribution.objects.values(
                'contributor__full_name', 'amount', 'deposited_date'
            ))
            return JsonResponse({
                'misc_contrib_details': misc_contrib_details,
            })

    # for attendance per year chart
    if year:
        year = int(year)
    all_months = [datetime(year, month, 1).strftime('%b') for month in range(1, 13)]
    monthly_attendance_totals = defaultdict(int)
    attendance_data = Attendance.objects.filter(date__year=year)
    if region:
        attendance_data = attendance_data.filter(local_church__region_id=region)
    if local_church:
        attendance_data = attendance_data.filter(local_church_id=local_church)
    monthly_attendance = (
        attendance_data
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(
            total_adult_male=Sum('adult_male'),
            total_adult_female=Sum('adult_female'),
            total_youth_male=Sum('youth_male'),
            total_youth_female=Sum('youth_female'),
            total_children_male=Sum('children_male'),
            total_children_female=Sum('children_female'),
            total_campus_male=Sum('campus_male'),
            total_campus_female=Sum('campus_female'),
            total_cau=Sum('cau'),
            total_visitor=Sum('visitor'),
            total_conv=Sum('conv'),
            total_ypf_male=Sum('ypf_male'),
            total_ypf_female=Sum('ypf_female'),
            total_zoom=Sum('zoom'),
            total_youtube=Sum('youtube')
        )
        .annotate(
            total_attendance=(
                    F('total_adult_male') +
                    F('total_adult_female') +
                    F('total_youth_male') +
                    F('total_youth_female') +
                    F('total_children_male') +
                    F('total_children_female') +
                    F('total_campus_male') +
                    F('total_campus_female') +
                    F('total_cau') +
                    F('total_visitor') +
                    F('total_conv') +
                    F('total_ypf_male') +
                    F('total_ypf_female') +
                    F('total_zoom') +
                    F('total_youtube')
            )
        )
        .order_by('month')
    )
    for attendance in monthly_attendance:
        month_name = attendance['month'].strftime('%b')
        monthly_attendance_totals[month_name] = attendance['total_attendance']

    months = all_months
    attendance_totals = [monthly_attendance_totals[month] for month in months]
    # end attendance chart
    table_data = zip(labels, income_amounts, expense_amounts, balances)

    context = {
        "current_month_income": current_month_income(user=request.user, region=region, local_church=local_church),
        "current_year_income": current_year_income(user=request.user, region=region, local_church=local_church),
        "current_month_expense": current_month_expense(user=request.user, region=region, local_church=local_church),
        "current_year_expense": current_year_expense(user=request.user, region=region, local_church=local_church),
        "total_attendance_for_user_local_church": total_attendance_for_user_local_church(local_church_id=local_church,
                                                                                         region_id=region,
                                                                                         start_date=start_date,
                                                                                         end_date=end_date),
        'table_data': table_data,
        'labels': labels,
        'income_amounts': income_amounts,
        'expense_amounts': expense_amounts,
        "balances": balances,
        'expense_categories': expense_categories,
        'expenses_last_year': expenses_last_year,
        'contributors': get_unique_users_count(request.user),
        'current_month_contributions': current_months_contribution(region_id=region, local_church=local_church),
        'current_year_contributions': current_year_contribution(region_id=region, local_church=local_church),
        'cumulative_ie_chart_data_json': json.dumps(
            cumulative_income_expense_chart(local_church_id=local_church, region_id=region, start_date=start_date,
                                            end_date=end_date)),
        'properties_chart_data_json': json.dumps(
            properties_chart(local_church_id=local_church, region_id=region, start_date=start_date, end_date=end_date)),
        'incoming_amount_local_church_chart_data_json':
            incoming_amount_local_church_chart(local_church_id=local_church, region_id=region, start_date=start_date,
                                               end_date=end_date),
        'expense_amount_local_church_chart_data_json': json.dumps(
            expense_amount_local_church_chart(local_church_id=local_church, region_id=region, start_date=start_date,
                                              end_date=end_date)),
        'monthly_expense_by_category_chart_data_json':
            monthly_expense_by_category_chart(local_church_id=local_church, region_id=region, start_date=start_date,
                                              end_date=end_date),
        'contributions_by_local_church_chart': json.dumps(
            contributions_by_local_church_chart(local_church_id=local_church, region_id=region, start_date=start_date,
                                                end_date=end_date)),
        'attendance_chart_data_json': json.dumps(
            attendance_donut_chart_data(local_church_id=local_church, region_id=region, start_date=start_date,
                                        end_date=end_date)),
        'local_church_list': local_church_list,
        'region_list': region_list,
        'contrib_totals': contrib_totals,
        'grand_total_misc': grand_total_misc,
        'overall_grand_total': overall_grand_total,
        'months': months,
        'attendance_totals': attendance_totals,
        'selected_year': year,
        'years': range(2020, datetime.now().year + 1),
        'income_total': income_total,
        'online_deposited': online_deposited,
        'direct_deposit': direct_deposit,
    }
    return render(request, "organization/dashboard.html", context=context)


# Function to get local churches by region
def get_local_churches_by_region(request):
    region_id = request.GET.get('region_id')
    if region_id:
        local_churches = LocalChurch.objects.filter(region_id=region_id)
    else:
        local_churches = get_user_local_church(request.user)
    local_church_list = [{'id': local_church.id, 'name': local_church.local_church_name.title} for local_church in
                         local_churches]
    return JsonResponse({'local_churches': local_church_list})


# Function to get regions by local church
def get_regions_by_local_church(request):
    local_church_id = request.GET.get('local_church_id')
    if local_church_id:
        try:
            local_church = LocalChurch.objects.get(id=local_church_id)
            region_list = [
                {'id': local_church.region.id, 'name': local_church.region.name}] if local_church.region else [
                {'id': region.id, 'name': region.name} for region in Region.objects.all()]
        except LocalChurch.DoesNotExist:
            region_list = [{'id': region.id, 'name': region.name} for region in Region.objects.all()]
    else:
        region_list = [{'id': region.id, 'name': region.name} for region in Region.objects.all()]

    return JsonResponse({'regions': region_list})


# Function to manage organization reports
def report_management(request):
    if request.method == 'GET':
        churches = get_user_local_church(request.user)

        church_id = request.GET.get('church_id')
        if request.user.role == 2:
            church_id = get_user_local_church(request.user).first().id

        if church_id:
            church_id = int(church_id)
        months = [
            ('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
            ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'),
            ('09', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
        ]

        if church_id:
            reports = DetailReport.objects.filter(local_church_id=church_id).order_by('date')
            reports_dict = {r.date.month: r for r in reports}

            current_year = datetime.now().year
            for month in range(1, 13):
                report_date = datetime(year=current_year, month=month, day=1).date()
                if month not in reports_dict:
                    DetailReport.objects.create(local_church_id=church_id, date=report_date)

            reports = DetailReport.objects.filter(local_church_id=church_id).order_by('date')
            reports_dict = {r.date.month: r for r in reports}

        else:
            reports_dict = {}

        context = {
            'churches': churches,
            'months': months,
            'reports_dict': reports_dict,
            'current_year': datetime.now().year,
            'selected_church_id': church_id
        }
        return render(request, 'organization/detail_report.html', context)

    elif request.method == 'POST':
        local_church_id = request.POST.get('local_church')
        month = request.POST.get('month')
        date_str = f"{datetime.now().year}-{month}-01"
        report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        report, created = DetailReport.objects.update_or_create(
            local_church_id=local_church_id,
            date=report_date,
            defaults={
                'comment': request.POST.get(f'comment_{month}', ''),
                'problem': request.POST.get(f'problem_{month}', ''),
                'testimony': request.POST.get(f'testimony_{month}', ''),
                'follow_up': request.POST.get(f'follow_up_{month}', '')
            }
        )
        messages.success(request, "Successfully updated the detail report")
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


# Function to convert date format
def convert_date_format(date_string):
    try:
        # Assuming the date is in MM/DD/YYYY format
        return datetime.strptime(date_string, '%m/%d/%Y').strftime('%Y-%m-%d')
    except ValueError:
        # If the date format is not valid, return None or handle it accordingly
        return None


# View to manage reconciliation and allocation
def reconciliation_and_allocation(request):
    can_upload = False
    region_id = None
    user = request.user
    all_regions = []
    bank_income = Decimal(0.00)
    bank_expense = Decimal(0.00)
    app_expense = Decimal(0.00)
    app_income = Decimal(0.00)
    current_year = datetime.now().year
    months = [{'value': i, 'name': month_name[i]} for i in range(1, 13)]
    years = list(range(2020, current_year + 1))
    selected_month = request.GET.get('month')
    selected_year = request.GET.get('year')
    app_matches_income = False
    app_matches_expense = False
    last_month = None
    current_month_date = None

    if selected_month and selected_year:
        current_month_date = datetime.strptime(f"{selected_month},{selected_year}", "%m,%Y").replace(day=1)
        last_month = current_month_date - timedelta(days=1)

    if user.is_staff or user.role == 3:
        all_regions = Region.objects.all()
    else:
        all_regions = Region.objects.filter(region_overseer=user)

    if 'region_id' in request.GET and all_regions.count() > 1:
        region_id = request.GET.get('region_id')
        if region_id:
            region_id = int(region_id)

    try:
        user_region = Region.objects.get(region_overseer=request.user)
    except Exception as e:
        print(e)
        user_region = None

    if region_id:
        payment_allocation = PaymentAllocation.objects.filter(region_id=region_id)
        reconciliation_objects = Reconciliation.objects.filter(region_id=region_id)
        can_upload = True
        selected_id = region_id
    elif user_region:
        can_upload = True
        selected_id = user_region.id
        payment_allocation = PaymentAllocation.objects.filter(region=user_region)
        reconciliation_objects = Reconciliation.objects.filter(region=user_region)
    else:
        payment_allocation = []
        reconciliation_objects = []
        can_upload = False
        selected_id = None

    if selected_id:
        income_object_query = Income.objects.filter(
            local_church__region_id=selected_id).aggregate(Sum('amount'))['amount__sum'] or Decimal(0.00)
        contrib_object_query = Contribution.objects.filter(
            local_church__region_id=selected_id).aggregate(Sum('amount'))['amount__sum'] or Decimal(0.00)
        misc_contrib_object_query = MiscellaneousContribution.objects.filter(
            local_church__region_id=selected_id).aggregate(Sum('amount'))['amount__sum'] or Decimal(0.00)
        anon_contrib_object_query = AnonymousContribution.objects.filter(
            local_church__region_id=selected_id).aggregate(Sum('amount'))['amount__sum'] or Decimal(0.00)
        recon_app_expense_query = Expense.objects.filter(
            local_church__region_id=selected_id).aggregate(Sum('amount'))['amount__sum'] or Decimal(0.00)

        if selected_month and selected_year:
            reconciliation_objects = reconciliation_objects.filter(
                date__year=selected_year, date__month=selected_month)
            payment_allocation = payment_allocation.filter(
                date__year=last_month.year, date__month=last_month.month)
            income_object_query = Income.objects.filter(
                local_church__region_id=selected_id,
                date__year=selected_year,
                date__month=selected_month).aggregate(Sum('amount'))['amount__sum'] or Decimal(0.00)
            contrib_object_query = Contribution.objects.filter(
                local_church__region_id=selected_id,
                deposited_date__year=selected_year,
                deposited_date__month=selected_month).aggregate(Sum('amount'))['amount__sum'] or Decimal(0.00)
            misc_contrib_object_query = MiscellaneousContribution.objects.filter(
                local_church__region_id=selected_id,
                deposited_date__year=selected_year,
                deposited_date__month=selected_month).aggregate(Sum('amount'))['amount__sum'] or Decimal(0.00)
            anon_contrib_object_query = AnonymousContribution.objects.filter(
                local_church__region_id=selected_id,
                deposited_date__year=selected_year,
                deposited_date__month=selected_month).aggregate(Sum('amount'))['amount__sum'] or Decimal(0.00)
            recon_app_expense_query = Expense.objects.filter(
                local_church__region_id=selected_id,
                date__year=selected_year,
                date__month=selected_month).aggregate(Sum('amount'))['amount__sum'] or Decimal(0.00)

        app_expense = recon_app_expense_query
        app_income = (income_object_query + contrib_object_query +
                      misc_contrib_object_query + anon_contrib_object_query)
        bank_income = reconciliation_objects.filter(
            recon_type='income').aggregate(Sum('amount'))['amount__sum'] or Decimal(0.00)
        bank_expense = reconciliation_objects.filter(
            recon_type='expense').aggregate(Sum('amount'))['amount__sum'] or Decimal(0.00)

    # helper for redirect
    def redirect_with_params():
        path = request.path
        query_params = request.GET.copy()
        encoded_params = urlencode(query_params)
        return HttpResponseRedirect(f"{path}?{encoded_params}")

    # --- PAYMENT ALLOCATION UPDATE ---
    if 'payment_allocation_id' in request.POST and selected_id:
        payment_allocation_id = request.POST.get('payment_allocation_id')
        payment_date = request.POST.get('payment_date')
        if not payment_date:
            messages.error(request, "Date is required")
            return redirect_with_params()

        payment_date = datetime.strptime(payment_date, "%Y-%m-%d")
        note = request.POST.get('note')
        paid_amount = request.POST.get('paid_amount')

        if payment_allocation_id and paid_amount and payment_date:
            payment_allocation_object = PaymentAllocation.objects.get(id=payment_allocation_id)
            payment_allocation_object.paid_amount = paid_amount
            payment_allocation_object.payment_date = payment_date.date()
            if note:
                payment_allocation_object.note = note
            payment_allocation_object.save()
            messages.success(request, "Payment Updated Successfully")

        return redirect_with_params()

    # --- UPLOAD CSV/XLSX FOR RECONCILIATION ---
    if 'upload_file_for_recon' in request.POST and selected_id:
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            fs = FileSystemStorage()
            filename = fs.save(file.name, file)
            file_path = fs.path(filename)

            try:
                rows = []

                if file.name.endswith('.xlsx'):
                    wb = load_workbook(file_path)
                    ws = wb.active
                    for row in ws.iter_rows(min_row=2, values_only=True):
                        rows.append(row)

                elif file.name.endswith('.csv'):
                    with open(file_path, newline='', encoding='utf-8-sig') as f:
                        reader = csv.reader(f)
                        first_row = next(reader)
                        if re.match(r'\d{1,2}/\d{1,2}/\d{4}', str(first_row[0]).strip()):
                            rows.append(first_row)
                        for row in reader:
                            rows.append(row)
                else:
                    messages.error(request, "Unsupported file type. Please upload CSV or XLSX.")

                saved_count = 0
                errors = []

                for i, row in enumerate(rows, start=1):
                    try:
                        if not any(row) or len(row) < 4:
                            continue

                        date_val, description, expenses, income = row[0], row[1], row[2], row[3]

                        if hasattr(date_val, 'date'):
                            parsed_date = date_val.date()
                        else:
                            parsed_date = None
                            for fmt in ["%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d", "%m-%d-%Y", "%d-%b-%y", "%d-%b-%Y"]:
                                try:
                                    parsed_date = datetime.strptime(str(date_val).strip(), fmt).date()
                                    break
                                except ValueError:
                                    continue

                        if not parsed_date:
                            errors.append(f"Row {i}: Could not parse date '{date_val}'")
                            continue

                        expenses = Decimal(str(expenses).strip()) if expenses is not None and str(expenses).strip() else None
                        income = Decimal(str(income).strip()) if income is not None and str(income).strip() else None

                        if expenses is not None:
                            recon_type = 'expense'
                            amount = expenses
                        elif income is not None:
                            recon_type = 'income'
                            amount = income
                        else:
                            recon_type = 'other'
                            amount = Decimal(0)

                        Reconciliation.objects.create(
                            region_id=selected_id,
                            date=parsed_date,
                            description=str(description).strip() if description else '',
                            recon_type=recon_type,
                            amount=amount,
                        )
                        saved_count += 1

                    except Exception as e:
                        errors.append(f"Row {i}: {str(e)}")

                if saved_count:
                    messages.success(request, f"{saved_count} transactions saved successfully.")
                for error in errors:
                    messages.error(request, error)

            except Exception as e:
                import traceback
                print(traceback.format_exc())
                messages.error(request, f"Error processing file: {str(e)}")
            finally:
                fs.delete(filename)

        return redirect_with_params()  # PRG — prevents resubmit on refresh

    # --- GCK ALLOCATION UPDATE ---
    if "gck_allocation" in request.POST:
        allocation_amount = request.POST.get('allocation_amount')
        if not last_month:
            messages.error(request, 'Please select the month and year')
            return redirect_with_params()

        allocation_object = PaymentAllocation.objects.filter(
            region_id=selected_id,
            date__year=last_month.year,
            date__month=last_month.month,
            name="gck_canada"
        ).first()
        allocation_object.total_amount = allocation_amount
        allocation_object.save()
        return redirect_with_params()

    # --- UPLOAD PDF/CSV/XLSX FOR ALLOCATION RECONCILIATION ---
    if "upload_allocation_reconciliation_bank_statement" in request.POST:
        # Get region from POST hidden input since GET params may not be set
        post_region_id = request.POST.get('selected_region_id')
        if post_region_id:
            selected_id = int(post_region_id)

        if not selected_id:
            messages.error(request, "Please select a region before uploading.")
            return redirect_with_params()

        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            fs = FileSystemStorage()
            filename = fs.save(file.name, file)
            file_path = fs.path(filename)

            try:
                saved_transactions = 0
                duplicate_transactions = 0
                errors = []

                if file.name.endswith('.csv') or file.name.endswith('.xlsx'):
                    rows = []

                    if file.name.endswith('.xlsx'):
                        wb = load_workbook(file_path)
                        ws = wb.active
                        for row in ws.iter_rows(min_row=2, values_only=True):
                            rows.append(row)

                    elif file.name.endswith('.csv'):
                        with open(file_path, newline='', encoding='utf-8-sig') as f:
                            reader = csv.reader(f)
                            first_row = next(reader)
                            if re.match(r'\d{1,2}/\d{1,2}/\d{4}', str(first_row[0]).strip()):
                                rows.append(first_row)
                            for row in reader:
                                rows.append(row)

                    for i, row in enumerate(rows, start=1):
                        try:
                            if not any(row) or len(row) < 4:
                                continue

                            date_val, description, expenses, income = row[0], row[1], row[2], row[3]

                            if hasattr(date_val, 'date'):
                                payment_date = date_val.date()
                            else:
                                payment_date = None
                                for fmt in ["%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d", "%m-%d-%Y"]:
                                    try:
                                        payment_date = datetime.strptime(str(date_val).strip(), fmt).date()
                                        break
                                    except ValueError:
                                        continue

                            if not payment_date:
                                errors.append(f"Row {i}: Could not parse date '{date_val}'")
                                continue

                            expenses = Decimal(str(expenses).strip()) if expenses is not None and str(expenses).strip() else None
                            income = Decimal(str(income).strip()) if income is not None and str(income).strip() else None

                            if expenses is not None:
                                amount = expenses
                            elif income is not None:
                                amount = income
                            else:
                                continue

                            region = Region.objects.filter(id=selected_id).first()
                            if not region:
                                errors.append(f"Row {i}: Region not found")
                                continue

                            allocation, created = AllocationReconciliation.objects.get_or_create(
                                region=region,
                                account_type="dclm_gck",
                                payment_date=payment_date,
                                amount=amount,
                            )

                            if created:
                                saved_transactions += 1
                            else:
                                duplicate_transactions += 1

                        except Exception as e:
                            errors.append(f"Row {i}: {str(e)}")

                elif file.name.endswith('.pdf'):
                    transactions = extract_transactions_from_pdf(file_path)

                    for transaction in transactions:
                        try:
                            region_name = transaction["region_name"].split()[-1]
                            region = Region.objects.filter(name__iexact=region_name).first()
                            if not region:
                                region = Region.objects.filter(name__icontains=region_name).first()
                            if not region:
                                errors.append(f"No region found for: {transaction['region_name']}")
                                continue

                            payment_date = None
                            for fmt in ["%b %d, %Y", "%b  %d, %Y", "%m/%d/%Y", "%Y-%m-%d"]:
                                try:
                                    payment_date = datetime.strptime(transaction["payment_date"].strip(), fmt)
                                    break
                                except ValueError:
                                    continue

                            if not payment_date:
                                errors.append(f"Could not parse date: {transaction['payment_date']}")
                                continue

                            amount = Decimal(transaction["amount"].replace("$", "").replace(",", "").strip())

                            allocation, created = AllocationReconciliation.objects.get_or_create(
                                region=region,
                                account_type="dclm_gck",
                                payment_date=payment_date,
                                amount=amount,
                            )

                            if created:
                                saved_transactions += 1
                            else:
                                duplicate_transactions += 1

                        except Exception as e:
                            errors.append(f"Transaction error: {str(e)}")

                else:
                    messages.error(request, "Unsupported file type. Please upload CSV, XLSX, or PDF.")

                if saved_transactions:
                    messages.success(request, f"{saved_transactions} transactions saved successfully.")
                if duplicate_transactions:
                    messages.warning(request, f"{duplicate_transactions} duplicate transactions skipped.")
                for error in errors:
                    messages.error(request, error)

            except Exception as e:
                import traceback
                print(traceback.format_exc())
                messages.error(request, f"Error processing file: {str(e)}")
            finally:
                fs.delete(filename)

        return redirect_with_params()  # PRG — prevents resubmit on refresh

    # --- FORM FOR GET REQUEST ---
    form = UploadFileForm()

    try:
        if app_income == bank_income:
            app_matches_income = True
        if bank_expense == app_expense:
            app_matches_expense = True
    except Exception as e:
        print(e)

    # --- PAYMENT ALLOCATION RECONCILIATION CONTEXT ---
    payment_allocation_reconciliation_context = {
        'region_name': "None",
        'total_allocation_paid_dclm_gck': 0.00,
        'bank_statement_dclm_gck': 0.00,
        'reconciliation_matched': True,
        "payment_date": "None",
        "account_type": "DCLM/GCK",
        'dclm_total': 0.00,
        'gck_total': 0.00,
    }

    if region_id and selected_month and selected_year:
        try:
            selected_month = int(selected_month)
            selected_year = int(selected_year)
            region_id = int(region_id)

            region = Region.objects.get(id=region_id)

            dclm_total = PaymentAllocation.objects.filter(
                region=region,
                date__year=selected_year,
                date__month=selected_month,
                name='dclm'
            ).aggregate(paid_amount=Sum('paid_amount'))['paid_amount'] or Decimal(0.00)

            gck_total = PaymentAllocation.objects.filter(
                region=region,
                date__year=selected_year,
                date__month=selected_month,
                name='gck'
            ).aggregate(paid_amount=Sum('paid_amount'))['paid_amount'] or Decimal(0.00)

            total_allocation_paid_dclm_gck = dclm_total + gck_total

            bank_statement_dclm_gck = AllocationReconciliation.objects.filter(
                region=region,
                payment_date__year=selected_year,
                payment_date__month=selected_month,
                account_type='dclm_gck'
            ).aggregate(amount=Sum('amount'))['amount'] or Decimal(0.00)

            reconciliation_matched = total_allocation_paid_dclm_gck == bank_statement_dclm_gck

            payment_allocation_reconciliation_context.update({
                'region_name': region.name,
                'total_allocation_paid_dclm_gck': total_allocation_paid_dclm_gck,
                'bank_statement_dclm_gck': bank_statement_dclm_gck,
                'reconciliation_matched': reconciliation_matched,
                'dclm_total': dclm_total,
                'gck_total': gck_total,
            })
        except Region.DoesNotExist:
            messages.error(request, f"Region with ID {region_id} does not exist.")
        except Exception as e:
            messages.error(request, f"Error during payment allocation reconciliation: {str(e)}")

    context = {
        'payment_allocation': payment_allocation,
        'reconciliation_objects': reconciliation_objects,
        'form': form,
        'can_upload': can_upload,
        'all_regions': all_regions,
        'region_id': region_id,
        'user_region': user_region,
        'bank_income': bank_income,
        'bank_expense': bank_expense,
        'app_expense': app_expense,
        'app_income': app_income,
        'months': months,
        'years': years,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'app_matches_income': app_matches_income,
        'app_matches_expense': app_matches_expense,
        'current_month_date': current_month_date,
        **payment_allocation_reconciliation_context
    }
    return render(request, 'organization/reconciliation_and_allocation.html', context)

# Function to download a sample reconciliation file
def download_sample_reconciliation(request):
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sample_reconciliation.csv"'

    # Create a CSV writer
    writer = csv.writer(response)

    # Write the header row
    # writer.writerow(['Date', 'Description', 'Expenses', 'Income', 'Balance'])

    # Write the sample rows as per the format you provided
    sample_data = [
        ['10/3/2022', 'SEND E-TFR ***eUV', '561.6219701', '', '5775.337803'],
        ['10/3/2022', 'SEND E-TFR ***pkD', '345.2836514', '', '5430.054152'],
        ['10/3/2022', 'SEND E-TFR ***zcs', '646.101083', '', '4783.953069'],
        ['10/3/2022', 'SEND E-TFR ***Vqp', '644.662197', '', '4139.290872'],
        ['10/3/2022', 'E-TRANSFER ***vxd', '', '77.35946364', '4216.650335'],
        ['10/3/2022', 'E-TRANSFER ***Rup', '', '51.57297576', '4268.223311'],
        ['10/3/2022', 'E-TRANSFER ***GWT', '', '99.02011346', '4367.243424'],
    ]

    # Write each row of sample data
    for row in sample_data:
        writer.writerow(row)

    return response


# Function to get payment allocation details
def get_payment_allocation(request, id):
    payment_allocation = get_object_or_404(PaymentAllocation, id=id)
    data = {
        'region': payment_allocation.region.name,  # Assuming `Region` model has a `name` field
        'date': payment_allocation.date,
        'income': str(payment_allocation.income),
        'total_amount': str(payment_allocation.total_amount),
        'paid_amount': str(payment_allocation.paid_amount),
        'note': payment_allocation.note,
        'name': payment_allocation.get_name_display(),
    }
    return JsonResponse(data)
