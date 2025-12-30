import os
import re
import time
import logging
from typing import TYPE_CHECKING, Any, Dict, Optional, Sequence, Tuple, Union

from markupsafe import escape
from starlette_admin._types import RequestAction
from starlette_admin.exceptions import FormValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from starlette_admin.fields import BaseField


INVOICE_PDF_FOOTER_TEXT = "Purchaser is responsible for applicable local tobacco taxes. "\
    "All interstate wholesale purchases are designated for delivery outside the state."

QUOTATION_PDF_FOOTER_TEXT = "- Due to the unprecedented increase of shipping and materials cost, "\
    "minimum shipping charge will be $15 as of 3/29/2022." \
    "CUSTOMER IS RESPONSIBLE FOR LOCAL TOBACCO TAXES."


def prettify_class_name(name: str) -> str:
    return re.sub(r"(?<=.)([A-Z])", r" \1", name)


def slugify_class_name(name: str) -> str:
    return "".join(["-" + c.lower() if c.isupper() else c for c in name]).lstrip("-")


def is_empty_file(file: Any) -> bool:
    pos = file.tell()
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(pos)
    return size == 0


def get_file_icon(mime_type: str) -> str:
    mapping = {
        "image": "fa-file-image",
        "audio": "fa-file-audio",
        "video": "fa-file-video",
        "application/pdf": "fa-file-pdf",
        "application/msword": "fa-file-word",
        "application/vnd.ms-word": "fa-file-word",
        "application/vnd.oasis.opendocument.text": "fa-file-word",
        "application/vnd.openxmlformatsfficedocument.wordprocessingml": "fa-file-word",
        "application/vnd.ms-excel": "fa-file-excel",
        "application/vnd.openxmlformatsfficedocument.spreadsheetml": "fa-file-excel",
        "application/vnd.oasis.opendocument.spreadsheet": "fa-file-excel",
        "application/vnd.ms-powerpoint": "fa-file-powerpoint",
        "application/vnd.openxmlformatsfficedocument.presentationml": (
            "fa-file-powerpoint"
        ),
        "application/vnd.oasis.opendocument.presentation": "fa-file-powerpoint",
        "text/plain": "fa-file-text",
        "text/html": "fa-file-code",
        "text/csv": "fa-file-csv",
        "application/json": "fa-file-code",
        "application/gzip": "fa-file-archive",
        "application/zip": "fa-file-archive",
    }
    if mime_type:
        for key in mapping:
            if key in mime_type:
                return mapping[key]
    return "fa-file"


def html_params(kwargs: Dict[str, Any]) -> str:
    """Converts a dictionary of HTML attribute name-value pairs into a string of HTML parameters."""
    params = []
    for k, v in kwargs.items():
        if v is None or v is False:
            continue
        if v is True:
            params.append(k)
        else:
            params.append('{}="{}"'.format(str(k).replace("_", "-"), escape(v)))
    return " ".join(params)


def extract_fields(
    fields: Sequence["BaseField"], action: RequestAction = RequestAction.LIST
) -> Sequence["BaseField"]:
    """Extract fields based on the requested action and exclude flags."""
    arr = []
    for field in fields:
        if (
            (action == RequestAction.LIST and field.exclude_from_list)
            or (action == RequestAction.DETAIL and field.exclude_from_detail)
            or (action == RequestAction.CREATE and field.exclude_from_create)
            or (action == RequestAction.EDIT and field.exclude_from_edit)
        ):
            continue
        arr.append(field)
    return arr


def pydantic_error_to_form_validation_errors(exc: Any) -> FormValidationError:
    """Convert Pydantic Error to FormValidationError"""
    from pydantic import ValidationError

    assert isinstance(exc, ValidationError)
    errors: Dict[Union[str, int], Any] = {}
    for pydantic_error in exc.errors():
        loc: Tuple[Union[int, str], ...] = pydantic_error["loc"]
        _d = errors
        for i in range(len(loc)):
            if i == len(loc) - 1:
                _d[loc[i]] = pydantic_error["msg"]
            elif loc[i] not in _d:
                _d[loc[i]] = {}
            _d = _d[loc[i]]
    return FormValidationError(errors)

DB_MAPPING = {"DB1": "S2S", "DB2": "5 Stars", "DB3": "RAND", "DB11": "SCW"}


def generate_unique_quotation_number_simple(
    session: Session,
    quotations_table,
    max_retries: int = 5,
    base_delay: float = 0.1,
) -> int:
    """
    Generate a unique quotation number using MAX + 1 with row locking and retry logic.

    This function uses SELECT ... FOR UPDATE to lock the row with the maximum
    QuotationNumber, preventing race conditions where multiple concurrent requests
    could generate the same number.

    Args:
        session: SQLAlchemy session (must be within a transaction)
        quotations_table: The Quotations_tbl model class
        max_retries: Maximum number of retry attempts on collision
        base_delay: Base delay in seconds for exponential backoff

    Returns:
        A unique quotation number (integer)

    Raises:
        RuntimeError: If unable to generate unique number after max_retries
    """
    for attempt in range(max_retries):
        try:
            stmt = (
                select(func.coalesce(func.max(quotations_table.QuotationNumber), 0))
                .with_for_update()
            )
            max_qn = session.scalar(stmt)
            new_number = max_qn + 1
            return new_number
        except IntegrityError as e:
            session.rollback()
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    f"Quotation number collision on attempt {attempt + 1}, "
                    f"retrying in {delay:.2f}s: {e}"
                )
                time.sleep(delay)
            else:
                logger.error(
                    f"Failed to generate unique quotation number after {max_retries} attempts"
                )
                raise RuntimeError(
                    f"Unable to generate unique quotation number after {max_retries} attempts"
                ) from e
    raise RuntimeError("Unexpected error in quotation number generation")


def generate_unique_quotation_number_with_prefix(
    session_main: Session,
    session_admin: Session,
    quotations_table,
    quotations_status_table,
    date_prefix: int,
    max_retries: int = 5,
    base_delay: float = 0.1,
) -> str:
    """
    Generate a unique quotation number using date-based prefix with collision loop.

    This function:
    1. Queries QuotationsStatus for existing numbers with the date prefix
    2. Calculates the next sequence number
    3. Validates against both QuotationsStatus and Quotations_tbl
    4. Loops until a unique number is found (or max iterations reached)

    Args:
        session_main: SQLAlchemy session for main database (Quotations_tbl)
        session_admin: SQLAlchemy session for admin database (QuotationsStatus)
        quotations_table: The Quotations_tbl model class
        quotations_status_table: The QuotationsStatus model class
        date_prefix: The date-based prefix (e.g., 120320251 for 12/03/2025, DB1)
        max_retries: Maximum retry attempts on collision
        base_delay: Base delay for exponential backoff

    Returns:
        A unique quotation number (string)

    Raises:
        RuntimeError: If unable to generate unique number after max_retries
    """
    prefix_str = str(date_prefix)
    max_iterations = 100

    for attempt in range(max_retries):
        try:
            stmt_existing = (
                select(quotations_status_table.__table__.columns)
                .where(quotations_status_table.QuotationNumber.like(f"{prefix_str}%"))
                .order_by(quotations_status_table.id.desc())
                .with_for_update()
            )
            existing_rows = session_admin.execute(stmt_existing).mappings().all()

            if not existing_rows:
                candidate_number = f"{prefix_str}1"
            else:
                last_qn = str(existing_rows[0]["QuotationNumber"])
                if len(prefix_str) < len(last_qn):
                    suffix = last_qn[len(prefix_str):]
                    try:
                        next_suffix = int(suffix) + 1
                    except ValueError:
                        next_suffix = 1
                    candidate_number = f"{prefix_str}{next_suffix}"
                else:
                    candidate_number = f"{last_qn}1"

            for iteration in range(max_iterations):
                exists_in_status = session_admin.scalar(
                    select(func.count())
                    .select_from(quotations_status_table)
                    .where(quotations_status_table.QuotationNumber == candidate_number)
                )

                exists_in_main = session_main.scalar(
                    select(func.count())
                    .select_from(quotations_table)
                    .where(quotations_table.QuotationNumber == candidate_number)
                )

                if not exists_in_status and not exists_in_main:
                    return candidate_number

                try:
                    candidate_number = str(int(candidate_number) + 1)
                except ValueError:
                    candidate_number = f"{prefix_str}{iteration + 2}"

            raise RuntimeError(
                f"Could not find unique quotation number after {max_iterations} iterations"
            )

        except IntegrityError as e:
            session_admin.rollback()
            session_main.rollback()
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    f"Quotation number collision on attempt {attempt + 1}, "
                    f"retrying in {delay:.2f}s: {e}"
                )
                time.sleep(delay)
            else:
                logger.error(
                    f"Failed to generate unique quotation number after {max_retries} attempts"
                )
                raise RuntimeError(
                    f"Unable to generate unique quotation number after {max_retries} attempts"
                ) from e

    raise RuntimeError("Unexpected error in quotation number generation")