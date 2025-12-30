import logging
from logging.handlers import RotatingFileHandler
import smtplib


smtp_logger = logging.getLogger("smtp")
smtp_logger.setLevel(logging.DEBUG)

file_handler = RotatingFileHandler(
    filename="smtp.log",
    maxBytes=10 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8",
)
file_handler.setFormatter(logging.Formatter(
    "[%(asctime)s] %(levelname)s %(name)s: %(message)s"
))
smtp_logger.addHandler(file_handler)

def _smtp_debug(self, *args):
    smtp_logger.debug(*args)

smtplib.SMTP._print_debug = _smtp_debug
smtplib.SMTP_SSL._print_debug = _smtp_debug
