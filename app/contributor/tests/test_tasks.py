from collections import defaultdict

from django.test import TestCase, Client
from django.utils.timezone import now
from unittest.mock import patch, MagicMock
from contributor.models import MiscellaneousUser, MiscellaneousContribution
from organization.models import LocalChurchName
from utils.send_emails import send_email
from utils.test_db import Testdb


class MiscellaneousUserProfileReminderTest(TestCase):

    def setUp(self):
        # Create a local church
        self.testdb = Testdb()

        self.client = Client()
        self.pastor = self.testdb.create_user(role=2, first_name="Pastor")
        self.pastor2 = self.testdb.create_user(email="past2@example.com", role=2, middle_name="Sum",
                                               first_name="Pastor2", last_name="Jons")
        self.local_church = self.testdb.create_local_church(local_church_pastor=self.pastor)
        church_name = LocalChurchName.objects.create(title="Latest")
        self.local_church2 = self.testdb.create_local_church(local_church_name=church_name,
                                                             local_church_pastor=self.pastor2)

        # Completed profile. test should skip this
        MiscellaneousUser.objects.create(
            full_name="Test first",
            email="completed@example.com",
            first_name="Test",
            middle_name="S",
            last_name="Z",
            address="123",
        )

        # FIRST LOCAL CHURCH
        self.incomplete_user = MiscellaneousUser.objects.create(
            email="incomplete@example.com",
        )

        # Create a contribution for the incomplete user
        self.contribution = MiscellaneousContribution.objects.create(
            contributor=self.incomplete_user,
            deposited_date=now().date(),
            amount=1.00,
            local_church=self.local_church
        )

        another = MiscellaneousUser.objects.create(
            full_name="another first",
            email="incomplete1@example.com",
            first_name="another"
        )

        MiscellaneousContribution.objects.create(
            contributor=another,
            deposited_date=now().date(),
            amount=1.00,
            local_church=self.local_church
        )

        # second local church
        second = MiscellaneousUser.objects.create(
            full_name="second local church",
            email="incomplete11@example.com",
            first_name="second "
        )
        MiscellaneousContribution.objects.create(
            contributor=second,
            deposited_date=now().date(),
            amount=200.00,
            local_church=self.local_church2
        )

    @patch("utils.send_emails.EmailMultiAlternatives.send")
    def test_email_sent_to_regional_overseer_for_no_local_church(self, mock_send):
        # Create a regional overseer
        regional_overseer = self.testdb.create_user(role=3, first_name="Regional1", email="regional@example.com")
        regional_overseer2 = self.testdb.create_user(role=3, first_name="other Regional2",
                                                     email="regional2@example.com")

        # Create a user without a local church
        user_without_local_church = MiscellaneousUser.objects.create(
            full_name="No Church User",
            registered_miscellaneous=regional_overseer,
        )

        # Create a contribution for the user without a local church
        MiscellaneousContribution.objects.create(
            contributor=user_without_local_church,
            deposited_date=now().date(),
            amount=50.00,
            local_church=None
        )

        MiscellaneousContribution.objects.create(
            contributor=user_without_local_church,
            deposited_date=now().date(),
            amount=50.00,
            local_church=None
        )

        # Create a user without a local church
        user_without_local_church2 = MiscellaneousUser.objects.create(
            full_name="No Church User",
            registered_miscellaneous=regional_overseer2,
        )

        MiscellaneousContribution.objects.create(
            contributor=user_without_local_church2,
            deposited_date=now().date(),
            amount=50.00,
            local_church=None
        )

        mock_send.return_value = 1

        # Identify contributions for users with no local church
        contributions = MiscellaneousContribution.objects.filter(
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

        self.assertEqual(contributions.count(), 6)

        pastor_contribution_map = defaultdict(list)
        regional_overseer_contribution_map = defaultdict(list)

        # Iterate through contributions
        for contribution in contributions:
            local_church = contribution.local_church
            if local_church and local_church.local_church_pastor:
                pastor_contribution_map[local_church.local_church_pastor].append(contribution)
            else:
                # Assign contributions without a local pastor to the regional overseer
                regional_overseer = contribution.contributor.registered_miscellaneous
                regional_overseer_contribution_map[regional_overseer].append(contribution)

        self.assertEqual(len(pastor_contribution_map), 2)
        self.assertEqual(len(regional_overseer_contribution_map), 2)

        subject = "Reminder: Update Incomplete User Profiles"
        # Send a single email per pastor
        for pastor, contributions in pastor_contribution_map.items():
            incomplete_count = len(contributions)
            success = send_email(
                subject=subject,
                recipient_list=[pastor.email],
                context={},
                plain_text_body=f"{incomplete_count} Reminder",
            )
            self.assertTrue(success)

        # Send a single email per regional overseer
        for regional_overseer, contributions in regional_overseer_contribution_map.items():
            incomplete_count = len(contributions)
            success = send_email(
                subject=subject,
                recipient_list=[regional_overseer.email],
                context={},
                plain_text_body=f"{incomplete_count} Reminder",
            )
            self.assertTrue(success)

        # Verify send was called 4 times
        self.assertEqual(mock_send.call_count, 4)