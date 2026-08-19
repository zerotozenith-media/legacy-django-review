import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template

logger = logging.getLogger(__name__)
admin_sender = settings.DEFAULT_FROM_EMAIL


def send_email(
        subject: str,
        recipient_list: list,
        template_name: str = None,
        context: dict = None,
        plain_text_body: str = None,
        cc: list = None,
        bcc: list = None,
        attachments: list = None  # List of file paths or (filename, content, mimetype)
):
    try:
        html_content = get_template(template_name).render(context or {}) if template_name else None

        bcc_list = ["it-support@deeperlife.ca"]  # Default BCC
        if bcc:
            bcc_list += bcc

        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_text_body or "Default plain text body.",
            from_email=admin_sender,
            to=recipient_list,
            cc=cc or [],
            bcc=bcc_list,
        )

        if html_content:
            email.attach_alternative(html_content, "text/html")

        if attachments:
            for attachment in attachments:
                if isinstance(attachment, tuple):
                    filename, content, mimetype = attachment
                    email.attach(filename, content, mimetype)
                else:
                    email.attach_file(attachment)

        email.send()
        logger.info(f"Email sent to {', '.join(recipient_list)}.")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {', '.join(recipient_list)}: {e}")
        return False