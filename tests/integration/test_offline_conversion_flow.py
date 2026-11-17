"""Integration tests for offline conversion flow and network fallback behavior."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock
import pytest

from currency_converter.bnm import BnmClient
from currency_converter.cache import CacheService
from currency_converter.errors import EmptyDateError, NetworkError, RateParsingError
from currency_converter.models import Currency, ExchangeRateSet, RateState
from currency_converter.orchestration import ConversionOrchestrator


@pytest.fixture
def sample_rate_set() -> ExchangeRateSet:
    return ExchangeRateSet(
        effective_date=date(2026, 11, 14),
        retrieved_at=datetime(2026, 11, 14, 10, 0, tzinfo=timezone.utc),
        currencies={
            "MDL": Currency("MDL", "Moldovan Leu", Decimal("1"), Decimal("1"), Decimal("1")),
            "EUR": Currency("EUR", "Euro", Decimal("1"), Decimal("20.1666"), Decimal("20.1666")),
            "USD": Currency("USD", "US Dollar", Decimal("1"), Decimal("18.5000"), Decimal("18.5000")),
        },
        source="National Bank of Moldova (BNM)",
    )


class TestNetworkAndFallbackBehavior:
    """Integration test suite covering live retrieval, multi-day fallback, cache, and error paths."""

    def test_successful_live_response_saved_to_cache(self, tmp_path: Path, sample_rate_set):
        cache_path = tmp_path / "rates.json"
        cache = CacheService(cache_path)
        mock_client = MagicMock(spec=BnmClient)
        mock_client.fetch_rates_for_date.return_value = sample_rate_set

        orchestrator = ConversionOrchestrator(bnm_client=mock_client, cache_service=cache)
        result = orchestrator.load_rates(target_date=date(2026, 11, 14))

        assert result.rate_state == RateState.LIVE
        assert result.effective_date == date(2026, 11, 14)
        assert result.error_message is None
        assert "Live official exchange rates loaded" in result.status_message

        # Assert data was persisted to cache
        cached = cache.load_latest_rate_set()
        assert cached is not None
        assert cached.effective_date == date(2026, 11, 14)

    def test_network_timeout_uses_cached_response(self, tmp_path: Path, sample_rate_set):
        cache_path = tmp_path / "rates.json"
        cache = CacheService(cache_path)
        cache.save_rate_set(sample_rate_set)

        mock_client = MagicMock(spec=BnmClient)
        mock_client.fetch_rates_for_date.side_effect = NetworkError("Request to BNM timed out")

        orchestrator = ConversionOrchestrator(bnm_client=mock_client, cache_service=cache)
        result = orchestrator.load_rates(target_date=date(2026, 11, 17))

        assert result.rate_state == RateState.CACHED
        assert result.effective_date == date(2026, 11, 14)
        assert result.error_message is None
        assert "Offline / Cached rates in use" in result.status_message
        assert orchestrator.active_rate_set is not None

        # Conversion works seamlessly using cached rates
        conv = orchestrator.convert("100", "EUR", "MDL")
        assert conv.amount_in_target == Decimal("2016.66")
        assert conv.rate_state == RateState.CACHED
        assert conv.effective_date == date(2026, 11, 14)

    def test_http_error_uses_cached_response(self, tmp_path: Path, sample_rate_set):
        cache_path = tmp_path / "rates.json"
        cache = CacheService(cache_path)
        cache.save_rate_set(sample_rate_set)

        mock_client = MagicMock(spec=BnmClient)
        mock_client.fetch_rates_for_date.side_effect = NetworkError("BNM returned HTTP status 503")

        orchestrator = ConversionOrchestrator(bnm_client=mock_client, cache_service=cache)
        result = orchestrator.load_rates(target_date=date(2026, 11, 17))

        assert result.rate_state == RateState.CACHED
        assert result.effective_date == date(2026, 11, 14)

    def test_network_failure_with_no_cache_available(self, tmp_path: Path):
        cache_path = tmp_path / "non_existent.json"
        cache = CacheService(cache_path)

        mock_client = MagicMock(spec=BnmClient)
        mock_client.fetch_rates_for_date.side_effect = NetworkError("Connection refused")

        orchestrator = ConversionOrchestrator(bnm_client=mock_client, cache_service=cache)
        result = orchestrator.load_rates(target_date=date(2026, 11, 17))

        assert result.rate_state == RateState.NOT_APPLICABLE
        assert result.error_message is not None
        assert "no local cached rates are available" in result.error_message

        # Application remains alive and operational for same-currency conversions
        same_conv = orchestrator.convert("50,25", "MDL", "MDL")
        assert same_conv.amount_in_target == Decimal("50.25")
        assert same_conv.rate_state == RateState.NOT_APPLICABLE
        assert same_conv.effective_date is None

    def test_empty_bnm_response_searches_backward_up_to_previous_valid_date(self, tmp_path: Path, sample_rate_set):
        # Target date is Monday (2026-11-16), Sunday and Saturday are empty, Friday (2026-11-13) has rates
        cache_path = tmp_path / "rates.json"
        cache = CacheService(cache_path)

        friday_date = date(2026, 11, 13)
        friday_rates = ExchangeRateSet(
            effective_date=friday_date,
            retrieved_at=datetime(2026, 11, 13, 10, 0, tzinfo=timezone.utc),
            currencies=sample_rate_set.currencies,
        )

        requested_date = date(2026, 11, 16)

        def mock_fetch(d):
            if d == requested_date:
                raise EmptyDateError("Empty date")
            if d == requested_date - timedelta(days=1):
                raise EmptyDateError("Empty date")
            if d == requested_date - timedelta(days=2):
                raise EmptyDateError("Empty date")
            if d == friday_date:
                return friday_rates
            raise EmptyDateError("Empty date")

        mock_client = MagicMock(spec=BnmClient)
        mock_client.fetch_rates_for_date.side_effect = mock_fetch

        orchestrator = ConversionOrchestrator(bnm_client=mock_client, cache_service=cache)
        result = orchestrator.load_rates(target_date=requested_date)

        assert result.rate_state == RateState.LIVE
        assert result.effective_date == friday_date
        assert result.date_differs is True
        assert "searched backward 3 days" in result.status_message
        assert mock_client.fetch_rates_for_date.call_count == 4

    def test_search_limit_exhausted_falls_back_to_cache(self, tmp_path: Path, sample_rate_set):
        cache_path = tmp_path / "rates.json"
        cache = CacheService(cache_path)
        cache.save_rate_set(sample_rate_set)

        mock_client = MagicMock(spec=BnmClient)
        # Always return EmptyDateError for all 15 attempts
        mock_client.fetch_rates_for_date.side_effect = EmptyDateError("Empty")

        orchestrator = ConversionOrchestrator(bnm_client=mock_client, cache_service=cache)
        result = orchestrator.load_rates(target_date=date(2026, 11, 17))

        assert result.rate_state == RateState.CACHED
        assert result.effective_date == sample_rate_set.effective_date
        assert mock_client.fetch_rates_for_date.call_count == 15  # Day 0 to 14

    def test_malformed_xml_response_does_not_overwrite_valid_cache(self, tmp_path: Path, sample_rate_set):
        cache_path = tmp_path / "rates.json"
        cache = CacheService(cache_path)
        cache.save_rate_set(sample_rate_set)

        mock_client = MagicMock(spec=BnmClient)
        mock_client.fetch_rates_for_date.side_effect = RateParsingError("Truncated XML received")

        orchestrator = ConversionOrchestrator(bnm_client=mock_client, cache_service=cache)
        result = orchestrator.load_rates(target_date=date(2026, 11, 17))

        # Falls back to cache
        assert result.rate_state == RateState.CACHED
        assert result.effective_date == sample_rate_set.effective_date

        # Cache remains uncorrupted
        loaded = cache.load_latest_rate_set()
        assert loaded is not None
        assert loaded.effective_date == sample_rate_set.effective_date
        assert loaded.currencies["EUR"].rate_mdl_per_unit == Decimal("20.1666")
