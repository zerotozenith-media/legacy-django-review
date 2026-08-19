from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection

class Command(BaseCommand):
    help = "Resets the database by dropping and recreating all tables."

    def handle(self, *args, **options):
        self.stdout.write("Resetting the database...")

        with connection.cursor() as cursor:
            cursor.execute("DROP SCHEMA public CASCADE;")
            cursor.execute("CREATE SCHEMA public;")

        # Apply all migrations to recreate the database schema
        call_command('migrate')

        self.stdout.write(self.style.SUCCESS("Database reset completed."))
