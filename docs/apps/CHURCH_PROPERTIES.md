# Church Properties App Documentation

This document explains the key concepts, models, views,
and URLs in the Church Properties application, which handles the management of
the properties associated with local churches.

---

## Table of Contents

1. [Models](#models)
2. [Views](#views)
3. [URLs](#urls)
4. [Permissions](#permissions)
5. [Error Handling & Validation](#error-handling--validation)

---

## Models

### `ChurchProperties`

This model represents a property associated with a local church (e.g., buildings, equipment). It includes various fields
like:

- **`local_church`**: A foreign key that links the property to a specific local church.
- **`name`**: The name of the property.
- **`purchase_date`**: The date the property was purchased.
- **`description`**: A text field for describing the property.
- **`serial_no`**: A unique serial number for the property.
- **`amount_paid`**: The amount paid for the property.
- **`disposal_date`**: The date the property was disposed of (optional).
- **`mode_of_disposal`**: The method used to dispose of the property (optional).
- **`amount_sold`**: The amount the property was sold for, if applicable (optional).

The `__str__` method returns the name of the property for easy identification.

---

## Views

### `PropertyAddView`

Handles adding a new property.

- **GET method**: Renders a form to add a new property, filtering available local churches based on the user's role (
  staff, pastor, or overseer).
- **POST method**: Validates the data submitted in the form and saves the new property to the database. It ensures
  required fields are filled, handles potential errors (e.g., duplicate serial numbers), and commits the data to the
  database within a transaction.

### `PropertiesListView`

Displays a list of properties associated with the local churches the current user has access to.

- **GET method**: Filters properties based on the local churches accessible by the current user (
  using `get_user_local_church`).
- **`ListView`**: This class-based view is used to list properties, ordered by their ID.

### `PropertyUploadView`

Handles bulk upload of property data via Excel files.

- **GET method**: Displays a form to upload an Excel file.
- **POST method**: Validates the uploaded file, ensuring the data is correctly formatted (e.g., proper dates and
  amounts). After validation, the properties are saved to the database. Errors are displayed if there are issues with
  the file format or data.

### `download_property_uploader_sample`

Generates and provides a downloadable Excel file with a sample property dataset. This helps users understand the
expected format for bulk uploads.

---

## Permissions

Permissions are applied based on the user's role. The app uses role-based filtering to determine which local churches a
user can access. The roles include:

- `Staff (role == 3):` Has access to all local churches.
- `Pastor (role == 2):` Has access to local churches they are assigned to.
- `Overseer (role == 4):` Has access to local churches under their region.
- In PropertyAddView and PropertyUploadView, the views are filtered according to the user's role, ensuring that users only
- see and manage the properties relevant to their assigned churches.

---

## URLs

### URL Configuration

The URLs are mapped to the views using Django's `path` function. Here are the main URLs:

- **`/`**: Renders the list of properties using `PropertiesListView`.
- **`/add/`**: Displays the form for adding a new property using `PropertyAddView`.
- **`/upload/`**: Displays the bulk upload form using `PropertyUploadView`.
- **`/property-uploader-sample/`**: Provides a downloadable sample file for uploading properties.

Example URL configuration:

```python
urlpatterns = [
    path("", PropertiesListView.as_view(), name="church_properties_list"),
    path("add/", PropertyAddView.as_view(), name="add-property"),
    path("upload/", PropertyUploadView.as_view(), name="property_uploader"),
    path('property-uploader-sample/', download_property_uploader_sample, name='download_property_uploader_sample'),
]

