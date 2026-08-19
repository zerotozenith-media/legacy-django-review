from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from core import settings

admin_sender = settings.DEFAULT_FROM_EMAIL


def send_reminder_email(
    sender=None,
    receive=None,
    message=None,
    subject=None,
    bcc=[],
    text_message=None,
):
    try:
        context_email = {
            "heading": subject,
            "sub_heading": message,
            "text": "",
            "text_message": text_message,
        }
        html_content = render_to_string("email/detail_report_reminder.html", context_email)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_message or subject,
            from_email=admin_sender,
            to=[receive],
            bcc=bcc or [],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()

    except Exception as e:
        print(e)
        print("email not sent")