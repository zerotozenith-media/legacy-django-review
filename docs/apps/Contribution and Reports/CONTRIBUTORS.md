# Contributor App Documentation

---

[Contributors Type](#contributors-type)<br>
[1. Cash Donation](#1-cash-donation)<br>
[2. Offerings USD](#2-offerings-usd)<br>
[3. Cash Donation List](#3-cash-donation-list)<br>
[4. Offerings USD List](#4-offerings-usd-list)<br>
[5. Download Sample](#5-download-sample)<br>
[6. Upload File](#6-upload-file)<br>
[7. Interac Transfer List](#7-interac-transfer-list)<br>
[8. Add Interac](#8-add-interac)<br>
[8. Bank Statement Importer](#9-bank-statement-importer)<br>

## Contributors Type

The **CashDonationView** in the church app handles three distinct types of contributors or donors. These types ensure
flexibility in accommodating various donation preferences and scenarios. Below is an explanation of each type:

---

## 1. Miscellaneous Donors

### Concept:

- Miscellaneous donors are contributors who are not regular members or registered users of the church system.
- Their donations are categorized as miscellaneous. Useful for one-off donations from visitors, guests, or
  individuals who are not registered in the system.

### How It Works:

- When the **toggle switch** (`toggleSwitch`) is turned on, the system treats the donor as a miscellaneous contributor.
- Details like the donor's name, local church, date, amount, and whether the contribution is special are provided in the
  form.
- A record is created using the `add_contribution` function.

## 2. Anonymous Donors

### Concept:

- Anonymous donors are contributors who prefer to remain unidentified.
- Their contributions are tracked without personal details to maintain their anonymity.
- Allows individuals to donate without revealing their identities.

### How It Works:

- When the **anonymous donor checkbox** (`anonymous_donor`) is selected in the form, the system flags the contribution
  as anonymous.
- Contributions are added to the **`AnonymousContribution`** model.
- Data recorded includes:
    - Local church ID
    - Deposit date
    - Payment type
    - Amount
    - Special contribution status
    - Month of the contribution

---

## 3. Registered Contributors

### Concept:

- Registered contributors are regular church members or users who make donations.
- Their contributions are logged under their user accounts for tracking and transparency.
- Facilitates tracking donations made by registered members, enabling personalized reports, acknowledgments, or tax
  receipts.

### How It Works:

- The `donor` field in the form payload contains the **user ID** of the registered contributor.
- The system fetches the contributor's details from the `User` model using the provided ID.
- A record is created using the `add_contribution` function with the contributor's name and donation details.

---

## Summary of Contributor Types

| **Contributor Type** | **Key Differentiator**                                              | **Handling in the App**                                   |
|----------------------|---------------------------------------------------------------------|-----------------------------------------------------------|
| **Miscellaneous**    | Unregistered contributors providing their name and details.         | Handled with `toggleSwitch`. Adds via `add_contribution`. |
| **Anonymous**        | Donors who prefer to remain unidentified.                           | Logged in `AnonymousContribution`.                        |
| **Registered**       | Church members or registered users tracked via their user accounts. | User fetched by `donor ID` and logged in contributions.   |

---

## Endpoints

### 1. **Cash Donation**

`/cash-donation`

**HTTP Method:** GET, POST  
**Description:**  
Handles the addition of cash donations for the church. Includes options for handling
miscellaneous contributors, anonymous donors, or registered contributors.  
**View Used:** `CashDonationView`

#### POST Method

**Request Payload:**

| Field               | Type    | Description                               | Required |
|---------------------|---------|-------------------------------------------|----------|
| local_church        | String  | The ID of the local church.               | Yes      |
| toggleSwitch        | Boolean | Specifies if it's a miscellaneous donor.  | Optional |
| donor               | Integer | ID of the donor (if registered).          | Optional |
| miscellaneous       | String  | Name of the miscellaneous donor.          | Optional |
| donation_date       | String  | Date of the donation (YYYY-MM-DD).        | Yes      |
| amount              | Decimal | Amount of the donation.                   | Yes      |
| specialToggleSwitch | Boolean | Indicates if it's a special contribution. | Optional |
| anonymous_donor     | Boolean | Marks the contribution as anonymous.      | Optional |

**Returns:**

- **Success:** Redirects to the `cash-donation-list` page with a success message: `Donation successfully added!`.
- **Error:** Redirects to the `cash-donation` page with an error message: `Something went wrong`.

---

### 2. **Offerings USD:**

`/offerings-usd`

**HTTP Method:** GET, POST  
**Description:**  
Handles contributions made in USD currency for the church. This includes handling miscellaneous, anonymous, and
registered donor contributions.  
**View Used:** `OfferingsUSDView`

#### POST Method

**Request Payload:**

| Field               | Type    | Description                               | Required |
|---------------------|---------|-------------------------------------------|----------|
| local_church        | String  | The ID of the local church.               | Yes      |
| toggleSwitch        | Boolean | Specifies if it's a miscellaneous donor.  | Optional |
| donor               | Integer | ID of the donor (if registered).          | Optional |
| miscellaneous       | String  | Name of the miscellaneous donor.          | Optional |
| donation_date       | String  | Date of the donation (YYYY-MM-DD).        | Yes      |
| amount              | Decimal | Amount of the donation.                   | Yes      |
| specialToggleSwitch | Boolean | Indicates if it's a special contribution. | Optional |
| anonymous_donor     | Boolean | Marks the contribution as anonymous.      | Optional |

**Returns:**

- **Success:** Redirects to the `offerings_usd_list` page with a success message: `Donation successfully added!`.
- **Error:** Redirects to the `offerings_usd_add` page with an error message: `Something went wrong`.

---

### 3. **Cash Donation List**

`/cash-donation-list`

- Displays a categorized list of cash donations received by the logged-in user’s local churches.
- Organizes contributions by their source, enabling clear reporting and tracking.

### **Donation Categories**

1. **Registered Donors (`Contribution`)**:
    - Represents offerings made by registered users.
    - Fetched using the `Contribution` model, filtered by:
        - `payment_type`: Matches the `TransactionType.OFFERINGS_CAN` enumeration, representing Canadian dollar
          offerings.
        - `local_church`: Restricts to churches associated with the logged-in user.

2. **Miscellaneous Donors (`MiscellaneousContribution`)**:
    - Contributions from one-time or irregular donors who are not system-registered users.
    - Fetched using the `MiscellaneousContribution` model, joined with the `Contributor` model for additional details.
    - Filtered by:
        - `payment_type`: Matches `TransactionType.OFFERINGS_CAN`.
        - `local_church`: Limits to the logged-in user’s churches.

3. **Anonymous Donors (`AnonymousContribution`)**:
    - Contributions made without identifying the donor.
    - Fetched using the `AnonymousContribution` model, with the following filters:
        - `payment_type`: Matches `TransactionType.OFFERINGS_CAN`.
        - `deleted`: Excludes soft-deleted records.
        - `local_church`: Limits to the user’s churches.

---

### **Context Data Passed**

| Key             | Description                                                                                  |
|-----------------|----------------------------------------------------------------------------------------------|
| `contribution`  | List of donations from registered contributors filtered by the user’s local churches.        |
| `miscellaneous` | List of miscellaneous contributions linked to contributors, filtered by the user’s churches. |
| `anonymous`     | List of anonymous contributions (non-deleted), filtered by the user’s local churches.        |

---

## Key Concepts Used

### 1. **Transaction Type**

- Uses `TransactionType.OFFERINGS_CAN` to filter Canadian dollar offerings.

### 2. **Donor Categories**

- **Registered Donors**: Tracked users making donations.
- **Miscellaneous Donors**: Non-registered one-time contributors.
- **Anonymous Donors**: Individuals contributing without revealing identity.

### 3. **Query Optimization**

- **`select_related`**: Optimizes query performance for `MiscellaneousContribution` by joining related `Contributor`
  records.

---

### 4. **Offerings USD List**

`/offerings-usd-list`

# `offerings_usd_list` Function

The `offerings_usd_list`  displays a categorized list of USD offerings made
to the church. It organizes the data into two main categories: **Registered Donors** and **Miscellaneous Donors**.

---

## Key Concepts

### **Purpose**

- Displays all USD contributions received, categorizing them into **Registered Donors** and **Miscellaneous Donors**.
- Facilitates easy tracking and management of offerings in USD for church administrators.

---

## Detailed Breakdown

### **Steps**

1. **Fetch Contributions**:
    - Queries the **`Contribution`** model to fetch offerings made by registered users.
    - Filters the results to include only those with `payment_type` set to `TransactionType.OFFERINGS_USD`.

2. **Fetch Miscellaneous Contributions**:
    - Queries the **`MiscellaneousContribution`** model for one-time or irregular contributors.
    - Uses `select_related('contributor')` to optimize the query by prefetching related contributor data.
    - Filters by `payment_type` to include only USD offerings.

3. **Organize Data**:
    - Groups the contributions into two keys within the `context` dictionary:
        - `"contribution"`: Contains offerings from registered users.
        - `"miscellaneous"`: Contains offerings from miscellaneous donors.

4. **Render Template**:
    - Passes the `context` dictionary to the `contributors/offerings_USD_list.html` template for display.

---

### **Context Data Passed**

| Key             | Description                                                                                  |
|-----------------|----------------------------------------------------------------------------------------------|
| `contribution`  | List of USD offerings made by registered users.                                              |
| `miscellaneous` | List of USD offerings made by miscellaneous (non-registered) contributors, linked to donors. |

---

**HTTP Method:** GET  
**Description:**  
Displays a list of USD currency offerings for the church. Includes contributions from both registered and miscellaneous
donors.  
**View Used:** Function-based view: `offerings_usd_list`

**Returns:**

- **HTML Page:** Renders the `contributors/offerings_USD_list.html` template with the context containing `contribution`
  and `miscellaneous` donation lists.

---

### 5. **Download Sample:**

`/download-sample/<type>`

This is a sample of the Excel file that need to be uploaded.

**HTTP Method:** GET  
**Description:**  
Generates and downloads a sample Excel file based on the provided type (`OFFERINGS_CAN` or `OFFERINGS_USD`).  
**View Used:** Function-based view: `download_sample`

**Returns:**

- **File Download:** A dynamically generated `.xlsx` file with headers and sample data for the specified type.

---

### 6. **Upload File**

`/upload-file`

**HTTP Method:** GET, POST  
**Description:**  
Allows uploading and processing of contributor files for contributions.  
**View Used:** Function-based view: `upload_file`

#### POST Method

**Request Payload:**

| Field        | Type   | Description                        | Required |
|--------------|--------|------------------------------------|----------|
| local_church | String | The ID of the local church.        | Yes      |
| file         | File   | The uploaded file containing data. | Yes      |

**Returns:**

- **Success:** Renders the `upload.html` page with a success message: `File uploaded and processed successfully!`.
- **Error:** Renders the `upload.html` page with a list of processing errors.

---

### 7. **Interac Transfer List**

`/interac-transfer-list`

The `interac_transfer_list` function is a retrieves and displays a categorized list of contributions made via bank
payment methods, such as Interac e-Transfer, direct bank transfers, and cheque deposits. This view allows church
administrators to easily track these specific types of contributions.

---

### **Purpose**

- Displays all contributions made through specific bank payment methods, categorized into:
    - **Registered Donors**: Contributions from registered users.
    - **Miscellaneous Donors**: Contributions from unregistered.

---

### **Context Data Passed**

| Key             | Description                                                                    |
|-----------------|--------------------------------------------------------------------------------|
| `contribution`  | List of contributions made by registered users via bank payment methods.       |
| `miscellaneous` | List of contributions made by miscellaneous donors using bank payment methods. |

---

**HTTP Method:** GET  
**Description:**  
Displays a list of Interac contributions (e.g., e-transfers, direct transfers, cheques) for the church.  
**View Used:** Function-based view: `interac_transfer_list`

**Returns:**

- **HTML Page:** Renders the `contributors/interac_transfer_list.html` template with the context
  containing `contribution` and `miscellaneous` donation lists.

---

### 8. **Add Interac**

`/add-interac`

**HTTP Method:** GET, POST  
**Description:**  
Manages manual addition of Interac transfers (e-transfers, direct transfers, cheques) for the church.  
**View Used:** Class-based view: `InteracAddView`

#### POST Method

**Request Payload:**

| Field        | Type    | Description                                | Required |
|--------------|---------|--------------------------------------------|----------|
| local_church | String  | The ID of the local church.                | Yes      |
| name         | String  | Contributor's name (if known).             | YES      |
| date         | String  | Date of the transfer (YYYY-MM-DD).         | Yes      |
| amount       | Decimal | Amount of the transfer.                    | Yes      |
| payment_type | String  | Type of payment (e.g., `direct_transfer`). | Yes      |

**Returns:**

- **Success:** Redirects to the `interac_transfer_list` page with a success message: `Donation successfully added!`.
- **Error:** Redirects to the `add-interac` page with an error message: `Something went wrong`.

---

### 9. **Bank Statement Importer**
`/bank-statement-importer`
Handles the uploading and processing of bank statements. It allows users to upload a bank statement file, which is then
processed to extract relevant contribution data, which can be associated with the church's finances.


**HTTP Method:** GET, POST  
**Description:**  
- This view allows users to upload a bank statement file and processes it to identify financial transactions related to
  church contributions.
- It provides feedback on whether the file was processed successfully and any errors encountered. 
**View Used:**  `bank_statement_importer`

#### POST Method

**Request Payload:**

| Field        | Type    | Description                                | Required |
|--------------|---------|--------------------------------------------|----------|
| local_church | String  | The ID of the local church.                | Yes      |


**Returns:**

- **Success:** Bank statement uploaded and processed successfully.
- **Error:** Error


### **Context Data Passed**

| Key               | Description                                                                 |
|-------------------|-----------------------------------------------------------------------------|
| `form`            | The form for uploading the bank statement file.                             |
| `success_message` | A message indicating whether the bank statement was processed successfully. |
| `errors`          | Any errors encountered during file processing.                              |
| `local_churches`  | The list of local churches associated with the logged-in user.              |
| `type`            | The transaction type value, `INTEREC_E_TRANSFER`.                           |

---

This view is useful for church administrators who need to upload and process bank statement files to track contributions
made via electronic transfers, such as Interac e-Transfers. It streamlines the process of importing financial data from
bank statements into the church's record system.

