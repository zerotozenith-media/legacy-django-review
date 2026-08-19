# Import necessary modules and classes
from datetime import datetime
from django.contrib import messages
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.shortcuts import redirect, get_object_or_404
from django.views import View
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font
from django.shortcuts import render
from django.http import HttpResponse

from organization.models import Region
from organization.utils import get_user_local_church
from utils.helpers import get_user_regions, get_filtered_context
from .forms import UploadFileForm, InteracContributionForm, EditInteracContributionForm
from authentication.models import User
from contributor.models import Contribution, MiscellaneousContribution, TransactionType, AnonymousContribution
from .helper import handle_uploaded_file, add_contribution, handle_uploaded_for_offering, handle_bank_statement, \
    get_user, create_or_get_miscellaneous_contributor


# View for handling cash donations
class CashDonationView(View):
    def get(self, request):
        login_user = request.user
        try:
            if login_user.is_superuser:
                users = User.objects.all()
            else:
                users = User.objects.filter(local_church=login_user.local_church)
        except Exception as e:
            print(e)
            users = User.objects.none()  # Return an empty queryset if there's an exception

        local_churches = get_user_local_church(login_user)
        # Render the cash donation form
        return render(request, "contributors/donation-cash__add-edit.html",
                      {'users': users, 'local_churches': local_churches})

    def post(self, request):
        # Get form data
        local_church_id = request.POST.get('local_church')
        toggle_switch_value = request.POST.get('toggleSwitch')
        donor_value = request.POST.get('donor')
        name = request.POST.get('miscellaneous')
        date = request.POST.get('donation_date')
        amount = request.POST.get('amount')
        special_contribution = request.POST.get('specialToggleSwitch')
        anonymous_contribution = request.POST.get('anonymous_donor')
        date_object = datetime.strptime(str(date), '%Y-%m-%d')
        month_name = date_object.strftime('%B')

        try:
            # Handle different types of donations based on the toggle switch value
            if toggle_switch_value == 'on':
                miscellaneous_data = {
                    "local_church_id": local_church_id,
                    "contributor_name": name,
                    "type": TransactionType.OFFERINGS_CAN.value,
                    "deposit_date": date,
                    "amount": Decimal(amount),
                    "special_contribution": special_contribution == 'on',
                    "registered_by": request.user,
                }
                add_contribution(**miscellaneous_data)
            elif anonymous_contribution:
                AnonymousContribution.objects.create(
                    local_church_id=local_church_id,
                    payment_type=TransactionType.OFFERINGS_CAN.value,
                    deposited_date=date_object,
                    amount=amount,
                    special_contribution=special_contribution == 'on',
                    month=month_name
                )
            else:
                user = User.objects.get(id=int(donor_value))
                contributor_data = {
                    "local_church_id": local_church_id,
                    "contributor_name": user.full_name,
                    "type": TransactionType.OFFERINGS_CAN.value,
                    "deposit_date": date,
                    "amount": Decimal(amount),
                    "special_contribution": special_contribution == 'on'
                }
                add_contribution(**contributor_data)
            messages.success(request, "Donation successfully added!")
        except Exception as e:
            print(str(e))
            messages.error(request, "Something went wrong")
            return redirect('cash-donation')

        return redirect('cash-donation-list')


def edit_cash_donations(request):
    return render(request, 'contributors/edit_cash_donations.html')



def offerings_USD_edit(request):    
    return render(request, 'contributors/offerings_USD_edit.html')


# View for handling USD offerings
class OfferingsUSDView(View):
    def get(self, request):
        login_user = request.user
        try:
            if login_user.is_superuser:
                users = User.objects.all()
            else:
                users = User.objects.filter(local_church=login_user.local_church)
        except Exception as e:
            print(e)
            users = User.objects.none()  # Return an empty queryset if there's an exception

        local_churches = get_user_local_church(login_user)
        # Render the USD offerings form
        return render(request, "contributors/offerings_USD_add.html",
                      {'users': users, 'local_churches': local_churches})

    def post(self, request):
        # Get form data
        local_church_id = request.POST.get('local_church')
        toggle_switch_value = request.POST.get('toggleSwitch')
        donor_value = request.POST.get('donor')
        name = request.POST.get('miscellaneous')
        date = request.POST.get('donation_date')
        amount = request.POST.get('amount')
        special_contribution = request.POST.get('specialToggleSwitch')
        anonymous_contribution = request.POST.get('anonymous_donor')
        date_object = datetime.strptime(str(date), '%Y-%m-%d')
        month_name = date_object.strftime('%B')

        try:
            # Handle different types of donations based on the toggle switch value
            if toggle_switch_value == 'on':
                miscellaneous_data = {
                    "local_church_id": local_church_id,
                    "contributor_name": name,
                    "type": TransactionType.OFFERINGS_USD.value,
                    "deposit_date": date,
                    "amount": Decimal(amount),
                    "special_contribution": special_contribution == 'on'
                }
                add_contribution(**miscellaneous_data)
            elif anonymous_contribution:
                AnonymousContribution.objects.create(
                    local_church_id=local_church_id,
                    payment_type=TransactionType.OFFERINGS_CAN.value,
                    deposited_date=date_object,
                    amount=amount,
                    special_contribution=special_contribution == 'on',
                    month=month_name
                )
            else:
                user = User.objects.get(id=int(donor_value))
                contributor_data = {
                    "local_church_id": local_church_id,
                    "contributor_name": user.full_name,
                    "type": TransactionType.OFFERINGS_USD.value,
                    "deposit_date": date,
                    "amount": Decimal(amount),
                    "special_contribution": special_contribution == 'on'
                }
                add_contribution(**contributor_data)
            messages.success(request, "Donation successfully added!")
        except Exception as e:
            print(str(e))
            messages.error(request, "Something went wrong")
            return redirect('offerings_usd_add')

        return redirect('offerings_usd_list')


# Function to list cash donations
def cash_donation_list(request):
    user = request.user
    local_churches = get_user_local_church(user)
    region = request.GET.get("region", None)
    regions = get_user_regions(user)

    if region:
        region_list = regions.filter(name__iexact=region)
        local_churches = local_churches.filter(region__in=region_list)

    # Filter contributions based on the payment type and local churches
    contribution = Contribution.objects.filter(payment_type=TransactionType.OFFERINGS_CAN.value,
                                               local_church__in=local_churches)
    miscellaneous = MiscellaneousContribution.objects.select_related('contributor').filter(
        payment_type=TransactionType.OFFERINGS_CAN.value, local_church__in=local_churches)
    anonymous = AnonymousContribution.objects.filter(payment_type=TransactionType.OFFERINGS_CAN.value, deleted=False,
                                                     local_church__in=local_churches)

    contribution, filter_context = get_filtered_context(
        request,
        contribution,
        model_field_map={
            "region": "local_church__region__name",
            "local_church": "local_church_id"
        }
    )
    miscellaneous, filter_context = get_filtered_context(
        request,
        miscellaneous,
        model_field_map={
            "region": "local_church__region__name",
            "local_church": "local_church_id"
        }
    )
    anonymous, filter_context = get_filtered_context(
        request,
        anonymous,
        model_field_map={
            "region": "local_church__region__name",
            "local_church": "local_church_id"
        }
    )
    context = {
        "contribution": contribution,
        "miscellaneous": miscellaneous,
        "anonymous": anonymous,
        "regions": regions,
        "churches": local_churches,
        **filter_context
    }
    return render(request, 'contributors/cash_donation_list.html', context)


# Function to list USD offerings
def offerings_usd_list(request):
    user = request.user
    local_churches = get_user_local_church(user)
    region = request.GET.get("region", None)
    regions = get_user_regions(user)

    if region:
        region_list = regions.filter(name__iexact=region)
        local_churches = local_churches.filter(region__in=region_list)

    contribution = Contribution.objects.filter(
        payment_type=TransactionType.OFFERINGS_USD.value, local_church__in=local_churches
    ).order_by('-modified_date')

    miscellaneous = MiscellaneousContribution.objects.select_related('contributor').filter(
        payment_type=TransactionType.OFFERINGS_USD.value, local_church__in=local_churches
    ).order_by('-modified_date')

    contribution, filter_context = get_filtered_context(
        request,
        contribution,
        model_field_map={
            "region": "local_church__region__name",
            "local_church": "local_church_id"
        }
    )
    miscellaneous, filter_context = get_filtered_context(
        request,
        miscellaneous,
        model_field_map={
            "region": "local_church__region__name",
            "local_church": "local_church_id"
        }
    )

    context = {
        "contribution": contribution,
        "miscellaneous": miscellaneous,
        "regions": regions,
        "churches": local_churches,
        **filter_context
    }
    return render(request, 'contributors/offerings_USD_list.html', context)


# Function to list Interac transfers
def interac_transfer_list(request):
    user = request.user
    local_churches = get_user_local_church(user)
    region = request.GET.get("region", None)
    regions = get_user_regions(user)

    if region:
        region_list = regions.filter(name__iexact=region)
        local_churches = local_churches.filter(region__in=region_list)

    bank_payment_type_list = ['interec_e_transfer', 'direct_transfer', 'cheque_deposit']
    # Filter contributions based on the payment type list
    contribution = Contribution.objects.filter(payment_type__in=bank_payment_type_list)
    miscellaneous = MiscellaneousContribution.objects.select_related('contributor').filter(
        payment_type__in=bank_payment_type_list)

    if user.role == 2 or user.role == 4:
        contribution = contribution.filter(local_church__in=local_churches)
        miscellaneous = miscellaneous.filter(local_church__in=local_churches)

    contribution, filter_context = get_filtered_context(
        request,
        contribution,
        model_field_map={
            "region": "local_church__region__name",
            "local_church": "local_church_id"
        }
    )
    miscellaneous, filter_context = get_filtered_context(
        request,
        miscellaneous,
        model_field_map={
            "region": "local_church__region__name",
            "local_church": "local_church_id"
        }
    )

    context = {
        "contribution": contribution,
        "miscellaneous": miscellaneous,
        "regions": regions,
        "churches": local_churches,
        **filter_context
    }
    return render(request, 'contributors/interac_transfer_list.html', context)


# Function to download a sample file for contributions
def download_sample(request, type):
    # Create a new workbook and add a worksheet
    workbook = Workbook()
    worksheet = workbook.active
    if TransactionType.OFFERINGS_CAN.value == type or TransactionType.OFFERINGS_USD.value == type or \
            TransactionType.INTEREC_E_TRANSFER.value == type:
        # Add headers for cash and USD offerings
        headers = ['First Name', 'Middle Name', 'Last Name', 'Email', 'Address', 'Date Deposited', 'Amount']
        worksheet.append(headers)
        header_row = worksheet[1]
        for cell in header_row:
            cell.font = Font(bold=True)
        data = [
            ['Liam', 'Andrew', 'Thompson', 'liam.thompson1@example.com', '123 Maple Street, Toronto, ON M5V 2T6',
             '2024-12-23', '$500'],
            ['Emily', '', 'Robertson', 'emily.robertson@example.com', '456 Oak Avenue, Vancouver, BC V6B 1A8',
             '2024-12-18', '$400'],
            ['Noah', 'James', 'Mitchell', 'emily.robertson@example.com', '456 Oak Avenue, Vancouver, BC V6B 1A8',
             '2024-12-13', '60'],
            ['Sophia', '', 'Carter', 'sophia.carter22@example.com', '321 Elm Road, Montreal, QC H2Y 3E4', '2024-12-20',
             '80']
        ]
        for sample_data in data:
            worksheet.append(sample_data)
    else:
        # Add headers for other types of contributions
        headers = ['Date Deposited', 'Received From', 'Amount']
        worksheet.append(headers)
        header_row = worksheet[1]
        for cell in header_row:
            cell.font = Font(bold=True)

        # Add sample rows
        sample_data = ['2024-11-17', 'Redwan Zaman', '$19.000']
        worksheet.append(sample_data)

    # Set column widths for better readability
    for col_num, column_letter in enumerate(get_column_letter(len(headers)), start=1):
        worksheet.column_dimensions[column_letter].width = 15

    # Create a response object with the XLSX content
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    file_type = type + '_sample_file.xlsx'
    response['Content-Disposition'] = f'attachment; filename={file_type}'
    workbook.save(response)

    return response


# Function to handle file uploads
def upload_file(request):
    local_churches = get_user_local_church(request.user)
    type = TransactionType.INTEREC_E_TRANSFER.value
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        local_church_id = request.POST.get('local_church')
        if form.is_valid():
            errors = handle_uploaded_file(request.FILES['file'], local_church_id)
            if errors:
                return render(request, 'contributors/upload.html', {'form': form, 'errors': errors, 'type': type})
            success_message = 'File uploaded and processed successfully!'
            return render(request, 'contributors/upload.html',
                          {'form': form, 'success_message': success_message, 'type': type})
    else:
        form = UploadFileForm()
    return render(request, 'contributors/upload.html', {'form': form, 'type': type, 'local_churches': local_churches})


# Function to handle bank statement imports
@login_required
def bank_statement_importer(request):
    _type = TransactionType.INTEREC_E_TRANSFER.value
    user = request.user
    region_list = []

    # Fetch regions based on user role
    if user.role == 3 or user.is_staff:
        region_list = Region.objects.all().order_by('name')
    elif user.role == 4:
        region_list = Region.objects.filter(region_overseer=user).order_by('name')

    # Handle POST request
    if request.method == 'POST':
        file = request.FILES.get('file')
        region_id = request.POST.get('region')
        account_type = request.POST.get('account_type')

        # Validation
        if not file:
            messages.error(request, "No file uploaded. Please upload a valid bank statement.")
        elif not region_id:
            messages.error(request, "No region selected. Please select a valid region.")
        elif not account_type:
            messages.error(request, "No account type selected. Please select a valid account type.")
        else:
            errors = handle_bank_statement(file, region_id, account_type)
            if errors:
                messages.error(request, "Some errors occurred during processing. Please review and retry.")
            else:
                messages.success(request, "Bank statement uploaded and processed successfully!")

    return render(request, 'contributors/bank_statement_importer.html', {
        'type': _type,
        'regions': region_list,
    })


# Function to handle offerings uploads
def offerings_uploader_view(request, type):
    login_in_user = request.user
    local_churches = get_user_local_church(login_in_user)
    if request.method == 'POST':
        local_church_id = request.POST.get('local_church')
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            if not (any(type == item.value for item in TransactionType)):
                return render(request, 'contributors/upload.html',
                              {'form': form, 'errors': {'error': 'invalid offering type'}, 'type': type})
            errors = handle_uploaded_for_offering(request.FILES['file'], type, local_church_id=local_church_id, registered_by=request.user)
            if errors:
                return render(request, 'contributors/upload.html', {'form': form, 'errors': errors, 'type': type})
            success_message = 'File uploaded and processed successfully!'
            messages.success(request, success_message)

            if type == "interec_e_transfer":
                return redirect('interac_transfer_list')

            return render(request, 'contributors/upload.html',
                          {'form': form, 'success_message': success_message, 'type': type})
    else:
        form = UploadFileForm()
    return render(request, 'contributors/upload.html', {'form': form, 'type': type, 'local_churches': local_churches})


# View for adding Interac contributions
class InteracAddView(View):
    def get(self, request):
        login_in_user = request.user
        local_churches = get_user_local_church(login_in_user)
        # Render the Interac contribution form
        return render(request, "contributors/interac_add.html", {'local_churches': local_churches})

    def post(self, request):
        try:
            # Get form data
            local_church_id = request.POST.get('local_church')
            name = request.POST.get('name')
            date = request.POST.get('date')
            amount = request.POST.get('amount')
            payment_type = request.POST.get('payment_type')
            special_contribution = request.POST.get("special_contribution")
            data = {
                "local_church_id": local_church_id,
                "contributor_name": name,
                "type": payment_type,
                "deposit_date": date,
                "amount": amount,
                "special_contribution": special_contribution == 'on'
            }
            add_contribution(**data)
            messages.success(request, "Donation successfully added!")
        except Exception as e:
            print(str(e))
            messages.error(request, "Something went wrong")
            return redirect('add-interac')

        return redirect('interac_transfer_list')


# Function to calculate the total contribution for the current month
def current_months_contribution(region_id=None, local_church=None):
    current_year = datetime.now().year
    current_month = datetime.now().month
    known = Contribution.objects.filter(
        deposited_date__month=current_month, deposited_date__year=current_year
    )
    if region_id:
        known = known.filter(local_church__region_id=region_id)
    if local_church:
        known = known.filter(local_church_id=local_church)

    known = known.aggregate(total=Sum('amount'))['total'] or 0.0

    miscellaneous = MiscellaneousContribution.objects.filter(
        deposited_date__month=current_month, deposited_date__year=current_year
    )
    if region_id:
        miscellaneous = miscellaneous.filter(local_church__region_id=region_id)
    if local_church:
        miscellaneous = miscellaneous.filter(local_church_id=local_church)
    miscellaneous = miscellaneous.aggregate(total=Sum('amount'))['total'] or 0.0

    anonymous = AnonymousContribution.objects.filter(
        deposited_date__month=current_month, deposited_date__year=current_year
    )
    if region_id:
        anonymous = anonymous.filter(local_church__region_id=region_id)
    if local_church:
        anonymous = anonymous.filter(local_church_id=local_church)
    anonymous = anonymous.aggregate(total=Sum('amount'))['total'] or 0.0

    total_contribution = float(known) + float(miscellaneous) + float(anonymous)

    return total_contribution


# Function to calculate the total contribution for the current year
def current_year_contribution(region_id=None, local_church=None):
    current_year = datetime.now().year

    known = Contribution.objects.filter(
        deposited_date__year=current_year
    )
    if region_id:
        known = known.filter(local_church__region_id=region_id)
    if local_church:
        known = known.filter(local_church_id=local_church)
    known = known.aggregate(total=Sum('amount'))['total'] or 0.0

    miscellaneous = MiscellaneousContribution.objects.filter(
        deposited_date__year=current_year
    )
    if region_id:
        miscellaneous = miscellaneous.filter(local_church__region_id=region_id)
    if local_church:
        miscellaneous = miscellaneous.filter(local_church_id=local_church)
    miscellaneous = miscellaneous.aggregate(total=Sum('amount'))['total'] or 0.0

    anonymous = AnonymousContribution.objects.filter(
        deposited_date__year=current_year
    )
    if region_id:
        anonymous = anonymous.filter(local_church__region_id=region_id)
    if local_church:
        anonymous = anonymous.filter(local_church_id=local_church)
    anonymous = anonymous.aggregate(total=Sum('amount'))['total'] or 0.0

    total_contribution = float(known) + float(miscellaneous) + float(anonymous)

    return total_contribution


class SingleInteracContributionCreateView(LoginRequiredMixin, View):
    """View to handle creating a new Single Interac contribution."""
    template_name = "contributors/add_single_interac.html"
    login_url = '/authentication/login'
    redirect_field_name = 'next'

    def get(self, request):
        """Render the Interac contribution form."""
        form = InteracContributionForm(user=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        """Handle form submission."""
        form = InteracContributionForm(request.POST, user=request.user)

        if form.is_valid():
            try:
                form.save()  # The `save` method handles the `add_contribution` logic
                messages.success(request, "Interac contribution successfully added!")
                return redirect('interac_transfer_list')
            except Exception as e:
                print(str(e))
                messages.error(request, "Something went wrong")
                return redirect('add-single-interac')

        messages.error(request, "Please correct the errors below.")
        return render(request, self.template_name, {'form': form})


class Offerings(View):
    def get(self, request, id, type, currency):
        login_user = request.user
        try:
            if login_user.is_superuser:
                users = User.objects.all()
            else:
                users = User.objects.filter(local_church=login_user.local_church)
        except Exception as e:
            print(e)
            users = User.objects.none()  # Return an empty queryset if there's an exception

        local_churches = get_user_local_church(login_user)
        # Render the USD offerings form

        # Get the contribution depending on the type
        contribution = None
        if id and type:
            if type == "Contribution":
                contribution = get_object_or_404(Contribution, id=id)
            elif type == "Anonymous":
                contribution = get_object_or_404(AnonymousContribution, id=id)
            else:
                contribution = get_object_or_404(MiscellaneousContribution, id=id)

        return render(request, "contributors/offerings_Update.html",
                      {'users': users, 'local_churches': local_churches,  'contribution': contribution, "type": type,
                       "currency": currency})

    def post(self, request, id, type, currency):
        # Get form data
        local_church_id = request.POST.get('local_church')
        toggle_switch_value = request.POST.get('toggleSwitch')
        donor_value = request.POST.get('donor')
        name = request.POST.get('miscellaneous')
        date = request.POST.get('donation_date')
        amount = request.POST.get('amount')
        special_contribution = request.POST.get('specialToggleSwitch')
        anonymous_contribution = request.POST.get('anonymous_donor')

        # Validate date format
        try:
            date_object = datetime.strptime(date, '%Y-%m-%d')
            month_name = date_object.strftime('%B')
        except ValueError:
            # Handle invalid date
            messages.error(request, "Please enter a valid date in the format YYYY-MM-DD.")
            return redirect(request.META.get('HTTP_REFERER', 'fallback_url'))  # Redirect back to the form

        try:
            # Handle different types of donations based on the toggle switch value

            if toggle_switch_value == 'on':
                miscellaneous_data = {
                    "local_church_id": local_church_id,
                    "contributor_name": name,
                    "type": TransactionType.OFFERINGS_USD.value if currency == "USD" else
                    TransactionType.OFFERINGS_CAN.value,
                    "deposit_date": date,
                    "amount": Decimal(amount),
                    "special_contribution": special_contribution == 'on'
                }

                if type == "Miscellaneous":
                    miscellaneous_contribution = get_object_or_404(MiscellaneousContribution, id=id)
                    miscellaneous_contribution.local_church_id = local_church_id
                    miscellaneous_contribution.contributor = miscellaneous_contribution.contributor
                    miscellaneous_contribution.payment_type = TransactionType.OFFERINGS_USD.value \
                        if currency == "USD" else TransactionType.OFFERINGS_CAN.value,
                    miscellaneous_contribution.deposit_date = date_object
                    miscellaneous_contribution.amount = Decimal(amount)
                    miscellaneous_contribution.month = month_name
                    miscellaneous_contribution.special_contribution = special_contribution == 'on'
                    miscellaneous_contribution.save()
                else:
                    if type == "Contribution":
                        Contribution.objects.filter(id=id).first().delete()
                    else:
                        AnonymousContribution.objects.filter(id=id).first().delete()

                    add_contribution(**miscellaneous_data)

            elif anonymous_contribution:
                anonymous_data = {
                    "local_church_id": local_church_id,
                    "payment_type": TransactionType.OFFERINGS_USD.value if currency == "USD" else
                    TransactionType.OFFERINGS_CAN.value,
                    "deposited_date": date_object,
                    "amount": Decimal(amount),
                    "month": month_name,
                    "special_contribution": special_contribution == 'on'
                }

                # Update the AnonymousContribution with the provided id
                if type == "Anonymous":
                    anonymous_contribution = get_object_or_404(AnonymousContribution, id=id)
                    for key, value in anonymous_data.items():
                        setattr(anonymous_contribution, key, value)
                    anonymous_contribution.save()
                else:
                    if type == "Contribution":
                        Contribution.objects.filter(id=id).first().delete()
                    else:
                        MiscellaneousContribution.objects.filter(id=id).first().delete()
                    AnonymousContribution.objects.create(**anonymous_data)
            else:
                user = User.objects.get(id=int(donor_value))

                # Update the Contribution with the provided id
                if type == "Contribution":
                    contribution = get_object_or_404(Contribution, id=id)
                    contribution.local_church_id = local_church_id
                    contribution.contributor = user
                    contribution.payment_type = TransactionType.OFFERINGS_USD.value if currency == "USD" else \
                        TransactionType.OFFERINGS_CAN.value
                    contribution.contributor_name = user.full_name if user else name
                    contribution.deposited_date = date_object
                    contribution.amount = Decimal(amount)
                    contribution.special_contribution = special_contribution == 'on'
                    contribution.month = month_name
                    contribution.save()
                else:
                    if type == "Anonymous":
                        AnonymousContribution.objects.filter(id=id).first().delete()
                    else:
                        MiscellaneousContribution.objects.filter(id=id).first().delete()
                    Contribution.objects.create(
                        local_church_id=local_church_id,
                        contributor=user,
                        payment_type=TransactionType.OFFERINGS_USD.value if currency == "USD" else
                        TransactionType.OFFERINGS_CAN.value,
                        deposited_date=date_object,
                        amount=amount,
                        special_contribution=special_contribution == 'on',
                        month=month_name
                    )

            messages.success(request, "Donation successfully updated!")

        except Exception as e:
            print(str(e))
            messages.error(request, "Something went wrong")
            return redirect('offerings', id=id, type=type, currency=currency)

        if currency == "USD":
            return redirect('offerings_usd_list')
        return redirect('cash-donation-list')

    def delete(self, request, id, type, currency):

        try:
            login_user = request.user
            if login_user.role != 1:
                if type == "Contribution":
                    Contribution.objects.filter(id=id).first().delete()
                elif type == "Anonymous":
                    AnonymousContribution.objects.filter(id=id).first().delete()
                else:
                    MiscellaneousContribution.objects.filter(id=id).first().delete()

            messages.success(request, "Donation successfully Deleted!")
        except Exception as e:
            print(str(e))
            messages.error(request, "Something went wrong")
            return redirect(request.META.get('HTTP_REFERER', 'fallback_url'))

        return redirect(request.META.get('HTTP_REFERER', 'fallback_url'))


class ManageBankDonation(View):
    def get(self, request, id, type):
        login_in_user = request.user
        local_churches = get_user_local_church(login_in_user)

        # Get the contribution depending on the type
        contribution = None
        if id and type:
            if type == "Contribution":
                contribution = get_object_or_404(Contribution, id=id)
            else:
                contribution = get_object_or_404(MiscellaneousContribution, id=id)
        return render(request, "contributors/interac_edit.html", {'local_churches': local_churches,

                                                                  "contribution": contribution})
    def post(self, request, id, type,):
        try:
            # Get form data
            local_church_id = request.POST.get('local_church')
            # name = request.POST.get('name')
            date = request.POST.get('date')
            amount = request.POST.get('amount')
            payment_type = request.POST.get('payment_type')
            special_contribution = request.POST.get("special_contribution") == 'on'
            print(special_contribution)

            # Validate date format
            try:
                date_object = datetime.strptime(date, '%Y-%m-%d')
                month_name = date_object.strftime('%B')
            except ValueError:
                # Handle invalid date
                messages.error(request, "Please enter a valid date in the format YYYY-MM-DD.")
                return redirect(request.META.get('HTTP_REFERER', 'fallback_url'))  # Redirect back to the form

            if type == "Miscellaneous":
                miscellaneous_contribution = get_object_or_404(MiscellaneousContribution, id=id)
                miscellaneous_contribution.local_church_id = local_church_id
                miscellaneous_contribution.payment_type = payment_type
                miscellaneous_contribution.deposited_date = date_object
                miscellaneous_contribution.amount = Decimal(amount)
                miscellaneous_contribution.month = month_name
                miscellaneous_contribution.special_contribution = special_contribution
                miscellaneous_contribution.save()
            else:
                contribution = get_object_or_404(Contribution, id=id)
                contribution.local_church_id = local_church_id
                contribution.payment_type = payment_type
                contribution.deposited_date = date_object
                contribution.amount = Decimal(amount)
                contribution.month = month_name
                contribution.special_contribution = special_contribution
                contribution.save()
            messages.success(request, "Donation successfully updated!")
        except Exception as e:
            print(str(e))
            messages.error(request, "Something went wrong")
            return redirect(request.META.get('HTTP_REFERER', 'fallback_url'))

        return redirect('interac_transfer_list')

    def delete(self, request, id, type):

        try:
            login_user = request.user
            if login_user.role != 1:
                if type == "Contribution":
                    Contribution.objects.filter(id=id).first().delete()
                elif type == "Anonymous":
                    AnonymousContribution.objects.filter(id=id).first().delete()
                else:
                    MiscellaneousContribution.objects.filter(id=id).first().delete()

            messages.success(request, "Donation successfully Deleted!")
        except Exception as e:
            print(str(e))
            messages.error(request, "Something went wrong")
            return redirect(request.META.get('HTTP_REFERER', 'fallback_url'))

        return redirect(request.META.get('HTTP_REFERER', 'fallback_url'))


class ManageSingleInteracContributionCreateView(LoginRequiredMixin, View):
    """View to handle editing a Single Interac contribution."""
    template_name = "contributors/single_interac_edit.html"
    login_url = '/authentication/login'
    redirect_field_name = 'next'

    def get(self, request, id, type):
        """Render the Interac contribution form."""
        # Retrieve the instance based on type
        contribution = None
        if id and type:
            if type == "Contribution":
                contribution = get_object_or_404(Contribution, id=id)
            else:
                contribution = get_object_or_404(MiscellaneousContribution, id=id)

            # Initialize the form with the instance and user
        form = EditInteracContributionForm(user=request.user, id=id, type=type)

        return render(request, self.template_name, {"form": form, "contribution": contribution})

    def post(self, request, id, type):
        """Handle form submission."""
        form = EditInteracContributionForm(request.POST, user=request.user, id=id, type=type)

        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Interac contribution successfully updated!")
                return redirect('interac_transfer_list')
            except Exception as e:
                print(str(e))
                messages.error(request, "Something went wrong")
                return redirect("interec_e_transfer", id=id, type=type)

        messages.error(request, "Please correct the errors below.")
        return redirect("interec_e_transfer", id=id, type=type)

    def delete(self, request, id, type):

        try:
            login_user = request.user
            if login_user.role != 1:
                if type == "Contribution":
                    Contribution.objects.filter(id=id).first().delete()
                elif type == "Anonymous":
                    AnonymousContribution.objects.filter(id=id).first().delete()
                else:
                    MiscellaneousContribution.objects.filter(id=id).first().delete()

            messages.success(request, "Donation successfully Deleted!")
        except Exception as e:
            print(str(e))
            messages.error(request, "Something went wrong")
            return redirect(request.META.get('HTTP_REFERER', 'fallback_url'))

        return redirect(request.META.get('HTTP_REFERER', 'fallback_url'))

