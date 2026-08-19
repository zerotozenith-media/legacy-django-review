from .views import (
    AdminUserRegistrationView,
    ContributorRegistrationView,
    UsernameValidationView,
    EmailValidationView,
    VerificationView,
    LoginView,
    LogoutView,
    RequestPasswordResetEmail,
    CompletePasswordReset,
    user_activate_deactivate,
    UserListView,
    UserProfile,
    UserUploaderView,
    download_user_uploader_sample,
    UserAddView, MiscellaneousUsersListView, UpdateMiscellaneousUserProfileView, help_page,
    ManageUserView,
    user_delete
)
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

# app_name = "authentication"

urlpatterns = [
    path("register", ContributorRegistrationView.as_view(), name="register"),
    path("invite-users", AdminUserRegistrationView.as_view(), name="invite-users"),
    path(
        "validate-username",
        csrf_exempt(UsernameValidationView.as_view()),
        name="validate-username",
    ),
    path(
        "validate-email",
        csrf_exempt(EmailValidationView.as_view()),
        name="validate_email",
    ),
    path("login", LoginView.as_view(), name="login"),
    path("logout", LogoutView.as_view(), name="logout"),
    path(
        "request-reset-link",
        RequestPasswordResetEmail.as_view(),
        name="request-password",
    ),
    path("activate/<uidb64>/<token>", VerificationView.as_view(), name="activate"),
    path(
        "set-new-password/<uidb64>/<token>",
        CompletePasswordReset.as_view(),
        name="reset-user-password",
    ),
    path('<int:user_id>/activate-deactivate/', user_activate_deactivate, name='user_activate_deactivate'),
    path('users/', UserListView.as_view(), name='user_list'),
    path('profile/<int:id>/', UserProfile.as_view(), name='user_profile'),
    path('user-uploader-sample/', download_user_uploader_sample, name='download_user_uploader_sample'),
    path('user/uploader/', UserUploaderView.as_view(), name='user_uploader'),
    path('user/add/', UserAddView.as_view(), name='user_add'),
    path('user/edit/<int:id>/', ManageUserView.as_view(), name='user_edit'),
    path('user/delete/<int:user_id>/', user_delete, name='user_delete'),
    path('miscellaneous-users/', MiscellaneousUsersListView.as_view(), name='miscellaneous_users_list'),
    path('update-miscellaneous-user-profile/<int:id>/', UpdateMiscellaneousUserProfileView.as_view(),
         name='update_miscellaneous_user_profile'),
    path('help/', help_page, name='help'),
]
