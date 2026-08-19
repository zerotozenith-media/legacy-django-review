from django.test import TestCase
from unittest.mock import patch, MagicMock
from utils.send_emails import send_email


class MailtrapEmailTest(TestCase):

    @patch("utils.send_emails.EmailMultiAlternatives.send")
    def test_send_email_success(self, mock_send):
        """
        Test that the send_email function sends an email successfully.
        """
        mock_send.return_value = 1

        success = send_email(
            subject="Test Email",
            recipient_list=["test@example.com"],
            template_name='email/account_activation_email.html',
            bcc=["other@example.com"],
            cc=["other2@example.com"],
            context={
                "first_name": "Test",
                "email": "test_user@example.com"
            }
        )

        self.assertTrue(success)
        mock_send.assert_called_once()

    @patch("utils.send_emails.EmailMultiAlternatives.send")
    def test_send_email_failure(self, mock_send):
        """
        Test that the send_email function handles a failure scenario.
        """
        mock_send.side_effect = Exception("Email sending error")

        success = send_email(
            subject="Test Email",
            recipient_list=["test@example.com"],
            plain_text_body="This is a test email.",
        )

        self.assertFalse(success)
        mock_send.assert_called_once()