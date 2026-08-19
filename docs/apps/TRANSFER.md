# Transfer App Documentation

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Models](#models)
    - [Transfer](#transfer)
- [Views](#views)
- [Permissions](#permissions)
    - [User Roles](#user-roles)
    - [Decorators](#decorators)
- [URLs](#urls)
    - [urlpatterns](#urlpatterns)

---

## Overview
Transfer app

## Features

- **Create, Edit, and Delete Transfers**: Users can add new transfers, edit existing transfers, and delete them as
  needed.
- **Bulk Upload**: Admins can upload multiple transfers at once using a predefined Excel template.
- **Search and Filter**: Users can search transfers by region, date, and other criteria.
- **Sample File Generation**: A sample file for bulk upload can be downloaded for user convenience.
- **Role-Based Access Control**: Different roles, such as admin and region overseer, are given specific access to
  regions and transfer data.

---

## Models

### `Transfer`

The `Transfer` model represents a financial transfer made between different regions and accounts. It contains the
following fields:

- **`region`** (ForeignKey to `Region`): The region where the transfer occurred. It is linked to the `Region` model and
  determines the location of the transfer.
- **`account`** (ForeignKey to `BankAccount`): The bank account involved in the transfer.
- **`amount`** (DecimalField): The amount of money being transferred.
- **`type`** (CharField): A brief description of the type of transfer (e.g., "Received", "Sent").
- **`description`** (TextField): A detailed description of the transfer.
- **`date`** (DateField): The date the transfer occurred, with a default value of the current date.

**Meta**:

- **Ordering**: Transfers are ordered by date in descending order.

---

## Views

### `index(request)`

The `index` view renders the main page of the transfer section. It allows users to view all transfers for a given date
range, with options to filter transfers by region and date. The view also calculates transfers for the current month and
year.

### `add_transfer(request)`

This view allows users to create new transfer records. Users are presented with a form to input transfer details (
region, account, amount, description, type, and date). If any required fields are missing, error messages are shown.

### `transfer_edit(request, id)`

The `transfer_edit` view allows users to edit an existing transfer. Users can modify the transfer’s description, date,
and amount. It performs validation to ensure that required fields are filled before saving the changes.

### `delete_transfer(request, id)`

This view handles the deletion of a transfer record. Once a transfer is deleted, a success message is shown, and the
user is redirected to the transfer list.

### `TransferUploaderHelper` and `TransferUploadView`

The `TransferUploaderHelper` class provides utility functions to validate and process an uploaded Excel file containing
multiple transfer records. It validates the file headers and processes each row to create new `Transfer` objects in the
database.

The `TransferUploadView` is a class-based view that handles the file upload. The view validates the file, processes it
if valid, and saves the transfer records. It also provides feedback on any errors encountered during the upload process.

### `download_transfer_uploader_sample(request)`

This view generates an Excel file with sample data for users to download. The file includes headers and example transfer
data, serving as a template for bulk uploads.

---

## Permissions

The application utilizes role-based access control to manage permissions for different users:

### User Roles

- **Admin (`is_staff`)**: Can view, edit, and delete all transfers. They have access to all regions and accounts.
- **Region Overseer (`role == 3`)**: Can view, add, and edit transfers related to the specific regions they oversee.
  They do not have access to transfers in other regions.
- **Regular Users**: May only have read access to transfers related to their specific regions.

### Decorators

- **`@login_required`**: Ensures that a user must be logged in to access the views. If not logged in, they will be
  redirected to the login page.
- **`csrf_exempt`**: Disables CSRF protection for certain views, like `search_transfer`, when handling external requests
  or APIs that do not require CSRF tokens.

---

## URLs

The following URL patterns are defined in the application, each corresponding to a specific view:

### `urlpatterns`

| URL Pattern                 | View Function                                | Description                                                                    |
|-----------------------------|----------------------------------------------|--------------------------------------------------------------------------------|
| `""`                        | `index(request)`                             | The main transfer page that lists and filters transfers.                       |
| `add-transfer`              | `add_transfer(request)`                      | The page for adding a new transfer.                                            |
| `edit-transfer/<int:id>`    | `transfer_edit(request, id)`                 | The page for editing a specific transfer identified by its `id`.               |
| `transfer-delete/<int:id>`  | `delete_transfer(request, id)`               | The URL for deleting a specific transfer identified by its `id`.               |
| `search-transfer`           | `search_transfer(request)`                   | A search endpoint that allows users to search for transfers based on criteria. |
| `upload/`                   | `TransferUploadView.as_view()`               | The page where users can upload bulk transfers through an Excel file.          |
| `transfer-uploader-sample/` | `download_transfer_uploader_sample(request)` | A URL to download a sample Excel file for bulk transfer upload.                |


---

