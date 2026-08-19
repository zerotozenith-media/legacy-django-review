from datetime import datetime
import calendar
from zipfile import ZipFile
from django.contrib import messages
from django.contrib.postgres.aggregates import BoolOr, StringAgg
from django.core.mail import EmailMessage
from django.db.models import Q, CharField
from django.db.models.functions import Cast
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now
from django.views import View
from django.views.generic import ListView
from django.db.models import Count, Sum, Max
from authentication.models import User
from contributor.models import Contribution, TransactionType, EmailQueue
from wkhtmltopdf.views import PDFTemplateResponse
import io
from io import BytesIO
import PyPDF2
from income.models import DonationInKind
from organization.models import LocalChurch
import base64
from core import settings
from utils.send_emails import send_email

admin_sender = settings.DEFAULT_FROM_EMAIL

def get_months():
    month_dict = {}
    for month in range(1, 13):
        month_name = calendar.month_name[month]
        month_dict[month_name] = []
    return month_dict


def calculate_special_contributions(year, contributor_id):
    result_dict = get_months()
    result_dict = {key: 0.0 for key in result_dict}

    month_wise_special_contributions = (
        Contribution.objects
        .filter(contributor=contributor_id)
        .filter(deposited_date__year=year)
        .filter(special_contribution=True)  # Filter by special contribution
        .values('month')
        .annotate(total_special_amount=Sum('amount'))
        .order_by('month')
    )

    result_list = list(month_wise_special_contributions)

    # result_dict = {entry['month']: float(entry['total_special_amount']) for entry in result_list}
    for entry in result_list:
        result_dict[entry['month']] = float(entry['total_special_amount'])
    return result_dict


def formatted_date_for_report(date):
    day = str(date.day)
    if day[-1] == '2':
        day += 'nd'
    elif day[-1] == '3':
        day += 'rd'
    elif day[-1] == '1':
        day += 'st'
    else:
        day += 'th'
    return day


def contributors_info_dict(payment_type, local_church=None):
    contribution_dict = {}
    contributor_ids = Contribution.objects.filter(payment_type=payment_type).values_list('contributor', flat=True).distinct()
    if local_church:
        contributor_ids = Contribution.objects.filter(payment_type=payment_type, local_church=local_church).values_list('contributor',
                                                                                             flat=True).distinct()
    contributors = User.objects.filter(id__in=contributor_ids)
    for donor in contributors:
        contribution_dict[donor.id] = {
            "id": donor.id,
            "first_name": donor.first_name if donor.first_name else '',
            "middle_name": donor.middle_name if donor.middle_name else '',
            "last_name": donor.last_name if donor.last_name else '',
            "full_name": donor.full_name if donor.full_name else '',
            "email": donor.email,
            "address": donor.address if donor.address else '',
            "donations": get_months(),
        }
    return contribution_dict


def receipts_index(request):
    return render(request, 'contributors/receipts_index.html')


def offering_can_summary_report(request):
    local_churches = []
    if request.method == 'GET' and request.GET.get('local_church') and request.GET.get('local_church') != 'all':
        selected_local_church_id = int(request.GET.get('local_church'))
        local_church_name = LocalChurch.objects.get(id=selected_local_church_id).local_church_name.title
        all_contributors_data = contributors_info_dict(TransactionType.OFFERINGS_CAN.value, local_church=selected_local_church_id)
        report_year = request.GET.get('year', datetime.now().year - 1)
        local_churches = []
        if request.user.is_staff or request.user.role == 3:
            local_churches = LocalChurch.objects.all().order_by('local_church_name__title')
        if request.user.role == 2:
            local_churches = LocalChurch.objects.filter(local_church_pastor=request.user).order_by('local_church_name__title')
        if request.user.role == 4:
            local_churches = LocalChurch.objects.filter(region__region_overseer=request.user).order_by('local_church_name__title')

        context = {
            "contributors": all_contributors_data,
            "report_year": report_year,
            "local_churches": local_churches,
            "local_church_name": local_church_name,
        }
        return render(request, "contributors/offerings_can_receipt_list.html", context)
    else:
        all_contributors_data = contributors_info_dict(TransactionType.OFFERINGS_CAN.value)
        report_year = request.GET.get('year', datetime.now().year - 1)
        if request.user.is_staff or request.user.role == 3:
            local_churches = LocalChurch.objects.all().order_by('local_church_name__title')
        if request.user.role == 2:
            local_churches = LocalChurch.objects.filter(local_church_pastor=request.user).order_by('local_church_name__title')
        if request.user.role == 4:
            local_churches = LocalChurch.objects.filter(region__region_overseer=request.user).order_by('local_church_name__title')
        context = {
            "contributors": all_contributors_data,
            "report_year": report_year,
            "local_churches": local_churches,
        }
        return render(request, "contributors/offerings_can_receipt_list.html", context)


def prepare_offerings_summary_report_data(request):
    if request.GET.get('local_church') and request.GET.get('local_church') != 'all':
        selected_local_church_id = int(request.GET.get('local_church'))
        contribution_dict = contributors_info_dict(TransactionType.OFFERINGS_CAN.value, local_church=selected_local_church_id)
    else:
        contribution_dict = contributors_info_dict(TransactionType.OFFERINGS_CAN.value)
    report_year = request.GET.get('year', datetime.now().year - 1)
    for key in contribution_dict.keys():
        total_donation = 0.0
        contributor_data = Contribution.objects.filter(contributor_id=key, deposited_date__year=report_year,
                                                       payment_type=TransactionType.OFFERINGS_CAN.value)
        contributor_data.order_by('deposited_date')
        special = calculate_special_contributions(report_year, key)
        contribution_dict[key]['special_contribution'] = special
        for data in contributor_data:
            formatted_date = formatted_date_for_report(data.deposited_date)
            month_name = data.month
            temp_dict = {
                "month": month_name,
                "formatted_date": formatted_date,
                "amount": round(float(data.amount), 6),
            }
            contribution_dict[data.contributor_id]['donations'][month_name].append(temp_dict)
            total_donation += round(float(data.amount), 6)
        contribution_dict[key]['total_donation'] = total_donation

    return contribution_dict


def generate_pdf_for_offerings_can_report(request):
    pass


def offerings_can_letter_report(request):
    local_churches = []
    if request.user.is_staff or request.user.role == 3:
        local_churches = LocalChurch.objects.all().order_by('local_church_name__title')
    if request.user.role == 2:
        local_churches = LocalChurch.objects.filter(local_church_pastor=request.user).order_by('local_church_name__title')
    if request.user.role == 4:
        local_churches = LocalChurch.objects.filter(region__region_overseer=request.user).order_by('local_church_name__title')
    if request.method == 'GET' and request.GET.get('local_church') and request.GET.get('local_church') != 'all':
        selected_local_church_id = int(request.GET.get('local_church'))
        local_church_name = LocalChurch.objects.get(id=selected_local_church_id).local_church_name.title
        all_contributors_data = contributors_info_dict(TransactionType.OFFERINGS_CAN.value, local_church=selected_local_church_id)
        report_year = request.GET.get('year', datetime.now().year - 1)
        context = {
            "contributors": all_contributors_data,
            "report_year": report_year,
            "local_churches": local_churches,
            "local_church_name": local_church_name
        }
        return render(request, "contributors/offerings_letter_receipt_list.html", context)
    all_contributors_data = contributors_info_dict(TransactionType.OFFERINGS_CAN.value)
    report_year = request.GET.get('year', datetime.now().year - 1)
    context = {
        "contributors": all_contributors_data,
        "report_year": report_year,
        "local_churches": local_churches,
    }
    return render(request, "contributors/offerings_letter_receipt_list.html", context)


def prepare_interac_summary_report_data(request):
    if request.GET.get('local_church') and request.GET.get('local_church') != 'all':
        selected_local_church_id = int(request.GET.get('local_church'))
        contribution_dict = contributors_info_dict(TransactionType.INTEREC_E_TRANSFER.value, local_church=selected_local_church_id)
    else:
        contribution_dict = contributors_info_dict(TransactionType.INTEREC_E_TRANSFER.value)
    report_year = request.GET.get('year', datetime.now().year - 1)
    for key in contribution_dict.keys():
        total_donation = 0.0
        contributor_data = Contribution.objects.filter(contributor_id=key, deposited_date__year=report_year,
                                                       payment_type=TransactionType.INTEREC_E_TRANSFER.value)
        contributor_data.order_by('deposited_date')
        for data in contributor_data:
            formatted_date = formatted_date_for_report(data.deposited_date)
            month_name = data.month
            temp_dict = {
                "month": month_name,
                "formatted_date": formatted_date,
                "amount": round(float(data.amount), 6),
            }
            contribution_dict[data.contributor_id]['donations'][month_name].append(temp_dict)
            total_donation += round(float(data.amount), 6)
        contribution_dict[key]['total_donation'] = total_donation

    return contribution_dict


def interac_summary_report(request):
    local_churches = []
    if request.user.is_staff or request.user.role == 3:
        local_churches = LocalChurch.objects.all().order_by('local_church_name__title')
    if request.user.role == 2:
        local_churches = LocalChurch.objects.filter(local_church_pastor=request.user).order_by('local_church_name__title')
    if request.user.role == 4:
        local_churches = LocalChurch.objects.filter(region__region_overseer=request.user).order_by('local_church_name__title')
    if request.method == 'GET' and request.GET.get('local_church') and request.GET.get('local_church') != 'all':
        selected_local_church_id = int(request.GET.get('local_church'))
        local_church_name = LocalChurch.objects.get(id=selected_local_church_id).local_church_name.title
        all_contributors_data = contributors_info_dict(TransactionType.INTEREC_E_TRANSFER.value, local_church=selected_local_church_id)
        report_year = request.GET.get('year', datetime.now().year - 1)
        context = {
            "contributors": all_contributors_data,
            "report_year": report_year,
            "local_churches": local_churches,
            "local_church_name": local_church_name,
        }
        return render(request, "contributors/interac_summary_receipt_list.html", context)
    all_contributors_data = contributors_info_dict(TransactionType.INTEREC_E_TRANSFER.value)
    report_year = request.GET.get('year', datetime.now().year - 1)
    context = {
        "contributors": all_contributors_data,
        "report_year": report_year,
        "local_churches": local_churches,
    }
    return render(request, "contributors/interac_summary_receipt_list.html", context)


def interac_letter_report(request):
    local_churches = []
    if request.user.is_staff or request.user.role == 3:
        local_churches = LocalChurch.objects.all().order_by('local_church_name__title')
    if request.user.role == 2:
        local_churches = LocalChurch.objects.filter(local_church_pastor=request.user).order_by('local_church_name__title')
    if request.user.role == 4:
        local_churches = LocalChurch.objects.filter(region__region_overseer=request.user).order_by('local_church_name__title')
    if request.method == 'GET' and request.GET.get('local_church') and request.GET.get('local_church') != 'all':
        selected_local_church_id = int(request.GET.get('local_church'))
        local_church_name = LocalChurch.objects.get(id=selected_local_church_id).local_church_name.title
        all_contributors_data = contributors_info_dict(TransactionType.INTEREC_E_TRANSFER.value, local_church=selected_local_church_id)
        report_year = request.GET.get('year', datetime.now().year - 1)
        context = {
            "contributors": all_contributors_data,
            "report_year": report_year,
            "local_churches": local_churches,
            "local_church_name": local_church_name,
        }
        return render(request, "contributors/interac_letter_receipt_list.html", context)
    all_contributors_data = contributors_info_dict(TransactionType.INTEREC_E_TRANSFER.value)
    report_year = request.GET.get('year', datetime.now().year - 1)
    context = {
        "contributors": all_contributors_data,
        "report_year": report_year,
        "local_churches": local_churches,
    }
    return render(request, "contributors/interac_letter_receipt_list.html", context)


def preview_offerings_summary_report(request, c_id=None):
    try:
        contributors = prepare_offerings_summary_report_data(request)
        ctr_ids = c_id.split()

        # Create a list to store the PDF content for each contributor
        pdf_contents = []

        for contributor_id in ctr_ids:
            contributor_id = int(contributor_id)
            report_year = request.GET.get('year', datetime.now().year - 1)
            contributor = contributors[contributor_id]
            logo_url = f"{request.scheme}://{request.get_host()}/static/img/logo.png"
            context = {
                "contributor": contributor,
                "report_year": report_year,
                "logo_url": logo_url
            }

            # Create an instance of PDFTemplateResponse
            pdf_response = PDFTemplateResponse(
                request=request,
                template='contributors/offerings_summary_report.html',
                context=context,
                show_content_in_browser=True,  # Set to True for browser preview
            )

            # Get the rendered PDF content
            pdf_content = pdf_response.rendered_content

            # Append the PDF content to the list
            pdf_contents.append(pdf_content)

        # Combine the PDF content for all contributors into a single PDF
        merged_pdf = PyPDF2.PdfMerger()
        for pdf_content in pdf_contents:
            merged_pdf.append(PyPDF2.PdfReader(io.BytesIO(pdf_content)))

        # Get the merged PDF content as a bytes object
        merged_pdf_content = io.BytesIO()
        merged_pdf.write(merged_pdf_content)
        merged_pdf_content.seek(0)

        # Return the merged PDF content as an HTTP response
        response = HttpResponse(merged_pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="offerings_summary_reports.pdf"'
        return response

    except Exception as e:
        print(e)
        messages.error(request, "Error occurred while generating preview.")
        return redirect('offering_can_summary_report')



def preview_interac_summary_report(request, c_id=None):
    try:
        contributors = prepare_interac_summary_report_data(request)
        ctr_ids = c_id.split()

        # Create a list to store the PDF content for each contributor
        pdf_contents = []

        for contributor_id in ctr_ids:
            contributor_id = int(contributor_id)
            report_year = request.GET.get('year', datetime.now().year - 1)
            contributor = contributors[contributor_id]
            logo_url = f"{request.scheme}://{request.get_host()}/static/img/logo.png"
            context = {
                "contributor": contributor,
                "report_year": report_year,
                "logo_url": logo_url
            }

            # Create an instance of PDFTemplateResponse
            pdf_response = PDFTemplateResponse(
                request=request,
                template='contributors/interac_summary_report.html',
                context=context,
                show_content_in_browser=True,  # Set to True for browser preview
            )

            # Get the rendered PDF content
            pdf_content = pdf_response.rendered_content

            # Append the PDF content to the list
            pdf_contents.append(pdf_content)

        # Combine the PDF content for all contributors into a single PDF
        merged_pdf = PyPDF2.PdfMerger()
        for pdf_content in pdf_contents:
            merged_pdf.append(PyPDF2.PdfReader(io.BytesIO(pdf_content)))

        # Get the merged PDF content as a bytes object
        merged_pdf_content = io.BytesIO()
        merged_pdf.write(merged_pdf_content)
        merged_pdf_content.seek(0)

        # Return the merged PDF content as an HTTP response
        response = HttpResponse(merged_pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="interac_summary_reports.pdf"'
        return response

    except Exception as e:
        print(e)
        messages.error(request, "Error occurred while generating preview.")
        return redirect('interac_summary_report')


def preview_offerings_letter_report(request, c_id=None):
    try:
        contributors = contributors_info_dict(TransactionType.OFFERINGS_CAN.value)
        ctr_ids = c_id.split()

        # Create a list to store the PDF content for each contributor
        pdf_contents = []

        for contributor_id in ctr_ids:
            contributor_id = int(contributor_id)
            report_year = request.GET.get('year', datetime.now().year - 1)
            contributor = contributors[contributor_id]
            total_contribution = Contribution.objects.filter(
                contributor_id=contributor_id,
                deposited_date__year=report_year,
                payment_type=TransactionType.OFFERINGS_CAN.value
            ).aggregate(total_amount=Sum('amount'))['total_amount'] or 0.0
            total_contribution = round(total_contribution, 2)
            report_issue_date = datetime.now().strftime("%B %d, %Y")
            logo_url = f"{request.scheme}://{request.get_host()}/static/img/logo.png"

            context = {
                "contributor": contributor,
                "report_year": report_year,
                "total_contribution": total_contribution,
                "amount_in_words": convert_amount_to_words(total_contribution),
                "report_issue_date": report_issue_date,
                "logo_url": logo_url
            }

            # Create an instance of PDFTemplateResponse
            pdf_response = PDFTemplateResponse(
                request=request,
                template='contributors/offerings_letter_report.html',
                context=context,
                show_content_in_browser=True,  # Set to True for browser preview
            )

            # Get the rendered PDF content
            pdf_content = pdf_response.rendered_content

            # Append the PDF content to the list
            pdf_contents.append(pdf_content)

        # Combine the PDF content for all contributors into a single PDF
        merged_pdf = PyPDF2.PdfMerger()
        for pdf_content in pdf_contents:
            merged_pdf.append(PyPDF2.PdfReader(io.BytesIO(pdf_content)))

        # Get the merged PDF content as a bytes object
        merged_pdf_content = io.BytesIO()
        merged_pdf.write(merged_pdf_content)
        merged_pdf_content.seek(0)

        # Return the merged PDF content as an HTTP response
        response = HttpResponse(merged_pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="offerings_letter_reports.pdf"'
        return response

    except Exception as e:
        print(e)
        messages.error(request, "Error occurred while generating preview.")
        return redirect('offerings_can_letter_report')



def preview_interac_letter_report(request, c_id=None):
    try:
        contributors = contributors_info_dict(TransactionType.INTEREC_E_TRANSFER.value)
        ctr_ids = c_id.split()

        # Create a list to store the PDF content for each contributor
        pdf_contents = []

        for contributor_id in ctr_ids:
            contributor_id = int(contributor_id)
            report_year = request.GET.get('year', datetime.now().year - 1)
            contributor = contributors[contributor_id]
            total_contribution = Contribution.objects.filter(
                contributor_id=contributor_id,
                deposited_date__year=report_year,
                payment_type=TransactionType.INTEREC_E_TRANSFER.value
            ).aggregate(total_amount=Sum('amount'))['total_amount'] or 0.0
            total_contribution = round(total_contribution, 2)
            report_issue_date = datetime.now().strftime("%B %d, %Y")
            logo_url = f"{request.scheme}://{request.get_host()}/static/img/logo.png"

            context = {
                "contributor": contributor,
                "report_year": report_year,
                "total_contribution": total_contribution,
                "amount_in_words": convert_amount_to_words(total_contribution),
                "report_issue_date": report_issue_date,
                "logo_url": logo_url
            }

            # Create an instance of PDFTemplateResponse
            pdf_response = PDFTemplateResponse(
                request=request,
                template='contributors/interac_letter_report.html',
                context=context,
                show_content_in_browser=True,  # Set to True for browser preview
            )

            # Get the rendered PDF content
            pdf_content = pdf_response.rendered_content

            # Append the PDF content to the list
            pdf_contents.append(pdf_content)

        # Combine the PDF content for all contributors into a single PDF
        merged_pdf = PyPDF2.PdfMerger()
        for pdf_content in pdf_contents:
            merged_pdf.append(PyPDF2.PdfReader(io.BytesIO(pdf_content)))

        # Get the merged PDF content as a bytes object
        merged_pdf_content = io.BytesIO()
        merged_pdf.write(merged_pdf_content)
        merged_pdf_content.seek(0)

        # Return the merged PDF content as an HTTP response
        response = HttpResponse(merged_pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="interac_letter_reports.pdf"'
        return response

    except Exception as e:
        print(e)
        messages.error(request, "Error occurred while generating preview.")
        return redirect('interac_letter_report')



def send_offerings_receipt(request, c_id=None):
    try:
        report_year = request.GET.get('year', datetime.now().year - 1)
        contributors = prepare_offerings_summary_report_data(request)
        ctr_ids = c_id.split()
        if len(ctr_ids) > 3:
            contributors = prepare_offerings_summary_report_data(request)
            for ctr in ctr_ids:
                contributor = contributors[int(ctr)]
                EmailQueue.objects.create(
                    contributor_id=int(ctr),
                    report_year=report_year,
                    email=contributor.get('email'),
                    report_type='offerings'
                )
            messages.success(request, "Offerings CAD reports queued for sending")
        else:
            for ctr in ctr_ids:
                contributor = contributors[int(ctr)]
                logo_url = f"{request.scheme}://{request.get_host()}/static/img/logo.png"
                context = {
                    "contributor": contributor,
                    "report_year": report_year,
                    "logo_url": logo_url
                }

                # Create an instance of PDFTemplateResponse
                pdf_response = PDFTemplateResponse(
                    request=request,
                    template='contributors/offerings_summary_report.html',
                    context=context,
                    show_content_in_browser=False,
                )

                # Encode the PDF content
                encoded_pdf = base64.b64encode(pdf_response.rendered_content).decode()

                email = EmailMessage(
                    subject='Offerings CAD Summary Report',
                    body=f"Greetings {contributor.get('first_name', contributor.get('full_name'))},\nHere's your Offerings CAD Report for {report_year}.\nThank you for being with DCLM.\n\n\nBest Regards,\nDCLM",
                    from_email=admin_sender,
                    to=[contributor.get('email')],
                )
                email.attach(f"{contributor.get('full_name')} offerings_summary_report.pdf", base64.b64decode(encoded_pdf), "application/pdf")
                email.send()

    except Exception as e:
        print(e)
        messages.error(request, "Some Emails Couldn't Sent Properly")
        return redirect('receipts_generation_page')

    messages.success(request, "Offerings CAD Receipts Sent to Contributor")
    return redirect('offering_can_summary_report')


def send_interac_summary_receipt(request, c_id=None):
    try:
        report_year = request.GET.get('year', datetime.now().year - 1)
        contributors = prepare_interac_summary_report_data(request)
        ctr_ids = c_id.split()
        if len(ctr_ids) > 3:
            contributors = prepare_interac_summary_report_data(request)
            for ctr in ctr_ids:
                contributor = contributors[int(ctr)]
                EmailQueue.objects.create(
                    contributor_id=int(ctr),
                    report_year=report_year,
                    email=contributor.get('email'),
                    report_type='interac'
                )
            messages.success(request, "Interac E-Transfer reports queued for sending")
        else:
            for ctr in ctr_ids:
                contributor = contributors[int(ctr)]
                logo_url = f"{request.scheme}://{request.get_host()}/static/img/logo.png"
                context = {
                    "contributor": contributor,
                    "report_year": report_year,
                    "logo_url": logo_url
                }

                # Create an instance of PDFTemplateResponse
                pdf_response = PDFTemplateResponse(
                    request=request,
                    template='contributors/interac_summary_report.html',
                    context=context,
                    show_content_in_browser=False,
                )

                # Encode the PDF content
                encoded_pdf = base64.b64encode(pdf_response.rendered_content).decode()

                email = EmailMessage(
                    subject='Interac E-Transfer Summary Report',
                    body=f"Greetings {contributor.get('first_name', contributor.get('full_name'))},\nHere's your Interac E-Transfer Report for {report_year}.\nThank you for being with DCLM.\n\n\nBest Regards,\nDCLM",
                    from_email=admin_sender,
                    to=[contributor.get('email')],
                )
                email.attach(f"{contributor.get('full_name')} interac_summary_report.pdf", base64.b64decode(encoded_pdf), "application/pdf")
                email.send()

    except Exception as e:
        print(e)
        messages.error(request, "Some Emails Couldn't Sent Properly")
        return redirect('receipts_generation_page')

    messages.success(request, "Interac E-Transfer Receipts Sent to Contributor")
    return redirect('interac_summary_report')


def send_interac_letter_receipt(request, c_id=None):
    try:
        report_year = request.GET.get('year', datetime.now().year - 1)
        contributors = contributors_info_dict(TransactionType.INTEREC_E_TRANSFER.value)
        ctr_ids = c_id.split()
        if len(ctr_ids) > 3:
            report_year = request.GET.get('year', datetime.now().year - 1)
            contributors = contributors_info_dict(TransactionType.INTEREC_E_TRANSFER.value)
            for ctr in ctr_ids:
                contributor = contributors[int(ctr)]
                EmailQueue.objects.create(
                    contributor_id=int(ctr),
                    report_year=report_year,
                    email=contributor.get('email'),
                    report_type='interac_letter'
                )
            messages.success(request, "Interac E-Transfer official reports queued for sending")
        else:
            for ctr in ctr_ids:
                contributor = contributors[int(ctr)]
                total_contribution = Contribution.objects.filter(
                    contributor_id=int(ctr),
                    deposited_date__year=report_year,
                    payment_type=TransactionType.INTEREC_E_TRANSFER.value
                ).aggregate(total_amount=Sum('amount'))['total_amount'] or 0.0
                total_contribution = round(total_contribution, 2)
                report_issue_date = datetime.now().strftime("%B %d, %Y")
                logo_url = f"{request.scheme}://{request.get_host()}/static/img/logo.png"

                context = {
                    "contributor": contributor,
                    "report_year": report_year,
                    "total_contribution": total_contribution,
                    "amount_in_words": convert_amount_to_words(total_contribution),
                    "report_issue_date": report_issue_date,
                    "logo_url": logo_url
                }

                # Create an instance of PDFTemplateResponse
                pdf_response = PDFTemplateResponse(
                    request=request,
                    template='contributors/interac_letter_report.html',
                    context=context,
                    show_content_in_browser=False,
                )

                # Encode the PDF content
                encoded_pdf = base64.b64encode(pdf_response.rendered_content).decode()

                email = EmailMessage(
                    subject='Interac E-Transfer Summary Report',
                    body=f"Greetings {contributor.get('first_name', contributor.get('full_name'))},\nHere's your Interac E-Transfer Official Report for {report_year}.\nThank you for being with DCLM.\n\n\nBest Regards,\nDCLM",
                    from_email=admin_sender,
                    to=[contributor.get('email')],
                )
                email.attach(f"{contributor.get('full_name')} interac_official_report.pdf", base64.b64decode(encoded_pdf), "application/pdf")
                email.send()

    except Exception as e:
        print(e)
        messages.error(request, "Some Emails Couldn't Sent Properly")
        return redirect('receipts_generation_page')

    messages.success(request, "Interac E-Transfer Receipts Sent to Contributor")
    return redirect('interac_letter_report')


def send_offerings_letter_receipt(request, c_id=None):
    try:
        report_year = request.GET.get('year', datetime.now().year - 1)
        contributors = contributors_info_dict(TransactionType.OFFERINGS_CAN.value)
        ctr_ids = c_id.split()
        if len(ctr_ids) > 3:
            report_year = request.GET.get('year', datetime.now().year - 1)
            contributors = contributors_info_dict(TransactionType.OFFERINGS_CAN.value)
            for ctr in ctr_ids:
                contributor = contributors[int(ctr)]
                EmailQueue.objects.create(
                    contributor_id=int(ctr),
                    report_year=report_year,
                    email=contributor.get('email'),
                    report_type='offerings_letter'
                )
            messages.success(request, "Offerings CAD official reports queued for sending")
        else:
            for ctr in ctr_ids:
                contributor = contributors[int(ctr)]
                total_contribution = Contribution.objects.filter(
                    contributor_id=int(ctr),
                    deposited_date__year=report_year,
                    payment_type=TransactionType.OFFERINGS_CAN.value
                ).aggregate(total_amount=Sum('amount'))['total_amount'] or 0.0
                total_contribution = round(total_contribution, 2)
                report_issue_date = datetime.now().strftime("%B %d, %Y")
                logo_url = f"{request.scheme}://{request.get_host()}/static/img/logo.png"

                context = {
                    "contributor": contributor,
                    "report_year": report_year,
                    "total_contribution": total_contribution,
                    "amount_in_words": convert_amount_to_words(total_contribution),
                    "report_issue_date": report_issue_date,
                    "logo_url": logo_url
                }

                # Create an instance of PDFTemplateResponse
                pdf_response = PDFTemplateResponse(
                    request=request,
                    template='contributors/offerings_letter_report.html',
                    context=context,
                    show_content_in_browser=False,
                )

                # Encode the PDF content
                encoded_pdf = base64.b64encode(pdf_response.rendered_content).decode()

                email = EmailMessage(
                    subject='Offerings Official Report',
                    body=f"Greetings {contributor.get('first_name', contributor.get('full_name'))},\nHere's your Offerings CAD Official Report for {report_year}.\nThank you for being with DCLM.\n\n\nBest Regards,\nDCLM",
                    from_email=admin_sender,
                    to=[contributor.get('email')],
                )
                email.attach(f"{contributor.get('full_name')} offerings_can_official_report.pdf", base64.b64decode(encoded_pdf), "application/pdf")
                email.send()

    except Exception as e:
        print(e)
        messages.error(request, "Some Emails Couldn't Sent Properly")
        return redirect('receipts_generation_page')

    messages.success(request, "Offerings CAD Official Receipts Sent to Contributor")
    return redirect('interac_letter_report')


def convert_amount_to_words(amount):
    try:
        # Define lists of words for numbers, tens, and units
        units = ['Zero', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine']
        teens = ['Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen',
                 'Nineteen']
        tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']

        # Define a function to convert three digits to words
        def three_digits_to_words(num):
            words = ''
            if num >= 100:
                words += units[num // 100] + ' Hundred '
                num %= 100
            if num >= 20:
                words += tens[num // 10] + ' '
                num %= 10
            if num >= 10:
                words += teens[num - 10] + ' '
                num = 0
            if num > 0:
                words += units[num] + ' '
            return words

        # Split the amount into dollars and cents
        dollars, cents = str(amount).split('.')
        dollars = int(dollars)
        cents = int(cents)

        # Convert dollars to words
        dollars_words = ''
        if dollars == 0:
            dollars_words = 'Zero'
        else:
            billions = dollars // 1000000000
            millions = (dollars % 1000000000) // 1000000
            thousands = (dollars % 1000000) // 1000
            hundreds = dollars % 1000

            if billions > 0:
                dollars_words += three_digits_to_words(billions) + ' Billion '
            if millions > 0:
                dollars_words += three_digits_to_words(millions) + ' Million '
            if thousands > 0:
                dollars_words += three_digits_to_words(thousands) + ' Thousand '
            if hundreds > 0:
                dollars_words += three_digits_to_words(hundreds)

        # Convert cents to words
        cents_words = three_digits_to_words(cents) if cents > 0 else 'Zero'

        # Construct the final amount in words
        amount_in_words = dollars_words + ' Dollars and ' + cents_words + ' Cents'
        return amount_in_words
    except Exception as e:
        print(e)
        return ''


def download_offerings_receipts(request, c_id=None):
    try:
        # Prepare contributors and PDF reports
        if request.GET.get('local_church') and request.GET.get('local_church') != 'all':
            selected_local_church_id = int(request.GET.get('local_church'))
            local_church_name = LocalChurch.objects.get(id=selected_local_church_id).local_church_name.title
        contributors = prepare_offerings_summary_report_data(request)
        ctr_ids = c_id.split()
        if c_id == 'all':
            ctr_ids = list(contributors.keys())
        all_pdfs = []

        for ctr in ctr_ids:
            report_year = request.GET.get('year', datetime.now().year - 1)
            contributor = contributors[int(ctr)]
            logo_url = f"{request.scheme}://{request.get_host()}/static/img/logo.png"
            context = {
                "contributor": contributor,
                "report_year": report_year,
                "logo_url": logo_url
            }

            # Create an instance of PDFTemplateResponse
            pdf_response = PDFTemplateResponse(
                request=request,
                template='contributors/offerings_summary_report.html',
                context=context,
                show_content_in_browser=False,
            )

            all_pdfs.append((f"{contributor.get('full_name')} offerings_summary_report.pdf", pdf_response.rendered_content))

        # Create a zip file containing all the PDF reports
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, 'a') as zip_file:
            for pdf_name, pdf_content in all_pdfs:
                zip_file.writestr(pdf_name, pdf_content)

        filename = f'Offerings Summary Receipts of {local_church_name} local_church' if request.GET.get('local_church') and request.GET.get('local_church') != 'all' else 'ALL Offerings Receipts' if c_id == 'all' else 'Offerings Summary Receipts'

        response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{filename}.zip"'

        return response

    except Exception as e:
        print(e)
        # Handle the exception as per your application's requirements
        return HttpResponse("Error occurred while generating the zip file")


def download_offerings_letter_receipts(request, c_id=None):
    try:
        if request.GET.get('local_church') and request.GET.get('local_church') != 'all':
            selected_local_church_id = int(request.GET.get('local_church'))
            local_church_name = LocalChurch.objects.get(id=selected_local_church_id).local_church_name.title
            contributors = contributors_info_dict(TransactionType.OFFERINGS_CAN.value, local_church=selected_local_church_id)
        else:
            contributors = contributors_info_dict(TransactionType.OFFERINGS_CAN.value)
        ctr_ids = c_id.split()
        if c_id == 'all':
            ctr_ids = list(contributors.keys())
        all_pdfs = []

        for ctr in ctr_ids:
            report_year = request.GET.get('year', datetime.now().year - 1)
            contributor = contributors[int(ctr)]
            total_contribution = Contribution.objects.filter(
                contributor_id=int(ctr),
                deposited_date__year=report_year,
                payment_type=TransactionType.INTEREC_E_TRANSFER.value
            ).aggregate(total_amount=Sum('amount'))['total_amount'] or 0.0
            total_contribution = round(total_contribution, 2)
            report_issue_date = datetime.now().strftime("%B %d, %Y")
            logo_url = f"{request.scheme}://{request.get_host()}/static/img/logo.png"

            context = {
                "contributor": contributor,
                "report_year": report_year,
                "total_contribution": total_contribution,
                "amount_in_words": convert_amount_to_words(total_contribution),
                "report_issue_date": report_issue_date,
                "logo_url": logo_url
            }

            # Create an instance of PDFTemplateResponse
            pdf_response = PDFTemplateResponse(
                request=request,
                template='contributors/offerings_letter_report.html',
                context=context,
                show_content_in_browser=False,  # Set to True for browser preview
            )

            all_pdfs.append((f"{contributor.get('full_name')}_offerings_can_official_report.pdf", pdf_response.rendered_content))

        # Create a zip file containing all the PDF reports
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, 'a') as zip_file:
            for pdf_name, pdf_content in all_pdfs:
                zip_file.writestr(pdf_name, pdf_content)

        filename = f'Offerings Official Receipts of {local_church_name} local_church' if request.GET.get('local_church') and request.GET.get('local_church') != 'all' else 'ALL Offerings Letter Receipts' if c_id == 'all' else 'Offerings Letter Receipts'
        response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{filename}.zip"'

        return response

    except Exception as e:
        print(e)
        # Handle the exception as per your application's requirements
        return HttpResponse("Error occurred while generating the zip file")


def download_interac_summary_receipts(request, c_id=None):
    try:
        if request.GET.get('local_church') and request.GET.get('local_church') != 'all':
            selected_local_church_id = int(request.GET.get('local_church'))
            local_church_name = LocalChurch.objects.get(id=selected_local_church_id).local_church_name.title
        contributors = prepare_interac_summary_report_data(request)
        ctr_ids = c_id.split()
        if c_id == 'all':
            ctr_ids = list(contributors.keys())
        all_pdfs = []

        for ctr in ctr_ids:
            report_year = request.GET.get('year', datetime.now().year - 1)
            contributor = contributors[int(ctr)]
            logo_url = f"{request.scheme}://{request.get_host()}/static/img/logo.png"
            context = {
                "contributor": contributor,
                "report_year": report_year,
                "logo_url": logo_url
            }

            # Create an instance of PDFTemplateResponse
            pdf_response = PDFTemplateResponse(
                request=request,
                template='contributors/interac_summary_report.html',
                context=context,
                show_content_in_browser=False,
            )

            all_pdfs.append((f"{contributor.get('full_name')}_interac_summary_report.pdf", pdf_response.rendered_content))

        # Create a zip file containing all the PDF reports
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, 'a') as zip_file:
            for pdf_name, pdf_content in all_pdfs:
                zip_file.writestr(pdf_name, pdf_content)

        filename = f'Interac Summary Receipts of {local_church_name} local_church' if request.GET.get('local_church') and request.GET.get('local_church') != 'all' else 'ALL Interac Summary Receipts' if c_id == 'all' else 'Interac Summary Receipts'
        response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{filename}.zip"'

        return response

    except Exception as e:
        print(e)
        # Handle the exception as per your application's requirements
        return HttpResponse("Error occurred while generating the zip file")


def download_interac_letter_receipts(request, c_id=None):
    try:
        if request.GET.get('local_church') and request.GET.get('local_church') != 'all':
            selected_local_church_id = int(request.GET.get('local_church'))
            local_church_name = LocalChurch.objects.get(id=selected_local_church_id).local_church_name.title
            contributors = contributors_info_dict(TransactionType.INTEREC_E_TRANSFER.value, local_church=selected_local_church_id)
        else:
            contributors = contributors_info_dict(TransactionType.INTEREC_E_TRANSFER.value)
        ctr_ids = c_id.split()
        if c_id == 'all':
            ctr_ids = list(contributors.keys())
        all_pdfs = []

        for ctr in ctr_ids:
            report_year = request.GET.get('year', datetime.now().year - 1)
            contributor = contributors[int(ctr)]
            total_contribution = Contribution.objects.filter(
                contributor_id=int(ctr),
                deposited_date__year=report_year,
                payment_type=TransactionType.INTEREC_E_TRANSFER.value
            ).aggregate(total_amount=Sum('amount'))['total_amount'] or 0.0
            total_contribution = round(total_contribution, 2)
            report_issue_date = datetime.now().strftime("%B %d, %Y")
            logo_url = f"{request.scheme}://{request.get_host()}/static/img/logo.png"

            context = {
                "contributor": contributor,
                "report_year": report_year,
                "total_contribution": total_contribution,
                "amount_in_words": convert_amount_to_words(total_contribution),
                "report_issue_date": report_issue_date,
                "logo_url": logo_url
            }

            # Create an instance of PDFTemplateResponse
            pdf_response = PDFTemplateResponse(
                request=request,
                template='contributors/interac_letter_report.html',
                context=context,
                show_content_in_browser=False,  # Set to True for browser preview
            )

            all_pdfs.append((f"{contributor.get('full_name')}_interac_official_report.pdf", pdf_response.rendered_content))

        # Create a zip file containing all the PDF reports
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, 'a') as zip_file:
            for pdf_name, pdf_content in all_pdfs:
                zip_file.writestr(pdf_name, pdf_content)

        filename = f'Interac Official Receipts of {local_church_name} local_church' if request.GET.get('local_church') and request.GET.get('local_church') != 'all' else 'ALL Interac Official Receipts' if c_id == 'all' else 'Interac Official Receipts'
        response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{filename}.zip"'

        return response

    except Exception as e:
        print(e)
        # Handle the exception as per your application's requirements
        return HttpResponse("Error occurred while generating the zip file")


def search_donor_names(request):
    if request.method == "GET":
        query = request.GET.get('term', '')
        selectedChurch = request.GET.get('church', '')

        donors = User.objects.filter(Q(full_name__icontains=query,local_church_id=selectedChurch)).values_list('full_name', flat=True)[:10]  # Limit to 10 suggestions
        return JsonResponse(list(donors), safe=False)


def prepare_offerings_summary_report_data_script(local_church=None,year=None):
    if local_church and local_church != 'all':
        selected_local_church_id = int(local_church)
        contribution_dict = contributors_info_dict(TransactionType.OFFERINGS_CAN.value, local_church=selected_local_church_id)
    else:
        contribution_dict = contributors_info_dict(TransactionType.OFFERINGS_CAN.value)
    if year:
        report_year = year
    else:
        report_year = datetime.now().year - 1

    for key in contribution_dict.keys():
        total_donation = 0.0
        contributor_data = Contribution.objects.filter(contributor_id=key, deposited_date__year=report_year,
                                                       payment_type=TransactionType.OFFERINGS_CAN.value)
        contributor_data.order_by('deposited_date')
        special = calculate_special_contributions(report_year, key)
        contribution_dict[key]['special_contribution'] = special
        for data in contributor_data:
            formatted_date = formatted_date_for_report(data.deposited_date)
            month_name = data.month
            temp_dict = {
                "month": month_name,
                "formatted_date": formatted_date,
                "amount": round(float(data.amount), 6),
            }
            contribution_dict[data.contributor_id]['donations'][month_name].append(temp_dict)
            total_donation += round(float(data.amount), 6)
        contribution_dict[key]['total_donation'] = total_donation

    return contribution_dict


def prepare_interac_summary_report_data_script(local_church=None,year=None):
    if local_church and local_church != 'all':
        selected_local_church_id = int(local_church)
        contribution_dict = contributors_info_dict(TransactionType.INTEREC_E_TRANSFER.value, local_church=selected_local_church_id)
    else:
        contribution_dict = contributors_info_dict(TransactionType.INTEREC_E_TRANSFER.value)
    if year:
        report_year = year
    else:
        report_year = datetime.now().year - 1

    for key in contribution_dict.keys():
        total_donation = 0.0
        contributor_data = Contribution.objects.filter(contributor_id=key, deposited_date__year=report_year,
                                                       payment_type=TransactionType.INTEREC_E_TRANSFER.value)
        contributor_data.order_by('deposited_date')
        for data in contributor_data:
            formatted_date = formatted_date_for_report(data.deposited_date)
            month_name = data.month
            temp_dict = {
                "month": month_name,
                "formatted_date": formatted_date,
                "amount": round(float(data.amount), 6),
            }
            contribution_dict[data.contributor_id]['donations'][month_name].append(temp_dict)
            total_donation += round(float(data.amount), 6)
        contribution_dict[key]['total_donation'] = total_donation

    return contribution_dict


class DonationUsersListView(ListView):
    """List unique users who have made donations."""
    model = DonationInKind
    template_name = "contributors/donation_in_kind_receipt_list.html"
    context_object_name = "donors"

    def get_queryset(self):
        donors = (
            DonationInKind.objects
            .filter(donor__isnull=False)
            .values(
                "donor_id",
                "donor__first_name",
                "donor__last_name",
                "donor__email"
            )
            .annotate(
                total_donations=Count("id"),
                total_value=Sum("estimated_value"),
                last_donation_date=Max("donation_date"),
                tax_receipt_issued=BoolOr("tax_receipt_issued"),
                last_tax_receipt_date=Max("tax_receipt_date"),
                local_churches=StringAgg(
                    Cast("local_church__local_church_name__title", CharField()), ", ", distinct=True
                )
            )
        )

        return donors


class DownloadDonationReceipt(View):
    """Generate a PDF donation receipt for a single donor."""

    def get(self, request, donor_id):
        try:
            donor = get_object_or_404(User, id=donor_id)
            donations = DonationInKind.objects.filter(donor_id=donor_id)

            if not donations.exists():
                messages.info(request, "No donation found.")
                return redirect("donations-receipt-list")

            total_value = donations.aggregate(total_value=Sum("estimated_value"))["total_value"] or 0.00

            # Mark tax receipts as issued & update date
            tax_receipt_date = now().date()

            logo_url = f"{request.scheme}://{request.get_host()}/static/img/logo.png"
            context = {
                "receipt_issue_date": tax_receipt_date.strftime("%B %d, %Y"),
                "donor": donor,
                "donations": donations,
                "tax_receipt_date": now().strftime("%B %d, %Y"),
                "total_value": total_value,
                "logo_url": logo_url,
            }

            # Check request parameters
            download = request.GET.get("mode", "false").lower() == "download"
            send_email_param = request.GET.get("mode", "false").lower() == "send"

            pdf_response = PDFTemplateResponse(
                request=request,
                template="contributors/donation_receipt_pdf.html",
                context=context,
                filename=f"Donation_Receipt_{donor_id}.pdf" if download else None,
                show_content_in_browser=not download,
            )

            if send_email_param:
                return self.send_email_with_pdf(donor, pdf_response.rendered_content, request, donations)

            if download:
                response = HttpResponse(pdf_response.rendered_content, content_type="application/pdf")
                response["Content-Disposition"] = f'attachment; filename="Donation_Receipt_{donor.first_name}.pdf"'
                return response

            return pdf_response

        except Exception as e:
            print(e)
            messages.error(request, "Error: Something went wrong. Please try again later.")
            return redirect("donations-receipt-list")

    @staticmethod
    def send_email_with_pdf(donor, pdf_content, request, donations):
        """Sends the donation receipt as an email attachment via SendGrid."""
        try:
            email_subject = "Your Donation Receipt"
            email_body = f"Dear {donor.first_name},\n\nAttached is your donation receipt. Thank you for your generosity!\n\nBest regards,\nDeeper Christian Life Ministry, Canada"

            # Encode PDF in Base64 for SendGrid
            encoded_pdf = base64.b64encode(pdf_content).decode()

            # Attachments format: (filename, content, mimetype)
            attachments = [(f"Donation_Receipt_{donor.first_name}.pdf", encoded_pdf, "application/pdf")]

            # Send the email
            email_sent = send_email(
                subject=email_subject,
                recipient_list=[donor.email],
                plain_text_body=email_body,
                attachments=attachments
            )

            if email_sent:
                tax_receipt_date = now().date()
                donations.update(tax_receipt_issued=True, tax_receipt_date=tax_receipt_date)
                messages.success(request, "Donation receipt sent successfully via email.")
                return redirect("donations-receipt-list")
            else:
                messages.error(request, "Error: Failed to send email")
                return redirect("donations-receipt-list")

        except Exception as e:
            print(f"Email sending error: {e}")
            messages.error(request, "Error: Something went wrong. Please try again later.")
            return redirect("donations-receipt-list")
