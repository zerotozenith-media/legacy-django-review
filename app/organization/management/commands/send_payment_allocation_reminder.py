import datetime

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils.timezone import now
from organization.email_utils import send_reminder_email
from organization.models import PaymentAllocation


class Command(BaseCommand):
    help = 'Check for payment Allocation and send reminders'

    def handle(self, *args, **kwargs):
        current_date = now()
        current_month = current_date.month
        current_year = current_date.year
        current_day = current_date.day
        today = datetime.date.today()
        first = today.replace(day=1)
        last_month = first - datetime.timedelta(days=1)
        national_overseer_email = 'it-support@deeperlife.ca'
        payment_allocations = PaymentAllocation.objects.filter(date__month=last_month.month, date__year=last_month.year)
        for allocation in payment_allocations:
            region_overseer = allocation.region.region_overseer
            if allocation.total_amount > allocation.paid_amount:
                if current_day == 3:
                    # Send reminder to region overseer
                    send_reminder_email(subject="Reminder: Please pay the pending allocation payments",receive=region_overseer.email,text_message="Please Pay the complete amount of allocation else this will be escalated to national overseer" )
                elif current_day == 6:
                    # Send mail to national overseer
                    send_reminder_email(subject="Alert: Region Overseer did not paid allocation payment", receive=national_overseer_email, text_message=f"Region Overseer {region_overseer.email} did not paid the allocation payments for the current month.")
