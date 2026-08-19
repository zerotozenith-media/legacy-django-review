import logging

from celery import shared_task

from utils.send_emails import send_email

logger = logging.getLogger(__name__)


@shared_task
def send_user_added_email_task(data):
    send_email(
        subject="DCLM Canada Church Management System Account Setup",
        recipient_list=[data["email"]],
        context=data,
        template_name='email/account_activation_email.html',
        plain_text_body="DCLM Canada Church Management System Account Setup.",
    )
    
    
