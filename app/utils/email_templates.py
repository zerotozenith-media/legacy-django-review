EMAIL_TEMPLATES = {
    "update_miscellaneous_users": {
        "subject": "Reminder: Update Miscellaneous Users Profile",
        "heading": "Reminder: Update Miscellaneous Users Profile",
        "template_name": "email/general_email.html",
        "message": """
            <p>This is a reminder that there are {count} miscellaneous users with incomplete profiles under your {role}.</p>
            <p>Only registered users are eligible to receive tax receipts for their contributions. 
            A miscellaneous user must have a valid Full Name and Email to be registered as a regular user. 
            These details are essential to issue tax receipts for their contributions.</p>
            <p>Please assist them in completing their profiles.</p>
        """,
    },
    "submit_detail_report_reminder": {
        "subject": "Reminder: Submit Your Detailed Report for the Current Month",
        "heading": "Detailed Report for the Current Month",
        "template_name": "email/general_email.html",
        "message": """
            <p>This is a gentle reminder for you to please submit your detailed report for the current month.</p>
            <p><strong>Note:</strong> The Region Overseer will be copied in the first escalation email if the report 
            is not completed within 2 days.</p>
        """,
    },
    "detail_report_first_escalation": {
        "subject": "Urgent (First Escalation): Detailed Report for last Month",
        "heading": "Detail Report for last Month",
        "template_name": "email/general_email.html",
        "message": """
            <p>We would like to bring to your attention that the detailed report for last month is overdue. 
            Please note that the Regional Overseer has been cc'd on this email.</p>
            <p>Kindly prioritize the completion and submission of the report at your earliest convenience.</p>
            <p><strong>Note:</strong> The National Overseer will be copied in the next escalation email if the report 
            is not completed within 2 days.</p>
            <p>Thank you for your prompt attention to this matter.</p>
        """,
    },
    "detail_report_second_escalation": {
        "subject": "Urgent (Second Escalation): Detailed Report for last Month",
        "heading": "Detail Report for last Month",
        "template_name": "email/general_email.html",
        "message": """
            <p>We would like to bring to your attention that the detailed report for last month is overdue. 
            Please note that the National Overseer has been cc'd on this email.</p>
            <p>Kindly prioritize the completion and submission of the report at your earliest convenience.</p>
            <p>Thank you for your prompt attention to this matter.</p>
        """,
    },

    "payment_allocation_reminder": {
        "subject": "Allocation Payment Reminder",
        "heading": "Allocation Payment Reminder",
        "template_name": "email/general_email.html",
        "message": """
            <p>We hope this message finds you well. This is a kind reminder that the monthly allocation payment is due.
            Please ensure that the necessary payments are made promptly.</p>
            <p>If you have already completed the payment, kindly disregard this message. Otherwise, we appreciate your
                immediate attention to this matter.</p>
            <p>Note: The National Overseer will be copied on the escalation email if payment is not received in 2 days.</p>
        """,
    },

    "payment_allocation_escalation": {
        "subject": "Escalation Notice: Allocation Payment Outstanding",
        "heading": "Escalation Notice: Allocation Payment Outstanding",
        "template_name": "email/general_email.html",
        "message": """
            <p>This is to notify you that the monthly allocation payment remains outstanding. As this is now overdue, 
            the National Overseer is copied in this email.
            </p>
            <p>We kindly urge you to ensure the payment is completed at your earliest convenience.</p>
            <p>If you have already made payment, we thank you for your cooperation. Otherwise, please prioritize this
                matter.
            </p>
        """,
    },

    "password_update_request": {
        "subject": "Password Reset Instructions",
        "heading": "Reset Your Password",
        "template_name": "email/general_email.html",
        "message": """
        <p>We received a request to reset the password associated with your account. To proceed, please click the Reset Password link
        below:</p>
        <p><a href="{reset_link}" style="color: #9ccfff; text-decoration: none; background-color: #16365e; padding: 10px 20px; border-radius: 5px; display: inline-block;">Reset Password</a></p>
        <p>If you did not make this request, you can safely ignore this email.</p>
    """,
    },

    "donation_receipt": {
        "subject": "Your Donation Receipt",
        "heading": "Your Donation Receipt",
        "template_name": "email/general_email.html",
        "message": """
       <p>Attached is your donation receipt.</p>
       <p>Thank you for your generosity!</p>
       <p>If you did not make this request, you can safely ignore this email.</p>
    """,
    }
}
