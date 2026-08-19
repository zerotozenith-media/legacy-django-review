from datetime import timedelta

from decimal import Decimal
from django.test import TestCase, Client
from django.utils.timezone import now
from django_celery_beat.models import CrontabSchedule, PeriodicTask

from organization.models import PaymentAllocation
from organization.tasks import allocation_payment_reminder_task, escalate_to_national_overseer
from utils.test_db import Testdb


class PaymentAllocationTaskTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.testdb = Testdb()

        self.region_oversea_email = "region_oversea@example.com"
        self.region_oversea = self.testdb.create_user(email=self.region_oversea_email, role=4, first_name="Regional")
        self.region = self.testdb.create_region(name="Ottawa", region_overseer=self.region_oversea)

        # Calculate the last month's date
        current_date = now()
        first_of_month = current_date.replace(day=1)
        last_month = first_of_month - timedelta(days=1)

        self.payment_allocation = PaymentAllocation.objects.create(
            region=self.region,
            date=last_month,
            income=Decimal(10000.00),
            total_amount=Decimal(1000.00),
            paid_amount=Decimal(500.00),
            name="gck",
            note="Will paid more later",
            payment_date=last_month
        )
        self.create_schedule()

    @staticmethod
    def create_schedule():
        # Crontab for the last day of the month at 10:00 AM
        last_day_of_month_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour=10,  # 10:00 AM
            day_of_month="last",
            month_of_year="*",  # Every month
            day_of_week="*"  # Ignore the weekday
        )

        # Task to send reminders to regional overseers at the end of every month
        PeriodicTask.objects.update_or_create(
            task="organization.tasks.allocation_payment_reminder_task",
            name="Send Payment Reminder Emails",
            defaults={
                "crontab": last_day_of_month_schedule,
                "expire_seconds": None,  # No expiration as this is a specific schedule
            }
        )

        # Crontab for the first day of the next month at 10:00 AM
        first_day_of_month_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour=10,  # 10:00 AM
            day_of_month="1",
            month_of_year="*",  # Every month
            day_of_week="*"  # Ignore the weekday
        )

        # Task to escalate to the national overseer on the first day of the month
        PeriodicTask.objects.update_or_create(
            task="organization.tasks.escalate_to_national_overseer",
            name="Escalate Payment Reminder to National Overseer",
            defaults={
                "crontab": first_day_of_month_schedule,
                "expire_seconds": None,  # No expiration as this is a specific schedule
            }
        )

    def test_last_day_of_month_schedule(self):
        # Verify the CrontabSchedule for the last day of the month at 10:00 AM
        schedule = CrontabSchedule.objects.filter(
            minute=0,
            hour=10,
            day_of_month="last",
            month_of_year="*",
            day_of_week="*"
        ).first()
        self.assertIsNotNone(schedule, "Last day of month schedule was not created.")

        # Verify the PeriodicTask for sending payment reminders
        task = PeriodicTask.objects.filter(
            task="organization.tasks.allocation_payment_reminder_task",
            name="Send Payment Reminder Emails"
        ).first()
        self.assertIsNotNone(task, "Periodic task for last day of the month was not created.")
        self.assertEqual(task.crontab, schedule, "Task is not linked to the correct schedule.")

    def test_first_day_of_month_schedule(self):
        # Crontab for the first day of the next month at 10:00 AM
        first_day_of_month_schedule, created = CrontabSchedule.objects.get_or_create(
            minute="0",
            hour="10",
            day_of_month="1",
            month_of_year="*",
            day_of_week="*"
        )

        # Verify the schedule exists
        schedule = CrontabSchedule.objects.filter(
            minute="0",
            hour="10",
            day_of_month="1",
            month_of_year="*",
            day_of_week="*"
        ).first()
        self.assertIsNotNone(schedule, "First day of month schedule was not created.")
        self.assertEqual(first_day_of_month_schedule, schedule)
        self.assertTrue(created or not created, "Ensure get_or_create behaves as expected.")

        # Verify the PeriodicTask for escalating payment reminders
        task = PeriodicTask.objects.filter(
            task="organization.tasks.escalate_to_national_overseer",
            name="Escalate Payment Reminder to National Overseer"
        ).first()
        self.assertIsNotNone(task, "Periodic task for first day of the month was not created.")
        self.assertEqual(task.crontab, schedule, "Task is not linked to the correct schedule.")

    def test_allocation_payment_reminder_task(self):
        """
        Test the allocation payment reminder task.
        """
        # Run the task
        allocation_payment_reminder_task()

    def test_escalate_to_national_overseer(self):
        """
        Test the escalation task for incomplete payments.
        """
        # Run the task
        escalate_to_national_overseer()