# Attendance App Documentation

This app is designed to manage and track church attendance data. It includes models for defining church services and
attendance records, views for handling user interactions, and URLs for endpoint definitions.

---

## **Models**

### 1. `ChurchServices`

- Represents a type of church service (e.g., Sunday Service, Midweek Service).
- Fields:
    - `name`: The name of the service (e.g., "Sunday Service").
    - `short_name`: An abbreviated name.
    - `description`: A brief description of the service.
    - `local_church`: Links the service to a specific local church.

### 2. `Attendance`

- Records attendance data for a church service on a specific date.
- Fields:
    - Various fields to record attendees by category (e.g., adults, youths, children).
    - `date`: The date of the service.
    - `comment`: Optional comments about the service.
    - `local_church`: Links attendance to a specific local church.

## **Views**

### 1. `attendance_list(request)`

- Displays a list of attendance records based on the user's role.
- Filters:
    - **Admin/Staff:** All records.
    - **Pastors:** Records for their assigned church.
    - **Regional Overseers:** Records for all churches in their region.
- Annotates attendance records with a `total` field (sum of all attendees).

### 2. `add(request)`

- Handles the creation of a new attendance record.
- Accepts data via POST (e.g., attendee counts, service date, and comments).
- Automatically sets default values for numeric fields if left empty.

### 3. `available_church_services(local_churches)`

- Retrieves a list of church services either global (not tied to a local church) or tied to specific local churches.

## **URLs**

| Path                           | HTTP Method | Description                                   | View Used                             |
|--------------------------------|-------------|-----------------------------------------------|---------------------------------------|
| `/`                            | GET         | Lists all attendance records.                 | `attendance_list`                     |
| `/add/`                        | POST        | Adds a new attendance record.                 | `add`                                 |
| `/<int:pk>/edit/`              | POST        | Edits an existing attendance record.          | `edit_attendance`                     |
| `/<int:pk>/delete/`            | POST        | Deletes an attendance record.                 | `delete_attendance`                   |
| `/church_services/`            | GET         | Lists all available church services.          | `ChurchServiceView`                   |
| `/upload/`                     | POST        | Bulk uploads attendance records via CSV file. | `AttendanceUploadView`                |
| `/attendance-uploader-sample/` | GET         | Provides a sample CSV template for uploads.   | `download_attendance_uploader_sample` |
| `/attendance-uploader/`        | POST        | Upload an attendance.                         | `attendance_uploader`                 |


---
