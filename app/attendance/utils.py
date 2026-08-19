import calendar
from datetime import datetime

from django.utils import timezone

from attendance.models import Day, GCKAttendance
from organization.models import LocalChurch, Region


def get_all_months():
    months = [
        {"value": f"{timezone.now().year}-{i:02d}", "name": calendar.month_name[i]}
        for i in range(1, 13)
    ]
    return months


def prepare_gck_workers_attendance_context_data(region=None, month=None, pastor=None, is_workers=False) -> list:
    data = []

    # Filter regions based on the provided `region` argument
    if region:
        all_regions = Region.objects.filter(name__iexact=region)  # Case-insensitive match
    else:
        all_regions = Region.objects.all().order_by("name")

    # Determine the month to filter
    if month:
        filter_month = datetime.strptime(month, "%Y-%m")
    else:
        now = datetime.now()
        filter_month = datetime(now.year, now.month, 1)  # First day of the current month

    for region in all_regions:
        region_data = {
            "name": region.name,
            "churches": []
        }

        churches = LocalChurch.objects.filter(region=region).order_by("local_church_name__title")
        if pastor:
            churches = churches.filter(local_church_pastor=pastor)

        for church in churches:
            church_data = {
                "name": church.local_church_name.title,
                "days": []
            }
            region_data["churches"].append(church_data)

            # Get the days for each church, filtered by the selected month
            days = Day.objects.filter(
                local_church=church,
                date__year=filter_month.year,
                date__month=filter_month.month,
                is_workers=is_workers
            ).order_by("name")

            for day in days:
                # Get attendance for the day
                attendance = GCKAttendance.objects.filter(day=day, is_workers=is_workers).first()
                if attendance:
                    day_data = {
                        "id": attendance.id,
                        "day": day.name,
                        "date": day.date.strftime('%d-%b-%Y'),  # Format date as '24-Oct-2024'
                        "adult": attendance.adult,
                        "young_prf": attendance.young_prf,
                        "campus": attendance.campus,
                        "youths": attendance.youths,
                        "children": attendance.children,
                        "zoom": attendance.zoom,
                        "youtube": attendance.youtube,
                        "fb_reached": attendance.fb_reached,
                        "fb_likes": attendance.fb_likes,
                        "fb_comments": attendance.fb_comments,
                        "ig_reached": attendance.ig_reached,
                        "ig_engagement": attendance.ig_engagement,
                        "remarks": attendance.remarks,
                        "converts": attendance.converts
                    }
                    church_data["days"].append(day_data)

        data.append(region_data)

    # Calculate totals for each church and region
    for region in data:
        # Initialize region totals
        region_total = {
            'adult': 0,
            'young_prf': 0,
            'campus': 0,
            'youths': 0,
            'children': 0,
            'zoom': 0,
            'youtube': 0,
            'fb_reached': 0,
            'fb_likes': 0,
            'fb_comments': 0,
            'ig_reached': 0,
            'ig_engagement': 0,
            'converts': 0,
        }

        for church in region['churches']:
            # Initialize church totals
            church_total = {
                'adult': 0,
                'young_prf': 0,
                'campus': 0,
                'youths': 0,
                'children': 0,
                'zoom': 0,
                'youtube': 0,
                'fb_reached': 0,
                'fb_likes': 0,
                'fb_comments': 0,
                'ig_reached': 0,
                'ig_engagement': 0,
                'converts': 0,
            }

            for day in church['days']:
                # Add day totals to church totals
                for key in church_total:
                    church_total[key] += day.get(key, 0)

            # Store the computed church total
            church['total'] = church_total

            # Add church totals to region totals
            for key in region_total:
                region_total[key] += church_total[key]

        # Store the computed region total
        region['total'] = region_total

    return data


def prepare_gck_attendance_context_data(region=None, event=None, pastor=None, is_workers=False) -> list:
    data = []

    if not event:
        return data  # If no event is passed, return empty list immediately

    # Preload all attendances for this event
    attendances = GCKAttendance.objects.filter(gck_event=event,
                                               is_workers=is_workers).select_related('day', 'day__local_church')

    if region:
        all_regions = Region.objects.filter(name__iexact=region)
    else:
        all_regions = Region.objects.all().order_by("name")

    # Group attendances by local church
    attendance_map = {}
    for attendance in attendances:
        church_id = attendance.day.local_church.id
        if church_id not in attendance_map:
            attendance_map[church_id] = []
        attendance_map[church_id].append(attendance)

    for region in all_regions:
        region_data = {
            "name": region.name,
            "churches": []
        }

        churches = LocalChurch.objects.filter(region=region).order_by("local_church_name__title")
        if pastor:
            churches = churches.filter(local_church_pastor=pastor)

        for church in churches:
            church_data = {
                "name": church.local_church_name.title,
                "days": []
            }
            region_data["churches"].append(church_data)

            # Get attendances for this church
            church_attendances = attendance_map.get(church.id, [])

            for attendance in church_attendances:
                day = attendance.day
                day_data = {
                    "id": attendance.id,
                    "day": day.name,
                    "date": day.date.strftime('%d-%b-%Y'),
                    "adult": attendance.adult,
                    "young_prf": attendance.young_prf,
                    "campus": attendance.campus,
                    "youths": attendance.youths,
                    "children": attendance.children,
                    "zoom": attendance.zoom,
                    "youtube": attendance.youtube,
                    "fb_reached": attendance.fb_reached,
                    "fb_likes": attendance.fb_likes,
                    "fb_comments": attendance.fb_comments,
                    "ig_reached": attendance.ig_reached,
                    "ig_engagement": attendance.ig_engagement,
                    "remarks": attendance.remarks,
                    "converts": attendance.converts,
                }
                church_data["days"].append(day_data)

        data.append(region_data)

    # Calculate totals
    for region in data:
        region_total = {key: 0 for key in [
            'adult', 'young_prf', 'campus', 'youths', 'children', 'zoom', 'youtube',
            'fb_reached', 'fb_likes', 'fb_comments', 'ig_reached', 'ig_engagement', 'converts'
        ]}

        for church in region['churches']:
            church_total = {key: 0 for key in region_total}

            for day in church['days']:
                for key in church_total:
                    church_total[key] += day.get(key, 0)

            church['total'] = church_total

            for key in region_total:
                region_total[key] += church_total[key]

        region['total'] = region_total

    return data
