"""Input parsing and validation rules for currency amounts and codes."""

from decimal import Decimal, InvalidOperation
import re
from typing import Optional

from currency_converter.errors import ValidationError

# Maximum supported value: 1 quadrillion
MAX_AMOUNT = Decimal("1000000000000000")

# Valid decimal number pattern: optional digits, separator (. or ,), one or more digits, OR digits only
VALID_NUMBER_RE = re.compile(r"^\d+([.,]\d+)?$")


def parse_and_validate_amount(raw_text: Optional[str]) -> Decimal:
    """
    Parse user amount input text into a positive finite Decimal.
    
    Accepts:
        - Numbers with a single period '.' or comma ',' decimal separator followed by digits.
        - Integers (digits only).
        - Surrounding whitespace (stripped).
        
    Rejects:
        - Empty or whitespace-only strings.
        - Alphabetic or special characters.
        - Negative numbers or explicit plus signs.
        - Zero.
        - Multiple or mixed separators (e.g. thousand separators like 1,234.50).
        - Trailing separators without digits (e.g. 10. or 10,).
        - Non-finite numbers (NaN, Infinity).
        - Numbers exceeding MAX_AMOUNT.
    """
    if raw_text is None:
        raise ValidationError("Amount is required. Please enter a positive number.")

    cleaned = raw_text.strip()
    if not cleaned:
        raise ValidationError("Amount is required. Please enter a positive number.")

    # Check for NaN or Infinity representations
    lower_val = cleaned.lower()
    if "nan" in lower_val or "inf" in lower_val:
        raise ValidationError("Amount must be a valid finite number.")

    # Check for negative amounts explicitly
    if cleaned.startswith("-"):
        raise ValidationError("Amount must be greater than zero. Negative numbers are not accepted.")

    # Check decimal separators
    comma_count = cleaned.count(",")
    period_count = cleaned.count(".")
    total_separators = comma_count + period_count

    if total_separators > 1:
        raise ValidationError(
            "Multiple or mixed decimal separators are not permitted. "
            "Use only a single period or comma as the decimal separator (e.g., '10.50' or '10,50')."
        )

    # Check if separator is at the end with no trailing digits
    if cleaned.endswith(".") or cleaned.endswith(","):
        raise ValidationError("A decimal separator must be followed by one or more digits (e.g., '10.50').")

    # Check if separator is at the start with trailing digits, e.g. '.5' -> allow as '0.5'
    if cleaned.startswith(".") or cleaned.startswith(","):
        cleaned = "0" + cleaned

    # Check regex for digits and single optional separator
    if not VALID_NUMBER_RE.match(cleaned):
        raise ValidationError(
            f"Invalid amount format '{raw_text.strip()}'. Please enter digits with an optional decimal separator."
        )

    # Standardize separator to period for Decimal parsing
    standardized = cleaned.replace(",", ".")

    try:
        amount = Decimal(standardized)
    except (InvalidOperation, ValueError) as exc:
        raise ValidationError(f"Invalid numeric amount '{raw_text.strip()}'.") from exc

    if not amount.is_finite():
        raise ValidationError("Amount must be a finite number.")

    if amount <= Decimal("0"):
        raise ValidationError("Amount must be greater than zero.")

    if amount > MAX_AMOUNT:
        raise ValidationError("Amount exceeds the maximum supported calculation range.")

    return amount


def validate_currency_code(code: Optional[str], field_name: str = "Currency") -> str:
    """Validate a currency code string."""
    if not code or not isinstance(code, str) or not code.strip():
        raise ValidationError(f"{field_name} must be selected.")
    return code.strip().upper()
