from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _

from contributor.models import MiscellaneousUser


class UserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """

    @staticmethod
    def create_full_name(first_name, middle_name, last_name):
        names = [name for name in [first_name, middle_name, last_name] if name]
        return ' '.join(names)

    def create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given email and password.
        """
        if not email:
            raise ValueError(_("The Email must be set"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.full_name = self.create_full_name(first_name=user.first_name, middle_name=user.middle_name,
                                               last_name=user.last_name)
        user.save()

        miscellaneous_user = MiscellaneousUser.objects.filter(email=email)
        if miscellaneous_user.exists():
            miscellaneous_user = miscellaneous_user.first()
            miscellaneous_user.registered_miscellaneous = user
            miscellaneous_user.save()

        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))
        return self.create_user(email, password, **extra_fields)

    def update_user(self, user_id, **update_fields):
        try:
            user = self.get(pk=user_id)
        except self.model.DoesNotExist:
            raise ValueError(f'User with id {user_id} does not exist')
        first_name = update_fields.get("first_name")
        middle_name = update_fields.get("middle_name")
        last_name = update_fields.get("last_name")
        gender = update_fields.get("gender")
        update_fields['full_name'] = self.create_full_name(first_name=first_name, middle_name=middle_name,
                                                           last_name=last_name)
        for field, value in update_fields.items():
            setattr(user, field, value)
        user.save(using=self._db)
        return user
