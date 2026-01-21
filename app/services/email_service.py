"""Email service for sending newsletter emails."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

from app.config import Settings
from app.utils.exceptions import EmailServiceError


class EmailService:
    """Service for sending emails via SMTP."""

    def __init__(self, settings: Settings):
        """
        Initialize the email service.

        Args:
            settings: Application settings with SMTP configuration
        """
        self.settings = settings
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.username = settings.smtp_username
        self.password = settings.smtp_password
        self.sender_email = settings.newsletter_sender_email or settings.smtp_username
        self.sender_name = settings.newsletter_sender_name

    def is_configured(self) -> bool:
        """Check if email service is properly configured."""
        return bool(
            self.smtp_host
            and self.smtp_port
            and self.username
            and self.password
            and self.sender_email
        )

    def send_email(
        self,
        recipients: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> None:
        """
        Send an email to one or more recipients.

        Args:
            recipients: List of recipient email addresses
            subject: Email subject line
            html_content: HTML body of the email
            text_content: Plain text fallback (optional)

        Raises:
            EmailServiceError: If sending fails
        """
        if not self.is_configured():
            raise EmailServiceError(
                "Email service not configured. Set SMTP_USERNAME, SMTP_PASSWORD, "
                "and NEWSLETTER_SENDER_EMAIL in your .env file."
            )

        if not recipients:
            raise EmailServiceError("No recipients specified")

        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.sender_name} <{self.sender_email}>"
        msg["To"] = ", ".join(recipients)

        # Add plain text version
        if text_content:
            text_part = MIMEText(text_content, "plain")
            msg.attach(text_part)

        # Add HTML version
        html_part = MIMEText(html_content, "html")
        msg.attach(html_part)

        try:
            # Connect and send
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.sendmail(self.sender_email, recipients, msg.as_string())

        except smtplib.SMTPAuthenticationError as e:
            raise EmailServiceError(
                f"SMTP authentication failed. Check your username and password. "
                f"For Gmail, use an App Password. Error: {e}"
            )
        except smtplib.SMTPException as e:
            raise EmailServiceError(f"Failed to send email: {e}")
        except Exception as e:
            raise EmailServiceError(f"Email sending failed: {e}")
