# Authentication App Documentation

---

## User Roles and Hierarchy

The app has four levels of users in a hierarchical structure:
This controlled buy the middleware.py to assign roles and permissions

- Member: Basic level user of the system.
Members are not allowed to login for now

- Local Church Pastor: Manages a local congregation and reports to higher authorities.
- Region Overseer: Supervises multiple local churches and reports to the national overseer.
- National Overseer: The highest role in the hierarchy.

All roles (including pastors and overseers) are also considered members within the system,
reflecting the church's structure.

---

## Middleware Execution Flow

The middleware intercepts every request via its __call__ method.

### Path Validation

Ignores paths that don't fall under specific modules (e.g., admin, authentication, expense).
Uses regex to filter acceptable path structures.

### Permission Logic

- `Anonymous Users:` Checked against public permissions.
- `Superuser:` Automatically has all permissions.
- `Role-based Users:` Matches `user.role` to the corresponding permissions map.
- `No Role:` Defaults to public.

- `Access Denied`
  If the user does not have the required permission, it renders a custom 403.html page with a 403 status code.

- `Error Handling`
  Logs exceptions and renders a 500.html page if unexpected errors occur.


---

## **Authentication Endpoints**


### **Table of Contents**

[1. Register a Contributor](#1-register-a-contributor)<br>
[2. Invite Users](#2-invite-users)<br>
[3. Validate Username](#3-validate-username)<br>
[4. Validate Email](#4-validate-email)<br>
[5. User Login](#5-user-login)<br>
[6. User Logout](#6-user-logout)<br>
[7. Request Password Reset Link](#7-request-password-reset-link)<br>
[8. Activate User](#8-activate-user-account)<br>
[9. Set New Password](#9-set-new-password)<br>
[10. Activate/Deactivate User](#10-activate-deactivate-user)<br>
[11. List Users](#11-list-users)<br>
[12. Get User Profile](#12-user-profile)<br>
[13. Download User Uploader Sample](#13-user-uploader-sample)<br>
[14. Upload Users](#14-user-uploader)<br>
[15. Add User](#15-add-new-user)<br>

---

### **1. Register a Contributor**

- Endpoint: authentication/register
- HTTP Method: POST
- Description: Allows contributors to register themselves.
- View Used: ContributorRegistrationView

```http
POST /register
```

**Request Payload:**

| Name        | Type   | Required | Description                      |
|-------------|--------|----------|----------------------------------|
| email       | string | YES      | Email of the contributor.        |
| password    | string | YES      | Password for the contributor.    |
| first_name  | string | YES      | First name for the contributor.  |
| middle_name | string | YES      | Middle name for the contributor. |
| last_name   | string | YES      | Last name for the contributor.   |
| role        | string | NO       | Assign contributor role          |

- role: As defined in `authentication.middleware.Role`

**Returns:**

- **Success:** Redirects to Login page. `message:` Check the Activation Link in your email to activate your account
- **Error:** Returns Register page.


## 2. Invite Users

This view is used to register a new admin user
including sending an activation email to confirm the email address.

**Endpoint:** authentication/invite-users  
**HTTP Method:** POST  
**Description:** Allows the admin to invite new users to register.  
**View Used:** AdminUserRegistrationView

### POST /invite-users

**Request Payload:**

| Name        | Type   | Required | Description                      |
|-------------|--------|----------|----------------------------------|
| email       | string | YES      | Email of the contributor.        |
| password    | string | YES      | Password for the contributor.    |
| first_name  | string | YES      | First name for the contributor.  |
| middle_name | string | YES      | Middle name for the contributor. |
| last_name   | string | YES      | Last name for the contributor.   |
| role        | string | YES      | Role to be assigned to the user. |

**Returns:**

- **Success:** User is invited and an email is sent to the user.
- **Error:** Invitation page.

---

## 3. Validate Username

**Endpoint:** authentication/validate-username  
**HTTP Method:** POST  
**Description:** Validates the availability of a username.  
**View Used:** UsernameValidationView

### POST /validate-username

**Request Payload:**

| Name     | Type   | Required | Description               |
|----------|--------|----------|---------------------------|
| username | string | YES      | Username to be validated. |

**Returns:**

- **Success:** Returns a success message if the username is available.
- **Error:** Returns an error message if the username is already taken.

---

## 4. Validate Email

**Endpoint:** authentication/validate-email  
**HTTP Method:** POST  
**Description:** Validates the availability of an email address.  
**View Used:** EmailValidationView

### POST /validate-email

**Request Payload:**

| Name  | Type   | Required | Description            |
|-------|--------|----------|------------------------|
| email | string | YES      | Email to be validated. |

**Returns:**

- **Success:** Returns a success message if the email is available.
- **Error:** Returns an error message if the email is already in use.

---

## 5. User Login

**Endpoint:** authentication/login  
**HTTP Method:** POST  
**Description:** Allows users to login to their accounts.  
**View Used:** LoginView

### POST /login

**Request Payload:**

| Name     | Type   | Required | Description                    |
|----------|--------|----------|--------------------------------|
| username | string | YES      | Username or email of the user. |
| password | string | YES      | Password for the user.         |

**Returns:**

- **Success:** Logs in the user and returns a token.
- **Error:** Returns an error message for invalid credentials.

---

## 6. User Logout

**Endpoint:** authentication/logout  
**HTTP Method:** POST  
**Description:** Logs the user out of their account.  
**View Used:** LogoutView

### POST /logout

**Returns:**

- **Success:** Logs the user out and redirects to the homepage.
- **Error:** Returns an error message.

---

## 7. Request Password Reset Link

**Endpoint:** authentication/request-reset-link  
**HTTP Method:** POST  
**Description:** Sends a password reset link to the user's email.  
**View Used:** RequestPasswordResetEmail

### POST /request-reset-link

**Request Payload:**

| Name  | Type   | Required | Description                         |
|-------|--------|----------|-------------------------------------|
| email | string | YES      | Email of the user requesting reset. |

**Returns:**

- **Success:** Sends a reset link to the user's email.
- **Error:** Returns an error message if email is not registered.

---

## 8. Activate User Account

**Endpoint:** authentication/activate/<uidb64>/<token>  
**HTTP Method:** GET  
**Description:** Activates the user's account using the provided token.  
**View Used:** VerificationView

### GET /activate/<uidb64>/<token>

**Returns:**

- **Success:** Redirects the user to the login page with an activation success message.
- **Error:** Returns an error if the token is invalid or expired.

---

## 9. Set New Password

**Endpoint:** authentication/set-new-password/<uidb64>/<token>  
**HTTP Method:** POST  
**Description:** Allows the user to reset their password.  
**View Used:** CompletePasswordReset

### POST /set-new-password/<uidb64>/<token>

**Request Payload:**

| Name     | Type   | Required | Description                |
|----------|--------|----------|----------------------------|
| password | string | YES      | New password for the user. |

**Returns:**

- **Success:** Resets the user's password and redirects to the login page.
- **Error:** Returns an error message.

---

## 10. Activate Deactivate User

**Endpoint:** authentication/<user_id>/activate-deactivate  
**HTTP Method:** POST  
**Description:** Allows the admin to activate or deactivate a user account.  
**View Used:** user_activate_deactivate

### POST /<user_id>/activate-deactivate

**Request Payload:**

| Name   | Type    | Required | Description                                                |
|--------|---------|----------|------------------------------------------------------------|
| status | boolean | YES      | Whether to activate (true) or deactivate (false) the user. |

**Returns:**

- **Success:** Changes the user's account status.
- **Error:** Returns an error message.

---

## 11. List Users
This view is responsible for displaying a list of 
users who belong to the same local churches as the currently logged-in use

**Endpoint:** authentication/users  
**HTTP Method:** GET  
**Description:** Returns a list of all users.  
**View Used:** UserListView

### GET /users

**Returns:**

- **Success:** Returns a list of users.
- **Error:** Returns an error message if the user list is not available.

---

## 12. User Profile
View that handles displaying and updating a user's profile.

**Endpoint:** authentication/profile/<id>  
**HTTP Method:** GET  
**Description:** Retrieves the profile details of a specific user.  
**View Used:** UserProfile

### GET /profile/<id>

**Returns:**

- **Success:** Returns the user's profile details.

```json
{
  "id": "user_id",
  "first_name": "First",
  "last_name": "Last",
  "middle_name": "Middle",
  "email": "email",
  "address": "address",
  "gender": "gender"
}
```

- **Error:** Returns an error message.

### POST /profile/<id>

**Request Payload:**

| Name        | Type   | Required | Description                      |
|-------------|--------|----------|----------------------------------|
| first_name  | string | Optional | First name for the contributor.  |
| middle_name | string | Optional | Middle name for the contributor. |
| last_name   | string | Optional | Last name for the contributor.   |
| address     | string | Optional | Address for the contributor.     |
| gender      | string | Optional | Gender of the contributor.       |

**Returns:**

- **Success:** Updates the new user details in the system. message: Profile Update Successfully
- **Error:** Returns an error message and Profile page.

---

## 13. User Uploader Sample

This view is designed to generate and return a sample Excel file (in .xlsx format) to the client.
This file contains headers and a few rows of sample user data that could be uploaded by users,
such as first name, last name, email, etc.

**Endpoint:** authentication/user-uploader-sample  
**HTTP Method:** GET  
**Description:** Provides a sample file for user data upload.  
**View Used:** download_user_uploader_sample

### GET /user-uploader-sample

**Returns:**

- **Success:** Returns the sample file for user upload.
- **Error:** Returns an error message.

---

## 14. User Uploader

Handles the functionality for uploading user data from an Excel file in read-only mode.
It processes an Excel file to extract user information, validates it, and saves the data to a database.
The view uses helper functions for validating the file's contents and saving the user data.

**Endpoint:** authentication/user/uploader  
**HTTP Method:** POST  
**Description:** Uploads user data through a specified format.  
**View Used:** UserUploaderView

### POST /user/uploader

**Request Payload:**

| Name | Type | Required | Description                          |
|------|------|----------|--------------------------------------|
| file | file | YES      | File containing user data to upload. |

**Returns:**

- **Success:** Returns a message confirming successful upload.
- **Error:** Returns an error message if the file upload fails.

---

## 15. Add New User

**Endpoint:** authentication/user/add  
**HTTP Method:** POST  
**Description:** Allows an admin to add a new user.  
**View Used:** UserAddView

### POST /user/add

**Request Payload:**

| Name         | Type   | Required | Description                            |
|--------------|--------|----------|----------------------------------------|
| email        | string | YES      | Email of the contributor.              |
| password     | string | YES      | Password for the contributor.          |
| first_name   | string | YES      | First name for the contributor.        |
| middle_name  | string | YES      | Middle name for the contributor.       |
| last_name    | string | YES      | Last name for the contributor.         |
| role         | string | YES      | Role to be assigned to the user.       |
| address      | string | YES      | First name for the contributor.        |
| full_name    | string | YES      | Middle name for the contributor.       |
| local_church | string | YES      | local_church for the admin adding user |

**Returns:**

- **Success:** Adds the new user to the system.
- **Error:** Returns an error message.

