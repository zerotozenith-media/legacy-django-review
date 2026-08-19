from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils.timezone import now
from organization.email_utils import send_reminder_email
from organization.models import LocalChurch, DetailReport


class Command(BaseCommand):
    help = 'Check for pastor detail reports and send reminders'

    def handle(self, *args, **kwargs):
        current_date = now()
        current_month = current_date.month
        current_day = current_date.day
        local_churches = LocalChurch.objects.all()
        print("in email")
        print("local", local_churches)
        for church in local_churches:
            pastor = church.local_church_pastor
            region_overseer = church.region.region_overseer
            print(DetailReport.objects.filter(local_church=church, date__month=current_month).exists(), current_month, current_day)
            if not DetailReport.objects.filter(local_church=church, date__month=current_month).exists():
                if current_day == 23:
                    # Send reminder to pastor
                    send_reminder_email(subject="Reminder: Submit your Detail Report",receive=pastor.email,text_message="Please submit your detail report for the current month." )
                    print(f'Sent reminder to pastor: {pastor.email}')
                elif current_day == 30:
                    # Send mail to region overseer
                    send_reminder_email(subject="Alert: Pastor did not submit Detail Report", receive=region_overseer.email, text_message="Pastor {pastor.email} did not submit the detail report for the current month.")
                    print(f'Sent alert to overseer: {region_overseer.email}')
