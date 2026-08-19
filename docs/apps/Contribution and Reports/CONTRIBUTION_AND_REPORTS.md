# Contributor and Report App Documentation

---

## Table of Contents

1. [General Overview](#general-overview)

2. [Purpose](#purpose)

3. [Models](#models)

4. [Views and Permissions](#views-and-permissions)

5. [URLs](#urls)

---

## General Overview
This application provides tools to manage contributions and reports for local churches. It supports managing financial
contributions, generating receipts, preparing reports, and facilitating user interactions for tracking and processing
donations. The system is designed for transparency, ease of use, and accuracy.

---

## Purpose

- **Manage Contributions**: Tracks various types of contributions, including offerings (USD/CAD), interac transfers, and
  miscellaneous contributions.

- **Generate Reports**: Provides summary and detailed reports for contributors, categorized by local churches or time
  frames.

- **Facilitate User Interactions**: Ensures administrators and contributors can efficiently manage their transactions.

- **Email Notifications**: Automates the generation and delivery of receipts and summary reports via email.

---

## Models

### **TransactionType Enum**

Defines the types of transactions allowed within the system.

| Value                | Description                        |
|----------------------|------------------------------------|
| `offerings_can`      | Contributions in Canadian dollars. |
| `offerings_usd`      | Contributions in US dollars.       |
| `interec_e_transfer` | Interac e-transfers.               |
| `direct_transfer`    | Direct bank transfers.             |
| `cheque_deposit`     | Cheque deposits.                   |

---

### **Contribution**

Tracks contributions made by registered users.

| Field                  | Type         | Description                                |
|------------------------|--------------|--------------------------------------------|
| `contributor`          | ForeignKey   | Links to the user making the contribution. |
| `amount`               | DecimalField | Amount contributed.                        |
| `deposited_date`       | DateField    | Date the contribution was made.            |
| `payment_type`         | CharField    | Type of contribution.                      |
| `special_contribution` | BooleanField | Indicates if it's a special contribution.  |
| `month`                | CharField    | Month of the contribution.                 |
| `local_church`         | ForeignKey   | Links to the church receiving the funds.   |

---

### **TaxReceipt**

Stores tax receipts issued to contributors.

| Field              | Type       | Description                    |
|--------------------|------------|--------------------------------|
| `receipt_receiver` | ForeignKey | User receiving the receipt.    |
| `pdf_file`         | FileField  | File path for the receipt PDF. |

---

### **MiscellaneousUser**

Track details of unregistered contributors (e.g., guests).

| Field                      | Type       | Description                            |
|----------------------------|------------|----------------------------------------|
| `full_name`                | CharField  | Full name of the contributor.          |
| `first_name`               | CharField  | First name of the contributor.         |
| `middle_name`              | CharField  | Middle name of the contributor.        |
| `last_name`                | CharField  | Last name of the contributor.          |
| `email`                    | EmailField | Email address of the contributor.      |
| `address`                  | CharField  | Address of the contributor.            |
| `registered_miscellaneous` | ForeignKey | Links to the registered user (if any). |

---

### **MiscellaneousContribution**

Handles contributions from unregistered users.

| Field                  | Type         | Description                               |
|------------------------|--------------|-------------------------------------------|
| `contributor`          | ForeignKey   | Links to the miscellaneous user.          |
| `deposited_date`       | DateField    | Date the contribution was made.           |
| `amount`               | DecimalField | Amount contributed.                       |
| `payment_type`         | CharField    | Type of contribution.                     |
| `special_contribution` | BooleanField | Indicates if it's a special contribution. |
| `month`                | CharField    | Month of the contribution.                |
| `local_church`         | ForeignKey   | Links to the church receiving the funds.  |

---

### **AnonymousContribution**

Tracks anonymous contributions made without identifying the contributor.

| Field                  | Type         | Description                               |
|------------------------|--------------|-------------------------------------------|
| `deposited_date`       | DateField    | Date the contribution was made.           |
| `amount`               | DecimalField | Amount contributed.                       |
| `payment_type`         | CharField    | Type of contribution.                     |
| `special_contribution` | BooleanField | Indicates if it's a special contribution. |
| `month`                | CharField    | Month of the contribution.                |
| `local_church`         | ForeignKey   | Links to the church receiving the funds.  |

---

### **EmailQueue**

Handles email-related tasks for contributors.

| Field            | Type          | Description                                |
|------------------|---------------|--------------------------------------------|
| `contributor_id` | IntegerField  | ID of the contributor receiving the email. |
| `report_year`    | IntegerField  | Year of the report being sent.             |
| `email`          | EmailField    | Email address of the recipient.            |
| `report_type`    | CharField     | Type of report being emailed.              |
| `created_at`     | DateTimeField | Date and time the email was queued.        |

---

## Relationships

1. **Contribution** and **User**:
    - Each contribution links to a registered user if applicable.

2. **MiscellaneousContribution** and **MiscellaneousUser**:
    - Contributions from unregistered users link to their corresponding details.

3. **AnonymousContribution**:
    - Tracks contributions without user information.

4. **LocalChurch**:
    - Each contribution is linked to a specific local church.

5. **TaxReceipt**:
    - Link receipts to registered users.

---

## Views and Permissions

### 1. **CashDonationView**

- **Purpose**: Handles cash donations for local churches.

- **Permissions**: Available to authenticated users linked to a local church.

- **Endpoints**: `/cash-donation/`, `/cash-donation-list/`.

### 2. **OfferingsUSDView**

- **Purpose**: Handles offerings in USD.

- **Permissions**: Requires authenticated users with permissions to access contributions.

- **Endpoints**: `/offerings_usd_add/`, `/offerings_usd_list/`.

### 3. **InteracAddView**

- **Purpose**: Adds interac transfer contributions.

- **Permissions**: Authenticated users with valid local church affiliations.

- **Endpoint**: `/add_interac/`.

### 4. **Receipts and Report Views**

- **Purpose**: Generate and manage various reports and receipts.

- **Key Views**: `send_offerings_receipt`, `send_interac_summary_receipt`, `download_offerings_receipts`.

---

## URLs

| **Endpoint**                                  | **HTTP Method** | **Description**                                                      | **View Used**                        |
|-----------------------------------------------|-----------------|----------------------------------------------------------------------|--------------------------------------|
| `/cash-donation/`                             | GET, POST       | Handles adding cash donations.                                       | `CashDonationView`                   |
| `/cash-donation-list/`                        | GET             | Displays a list of cash donations.                                   | `cash_donation_list`                 |
| `/interac-uploader/`                          | POST            | Allows the upload of Interac contribution files.                     | `upload_file`                        |
| `/bank-statement-importer/`                   | POST            | Handles the import of bank statements.                               | `bank_statement_importer`            |
| `/download-interac-sample/<str:type>/`        | GET             | Downloads a sample Interac contribution file for the specified type. | `download_sample`                    |
| `/donation-list/`                             | GET             | Displays a list of Interac contributions.                            | `interac_transfer_list`              |
| `/offerings_usd_add/`                         | GET, POST       | Adds new USD offerings.                                              | `OfferingsUSDView`                   |
| `/offerings_usd_list/`                        | GET             | Displays a list of USD offerings.                                    | `offerings_usd_list`                 |
| `/receipts/`                                  | GET             | Displays the receipts generation page.                               | `receipts_index`                     |
| `/offering_can_summary/`                      | GET             | Displays a summary report of CAN offerings.                          | `offering_can_summary_report`        |
| `/send_offerings_can_summary/<str:c_id>/`     | POST            | Sends the CAN offerings summary receipt.                             | `send_offerings_receipt`             |
| `/download_offerings_can_summary/<str:c_id>/` | GET             | Downloads the CAN offerings summary receipt.                         | `download_offerings_receipts`        |
| `/send_interac_summary/<str:c_id>/`           | POST            | Sends the Interac contribution summary receipt.                      | `send_interac_summary_receipt`       |
| `/offerings_can_letter/`                      | GET             | Displays a letter report for CAN offerings.                          | `offerings_can_letter_report`        |
| `/interac_summary/`                           | GET             | Displays a summary report for Interac contributions.                 | `interac_summary_report`             |
| `/interac_letter/`                            | GET             | Displays a letter report for Interac contributions.                  | `interac_letter_report`              |
| `/offerings-uploader/<str:type>/`             | POST            | Handles the upload of offering files for the specified type.         | `offerings_uploader_view`            |
| `/preview_offerings_can_summary/<str:c_id>/`  | GET             | Previews the CAN offerings summary report.                           | `preview_offerings_summary_report`   |
| `/preview_interac_summary/<str:c_id>/`        | GET             | Previews the Interac contribution summary report.                    | `preview_interac_summary_report`     |
| `/preview_offerings_can_letter/<str:c_id>/`   | GET             | Previews the CAN offerings letter report.                            | `preview_offerings_letter_report`    |
| `/preview_interac_letter/<str:c_id>/`         | GET             | Previews the Interac letter report.                                  | `preview_interac_letter_report`      |
| `/send_offerings_can_letter/<str:c_id>/`      | POST            | Sends the CAN offerings letter receipt.                              | `send_offerings_letter_receipt`      |
| `/send_interac_letter/<str:c_id>/`            | POST            | Sends the Interac letter receipt.                                    | `send_interac_letter_receipt`        |
| `/add_interac/`                               | GET, POST       | Handles adding new Interac contributions.                            | `InteracAddView`                     |
| `/download_offerings_can_letter/<str:c_id>/`  | GET             | Downloads the CAN offerings letter receipt.                          | `download_offerings_letter_receipts` |
| `/download_interac_summary/<str:c_id>/`       | GET             | Downloads the Interac contribution summary receipt.                  | `download_interac_summary_receipts`  |
| `/download_interac_letter/<str:c_id>/`        | GET             | Downloads the Interac letter receipt.                                | `download_interac_letter_receipts`   |
| `/search-donor-names/`                        | GET             | Searches for donor names.                                            | `search_donor_names`                 |



