from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand
from django.db.models import Sum
from wkhtmltopdf.views import PDFTemplateResponse

from contributor.models import EmailQueue, Contribution, TransactionType
from datetime import datetime
import base64

from contributor.reports import contributors_info_dict, convert_amount_to_words, prepare_interac_summary_report_data_script, \
    prepare_offerings_summary_report_data_script

admin_sender = settings.DEFAULT_FROM_EMAIL

from contributor.reports import contributors_info_dict, convert_amount_to_words, prepare_interac_summary_report_data_script, \
    prepare_offerings_summary_report_data_script

admin_sender = settings.DEFAULT_FROM_EMAIL


class Command(BaseCommand):
    help = 'Send queued user reports'

    def handle(self, *args, **kwargs):
        # Fetch all pending reports
        logo_url = f"/static/img/logo.png"
        queued_emails = EmailQueue.objects.all()
        for email in queued_emails:
            if email.report_type == 'interac':
                contributors = prepare_interac_summary_report_data_script(year=email.report_year)
                template = 'contributors/interac_summary_report.html'
                subject = 'Interac E-Transfer Summary Report'
                context = {
                    "contributor": contributors[email.contributor_id],
                    "report_year": email.report_year,
                    "logo_url": logo_url
                }
            elif email.report_type == 'offerings':
                contributors = prepare_offerings_summary_report_data_script(year=email.report_year)
                template = 'contributors/offerings_summary_report.html'
                subject = 'Offerings CAD Summary Report'
                context = {
                    "contributor": contributors[email.contributor_id],
                    "report_year": email.report_year,
                    "logo_url": logo_url
                }
            elif email.report_type == 'interac_letter':
                contributors = contributors_info_dict(TransactionType.INTEREC_E_TRANSFER.value)
                template = 'contributors/interac_letter_report.html'
                subject = 'Interac E-Transfer Official Report'
                total_contribution = Contribution.objects.filter(
                    contributor_id=email.contributor_id,
                    deposited_date__year=email.report_year,
                    payment_type=TransactionType.INTEREC_E_TRANSFER.value
                ).aggregate(total_amount=Sum('amount'))['total_amount'] or 0.0
                total_contribution = round(total_contribution, 2)
                report_issue_date = datetime.now().strftime("%B %d, %Y")
                context = {
                    "contributor": contributors[email.contributor_id],
                    "report_year": email.report_year,
                    "total_contribution": total_contribution,
                    "amount_in_words": convert_amount_to_words(total_contribution),
                    "report_issue_date": report_issue_date,
                    "logo_url": logo_url
                }
            elif email.report_type == 'offerings_letter':
                contributors = contributors_info_dict(TransactionType.OFFERINGS_CAN.value)
                template = 'contributors/offerings_letter_report.html'
                subject = 'Offerings CAD Official Report'
                total_contribution = Contribution.objects.filter(
                    contributor_id=email.contributor_id,
                    deposited_date__year=email.report_year,
                    payment_type=TransactionType.OFFERINGS_CAN.value
                ).aggregate(total_amount=Sum('amount'))['total_amount'] or 0.0
                total_contribution = round(total_contribution, 2)
                report_issue_date = datetime.now().strftime("%B %d, %Y")
                context = {
                    "contributor": contributors[email.contributor_id],
                    "report_year": email.report_year,
                    "total_contribution": total_contribution,
                    "amount_in_words": convert_amount_to_words(total_contribution),
                    "report_issue_date": report_issue_date,
                    "logo_url": logo_url
                }

            # Generate the PDF and email content here...

            # Create an instance of PDFTemplateResponse
            pdf_response = PDFTemplateResponse(
                request=None,
                template=template,
                context=context,
                show_content_in_browser=False,
            )

                        # Encode the PDF content
            encoded_pdf = base64.b64encode(pdf_response.rendered_content).decode()

            contributor_name = contributors[email.contributor_id].get('full_name')
            first_name = contributors[email.contributor_id].get('first_name', contributor_name)

            # Send the email
            message = EmailMessage(
                subject=subject,
                body=f"Greetings {first_name},\nHere's your report for {email.report_year}.\nThank you for being with DCLM.\n\n\nBest Regards,\nDCLM",
                from_email=admin_sender,
                to=[email.email],
            )
            message.attach(f"{contributor_name}_{email.report_type}_report.pdf", base64.b64decode(encoded_pdf), "application/pdf")
            message.send()

            # Delete the email from the queue after sending
            email.delete()
