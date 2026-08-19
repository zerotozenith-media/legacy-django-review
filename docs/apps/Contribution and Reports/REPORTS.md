# Report App Documentation

The app generally helps users in generating, 
download and send reports, letter receipts, and more.

---
`Legend`
-  can = Canadian Dollar
-  OFFERINGS_CAN = 'offerings_can' `Offerings in canadian dollar`

## Table of Contents

1. [Receipts Generation Page](#1-receipts-generation-page)
2. [Offering Can Summary Report](#2-offering-can-summary-report)
3. [Send Offerings Can Summary Report](#3-send-offerings-can-summary-report)
4. [Download Offerings Can Summary Report](#4-download-offerings-can-summary-report)
5. [Send Interac Summary Report](#5-send-interac-summary-report)
6. [Offerings Can Letter Report](#6-offerings-can-letter-report)
7. [Interac Summary Report](#7-interac-summary-report)
8. [Interac Letter Report](#8-interac-letter-report)
9. [Offerings Uploader View](#9-offerings-uploader-view)
10. [Preview Reports and Letters](#10-preview-reports-and-letters)
11. [Send Letter Receipts](#11-send-letter-receipts)

---

### 1. Receipts Generation Page

**URL:** `/receipts/`  
**Purpose:** Displays the page for generating donation receipts.  
**Permissions:** Requires authenticated users.

**Concept:**  
Provides an interface to generate receipts for various donations.

**Responses:**

- **Success:** HTML page for generating receipts.
- **Error:** HTTP 400 Bad Request - Invalid request parameters.

---

### 2. Offering Can Summary Report

**URL:** `/offering_can_summary/`  
**Purpose:** Generates an offering can summary report.  
**Permissions:** Requires administrative privileges.

**Responses:**

- **Success:** PDF report.
- **Error:** HTTP 400 Bad Request - Invalid request parameters.

---

### 3. Send Offerings Can Summary Report

**URL:** `/send_offerings_can_summary/<str:c_id>`  
**Purpose:** Sends an offering can summary report to a contributor.  
**Permissions:** Requires administrative privileges.

**Concept:**  
Sends a PDF summary of offerings to a contributor.

**Responses:**

- **Success:** HTTP 200 OK - Message confirming the successful report send.
- **Error:** HTTP 400 Bad Request - Invalid contributor ID.

---

### 4. Download Offerings Can Summary Report

**URL:** `/download_offerings_can_summary/<str:c_id>`  
**Purpose:** Downloads an offering can summary report for a contributor.  
**Permissions:** Requires administrative privileges.

**Concept:**  
Provides the option to download a summary report as a ZIP file.

**Responses:**

- **Success:** HTTP 200 OK - ZIP file containing the requested summary report.
- **Error:** HTTP 400 Bad Request - Invalid contributor ID or request issues.

---

### 5. Send Interac Summary Report

**URL:** `/send_interac_summary/<str:c_id>`  
**Purpose:** Sends an Interac summary report to a contributor.  
**Permissions:** Requires administrative privileges.

**Concept:**  
Sends a PDF summary of Interac donations to a contributor.

**Responses:**

- **Success:** HTTP 200 OK - Success message.
- **Error:** HTTP 400 Bad Request - Invalid contributor ID.

---

### 6. Offerings Can Letter Report

**URL:** `/offerings_can_letter/`  
**Purpose:** Generates an offering can letter report.  
**Permissions:** Requires administrative privileges.

**Concept:**  
Generates a letter report for offering can donations.

**Responses:**

- **Success:** HTTP 200 OK - PDF report generated.
- **Error:** HTTP 400 Bad Request - Invalid parameters.

---

### 7. Interac Summary Report

**URL:** `/interac_summary/`  
**Purpose:** Generates an Interac donation summary report.  
**Permissions:** Requires administrative privileges.

**Concept:**  
Generates a summary report for all Interac donations.

**Responses:**

- **Success:** HTTP 200 OK - PDF report generated.
- **Error:** HTTP 400 Bad Request - Invalid request.

---

### 8. Interac Letter Report

**URL:** `/interac_letter/`  
**Purpose:** Generates an Interac donation letter report.  
**Permissions:** Requires administrative privileges.

**Concept:**  
Generates a letter-style report for Interac donations.

**Responses:**

- **Success:** HTTP 200 OK - PDF letter generated.
- **Error:** HTTP 400 Bad Request - Invalid request.

---

### 9. Offerings Uploader View

**URL:** `/offerings-uploader/<str:type>/`  
**Purpose:** Handles the uploading of offering data.  
**Permissions:** Requires administrative privileges.

**Concept:**  
Handles uploading of offering data in different formats.

**Responses:**

- **Success:** HTTP 200 OK - Confirmation message.
- **Error:** HTTP 400 Bad Request - Invalid file format.

---

### 10. Preview Reports and Letters

**Preview Offerings Can Summary Report**

- **URL:** `/preview_offerings_can_summary/<str:c_id>`
- **Purpose:** Previews an offering can summary report.
- **Permissions:** Requires administrative privileges.

**Preview Interac Summary Report**

- **URL:** `/preview_interac_summary/<str:c_id>`
- **Purpose:** Previews an Interac donation summary report.

**Responses:**

- **Success:** A preview page for the report.
- **Error:** HTTP 400 Bad Request - Invalid contributor ID.

---

### 11. Send Letter Receipts

**Send Offerings Can Letter Receipt**

- **URL:** `/send_offerings_can_letter/<str:c_id>`
- **Purpose:** Sends an offering can letter receipt to a contributor.

**Send Interac Letter Receipt**

- **URL:** `/send_interac_letter/<str:c_id>`
- **Purpose:** Sends an Interac donation letter receipt.

**Responses:**

- **Success:** HTTP 200 OK - Confirmation message.
- **Error:** HTTP 400 Bad Request - Invalid contributor ID.
  """