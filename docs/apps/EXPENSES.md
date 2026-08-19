# Expenses App Documentation

## Table of Contents

1. [Overview](#overview)
2. [Models](#models)
    - [Category](#1-category)
    - [SubCategory](#2-subcategory)
    - [Expense](#3-expense)
3. [URL Patterns](#url-patterns)
4. [Views](#views)
    - [index](#index)
    - [add_expense](#add_expense)
    - [search_expenses](#search_expenses)
    - [ExpenseUploadView](#expenseuploadview)
    - [download_expense_uploader_sample](#download_expense_uploader_sample)
5. [Permissions](#permissions)
6. [Key Features](#key-features)
7. [Example Workflow](#example-workflow)
8. [Notes for Developers](#notes-for-developers)

---

## Overview

The **Expenses** app provides functionalities for managing church-related expenses. It allows categorization, record
tracking, uploading expenses, and generating sample files for uploads.

---

## Models

### 1. **Category**

- Represents an overarching classification of expenses.
- **Fields**:
    - `name` (CharField): The category name.
    - `category_type` (PositiveSmallIntegerField): Either **Recurrent** (1) or **Capital** (2).
- **Meta**:
    - `verbose_name_plural`: "Categories".
- **Example**: "Travel and Vehicle Expenses".

### 2. **SubCategory**

- Represents a more specific category under a parent category.
- **Fields**:
    - `name` (CharField): Subcategory name.
    - `parent` (ForeignKey): Reference to a `Category`.
- **Meta**:
    - `verbose_name_plural`: "Sub Categories".

### 3. **Expense**

- Represents an expense record.
- **Fields**:
    - `local_church` (ForeignKey): The church related to the expense.
    - `amount` (DecimalField): Total expense amount.
    - `tax_amount` (DecimalField): Tax paid.
    - `description` (TextField): Detailed description.
    - `date` (DateField): Expense date.
    - `category` (ForeignKey): Reference to `Category`.
    - `sub_category` (ForeignKey): Reference to `SubCategory`.
    - `tax_category` (CharField): Tax type (e.g., HST, GST).

---

## URL Patterns

| **URL**                     | **View**                           | **HTTP Method** | **Description**                                |
|-----------------------------|------------------------------------|-----------------|------------------------------------------------|
| `/`                         | `index`                            | GET             | List and filter expenses.                      |
| `/add-expense`              | `add_expense`                      | GET, POST       | Create a new expense.                          |
| `/edit-expense/<int:id>`    | `expense_edit`                     | GET, POST       | Edit an existing expense.                      |
| `/expense-delete/<int:id>`  | `delete_expense`                   | POST            | Delete an expense.                             |
| `/search-expenses`          | `search_expenses`                  | POST            | Search for expenses by various fields.         |
| `/get-subcategories`        | `get_subcategories`                | GET             | Fetch subcategories for a given category.      |
| `/upload/`                  | `ExpenseUploadView`                | GET, POST       | Upload a file to batch-create expenses.        |
| `/expense-uploader-sample/` | `download_expense_uploader_sample` | GET             | Download a sample file for uploading expenses. |

---

## Views

### `index`

- **Permission**: User must be authenticated.
- **Description**: Displays a filtered list of expenses.
- **Filters**:
    - `start_date` and `end_date` for a date range.
    - `category` for filtering by category.

---

### `add_expense`

- **Permission**: User must be authenticated.
- **Description**: Handles the creation of new expenses.
- **Validation**:
    - Checks for required fields: `amount`, `local_church`, `description`, etc.

---

### `search_expenses`

- **Permission**: User must be authenticated.
- **Description**: Searches expenses based on:
    - Amount
    - Date
    - Description
    - Category
- **Response**: Returns a JSON response of matching expenses.

---

### `ExpenseUploadView`

- **Permission**:
    - User must be authenticated.
    - User must have access to upload expenses (role-specific validation).
- **Description**:
    - Handles uploading expenses in bulk via an Excel file.
    - Validates the uploaded file for:
        - Correct headers.
        - Required fields (`amount`, `date`, `category`).
        - Valid formats for dates and amounts.
    - Saves expenses if the file passes validation.

---

### `download_expense_uploader_sample`

- **Permission**: User must be authenticated.
- **Description**: Generates a downloadable Excel file as a sample format for bulk expense uploads.

---

## Permissions

The views rely on the following permissions:

- **Authentication Required**: Most views require the user to be logged in.
    - This is enforced using `@login_required`.
- **Role-Based Access**:
    - Specific views like `ExpenseUploadView` check the user's role to determine which local churches they can upload
      expenses for:
        - **Staff/Role 3**: Can upload for all local churches.
        - **Role 2 (Pastor)**: Restricted to their assigned local church.
        - **Role 4 (Region Overseer)**: Restricted to churches in their region.

---

## Key Features

- **Categories/Subcategories**: Provides hierarchical classification for expenses.
- **Expense Tracking**: Records essential details such as tax amount, local church, and category.
- **Search**: Easily search through expense records with filters.
- **File Upload**: Streamlines the process of adding multiple records.
- **Sample File Download**: Guides users on the correct upload format.

---

## Example Workflow

1. **Add a New Expense**:
    - Navigate to `/add-expense`.
    - Fill in the required fields: amount, local church, date, and description.
    - Save the record.

2. **Search for Expenses**:
    - Use the search bar or filters (date range, category) in `/`.

3. **Upload Expenses in Bulk**:
    - Download the sample file from `/expense-uploader-sample/`.
    - Populate the file with records and upload it via `/upload/`.

---

## Notes for Developers

- **Validation**:
    - Ensure fields like `amount`, `date`, and `category` are always present.
    - Tax-related data should align with the predefined `TAX_CATEGORY_CHOICES`.
- **Performance**:
    - Use `Paginator` for managing large datasets in views like `index`.
- **Error Handling**:
    - Carefully handle exceptions in file processing (e.g., date or amount formatting errors).

---
