# Organization App Documentation

## Table of Contents

1. [General Overview](#general-overview)
2. [Models Overview](#models-overview)
    - [Source Model](#source-model)
    - [Income Model](#income-model)
    - [BankAccount Model](#bankaccount-model)
3. [Views Overview](#views-overview)
    - [Permissions in Views](#permissions-in-views)
    - [View Functions](#view-functions)
4. [URL Routing](#url-routing)

---

## General Overview

The **Organization App** is part of a larger system designed to manage the financial operations of a church or similar
organization. It tracks income, expenses, and generates reports on financial activities related to local churches,
regions, and accounts.

- **Income Management**: Handling various sources of income, including details of each transaction (amount, source,
  account, etc.).
- **Reconciliation**: Reconciliation of financial records to ensure accuracy between reported income and actual
  payments.
- **Reports**: Detailed reporting features to track monthly activities, financial allocations, and other administrative
  needs.
- **Permissions and Roles**: Role-based access control is implemented to ensure that users can only access specific data
  based on their role.

### Reconciliation

In addition to the data and records saved in the app, each local church also maintains its own records or bank
statements. At the end of the day, we need to verify that the data in the app matches the bank statements.

Users can:

1. **Download a sample file**.
2. **Choose their region**.
3. **Compare the app data with the bank statement**.
4. **Provide feedback** on any discrepancies.

---

### Payment Allocation

Each region or local church has its own bank account and collects donations or contributions.  
They are required to allocate these funds as follows:

- **30%** to DCLM.
- **10%** to GCK.

For **GCK Canada**, the allocation percentage is set by the admin, and regions must pay the amount specified.

#### Monthly Payment Process:

1. At the end of every month, regions must log into the app and input the amount they have paid.
2. If the amount paid is **less than the required allocation**, an email will be sent to remind them.
3. If the payment remains incomplete by the end of the next month:
    - Another email is sent.
    - The **General Overseer** is **CC’d** in the follow-up email.
 
---

## Models Overview


### Source Model

Represents a source of income or expense, such as donations or specific types of funds. It is linked to `Income`
and `Expense` models to trace the origin of funds.

**Fields**:

| Field         | Description                                                |
|---------------|------------------------------------------------------------|
| `name`        | Name of the source (e.g., "Tithe", "Donation")             |
| `type`        | Type of the source (Income/Expense). Defaults to "Income". |
| `description` | A description of the source's nature or purpose.           |
| `entry_by`    | ForeignKey to `User` who entered the source.               |

**Meta**:

- `ordering`: Orders `Source` entries by `name` alphabetically.

**Methods**:

- `__str__()`: Returns the name of the source.

---

### Income Model

Represents income transactions, linking them to a local church, bank account, and source. Each income record includes
the amount, date, description, and source of the income.

**Fields**:
| Field | Description |
|----------------|------------------------------------------------------------------|
| `local_church` | ForeignKey to `LocalChurch`, linking income to a specific church|
| `account`      | ForeignKey to `BankAccount`, linking income to an account |
| `amount`       | Decimal amount of income |
| `description`  | Description of the income (e.g., "Tithe for April")              |
| `date`         | Date of the income (defaults to current date)                    |
| `source`       | ForeignKey to `Source`, linking income to its origin |

**Meta**:

- `ordering`: Orders `Income` entries by `date` in descending order.

**Methods**:

- `__str__()`: Returns a string representation of the income with the amount and date.

---

### BankAccount Model

This model manages details about bank accounts used by the church for handling funds. It's linked to both `Income`
and `Expense` models to track transactions associated with specific bank accounts.

---

## Views Overview

The views handle various aspects of the church’s financial system, including income management, reconciliation, and
report generation. They are primarily responsible for rendering pages, handling data via GET and POST requests, and
responding with JSON for dynamic updates.

### Permissions in Views

The application uses role-based access control (RBAC) to restrict access to specific views and functionalities based on
the user's role. Below are the roles and their respective permissions as used in the views:

- **Role 1 (General Users)**: Limited access to view reports and income-related data for a specific church.
- **Role 2 (Church Pastors)**: Can view and manage income data for their local church. Can also manage and view reports
  related to their local church.
- **Role 3 (Region Overseers)**: Have access to all churches within their region. They can manage income and reports for
  churches in their region.
- **Role 4 (Admins/Staff)**: Full access to manage all regions, churches, and financial records across the organization.

Each view checks the user's role and adjusts the data they can access or modify accordingly. For instance:

- Users with the role `Region Overseer` can only view data for their assigned region and its churches.
- Users with the role `Admin` have unrestricted access to all regions and churches.

### View Functions

#### 1. `index(request)`

- Renders the dashboard with a summary of income and expense data, including charts for financial reports.
- **Permissions**: Available to all authenticated users based on their role.
- **Logic**:
    - Users with role `Admin` or `Region Overseer` can see all regions and local churches.
    - Users with role `Church Pastor` can only access their local church's data.

#### 2. `get_local_churches_by_region(request)`

- Returns a list of local churches in a selected region via AJAX.
- **Permissions**: Accessible to all authenticated users with access to the given region.

#### 3. `get_regions_by_local_church(request)`

- Returns the region associated with a selected local church via AJAX.
- **Permissions**: Accessible to all authenticated users with access to the given local church.

#### 4. `report_manage(request)`

- Manages detailed reports for each local church, allowing users to view and edit monthly reports.
- **Permissions**: Only accessible to users with role `Admin`, `Region Overseer`, or `Church Pastor` with access to
  specific local church reports.

#### 5. `reconciliation_n_allocation(request)`

- Displays a page for handling reconciliation and financial allocations for regions.
- **Permissions**: Available to users with roles `Admin`, `Region Overseer`, or other users assigned to manage a
  region’s reconciliation.

#### 6. `download_sample_reconciliation(request)`

- Provides a sample CSV file for reconciliation records.
- **Permissions**: Accessible to users with role `Admin` or `Region Overseer`.

#### 7. `get_payment_allocation(request, id)`

- Returns details about a specific payment allocation via AJAX.
- **Permissions**: Accessible to users with role `Admin` or `Region Overseer`.

---

## URL Routing

The URLs in this Django app map specific routes to views, allowing for proper routing and access control based on user
roles. Below is an overview of the routes and their respective views:

| URL Pattern                     | View Function                    | Description                                                                              |
|---------------------------------|----------------------------------|------------------------------------------------------------------------------------------|
| `/`                             | `index`                          | Renders the dashboard with financial summaries and charts.                               |
| `/ajax/local_churcheses/`       | `get_local_churches_by_region`   | Returns a list of local churches based on the selected region.                           |
| `/ajax/regions/`                | `get_regions_by_local_church`    | Returns a list of regions based on the selected local church.                            |
| `/detail_reports/`              | `report_manage`                  | Manages detailed reports for local churches, with options to view and edit monthly data. |
| `/reconciliation_n_allocation/` | `reconciliation_n_allocation`    | Displays reconciliation and financial allocation information for regions.                |
| `/reconciliation/export/`       | `download_sample_reconciliation` | Allows users to download a sample reconciliation CSV file.                               |
| `/payment_allocation/<int:id>/` | `get_payment_allocation`         | Returns detailed information about a specific payment allocation.                        |

---
