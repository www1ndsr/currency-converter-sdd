"""Domain models for the Currency Converter application."""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, Optional

from currency_converter.errors import ValidationError, RateParsingError

BNM_SOURCE_NAME = "National Bank of Moldova (BNM)"
MDL_CURRENCY_CODE = "MDL"
MDL_CURRENCY_NAME = "Moldovan Leu"


class RateState(str, Enum):
    """Provenance state indicating how the rate set was obtained."""
    LIVE = "live"
    CACHED = "cached"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True)
class Currency:
    """Represents a validated currency and its normalized exchange rate."""
    code: str
    name: str
    nominal: Decimal
    value: Decimal
    rate_mdl_per_unit: Decimal

    def __post_init__(self) -> None:
        if not self.code or not isinstance(self.code, str) or not self.code.strip():
            raise RateParsingError("Currency code must be a non-empty string.")
        if not self.name or not isinstance(self.name, str) or not self.name.strip():
            raise RateParsingError("Currency name must be a non-empty string.")
        if not isinstance(self.nominal, Decimal) or not self.nominal.is_finite() or self.nominal <= 0:
            raise RateParsingError("Currency nominal must be a finite positive Decimal.")
        if not isinstance(self.value, Decimal) or not self.value.is_finite() or self.value <= 0:
            raise RateParsingError("Currency value must be a finite positive Decimal.")
        if not isinstance(self.rate_mdl_per_unit, Decimal) or not self.rate_mdl_per_unit.is_finite() or self.rate_mdl_per_unit <= 0:
            raise RateParsingError("Currency normalized rate must be a finite positive Decimal.")


@dataclass(frozen=True)
class ExchangeRateSet:
    """A complete, validated set of exchange rates from BNM for one effective date."""
    effective_date: date
    retrieved_at: datetime
    currencies: Dict[str, Currency]
    source: str = BNM_SOURCE_NAME

    def __post_init__(self) -> None:
        if not isinstance(self.effective_date, date):
            raise RateParsingError("ExchangeRateSet effective_date must be a valid date.")
        if not isinstance(self.retrieved_at, datetime):
            raise RateParsingError("ExchangeRateSet retrieved_at must be a valid datetime.")
        if not self.currencies or not isinstance(self.currencies, dict):
            raise RateParsingError("ExchangeRateSet currencies must be a non-empty dictionary.")
        if MDL_CURRENCY_CODE not in self.currencies:
            raise RateParsingError(f"ExchangeRateSet must include base currency {MDL_CURRENCY_CODE}.")
        mdl = self.currencies[MDL_CURRENCY_CODE]
        if mdl.rate_mdl_per_unit != Decimal("1"):
            raise RateParsingError(f"Base currency {MDL_CURRENCY_CODE} rate must be exactly 1.")

    def get_currency(self, code: str) -> Optional[Currency]:
        """Look up a currency by normalized uppercase code."""
        return self.currencies.get(code.upper().strip())


@dataclass(frozen=True)
class ConversionRequest:
    """User request to convert an amount between currencies."""
    amount: Decimal
    source_code: str
    target_code: str

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal) or not self.amount.is_finite() or self.amount <= 0:
            raise ValidationError("Conversion amount must be a finite positive Decimal.")
        if not self.source_code or not isinstance(self.source_code, str) or not self.source_code.strip():
            raise ValidationError("Source currency code is required.")
        if not self.target_code or not isinstance(self.target_code, str) or not self.target_code.strip():
            raise ValidationError("Target currency code is required.")


@dataclass(frozen=True)
class ConversionResult:
    """The result of converting an amount between currencies."""
    amount_in_target: Decimal
    source_code: str
    target_code: str
    rate_state: RateState
    effective_date: Optional[date] = None
    source: str = BNM_SOURCE_NAME
    source_rate: Optional[Decimal] = None
    target_rate: Optional[Decimal] = None

    def __post_init__(self) -> None:
        if not isinstance(self.amount_in_target, Decimal) or not self.amount_in_target.is_finite():
            raise ValidationError("Result amount must be a finite Decimal.")
