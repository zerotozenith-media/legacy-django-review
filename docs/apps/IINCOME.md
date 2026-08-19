# Income App Documentation

The **Income** app is a financial management tool for local churches, designed to track and manage income records,
including donations, sales, and other sources of revenue. The app allows users to:

- Create, update, delete, and view income transactions.
- Upload income data in bulk using Excel files.
- Manage income sources, which are categorized as either "Income" or "Expense".
- Filter income records by date range, with monthly and yearly income summaries.
- Ensure secure and role-based access to all features with appropriate permissions.

The app ensures that only authorized users can manage or view specific income data, with checks for local church
affiliation and user roles (admin, pastor, overseer, etc.).

---

## Table of Contents

1. [Overview](#overview)
2. [Models](#models)
    - [Source](#source)
    - [Income](#income)
3. [Views](#views)
    - [Function-Based Views](#function-based-views)
    - [Class-Based Views](#class-based-views)
4. [URL Patterns](#url-patterns)

---

## Overview

## Models

### Source

This model tracks the sources of income, including:

- `name`: The name of the income source (e.g., "Donation", "Fundraiser").
- `type`: Indicates whether it's related to income or expense.
- `description`: Additional description of the income source.
- `entry_by`: The user who created the source.

### Income

This model records the financial transactions related to income, including:

- `local_church`: A foreign key to the local church where the income is registered.
- `account`: The bank account associated with the income.
- `amount`: The monetary amount of the income.
- `description`: A detailed description of the income source or event.
- `date`: The date the income was received.
- `source`: A foreign key linking to the `Source` model, describing the source of the income (e.g., "Donation", "
  Sales").

---

## Views

### Function-Based Views

#### `search_income(request)`

- **Purpose**: Allows the user to search for income records based on amount, description, or date.
- **Permissions**:
    - Only authenticated users (`@login_required`) can search for income records.
    - Filters income based on the logged-in user’s local church and its associated records.
- **Details**: Accepts a POST request with the search string (`searchText`) and returns a list of matching income
  records.

#### `index(request)`

- **Purpose**: Displays the list of income records with an optional date range filter.
- **Permissions**:
    - Users must be logged in to view the income records.
    - Income records are filtered based on the local church associated with the user, ensuring users can only see income
      records of their church.
    - Only allows access to records from local churches the user is associated with (using `get_user_local_church()`).
- **Details**:
    - Supports date filters (`start_date` and `end_date`) to narrow the income records.
    - Displays the income records for the current month and year.

#### `add_income(request)`

- **Purpose**: Allows the user to create new income records.
- **Permissions**:
    - Users must be authenticated (`@login_required`).
    - Users can only create income records for local churches they are associated with.
- **Details**:
    - Requires form fields such as `local_church`, `account`, `amount`, `description`, `date`, and `source`.
    - Validates the input and saves the income record if all required fields are provided.

#### `income_edit(request, id)`

- **Purpose**: Allows the user to edit an existing income record.
- **Permissions**:
    - Users must be logged in (`@login_required`).
    - Users can only edit income records that are linked to the local church they manage.
- **Details**:
    - Retrieves the income record by its ID and allows the user to modify the amount, description, date, and source.
    - Validation checks are performed before saving the updated income.

#### `delete_income(request, id)`

- **Purpose**: Deletes an income record.
- **Permissions**:
    - Users must be logged in (`@login_required`).
    - Only users with proper permissions (e.g., church admin or pastor) can delete income records associated with their
      local church.
- **Details**:
    - Deletes the income record identified by its ID and redirects to the income listing page with a success message.

---

### Class-Based Views

#### `SourceListView`

- **Purpose**: Displays a list of income sources.
- **Permissions**:
    - Only authenticated users can view the list of income sources.
- **Details**:
    - Uses Django's `ListView` to display all income sources, with additional context like `Income` and `Expense` types.

#### `SourceView`

- **Purpose**: Handles the creation and retrieval of income sources.
- **Permissions**:
    - Only logged-in users can access this view.
    - Only users with permissions to manage sources (e.g., admin or manager) can create new income sources.
- **Details**:
    - **GET**: Renders a form for creating a new income source.
    - **POST**: Creates a new source when submitted.

#### `SourceEditDeleteView`

- **Purpose**: Allows editing or deleting income sources.
- **Permissions**:
    - Users must be logged in to perform these actions.
    - Users can only modify or delete income sources that they have created.
- **Details**:
    - **GET**: Deletes the source with the given ID.
    - **POST**: Updates the source's name and description.

#### `IncomeUploadView`

- **Purpose**: Handles bulk uploading of income records from an Excel file.
- **Permissions**:
    - Users must be logged in and have the appropriate role to upload income data (admin, pastor, or overseer).
    - Role-based permissions determine which local churches are available for upload.
- **Details**:
    - **GET**: Displays the income uploader form.
    - **POST**: Validates the uploaded Excel file, processes it, and saves the income records.

---

## URL Patterns

| **Path**                          | **View**                                | **Name**                          |
|-----------------------------------|-----------------------------------------|-----------------------------------|
| `/`                               | `views.index`                           | `income`                          |
| `/add-income`                     | `views.add_income`                      | `add-income`                      |
| `/edit-income/<int:id>`           | `views.income_edit`                     | `income-edit`                     |
| `/income-delete/<int:id>`         | `views.delete_income`                   | `income-delete`                   |
| `/search-income`                  | `csrf_exempt(views.search_income)`      | `search_income`                   |
| `/source-list/`                   | `views.SourceListView.as_view()`        | `source-list`                     |
| `/source-income/`                 | `views.SourceView.as_view()`            | `source-income`                   |
| `/source-update-delete/<int:id>/` | `views.SourceEditDeleteView.as_view()`  | `source-income-update-delete`     |
| `/upload/`                        | `views.IncomeUploadView.as_view()`      | `income_uploader`                 |
| `/income-uploader-sample/`        | `views.download_income_uploader_sample` | `download_income_uploader_sample` |
