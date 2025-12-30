from abc import ABC, abstractmethod
from datetime import time
import socket
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path
from typing import Optional

from api1.constants import DEFAULT_ACTIVE_TIME_RANGE, WEEKS_PER_MONTH
from api1.helpers import load_time_range_config
from api1.smtp_logging import smtp_logger

class AbstractEmailDeliveryService(ABC):
    @abstractmethod
    def deliver(
        self,
        to_email: str,
        subject: str,
        body: str,
        attachment_path: Optional[str] = None,
    ) -> None:
        pass


class SMTPEmailDeliveryService(AbstractEmailDeliveryService):
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        sender_email: str,
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.sender_email = sender_email
        # Maximum retry attempts for temporary (4xx) errors
        self._max_retries = 3
        # Delay between retries in seconds
        self._retry_delay = 5

    def deliver(
        self,
        to_email: str,
        subject: str,
        body: str,
        attachment_path: Optional[str] = None,
    ) -> None:
        to_email = to_email.lower()

        message = EmailMessage()
        message["From"] = self.sender_email
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body)

        if attachment_path:
            try:
                with open(attachment_path, "rb") as f:
                    data = f.read()
                    filename = Path(attachment_path).name
                    message.add_attachment(
                        data,
                        maintype="application",
                        subtype="octet-stream",
                        filename=filename,
                    )
                smtp_logger.debug("Attached file %s (%d bytes)", filename, len(data))
            except FileNotFoundError as e:
                smtp_logger.error("Attachment file not found: %s", e)
                raise

        attempt = 0
        while True:
            try:
                smtp_logger.debug("Connecting to %s:%d", self.smtp_host, self.smtp_port)
                if self.smtp_port == 465:
                    # Use implicit SSL/TLS for port 465
                    server = smtplib.SMTP_SSL(
                        self.smtp_host, self.smtp_port, context=ssl.create_default_context()
                    )
                else:
                    # Use STARTTLS for other ports
                    server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10)
                    server.set_debuglevel(1)
                    server.ehlo()
                    server.starttls(context=ssl.create_default_context())
                    server.ehlo()

                with server:
                    smtp_logger.debug("Logging in as %s", self.smtp_user)
                    server.login(self.smtp_user, self.smtp_password)
                    smtp_logger.debug("Sending message to %s", to_email)
                    server.send_message(message)

                smtp_logger.info("Email successfully sent to %s", to_email)
                return

            except smtplib.SMTPResponseException as e:
                code, err = e.smtp_code, e.smtp_error.decode(errors="ignore")
                smtp_logger.warning("SMTPResponseException: code=%s, error=%s", code, err)

                # Retry on temporary errors (4xx)
                if 400 <= code < 500 and attempt < self._max_retries:
                    attempt += 1
                    smtp_logger.info(
                        "Transient error – retry #%d in %d seconds", attempt, self._retry_delay
                    )
                    time.sleep(self._retry_delay)
                    continue
                else:
                    smtp_logger.error("Permanent SMTP failure or retries exhausted.")
                    raise

            except (smtplib.SMTPException, ssl.SSLError) as e:
                smtp_logger.error("SMTP/SSL exception during send: %s", e)
                raise

            except socket.gaierror as e:
                smtp_logger.error("Network or DNS resolution error: %s", e)
                raise

            except Exception as e:
                smtp_logger.exception("Unexpected exception during SMTP delivery: %s", e)
                raise


def get_time_range_limit() -> int:
    """
    Active time range limit specifies the retrospective window for database queries
    e.g., a value of 6 months retrieves all records from the past six months.
    """
    cfg = load_time_range_config()

    try:
        active_limit = cfg["months"] * WEEKS_PER_MONTH
    except:
        active_limit = DEFAULT_ACTIVE_TIME_RANGE * WEEKS_PER_MONTH
    
    return active_limit
