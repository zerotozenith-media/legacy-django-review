from datetime import date

from django.test import TestCase, Client

from attendance.models import Day, GCKAttendance
from attendance.utils import prepare_gck_attendance_context_data, get_gck_converts_data
from organization.models import LocalChurchName, Region, LocalChurch
from utils.test_db import Testdb


class AttendanceTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.testdb = Testdb()
        self.user = self.testdb.create_user(role=3)  # National Overseer
        self.client.force_login(self.user)

        region_bc = self.testdb.create_region(name="British Columbia")
        region_ab = self.testdb.create_region(name="Alberta")

        # Create churches
        l1 = LocalChurchName.objects.create(title="Ajax")
        l2 = LocalChurchName.objects.create(title="Burn")
        l3 = LocalChurchName.objects.create(title="Sydney")

        church_ajax = self.testdb.create_local_church(local_church_name=l1, region=region_bc)
        church_burn = self.testdb.create_local_church(local_church_name=l2, region=region_bc)
        church_sydney = self.testdb.create_local_church(local_church_name=l3, region=region_ab)

        # Create days for each church
        day_1 = Day.objects.create(name="DAY 1", date=date(2025, 1, 24), converts=20, local_church=church_ajax)
        day_2 = Day.objects.create(name="DAY 2", date=date(2025, 1, 25), converts=32, local_church=church_ajax)
        Day.objects.create(name="DAY 3", date=date(2025, 1, 25), converts=32, local_church=church_ajax)
        Day.objects.create(name="DAY 4 (Morning)", date=date(2025, 1, 25), converts=32, local_church=church_ajax)
        Day.objects.create(name="DAY 4 (Evening)", date=date(2025, 1, 25), converts=32, local_church=church_ajax)
        Day.objects.create(name="DAY 5", date=date(2025, 1, 25), converts=32, local_church=church_ajax)
        Day.objects.create(name="DAY 6", date=date(2025, 1, 25), converts=32, local_church=church_ajax)

        day_1 = Day.objects.create(name="DAY 1", date=date(2025, 1, 24), converts=290, local_church=church_burn)
        day_2 = Day.objects.create(name="DAY 2", date=date(2025, 1, 25), converts=372, local_church=church_burn)

        # Create GCKAttendance records
        GCKAttendance.objects.create(
            day=day_1, adult=50, young_prf=30, campus=20, youths=40, children=25, zoom=10, youtube=4,
            fb_reached=0, fb_likes=0, fb_comments=0, ig_reached=0, ig_engagement=0, remarks="No Remarks"
        )
        GCKAttendance.objects.create(
            day=day_2, adult=60, young_prf=35, campus=25, youths=50, children=30, zoom=20, youtube=4,
            fb_reached=0, fb_likes=0, fb_comments=0, ig_reached=0, ig_engagement=0, remarks="Good Attendance"
        )

    def test_gck_list_func(self):
        data = prepare_gck_attendance_context_data()
        self.assertEqual(len(data), 2)

    def test_gck_convert_data(self):
        data = get_gck_converts_data()
        self.assertEqual(len(data), 2, data)

