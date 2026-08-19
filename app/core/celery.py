import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
app = Celery("core", broker=settings.CELERY_BROKER_URL)

# Celery configuration for broker and retry options
app.conf.broker_transport_options = {
    "priority_steps": list(range(10)),
    "sep": ":",
    "queue_order_strategy": "priority",
}

app.conf.broker_connection_retry = True
app.conf.broker_connection_retry_on_startup = True
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered django app configs
app.autodiscover_tasks()


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):  # noqa
    """This is just a test log task to make sure celery is working.
        Note: You will not see this in the django admin.
    """
    # Crontab for every third week of the month (Monday 10:00 AM)
    third_week_schedule, _ = crontab(
        minute="0",
        hour="10",
        day_of_month="15-21",  # Range covering the third week
        month_of_year="*",  # Every month
        day_of_week="1",  # Monday (0=Sunday, 1=Monday)
    )

    # Add periodic task for logging
    sender.add_periodic_task(
        third_week_schedule,
        test_task.s('TASKS ARE WORKING'),
        name="tasks_checks",
    )


@app.task
def test_task(arg):
    logger.info(f"PERIODIC TASK CHECK: {arg}")


@app.task(bind=True)
def debug_task(self):
    logger.info('Request: {0!r}'.format(self.request))


# Use django-celery-beat's DatabaseScheduler
app.conf.beat_scheduler = 'django_celery_beat.schedulers:DatabaseScheduler'


@app.on_after_finalize.connect
def schedule_reminder_tasks(sender, **kwargs):  # noqa
    """
    Schedule periodic tasks for sending reminder and escalation emails.
    """
    from django_celery_beat.models import CrontabSchedule, PeriodicTask

    # Crontab for the last day of the month at 10:00 AM
    last_day_of_month_schedule, _ = CrontabSchedule.objects.get_or_create(
        minute=0,
        hour=10,  # 10:00 AM
        day_of_month="last",
        month_of_year="*",  # Every month
        day_of_week="*"  # Ignore the weekday
    )

    first_day_of_month_schedule, _ = CrontabSchedule.objects.get_or_create(
        minute=0,
        hour=6,  # 6:00 am
        day_of_month="first",
        month_of_year="*",
        day_of_week="*"
    )

    # Task to create payment allocations for the last month for each region
    PeriodicTask.objects.update_or_create(
        task="organization.tasks.create_payment_allocation_task",
        name="Create Payment Allocations for Regions for Last Month",
        defaults={
            "crontab": last_day_of_month_schedule,
            "expire_seconds": None,
        }
    )

    # Task to send reminders to regional overseers at the end of every month
    PeriodicTask.objects.update_or_create(
        task="organization.tasks.allocation_payment_reminder_task",
        name="Send Payment Allocation Reminder Emails",
        defaults={
            "crontab": last_day_of_month_schedule,
            "expire_seconds": None,  # No expiration as this is a specific schedule
        }
    )

    # Crontab for the second day of the next month at 10:00 AM
    second_day_of_month_schedule, _ = CrontabSchedule.objects.get_or_create(
        minute=0,
        hour=10,
        day_of_month="2",
        month_of_year="*",  # Every month
        day_of_week="*"  # Ignore the weekday
    )

    # Task to escalate to the national overseer on the second day of the month
    PeriodicTask.objects.update_or_create(
        task="organization.tasks.escalate_payment_allocation_to_national_oversea",
        name="Escalate Payment Allocation Reminder to National Oversea",
        defaults={
            "crontab": second_day_of_month_schedule,
            "expire_seconds": None,  # No expiration as this is a specific schedule
        }
    )

    PeriodicTask.objects.update_or_create(
        task="organization.tasks.handle_pastor_detail_report_reminder",
        name="Pastor Reminders for Detailed Report Submission",
        defaults={
            "crontab": last_day_of_month_schedule,
            "expire_seconds": None,  # No expiration as this is a repeating schedule
        }
    )

    PeriodicTask.objects.update_or_create(
        task="organization.tasks.handle_pastor_detail_report_cc_regional_oversea",
        name="Escalate Pastor Detailed Report Issues to Regional Oversea",
        defaults={
            "crontab": second_day_of_month_schedule,
            "expire_seconds": None,  # No expiration as this is a specific schedule
        }
    )

    day_5th_schedule, _ = CrontabSchedule.objects.get_or_create(
        minute=0,
        hour=12,  # 12:00 PM
        day_of_month="5",
        month_of_year="*",  # Every month
        day_of_week="*",  # Ignore the weekday
    )

    PeriodicTask.objects.update_or_create(
        task="organization.tasks.handle_pastor_detail_report_cc_regional_overseer_and_national_oversea",
        name="Escalate Pastor Detailed Report Issues to Regional Oversea",
        defaults={
            "crontab": day_5th_schedule,
            "expire_seconds": None,  # No expiration as this is a specific schedule
        }
    )

    first_tuesday_of_every_month, _ = CrontabSchedule.objects.get_or_create(
        minute=0,
        hour=10,
        day_of_month="1-7",
        month_of_year="*",
        day_of_week="2",
    )

    PeriodicTask.objects.update_or_create(
        task="contributor.tasks.send_reminder_for_miscellaneous_users_profile_updating",
        name="First Pastor/Regional Oversea Reminders for Miscellaneous users updating.",
        defaults={
            "crontab": first_tuesday_of_every_month,
            "expire_seconds": None,  # No expiration as this is a repeating schedule
        }
    )

    first_friday_of_every_month, _ = CrontabSchedule.objects.get_or_create(
        minute=0,
        hour=10,
        day_of_month="1-7",
        month_of_year="*",
        day_of_week="5",
    )

    PeriodicTask.objects.update_or_create(
        task="contributor.tasks.send_reminder_for_miscellaneous_users_profile_updating",
        name="Second Pastor/Regional Oversea Reminders for Miscellaneous users updating.",
        defaults={
            "crontab": first_friday_of_every_month,
            "expire_seconds": None,  # No expiration as this is a repeating schedule
        }
    )
