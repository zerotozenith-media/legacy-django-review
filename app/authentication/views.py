# Import necessary modules and classes
from django.conf import settings
from django.shortcuts import render, redirect
from django.utils.crypto import get_random_string
from django.views import View
from django.http import JsonResponse
import json
from django.contrib import messages
from django.core.mail import EmailMessage
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.http import HttpResponse
from authentication.models import User
from contributor.models import MiscellaneousUser, MiscellaneousContribution, Contribution
from organization.models import LocalChurch
from organization.utils import get_user_local_church
from utils.email_templates import EMAIL_TEMPLATES
from utils.helpers import get_user_regions, get_filtered_context
from utils.send_emails import send_email
from .tasks import send_user_added_email_task
from .utils import account_activation_token, UserUploaderHelper
from django.urls import reverse
from django.contrib import auth
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from .middleware import Role
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.contrib.auth import get_user_model, logout
from django.views.decorators.http import require_POST
import threading

# Thread class for sending emails asynchronously
class EmailThread(threading.Thread):
    def __init__(self, email_message):
        self.email_message = email_message
        threading.Thread.__init__(self)

    def run(self):
        # Send the email message
        self.email_message.send(fail_silently=False)

# View for validating email
class EmailValidationView(View):
    def post(self, request):
        data = json.loads(request.body)
        email = data["email"]

        try:
            # Validate the email format
            validate_email(email)
        except ValidationError:
            return JsonResponse({"email_error": "Email is invalid"}, status=400)

        # Check if the email already exists in the database
        if User.objects.filter(email=email).exists():
            return JsonResponse({"email_error": "Email already exists"}, status=400)

        return JsonResponse({"email_valid": "Email is valid"})

# View for validating username
class UsernameValidationView(View):
    def post(self, request):
        data = json.loads(request.body)
        username = data["username"]

        # Check if the username contains only alphanumeric characters
        if not str(username).isalnum():
            return JsonResponse(
                {"username_error": "Only alphanumeric characters allowed"}, status=400
            )
        # Check if the username already exists in the database
        if User.objects.filter(username=username).exists():
            return JsonResponse(
                {"username_error": "Sorry, username exists"}, status=409
            )

        return JsonResponse({"username_valid": True})

# Function to create a user and send an activation email
def create_user_and_send_activation_email(request, **kwargs):
    email = kwargs.get("email")
    password = kwargs.get("password")
    first_name = kwargs.get("first_name", "")
    middle_name = kwargs.get("middle_name", "")
    last_name = kwargs.get("last_name", "")
    role = kwargs.get("role", None)

    # Check if the user already exists
    if not User.objects.filter(email=email).exists():
        # Check if the password is too short
        if len(password) < 6:
            messages.error(request, "Password too short")
            return False, None

        # Prepare the data for creating the user
        data = {
            "email": email,
            "password": password,
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "role": role if role else None,
            "is_active": False,
        }
        # Create the user
        user = User.objects.create_user(**data)
        # Send the activation email
        send_activation_email(request, user)
        return True, user

    messages.error(request, "User with this email already exists")
    return False, None

# Function to send an activation email
def send_activation_email(request, user):
    current_site = get_current_site(request)
    email_body = {
        "user": user,
        "domain": current_site.domain,
        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
        "token": account_activation_token.make_token(user),
    }

    # Generate the activation link
    link = reverse(
        "activate", kwargs={"uidb64": email_body["uid"], "token": email_body["token"]}
    )
    activate_url = "http://" + current_site.domain + link

    email_subject = "Activate your account"

    try:
        # Create and send the email message
        email_message = EmailMessage(
            email_subject,
            body="Hi "
            + user.first_name
            + ",\nPlease use the link below to activate your account:\n"
            + activate_url,
            from_email="dclmcafinance@gmail.com",
            to=[user.email],
            bcc=["ugurunedu@gmail.com"],
        )
        print("email sent")
        email_message.send()
    except Exception as e:
        messages.error(request, "An error occurred while sending the activation email.")

# View for contributor registration
class ContributorRegistrationView(View):
    template_name = "authentication/register.html"

    def get(self, request):
        # Render the registration form
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST["email"]
        password = request.POST["password"]
        first_name = request.POST["first_name"]
        middle_name = request.POST["middle_name"]
        last_name = request.POST["last_name"]

        context = {"fieldValues": request.POST}

        # Create the user and send an activation email
        success, user = create_user_and_send_activation_email(
            request,
            email=email,
            password=password,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            role=Role.contributor.value
        )
        if success:
            messages.success(request, "Check the Activation Link in your email to activate your account")
            return redirect("login")

        return render(request, self.template_name, context)

# View for admin user registration
class AdminUserRegistrationView(View):
    template_name = "authentication/register_admin.html"

    def get(self, request):
        # Render the admin registration form
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST["email"]
        password = request.POST["password"]
        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]
        role = request.POST["role"]

        context = {"fieldValues": request.POST}

        # Create the admin user and send an activation email
        success, user = create_user_and_send_activation_email(
            request,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role,
        )
        if success:
            messages.success(request, "Admin account successfully created")
            return redirect("#")

        return render(request, self.template_name, context)

# View for account verification
class VerificationView(View):
    def get(self, request, uidb64, token):
        try:
            # Decode the user ID from the URL
            id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=id)

            # Check if the activation token is valid
            if not account_activation_token.check_token(user, token):
                return redirect("login" + "?message=" + "User already activated")

            # Check if the user is already active
            if user.is_active:
                return redirect("login")
            user.is_active = True
            user.save()

            messages.success(request, "Account activated successfully")
            return redirect("login")

        except Exception as ex:
            pass

        return redirect("login")

# View for user login
class LoginView(View):
    def get(self, request):
        # Render the login form
        return render(request, "authentication/new_login.html")

    def post(self, request):
        email = request.POST["email"]
        password = request.POST["password"]

        if email and password:
            # Authenticate the user
            user = auth.authenticate(email=email, password=password)

            if user:
                if user.is_active:
                    auth.login(request, user)
                    if user.first_name:
                        message = f"Welcome {user.first_name}, you are now logged in"
                    else:
                        message = f"Welcome, you are now logged in"
                    messages.success(
                        request,
                        message,
                    )
                    return redirect("dashboard")
                messages.error(request, "Account is not active,please check your email")

                return render(request, "authentication/new_login.html")
            messages.error(request, "Invalid credentials, try again")
            return render(request, "authentication/new_login.html")

        messages.error(request, "Please fill all fields")
        return render(request, "authentication/new_login.html")

# View for user logout
class LogoutView(View):
    def post(self, request):
        # Log out the user
        auth.logout(request)
        messages.success(request, "You have been logged out")
        return redirect("login")

    def get(self, request):
        # Log out the user
        auth.logout(request)
        messages.success(request, "You have been logged out")
        return redirect("login")


# View for requesting password reset email
class RequestPasswordResetEmail(View):
    def get(self, request):
        # Render the password reset request form
        return render(request, "authentication/reset-password.html")

    def post(self, request):
        # Extract the email from the POST request
        email = request.POST.get("email", "").strip()
        context = {"values": request.POST}

        # Validate the email format
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Please provide a valid email address.")
            return render(request, "authentication/reset-password.html", context)

        # Attempt to find a user with the provided email
        user = User.objects.filter(email=email).first()
        if not user:
            messages.error(request, "No account is associated with this email.")
            return render(request, "authentication/reset-password.html", context)

        # Generate password reset details
        email_contents = {
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": PasswordResetTokenGenerator().make_token(user),
        }
        reset_link = reverse(
            "reset-user-password",
            kwargs={
                "uidb64": email_contents["uid"],
                "token": email_contents["token"],
            },
        )

        reset_url = f"https://cms.deeperlife.ca{reset_link}"

        # Email configuration
        email_config = EMAIL_TEMPLATES["password_update_request"]
        subject = email_config["subject"]
        heading = email_config["heading"]
        message = email_config["message"].format(reset_link=reset_url)
        template_name = email_config["template_name"]

        # Context for the email
        email_context = {
            "first_name": user.first_name or "User",
            "heading": heading,
            "reset_link": reset_url,
            "message": message,
        }

        print(reset_url)

        # Send the email
        success = send_email(
            subject=subject,
            recipient_list=[user.email],
            plain_text_body=subject,
            context=email_context,
            template_name=template_name,
        )

        if success:
            messages.success(request, "We have sent you an email with instructions to reset your password.")
        else:
            messages.info(request, "There is an issue on our side. Please try again later.")

        return render(request, "authentication/reset-password.html")


# View for completing password reset
class CompletePasswordReset(View):
    def get(self, request, uidb64, token):
        context = {"uidb64": uidb64, "token": token}

        try:
            # Decode the user ID from the URL
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=user_id)

            # Check if the password reset token is valid
            if not PasswordResetTokenGenerator().check_token(user, token):
                messages.info(
                    request, "Password link is invalid. Please request a new one"
                )
                return render(request, "authentication/reset-password.html")

        except Exception as identifier:
            pass

        return render(request, "authentication/set-new-password.html", context)

    def post(self, request, uidb64, token):
        context = {"uidb64": uidb64, "token": token}

        password = request.POST["password"]
        password2 = request.POST["password2"]

        # Check if the passwords match
        if password != password2:
            messages.error(request, "Passwords do not match")
            return render(request, "authentication/set-new-password.html", context)

        # Check if the password is too short
        if len(password) < 8:
            messages.error(
                request, "Passwords too short. Should be a minimum of 8 characters"
            )
            return render(request, "authentication/set-new-password.html", context)

        try:
            # Decode the user ID from the URL
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=user_id)
            # Set the new password
            user.set_password(password)
            user.save()

            print(user.email)

            messages.success(
                request, "Password reset successfully, login with your new password"
            )
            return redirect("login")

        except Exception as identifier:
            messages.info(request, "There is an issue. Please try again")
            return render(request, "authentication/set-new-password.html", context)

        # return render(request, 'authentication/set-new-password.html', context)

# Get the user model
UserModel = get_user_model()

# View for listing users
class UserListView(LoginRequiredMixin, ListView):
    model = UserModel
    template_name = 'user_list.html'
    context_object_name = 'users'

    def __init__(self):
        super().__init__()
        self.filter_context = None

    def get_queryset(self):
        user = self.request.user

        local_churches = get_user_local_church(user)

        # Base query: Get users within the same local churches
        queryset = UserModel.objects.filter(local_church__in=local_churches)

        # Role-based filtering
        if user.role == 2:
            queryset = queryset.exclude(role__in=[3, 4]).exclude(is_staff=True)
        elif user.role == 4:
            queryset = queryset.exclude(role=3)

        # Use get_filtered_context to apply additional filters
        queryset, self.filter_context = get_filtered_context(
            self.request,
            queryset,
            model_field_map={
                "region": "local_church__region__name",
                "local_church": "local_church_id"
            }
        )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        local_churches = get_user_local_church(user)

        region = self.request.GET.get("region", None)
        regions = get_user_regions(user)

        if region:
            region_list = regions.filter(name__iexact=region)
            local_churches = local_churches.filter(region__in=region_list)

        context.update({
            "regions": regions,
            "churches": local_churches,
            **getattr(self, 'filter_context', {})
        })

        return context

# View for activating or deactivating a user
@require_POST
def user_activate_deactivate(request, user_id):
    user = get_object_or_404(User, id=user_id)

    # Toggle the user's active status
    user.is_active = not user.is_active
    user.save()

    return JsonResponse({'status': 'success'})

# View for user profile
class UserProfile(View):

    def get(self, request, id):
        current_user = request.user
        # Check if the current user is authenticated and has access to the profile
        if not current_user.is_authenticated or current_user.id != id:
            return render(request, '403.html', status=403)

        user = User.objects.get(id=id)
        users = {
            'id': user.id,
            'first_name': user.first_name if user.first_name else '',
            'middle_name': user.middle_name if user.middle_name else '',
            'last_name': user.last_name if user.last_name else '',
            'email': user.email if user.email else '',
            'address': user.address if user.address else '',
            'gender': user.gender if user.gender else ''
        }
        return render(request, 'authentication/profile.html', {'user': users})

    def post(self, request, id):
        current_user = request.user
        # Check if the current user is authenticated and has access to the profile
        if not current_user.is_authenticated or current_user.id != id:
            return render(request, '403.html', status=403)

        user = User.objects.get(id=id)
        try:
            first_name = request.POST.get('first_name', '')
            middle_name = request.POST.get('middle_name', '')
            last_name = request.POST.get('last_name', '')
            address = request.POST.get('address', '')
            gender = request.POST.get('gender', '')
            update_data = {
                'first_name': first_name,
                'middle_name': middle_name,
                'last_name': last_name,
                'address': address,
                'gender': gender
            }
            # Update the user's profile
            user = User.objects.update_user(user_id=id, **update_data)
            messages.success(request, "Profile Update Successfully.")
        except Exception as e:
            print(str(e))
            messages.info(request, "There is an issue. Please try again.")

        return render(request, 'authentication/profile.html', {'user': user})

# View for downloading a sample user uploader file
def download_user_uploader_sample(request):
    # Create a new workbook and add a worksheet
    workbook = Workbook()
    worksheet = workbook.active

    # Add headers to the worksheet
    headers = ['First Name', 'Middle Name', 'Last Name', 'Email', 'Address']
    worksheet.append(headers)

    header_row = worksheet[1]
    for cell in header_row:
        cell.font = Font(bold=True)
    data = [
        ['Liam', 'Andrew', 'Thompson', 'liam.thompson1@example.com', '123 Maple Street, Toronto, ON M5V 2T6'],
        ['Emily', '', 'Robertson', 'emily.robertson@example.com', '456 Oak Avenue, Vancouver, BC V6B 1A8'],
        ['Noah', 'James', 'Mitchell',  'emily.robertson@example.com', '456 Oak Avenue, Vancouver, BC V6B 1A8'],
        ['Sophia', '', 'Carter', 'sophia.carter22@example.com', '321 Elm Road, Montreal, QC H2Y 3E4']
    ]
    for sample_data in data:
        worksheet.append(sample_data)

    # Set column widths for better readability
    for col_num, column_letter in enumerate(get_column_letter(len(headers)), start=1):
        worksheet.column_dimensions[column_letter].width = 15

    # Create a response object with the XLSX content
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=sample_user_uploader_file.xlsx'
    workbook.save(response)

    return response

# View for uploading users from a file
class UserUploaderView(View):

    @staticmethod
    def validate_user_uploader(file, local_church_id, host):
        user_upload_helper = UserUploaderHelper()
        try:
            workbook = load_workbook(file, read_only=True)
            worksheet = workbook.active

            # Validate the headers of the worksheet
            if not user_upload_helper.validate_headers(worksheet):
                return {'error': 'Invalid headers'}

            for row_number, row in enumerate(worksheet.iter_rows(min_row=2, values_only=True), start=2):
                row = list(row) + [None] * max(0, 5 - len(row))
                print(row[0], row[2], row[3], row[4])
                first_name, middle_name,last_name, email, address = row[0],row[1], row[2], row[3], row[4]
                if not any([first_name, middle_name, last_name, email, address]):
                 continue
                full_name = " ".join([first_name, last_name])
                if middle_name:
                    full_name = " ".join([first_name, middle_name, last_name])
                if not email and not first_name and not last_name:
                    continue

                # Check for required fields
                if not email:
                    data = 'email' if not email else 'role'
                    return {'error': f'Required field missing in row {row_number}. Please provide {data}.'}

                if not first_name or not last_name:
                    if not full_name:
                        return {'error': f'Required field missing in row {row_number}. Please provide name'}

                # Validate the email format
                if not user_upload_helper.validate_email(email):
                    return {'error': f'Invalid Email {email} at row {row_number}.'}

                # if not user_upload_helper.validate_role(role):
                #     return {'error': f'Invalid Role {role} at row {row_number}.'}

            user_upload_helper.process_and_save(worksheet, local_church_id, host)

        except Exception as e:
            return {'error': f'Error processing the file: {str(e)}'}

    def get(self, request):
        user = self.request.user
        # Get the local churches associated with the user
        local_churches = get_user_local_church(user)
        local_church = local_churches
        return render(request, 'authentication/user_uploader.html', {'local_churches': local_church})

    def post(self, request):
        host = request.get_host().split('://')[1] if '://' in request.get_host() else request.get_host()
        errors = self.validate_user_uploader(request.FILES['file'], request.POST.get('local_church'), host)
        print(errors)
        if errors:
            local_church = LocalChurch.objects.all()
            return render(request, 'authentication/user_uploader.html', {'errors': errors, 'local_churches': local_church})
        messages.success(request, 'User uploaded and processed successfully!')
        return redirect('user_uploader')

# View for adding a new user
class UserAddView(View):
    def get(self, request):
        local_churches = []
        user = self.request.user
        # Get the local churches associated with the user
        local_churches = get_user_local_church(user)
        return render(request, 'authentication/add_user.html', {'local_churches': local_churches})

    def post(self, request):
        try:
            request_data = request.POST
            # Check if the user already exists
            if not User.objects.filter(email=request_data.get('email')).exists():
                data = {
                    "email": request_data.get('email'),
                    "password": "123456",
                    "first_name": request_data.get('first_name'),
                    "middle_name": request_data.get('middle_name', ''),
                    "last_name": request_data.get('last_name'),
                    "address": request_data.get('address'),
                    "full_name": request_data.get('full_name'),
                    "is_active": True,
                    "role": request_data.get('role'),
                    'local_church': LocalChurch.objects.get(id=request_data.get('local_church'))
                }
                # Create the user
                user = User.objects.create_user(**data)
                user.save()
                user.refresh_from_db()

                print(user.role)

                if user.role != 1 and user.role != 6:
                    # Generate a random password
                    plain_password = get_random_string(length=12)  # Generate a 12-character password
                    user.set_password(plain_password)
                    user.save()
                    user.refresh_from_db()

                    if user.role == 2:
                        user.local_church.local_church_pastor = user
                        user.local_church.save()

                    if user.role == 4:
                        user.local_church.region.region_overseer = user
                        user.local_church.region.save()

                    # Prepare the email data
                    email_data = {
                        "email": user.email,
                        "first_name": user.first_name if user.role == 5 else f"Pastor {user.first_name}",
                        "token": plain_password,
                    }

                    # Trigger the asynchronous email task
                    send_user_added_email_task.delay(email_data)

                messages.success(request, 'User Added Successfully')
                return redirect('user_list')
            else:
                print("User already exists")
                messages.error(request, 'An User with Similar Email Address Already Exists')
                return redirect('user_add')
        except Exception as e:
            print(e)
            messages.error(request, "Something Went Wrong")
            return redirect('user_add')


# Function to get the number of unique contributors who are not deleted
def get_unique_users_count(user):
    """
    Returns the number of unique contributors who are not deleted.
    """
    users = User.objects.filter(is_active=True)

    if user.role == 2:
        users = users.filter(local_church=user.local_church)
    elif user.role == 4:
        users = users.filter(local_church__region__region_overseer=user)

    print(users.count(), user.role)

    return users.count()


class MiscellaneousUsersListView(LoginRequiredMixin, ListView):
    model = MiscellaneousUser
    template_name = 'authentication/misc_user_list.html'
    context_object_name = 'misc_users'

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return MiscellaneousUser.objects.all().order_by("-id")

        return MiscellaneousUser.objects.filter(registered_miscellaneous=user).order_by("-id")


class UpdateMiscellaneousUserProfileView(LoginRequiredMixin, View):

    def get(self, request, id):
        misc_user = get_object_or_404(MiscellaneousUser, id=id)
        try:
            registered_user = misc_user.registered_miscellaneous

            # Determine the local church or churches to display
            contributions = MiscellaneousContribution.objects.filter(contributor=misc_user)
            local_church = contributions.first().local_church if contributions.exists() else None

            if not local_church:
                if registered_user and registered_user.local_church:
                    if registered_user.role == 2:
                        local_church = registered_user.local_church
                    elif registered_user.role == 4:
                        local_church = list(LocalChurch.objects.filter(region=registered_user.local_church.region))
                else:
                    local_church = list(LocalChurch.objects.all())

            # Prepare the context for the template
            context = {
                'id': misc_user.id,
                'first_name': misc_user.first_name or '',
                'middle_name': misc_user.middle_name or '',
                'last_name': misc_user.last_name or '',
                'email': misc_user.email or '',
                'address': misc_user.address or '',
                'full_name': misc_user.full_name or '',
                'local_churches': local_church if isinstance(local_church, list) else [],
                'local_church': local_church if not isinstance(local_church, list) else None,
                'can_edit_full_name': misc_user.can_edit_full_name,
            }

            return render(request, 'authentication/update_misc_user_profile.html', {'user': context})

        except Exception as e:
            print(f"Error Get Miscellaneous User: {str(e)}")
            messages.error(request, "There is an issue. Please try again.")
            return redirect("miscellaneous_users_list")

    def post(self, request, id):
        misc_user = get_object_or_404(MiscellaneousUser, id=id)

        try:
            # Extract data from the POST request
            first_name = request.POST.get('first_name', '').strip()
            middle_name = request.POST.get('middle_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            address = request.POST.get('address', '').strip()
            local_church_id = request.POST.get('local_church', '').strip()
            email = request.POST.get('email', '').strip()
            full_name = request.POST.get('full_name', '').strip()

            local_church = None
            if local_church_id:
                local_church = get_object_or_404(LocalChurch, id=local_church_id)

            # If both full_name and email are provided, attempt to save to User model
            if full_name and email:
                # Check if the email already exists in the User model
                if User.objects.filter(email=email).exists():
                    messages.error(request, f"A user with the email {email} already exists.")
                    return redirect('update_miscellaneous_user_profile', id=misc_user.id)

                # Create a new user
                new_user = User.objects.create_user(
                    full_name=full_name if misc_user.can_edit_full_name else misc_user.full_name,
                    first_name=first_name,
                    middle_name=middle_name,
                    last_name=last_name,
                    email=email,
                    password='12345678',
                    local_church=local_church,
                    role=User.MEMBER,
                )
                new_user.save()

                # Move contributions from MiscellaneousContribution to Contributions
                contributions = MiscellaneousContribution.objects.filter(contributor=misc_user)
                for contribution in contributions:
                    Contribution.objects.create(
                        contributor=new_user,
                        local_church=contribution.local_church,
                        amount=contribution.amount,
                        payment_type=contribution.payment_type,
                        special_contribution=contribution.special_contribution,
                        month=contribution.month,
                        account_type=contribution.account_type,
                        deposited_date=contribution.deposited_date
                    )
                    contribution.delete()  # Delete the old contributions

                # Delete the MiscellaneousUser
                misc_user.delete()

                messages.success(request, "Miscellaneous user successfully registered as "
                                          "a regular user and contributions transferred.")
                return redirect('miscellaneous_users_list')

            # If full_name or email is missing, update as a Miscellaneous User
            update_data = {
                "id": misc_user.id,
                'first_name': first_name,
                'middle_name': middle_name,
                'last_name': last_name,
                'address': address,
                'email': email if email else None,
                'full_name': full_name if misc_user.can_edit_full_name else misc_user.full_name
            }
            # Update the MiscellaneousUser profile
            for field, value in update_data.items():
                setattr(misc_user, field, value)
            misc_user.save()

            if local_church:
                contributions = MiscellaneousContribution.objects.filter(contributor=misc_user)
                for contribution in contributions:
                    contribution.local_church = local_church
                    contribution.save()

            messages.success(request, "Miscellaneous User Profile Updated Successfully.")
            return redirect('miscellaneous_users_list')

        except Exception as e:
            print(f"Error: {str(e)}")
            messages.error(request, "There is an issue. Please try again.")
            return redirect('update_miscellaneous_user_profile', id=misc_user.id)

    def delete(self, request, id):
        try:
            if request.user.role != 1:
                user = get_object_or_404(MiscellaneousUser, id=id)
                user.delete()
                messages.success(request, "User successfully deleted!")
                return redirect('miscellaneous_users_list')
        except Exception as e:
            print(str(e))  # Log the error for debugging
            messages.error(request, "Something went wrong. Please try again.")
            return redirect(request.META.get("HTTP_REFERER", "fallback_url"))


class ManageUserView(LoginRequiredMixin, View):
    def get(self, request, id):
        user = self.request.user
        local_churches = get_user_local_church(user)
        instance = get_object_or_404(get_user_model(), id=id)
        return render(request, 'authentication/edit_user.html', {'local_churches': local_churches, "user": instance})

    def post(self, request, id):
        try:
            request_data = request.POST
            user = get_object_or_404(get_user_model(), id=id)
            data = {
                "first_name": request_data.get('first_name'),
                "middle_name": request_data.get('middle_name', ''),
                "last_name": request_data.get('last_name'),
                "address": request_data.get('address'),
                "full_name": request_data.get('full_name'),
                "is_active": True,
                "role": request_data.get('role'),
                'local_church': LocalChurch.objects.get(id=request_data.get('local_church'))
            }

            for attr, value in data.items():
                setattr(user, attr, value)
            user.save()
            user.refresh_from_db()

            if user.role != 1:
                if user.role == 2:
                    user.local_church.local_church_pastor = user
                    user.local_church.save()

                if user.role == 4:
                    user.local_church.region.region_overseer = user
                    user.local_church.region.save()

            messages.success(request, 'User Updated Successfully')
            return redirect('user_list')

        except Exception as e:
            print(e)
            messages.error(request, "Something Went Wrong")
            return redirect('user_edit', id=id)


def user_delete(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        user.delete()
        return JsonResponse({'message': 'User deleted successfully', 'ok': True}, status=200)
    except User.DoesNotExist:
        return JsonResponse({'message': 'User not found'}, status=404)


def help_page(request):
    return render(request, 'help/help.html')
