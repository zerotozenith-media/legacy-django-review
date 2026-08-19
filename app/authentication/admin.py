from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import User


# Custom User Admin
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm  # Form to create a new user
    form = CustomUserChangeForm  # Form to change an existing user
    model = User
    list_per_page = 20

    # Fields to display in the user list view
    list_display = ('email', 'full_name', 'role', 'is_active', 'is_staff', 'local_church')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name', 'full_name')

    # Fields to display when editing a user
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info',
         {'fields': ('full_name', 'first_name', 'middle_name', 'last_name', 'address', 'gender', 'local_church')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login',)}),
    )

    # Fields to display when adding a new user
    add_fieldsets = (
        (None, {'fields': ('email', 'password1', 'password2')}),
        ('Personal Info', {'fields': ('full_name', 'first_name', 'middle_name', 'last_name', 'local_church')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff')}),
    )

    # Ordering of users in the list view
    ordering = ('email',)
