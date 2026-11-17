"""Unit tests for currency conversion logic in currency_converter.conversion."""

from datetime import date, datetime, timezone
from decimal import Decimal
import pytest

from currency_converter.conversion import convert_currency, quantize_amount
from currency_converter.errors import CurrencyUnavailableError, ValidationError
from currency_converter.models import (
    Currency,
    ExchangeRateSet,
    ConversionRequest,
    RateState,
)


@pytest.fixture
def sample_rate_set() -> ExchangeRateSet:
    """Fixture providing a deterministic exchange-rate set for testing."""
    currencies = {
        "MDL": Currency(
            code="MDL",
            name="Moldovan Leu",
            nominal=Decimal("1"),
            value=Decimal("1"),
            rate_mdl_per_unit=Decimal("1"),
        ),
        "EUR": Currency(
            code="EUR",
            name="Euro",
            nominal=Decimal("1"),
            value=Decimal("20.1666"),
            rate_mdl_per_unit=Decimal("20.1666"),
        ),
        "USD": Currency(
            code="USD",
            name="US Dollar",
            nominal=Decimal("1"),
            value=Decimal("18.5000"),
            rate_mdl_per_unit=Decimal("18.5000"),
        ),
        "JPY": Currency(
            code="JPY",
            name="Japanese Yen",
            nominal=Decimal("100"),
            value=Decimal("12.2500"),
            rate_mdl_per_unit=Decimal("0.1225"),
        ),
    }
    return ExchangeRateSet(
        effective_date=date(2026, 11, 17),
        retrieved_at=datetime(2026, 11, 17, 10, 0, tzinfo=timezone.utc),
        currencies=currencies,
        source="National Bank of Moldova (BNM)",
    )


class TestCurrencyConversion:
    """Test suite for conversion arithmetic, rounding, and rate state."""

    def test_quantize_amount_round_half_up(self):
        # Test standard rounding half up to 2 decimal places
        assert quantize_amount(Decimal("10.124")) == Decimal("10.12")
        assert quantize_amount(Decimal("10.125")) == Decimal("10.13")
        assert quantize_amount(Decimal("10.126")) == Decimal("10.13")
        assert quantize_amount(Decimal("10.135")) == Decimal("10.14")
        assert quantize_amount(Decimal("10.145")) == Decimal("10.15")

    def test_eur_to_mdl(self, sample_rate_set):
        # 100 EUR * 20.1666 / 1 = 2016.66 MDL
        req = ConversionRequest(amount=Decimal("100"), source_code="EUR", target_code="MDL")
        result = convert_currency(req, sample_rate_set, rate_state=RateState.LIVE)

        assert result.amount_in_target == Decimal("2016.66")
        assert result.source_code == "EUR"
        assert result.target_code == "MDL"
        assert result.effective_date == date(2026, 11, 17)
        assert result.rate_state == RateState.LIVE
        assert result.source == "National Bank of Moldova (BNM)"

    def test_mdl_to_eur(self, sample_rate_set):
        # 100 MDL * 1 / 20.1666 = 4.958694... -> 4.96 EUR
        req = ConversionRequest(amount=Decimal("100"), source_code="MDL", target_code="EUR")
        result = convert_currency(req, sample_rate_set, rate_state=RateState.LIVE)

        assert result.amount_in_target == Decimal("4.96")
        assert result.source_code == "MDL"
        assert result.target_code == "EUR"
        assert result.effective_date == date(2026, 11, 17)

    def test_eur_to_usd_cross_currency(self, sample_rate_set):
        # 100 EUR * 20.1666 / 18.5000 = 109.008648... -> 109.01 USD
        req = ConversionRequest(amount=Decimal("100"), source_code="EUR", target_code="USD")
        result = convert_currency(req, sample_rate_set, rate_state=RateState.LIVE)

        assert result.amount_in_target == Decimal("109.01")
        assert result.source_code == "EUR"
        assert result.target_code == "USD"

    def test_usd_to_eur_reverse_direction(self, sample_rate_set):
        # 100 USD * 18.5000 / 20.1666 = 91.7358... -> 91.74 EUR
        req = ConversionRequest(amount=Decimal("100"), source_code="USD", target_code="EUR")
        result = convert_currency(req, sample_rate_set, rate_state=RateState.LIVE)

        assert result.amount_in_target == Decimal("91.74")
        assert result.source_code == "USD"
        assert result.target_code == "EUR"

    def test_currency_with_nominal_greater_than_one(self, sample_rate_set):
        # JPY has nominal 100, value 12.2500 -> rate_mdl_per_unit = 0.1225
        # 1000 JPY * 0.1225 / 1 = 122.50 MDL
        req = ConversionRequest(amount=Decimal("1000"), source_code="JPY", target_code="MDL")
        result = convert_currency(req, sample_rate_set)

        assert result.amount_in_target == Decimal("122.50")

    def test_same_currency_with_rate_set(self, sample_rate_set):
        # 50.555 EUR -> 50.56 EUR with rate_set provenance
        req = ConversionRequest(amount=Decimal("50.555"), source_code="EUR", target_code="EUR")
        result = convert_currency(req, sample_rate_set, rate_state=RateState.CACHED)

        assert result.amount_in_target == Decimal("50.56")
        assert result.effective_date == date(2026, 11, 17)
        assert result.rate_state == RateState.CACHED

    def test_same_currency_without_rate_set(self):
        # Same-currency fast path when no rates have been loaded
        req = ConversionRequest(amount=Decimal("123.456"), source_code="MDL", target_code="MDL")
        result = convert_currency(req, rate_set=None)

        assert result.amount_in_target == Decimal("123.46")
        assert result.effective_date is None
        assert result.rate_state == RateState.NOT_APPLICABLE
        assert result.source == "National Bank of Moldova (BNM)"

    def test_missing_source_currency_raises_error(self, sample_rate_set):
        req = ConversionRequest(amount=Decimal("100"), source_code="GBP", target_code="MDL")
        with pytest.raises(CurrencyUnavailableError, match="Source currency 'GBP' is unavailable"):
            convert_currency(req, sample_rate_set)

    def test_missing_target_currency_raises_error(self, sample_rate_set):
        req = ConversionRequest(amount=Decimal("100"), source_code="MDL", target_code="CHF")
        with pytest.raises(CurrencyUnavailableError, match="Target currency 'CHF' is unavailable"):
            convert_currency(req, sample_rate_set)

    def test_cross_currency_without_rate_set_raises_error(self):
        req = ConversionRequest(amount=Decimal("100"), source_code="EUR", target_code="MDL")
        with pytest.raises(CurrencyUnavailableError, match="No exchange rates loaded"):
            convert_currency(req, rate_set=None)
