from celery import shared_task
import logging
from collections import defaultdict

from contributor.models import MiscellaneousContribution
from utils.email_templates import EMAIL_TEMPLATES
from utils.send_emails import send_email

logger = logging.getLogger(__name__)


@shared_task
def send_reminder_for_miscellaneous_users_profile_updating():
    """
    Finds contributors with incomplete profiles and sends a consolidated email reminder
    to their respective local church pastor or regional oversea.
    """
    try:
        # Find contributions where the contributor has an incomplete profile
        contributions_with_incomplete_profiles = MiscellaneousContribution.objects.filter(
            contributor__isnull=False
        ).filter(
            contributor__full_name__isnull=True
        ) | MiscellaneousContribution.objects.filter(
            contributor__first_name__isnull=True
        ) | MiscellaneousContribution.objects.filter(
            contributor__last_name__isnull=True
        ) | MiscellaneousContribution.objects.filter(
            contributor__email__isnull=True
        ) | MiscellaneousContribution.objects.filter(
            contributor__address__isnull=True
        )

        # Group contributions
        pastor_contribution_map = defaultdict(list)
        regional_overseer_contribution_map = defaultdict(list)

        for contribution in contributions_with_incomplete_profiles:
            local_church = contribution.local_church
            if local_church and local_church.local_church_pastor:
                pastor_contribution_map[local_church.local_church_pastor].append(contribution)
            else:
                # Assign miscellaneous users without a local pastor to the regional overseer
                regional_overseer = contribution.contributor.registered_miscellaneous
                if regional_overseer:
                    regional_overseer_contribution_map[regional_overseer].append(contribution)
                else:
                    continue

        email_config = EMAIL_TEMPLATES["update_miscellaneous_users"]
        subject = email_config["subject"]
        heading = email_config["heading"]
        template_name = email_config["template_name"]

        # Send a single email per pastor
        for pastor, contributions in pastor_contribution_map.items():
            incomplete_count = len(contributions)
            context = {
                "first_name": f"Pastor {pastor.first_name}" if pastor.first_name else "Pastor",
                "heading": heading,
                "message": email_config["message"].format(count=incomplete_count, role="local church"),
            }

            send_email(
                subject=subject,
                recipient_list=[pastor.email],
                template_name=template_name,
                context=context,
                plain_text_body=context["message"],
            )

        # Send a single email per regional oversea
        for regional_overseer, contributions in regional_overseer_contribution_map.items():
            incomplete_count = len(contributions)
            context = {
                "first_name": f"Pastor {regional_overseer.first_name}" if regional_overseer.first_name else "Pastor",
                "heading": heading,
                "message": email_config["message"].format(count=incomplete_count, role="region"),
            }

            send_email(
                subject=subject,
                recipient_list=[regional_overseer.email],
                template_name=template_name,
                context=context,
                plain_text_body=context["message"],
            )

    except Exception as e:
        logger.error(f"Failed to send miscellaneous users profile update reminder emails: {e}")
