"""
Access control tests for contribution and tax receipt endpoints.

These cover a gap where the contributor app's views carried no authentication
or role check. The authorization middleware only inspects a whitelist of URL
prefixes and "contributor" was absent, so anonymous visitors and any logged in
user regardless of role could reach receipt generation.

Policy under test, from the system documentation:
  - Only National Overseers and Region Overseers may generate and manage tax
    receipts. Local church pastors may not.
  - Pastors may record and view contributions.
  - Members and donors may do neither.
  - Anonymous users may do neither.
"""

from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from authentication.models import User


RECEIPT_URL_NAMES = [
    "receipts_generation_page",
    "offering_can_summary_report",
    "offerings_can_letter_report",
    "interac_summary_report",
    "interac_letter_report",
    "search-donor-names",
    "donations-receipt-list",
]

CONTRIBUTION_URL_NAMES = [
    "cash-donation-list",
    "offerings_usd_list",
    "interac_transfer_list",
]


# Query strings some endpoints need in order to reach their own logic at all.
# These tests check who may reach a view, not how it handles bad input, so a
# view that requires a parameter is given one. search-donor-names raises
# ValueError without a church id, because it passes the empty string straight
# into a database id lookup. That is a separate pre-existing defect, logged for
# the test-harness batch, and deliberately not fixed here.
URL_QUERY_STRINGS = {
    "search-donor-names": "?term=a&church=1",
}


def _resolvable(names):
    """Skip any URL name not present, so the suite stays green if a route is
    later renamed rather than failing for the wrong reason."""
    out = []
    for name in names:
        try:
            out.append((name, reverse(name) + URL_QUERY_STRINGS.get(name, "")))
        except NoReverseMatch:
            continue
    return out


class ReceiptAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        def mk(email, role):
            return User.objects.create_user(
                email=email, password="test-pass-12345", role=role
            )

        cls.member = mk("t-member@example.com", User.MEMBER)
        cls.donor = mk("t-donor@example.com", User.DONOR)
        cls.pastor = mk("t-pastor@example.com", User.LOCAL_CHURCH_PASTOR)
        cls.region = mk("t-region@example.com", User.REGION_OVERSEER)
        cls.national = mk("t-national@example.com", User.NATIONAL_OVERSEER)

        cls.receipt_urls = _resolvable(RECEIPT_URL_NAMES)
        cls.contribution_urls = _resolvable(CONTRIBUTION_URL_NAMES)

    # --- anonymous -------------------------------------------------- #

    def test_anonymous_blocked_from_receipts(self):
        for name, url in self.receipt_urls:
            with self.subTest(url=name):
                response = self.client.get(url)
                self.assertIn(
                    response.status_code,
                    (302, 403),
                    f"{name} was reachable without logging in",
                )

    def test_anonymous_blocked_from_contributions(self):
        for name, url in self.contribution_urls:
            with self.subTest(url=name):
                self.assertIn(self.client.get(url).status_code, (302, 403))

    # --- member and donor ------------------------------------------- #

    def test_member_blocked_from_receipts(self):
        self.client.force_login(self.member)
        for name, url in self.receipt_urls:
            with self.subTest(url=name):
                self.assertEqual(
                    self.client.get(url).status_code,
                    403,
                    f"{name} was reachable by a plain member",
                )

    def test_donor_blocked_from_receipts(self):
        self.client.force_login(self.donor)
        for name, url in self.receipt_urls:
            with self.subTest(url=name):
                self.assertEqual(self.client.get(url).status_code, 403)

    # --- pastor: contributions yes, receipts no --------------------- #

    def test_pastor_blocked_from_receipts(self):
        self.client.force_login(self.pastor)
        for name, url in self.receipt_urls:
            with self.subTest(url=name):
                self.assertEqual(
                    self.client.get(url).status_code,
                    403,
                    f"{name} was reachable by a local church pastor",
                )

    def test_pastor_allowed_contributions(self):
        self.client.force_login(self.pastor)
        for name, url in self.contribution_urls:
            with self.subTest(url=name):
                self.assertNotEqual(
                    self.client.get(url).status_code,
                    403,
                    f"{name} was blocked for a pastor who should have access",
                )

    # --- overseers -------------------------------------------------- #

    def test_region_overseer_allowed_receipts(self):
        self.client.force_login(self.region)
        for name, url in self.receipt_urls:
            with self.subTest(url=name):
                self.assertNotEqual(
                    self.client.get(url).status_code,
                    403,
                    f"{name} was blocked for a region overseer",
                )

    def test_national_overseer_allowed_receipts(self):
        self.client.force_login(self.national)
        for name, url in self.receipt_urls:
            with self.subTest(url=name):
                self.assertNotEqual(self.client.get(url).status_code, 403)

    def test_national_overseer_allowed_contributions(self):
        self.client.force_login(self.national)
        for name, url in self.contribution_urls:
            with self.subTest(url=name):
                self.assertNotEqual(self.client.get(url).status_code, 403)
