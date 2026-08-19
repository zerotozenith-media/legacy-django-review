from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Send a test email using Anymail'

    def handle(self, *args, **kwargs):
        try:
            email = EmailMessage(
                subject='Sending with Mailtrap is Fun',
                body='and easy to do anywhere, even with Python',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=['it-support@deeperlife.ca'],
            )
            email.send()
            print("Email sent successfully")
        except Exception as e:
            print(e)