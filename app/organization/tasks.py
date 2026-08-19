import logging

from celery import shared_task
from datetime import timedelta

from django.conf import settings
from django.utils.timezone import now

from utils.email_templates import EMAIL_TEMPLATES
from utils.send_emails import send_email
from .models import PaymentAllocation, LocalChurch, DetailReport
from .utils import CreatePaymentAllocation

logger = logging.getLogger(__name__)
national_oversea_email = settings.NATIONAL_OVERSEA_EMAIL


@shared_task
def allocation_payment_reminder_task():
    """
    Sends reminder emails to regional overseers for incomplete payments.
    """
    current_date = now()
    today = current_date.date()

    # Calculate last month's details
    first_of_month = today.replace(day=1)
    last_month = first_of_month - timedelta(days=1)

    # Retrieve payment allocations for last month
    payment_allocations = PaymentAllocation.objects.filter(
        date__month=last_month.month,
        date__year=last_month.year
    )

    email_config = EMAIL_TEMPLATES["payment_allocation_reminder"]
    subject = email_config["subject"]
    heading = email_config["heading"]
    message = email_config["message"]
    template_name = email_config["template_name"]

    for allocation in payment_allocations:
        if allocation.paid_amount < allocation.total_amount:
            region_overseer = allocation.region.region_overseer
            # Send reminder email to regional overseer
            context = {
                "first_name": f"Pastor {region_overseer.first_name}" if region_overseer.first_name else "Pastor",
                "heading": heading,
                "message": message
            }

            send_email(
                subject=subject,
                recipient_list=[region_overseer.email],
                plain_text_body=subject,
                context=context,
                template_name=template_name
            )


@shared_task
def escalate_payment_allocation_to_national_oversea():
    """
    Sends escalation emails to the national overseer if payments remain incomplete.
    """
    today = now().date()

    # Calculate last month's details
    first_of_month = today.replace(day=1)
    last_month = first_of_month - timedelta(days=1)

    # Retrieve payment allocations for last month
    payment_allocations = PaymentAllocation.objects.filter(
        date__month=last_month.month,
        date__year=last_month.year
    )

    email_config = EMAIL_TEMPLATES["payment_allocation_escalation"]
    subject = email_config["subject"]
    heading = email_config["heading"]
    message = email_config["message"]
    template_name = email_config["template_name"]

    for allocation in payment_allocations:
        if allocation.total_amount > allocation.paid_amount:
            region_overseer = allocation.region.region_overseer
            # Send reminder email to regional overseer and cc national oversea
            context = {
                "first_name": f"Pastor {region_overseer.first_name}" if region_overseer.first_name else "Pastor",
                "heading": heading,
                "message": message
            }

            send_email(
                subject=subject,
                recipient_list=[region_overseer.email],
                plain_text_body=subject,
                context=context,
                cc=[national_oversea_email],
                template_name=template_name
            )


@shared_task
def handle_pastor_detail_report_reminder():
    """
    Sends reminders to pastors.
    """
    current_date = now()
    current_month = current_date.month

    email_config = EMAIL_TEMPLATES["submit_detail_report_reminder"]
    subject = email_config["subject"]
    heading = email_config["heading"]
    message = email_config["message"]
    template_name = email_config["template_name"]

    local_churches = LocalChurch.objects.all()
    for church in local_churches:
        pastor = church.local_church_pastor

        if pastor:
            if not DetailReport.objects.filter(local_church=church, date__month=current_month).exists():
                context = {
                    "first_name": f"Pastor {pastor.first_name}" if pastor.first_name else "Pastor",
                    "heading": heading,
                    "message": message
                }
                send_email(
                    subject=subject,
                    recipient_list=[pastor.email],
                    context=context,
                    plain_text_body=heading,
                    template_name=template_name
                )


@shared_task
def handle_pastor_detail_report_cc_regional_oversea():
    """
    Sends reminders to pastors for detail report for the month.
    """
    current_date = now()
    current_month = current_date.month

    email_config = EMAIL_TEMPLATES["detail_report_first_escalation"]
    subject = email_config["subject"]
    heading = email_config["heading"]
    message = email_config["message"]
    template_name = email_config["template_name"]

    local_churches = LocalChurch.objects.all()
    for church in local_churches:
        pastor = church.local_church_pastor
        region_overseer = church.region.region_overseer

        if pastor:
            if not DetailReport.objects.filter(local_church=church, date__month=current_month).exists():
                context = {
                    "first_name": f"Pastor {pastor.first_name}" if pastor.first_name else "Pastor",
                    "heading": heading,
                    "message": message
                }
                send_email(
                    subject=subject,
                    recipient_list=[pastor.email],
                    context=context,
                    cc=[region_overseer.email],
                    plain_text_body=heading,
                    template_name=template_name
                )


@shared_task
def handle_pastor_detail_report_cc_regional_overseer_and_national_oversea():
    """
    Sends reminders to pastors for detail report for the month.
    """
    current_date = now()
    current_month = current_date.month

    email_config = EMAIL_TEMPLATES["detail_report_second_escalation"]
    subject = email_config["subject"]
    heading = email_config["heading"]
    message = email_config["message"]
    template_name = email_config["template_name"]

    local_churches = LocalChurch.objects.all()
    for church in local_churches:
        pastor = church.local_church_pastor
        region_overseer = church.region.region_overseer

        if pastor:
            if not DetailReport.objects.filter(local_church=church, date__month=current_month).exists():
                context = {
                    "first_name": f"Pastor {pastor.first_name}" if pastor.first_name else "Pastor",
                    "heading": heading,
                    "message": message
                }
                send_email(
                    subject=subject,
                    recipient_list=[pastor.email],
                    context=context,
                    cc=[region_overseer.email, national_oversea_email],
                    plain_text_body=heading,
                    template_name=template_name
                )


@shared_task
def create_monthly_allocation_payment_for_regions():
    """
    Creates monthly payment allocations for each region if not already present.
    """
    task = CreatePaymentAllocation()
    task.run()
    logger.info("Monthly payment allocations created for regions.")
