import os

from django.core.management.base import BaseCommand

from authentication.models import User


class Command(BaseCommand):
    help = 'Create a superuser if not exists'

    def handle(self, *args, **kwargs):
        email = os.environ.get("ADMIN_EMAIL")
        password = os.environ.get("ADMIN_PASSWORD")

        if not User.objects.filter(email=email).exists():
            user = User.objects.create_superuser(email=email, password=password)
            user.role = 3
            user.save()

            self.stdout.write(self.style.SUCCESS(f"Superuser {email} created successfully"))
        else:
            self.stdout.write(self.style.WARNING(f"Superuser {email} already exists"))
