"""Serialization and deserialization helpers for JSON cache boundaries."""

from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict

from currency_converter.errors import CacheError
from currency_converter.models import BNM_SOURCE_NAME, Currency, ExchangeRateSet


def decimal_to_str(val: Decimal) -> str:
    """Serialize a Decimal value to string, rejecting non-finite values."""
    if not isinstance(val, Decimal) or not val.is_finite():
        raise CacheError(f"Expected finite Decimal, got {type(val)}: {val}")
    return str(val)


def str_to_decimal(val_str: Any) -> Decimal:
    """Deserialize a string to Decimal strictly without float coercion."""
    if not isinstance(val_str, str):
        raise CacheError(f"Expected string representation of Decimal, got {type(val_str)}")
    val_str = val_str.strip()
    if not val_str:
        raise CacheError("Cannot parse empty string as Decimal.")
    try:
        dec = Decimal(val_str)
        if not dec.is_finite():
            raise CacheError(f"Non-finite Decimal parsed from '{val_str}'")
        return dec
    except (InvalidOperation, ValueError) as exc:
        raise CacheError(f"Invalid decimal string '{val_str}': {exc}") from exc


def date_to_str(d: date) -> str:
    """Convert a date object to ISO format YYYY-MM-DD."""
    if not isinstance(d, date):
        raise CacheError(f"Expected date, got {type(d)}")
    return d.isoformat()


def str_to_date(s: Any) -> date:
    """Parse an ISO date string YYYY-MM-DD into a date object."""
    if not isinstance(s, str):
        raise CacheError(f"Expected string date, got {type(s)}")
    try:
        return date.fromisoformat(s.strip())
    except (ValueError, TypeError) as exc:
        raise CacheError(f"Invalid date string '{s}': {exc}") from exc


def datetime_to_iso(dt: datetime) -> str:
    """Convert a datetime object to an ISO 8601 string with timezone."""
    if not isinstance(dt, datetime):
        raise CacheError(f"Expected datetime, got {type(dt)}")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def iso_to_datetime(s: Any) -> datetime:
    """Parse an ISO 8601 datetime string into a datetime object."""
    if not isinstance(s, str):
        raise CacheError(f"Expected string datetime, got {type(s)}")
    try:
        dt = datetime.fromisoformat(s.strip())
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError) as exc:
        raise CacheError(f"Invalid datetime string '{s}': {exc}") from exc


def rate_set_to_dict(rate_set: ExchangeRateSet) -> Dict[str, Any]:
    """Convert an ExchangeRateSet into a JSON-serializable dictionary."""
    return {
        "effective_date": date_to_str(rate_set.effective_date),
        "retrieved_at": datetime_to_iso(rate_set.retrieved_at),
        "source": rate_set.source,
        "currencies": {
            code: {
                "code": curr.code,
                "name": curr.name,
                "nominal": decimal_to_str(curr.nominal),
                "value": decimal_to_str(curr.value),
                "rate_mdl_per_unit": decimal_to_str(curr.rate_mdl_per_unit),
            }
            for code, curr in rate_set.currencies.items()
        },
    }


def dict_to_rate_set(data: Dict[str, Any]) -> ExchangeRateSet:
    """Construct an ExchangeRateSet from a validated cache dictionary."""
    if not isinstance(data, dict):
        raise CacheError(f"Expected dictionary for rate set, got {type(data)}")

    eff_date = str_to_date(data.get("effective_date"))
    retrieved_at = iso_to_datetime(data.get("retrieved_at"))
    source = data.get("source", BNM_SOURCE_NAME)

    raw_currencies = data.get("currencies")
    if not isinstance(raw_currencies, dict) or not raw_currencies:
        raise CacheError("Cache record contains missing or invalid 'currencies' dictionary.")

    currencies: Dict[str, Currency] = {}
    for code, cdata in raw_currencies.items():
        if not isinstance(cdata, dict):
            raise CacheError(f"Invalid currency record for {code}")
        c_code = cdata.get("code", code).upper().strip()
        c_name = str(cdata.get("name", "")).strip()
        c_nominal = str_to_decimal(cdata.get("nominal"))
        c_value = str_to_decimal(cdata.get("value"))
        c_rate = str_to_decimal(cdata.get("rate_mdl_per_unit"))

        currencies[c_code] = Currency(
            code=c_code,
            name=c_name,
            nominal=c_nominal,
            value=c_value,
            rate_mdl_per_unit=c_rate,
        )

    return ExchangeRateSet(
        effective_date=eff_date,
        retrieved_at=retrieved_at,
        currencies=currencies,
        source=source,
    )
