import re
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.db import transaction
from six import text_type
from authentication.models import User
from organization.models import LocalChurch
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.urls import reverse
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import traceback


class AppTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return text_type(user.is_active) + text_type(user.pk) + text_type(timestamp)


account_activation_token = AppTokenGenerator()


def send_user_activation_email(user, password, host):
    email_body = {
        "user": user,
        "domain": host,
        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
        "token": account_activation_token.make_token(user),
    }
    link = reverse(
        "activate", kwargs={"uidb64": email_body["uid"], "token": email_body["token"]}
    )
    activate_url = "http://" + host + link

    email_subject = "Activate your account"

    try:
        email_body_html = render_to_string('authentication/seed_user_email.html', {
            'user': user,
            'password': password,
            'activate_url': activate_url,
        })
        email_message = EmailMessage(
            email_subject,
            body=email_body_html,
            from_email="dclmcafinance@gmail.com",
            to=[user.email],
            bcc=["ugurunedu@gmail.com"],
        )
        email_message.content_subtype = 'html'
        email_message.send()
    except Exception as e:
        print(str(e))
        traceback.print_exc()


class UserUploaderHelper:

    @staticmethod
    def name_split(full_name):
        name = str(full_name).split(' ')
        if len(name) == 1:
            return name[0], '', ''
        elif len(name) == 2:
            return name[0], '', name[1]
        elif len(name) == 3:
            return name[0], name[1], name[2]
        return full_name, '', ''


    @staticmethod
    def validate_headers(worksheet):
        headers = [cell.value.strip() if cell.value else None for cell in worksheet[1]]
        return headers == ['First Name', 'Middle Name', 'Last Name', 'Email', 'Address']

    @staticmethod
    def validate_email(email):
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_regex, email) is not None

    @staticmethod
    def validate_role(single_role):
        roles = ['local church pastor', 'national overseer', 'member', 'regional overseer']
        return str(single_role).strip().lower() in roles

    @staticmethod
    def process_and_save(worksheet, local_church_id, host):
        roles = {
            'member': 1,
            'local_church_pastor': 2,
            'national_overseer': 3,
            'region_overseer': 4,
        }

        with transaction.atomic():
            for row_number, row in enumerate(worksheet.iter_rows(min_row=2, values_only=True), start=2):
                row = list(row) + [None] * max(0, 5 - len(row))
                first_name, middle_name, last_name, email, address = row[0], row[1], row[2], row[3], row[4]
            
                if not any([first_name, middle_name, last_name, email, address]):
                  continue
                


                full_name = " ".join([first_name, last_name])
                if middle_name:
                    full_name = " ".join([first_name, middle_name, last_name])
                if not email and not first_name and not last_name:
                    continue

                if not first_name or not last_name:
                    first_name, middle_name, last_name = UserUploaderHelper.name_split(full_name)
                else:
                    if full_name:
                        full_name = full_name

                if not User.objects.filter(email=email).exists():
                    data = {
                        "email": email,
                        "password": "123456",
                        "first_name": first_name or '',
                        "middle_name": middle_name or '',
                        "last_name": last_name or '',
                        "address": address or '',
                        "full_name": full_name or '',
                        "is_active": True,
                        "role": roles.get('member'),
                        'local_church': LocalChurch.objects.get(id=local_church_id)
                    }
                    print(f"row: {row_number} data: {data}")
                    user = User.objects.create_user(**data)
                    """
                    Not Sending Emails to contributors during uploading Contributors won't have any interface to Login.
                    """
                    # send_user_activation_email(user, '123456', host)
                else:
                    print("User already exists")

