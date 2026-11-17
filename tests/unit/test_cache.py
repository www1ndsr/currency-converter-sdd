"""Unit tests for local cache service in currency_converter.cache."""

from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
import json
import pytest

from currency_converter.cache import CacheService
from currency_converter.errors import CacheError
from currency_converter.models import Currency, ExchangeRateSet


@pytest.fixture
def rate_set_nov17() -> ExchangeRateSet:
    return ExchangeRateSet(
        effective_date=date(2026, 11, 17),
        retrieved_at=datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc),
        currencies={
            "MDL": Currency("MDL", "Moldovan Leu", Decimal("1"), Decimal("1"), Decimal("1")),
            "EUR": Currency("EUR", "Euro", Decimal("1"), Decimal("20.1666"), Decimal("20.1666")),
        },
    )


@pytest.fixture
def rate_set_nov16() -> ExchangeRateSet:
    return ExchangeRateSet(
        effective_date=date(2026, 11, 16),
        retrieved_at=datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc),
        currencies={
            "MDL": Currency("MDL", "Moldovan Leu", Decimal("1"), Decimal("1"), Decimal("1")),
            "EUR": Currency("EUR", "Euro", Decimal("1"), Decimal("20.1500"), Decimal("20.1500")),
        },
    )


class TestCacheService:
    """Test suite for cache persistence, reinitialization, and atomic replacement."""

    def test_load_from_non_existent_file_returns_none(self, tmp_path: Path):
        cache_path = tmp_path / "rates_cache.json"
        service = CacheService(cache_path)

        assert service.load_latest_rate_set() is None
        assert service.load_all_rate_sets() == []

    def test_save_and_load_latest_rate_set(self, tmp_path: Path, rate_set_nov17):
        cache_path = tmp_path / "rates_cache.json"
        service = CacheService(cache_path)

        service.save_rate_set(rate_set_nov17)
        loaded = service.load_latest_rate_set()

        assert loaded is not None
        assert loaded.effective_date == date(2026, 11, 17)
        assert loaded.source == "National Bank of Moldova (BNM)"
        assert loaded.currencies["EUR"].rate_mdl_per_unit == Decimal("20.1666")
        assert isinstance(loaded.currencies["EUR"].rate_mdl_per_unit, Decimal)

    def test_load_rates_after_service_reinitialization(self, tmp_path: Path, rate_set_nov17):
        cache_path = tmp_path / "rates_cache.json"

        # First instance saves
        service1 = CacheService(cache_path)
        service1.save_rate_set(rate_set_nov17)

        # Fresh second instance loads
        service2 = CacheService(cache_path)
        loaded = service2.load_latest_rate_set()

        assert loaded is not None
        assert loaded.effective_date == date(2026, 11, 17)
        assert loaded.currencies["EUR"].value == Decimal("20.1666")

    def test_preserve_effective_date_and_select_most_recent(self, tmp_path: Path, rate_set_nov16, rate_set_nov17):
        cache_path = tmp_path / "rates_cache.json"
        service = CacheService(cache_path)

        # Save earlier date first, then later date
        service.save_rate_set(rate_set_nov16)
        service.save_rate_set(rate_set_nov17)

        all_sets = service.load_all_rate_sets()
        assert len(all_sets) == 2

        latest = service.load_latest_rate_set()
        assert latest is not None
        assert latest.effective_date == date(2026, 11, 17)
        assert latest.currencies["EUR"].rate_mdl_per_unit == Decimal("20.1666")

    def test_cache_uses_decimal_strings_in_json(self, tmp_path: Path, rate_set_nov17):
        cache_path = tmp_path / "rates_cache.json"
        service = CacheService(cache_path)
        service.save_rate_set(rate_set_nov17)

        with open(cache_path, "r", encoding="utf-8") as f:
            raw_json = json.load(f)

        eur_raw = raw_json["rate_sets"][0]["currencies"]["EUR"]
        assert isinstance(eur_raw["rate_mdl_per_unit"], str)
        assert eur_raw["rate_mdl_per_unit"] == "20.1666"

    def test_corrupted_cache_raises_cache_error_on_load(self, tmp_path: Path):
        cache_path = tmp_path / "corrupt_cache.json"
        cache_path.write_text("{ this is not valid json }", encoding="utf-8")

        service = CacheService(cache_path)
        with pytest.raises(CacheError, match="Error reading cache file"):
            service.load_all_rate_sets()

    def test_preserve_previous_valid_cache_after_failed_update(self, tmp_path: Path, rate_set_nov17):
        cache_path = tmp_path / "rates_cache.json"
        service = CacheService(cache_path)

        # 1. Save valid cache
        service.save_rate_set(rate_set_nov17)
        original_mtime = cache_path.stat().st_mtime
        original_content = cache_path.read_text(encoding="utf-8")

        # 2. Attempt saving an invalid object that raises an error during write
        with pytest.raises(Exception):
            # Pass something that causes serialization to fail
            service.save_rate_set(None)

        # 3. Assert previous valid cache file is completely intact
        assert cache_path.exists()
        assert cache_path.read_text(encoding="utf-8") == original_content

        # No leftover temporary files
        temp_file = cache_path.with_name(f"{cache_path.name}.tmp")
        assert not temp_file.exists()
