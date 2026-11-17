"""Local persistent JSON cache service for validated BNM exchange-rate sets."""

import json
import os
from pathlib import Path
from typing import List, Optional

from currency_converter.errors import CacheError
from currency_converter.models import ExchangeRateSet
from currency_converter.serialization import dict_to_rate_set, rate_set_to_dict

DEFAULT_CACHE_DIR = Path.home() / ".currency_converter"
DEFAULT_CACHE_FILE = DEFAULT_CACHE_DIR / "rates_cache.json"


class CacheService:
    """Manages reading and writing validated exchange-rate sets to a JSON file."""

    def __init__(self, cache_file_path: Optional[Path] = None):
        self.cache_file = cache_file_path or DEFAULT_CACHE_FILE

    def _ensure_dir(self) -> None:
        """Ensure parent directory exists."""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise CacheError(f"Could not create cache directory {self.cache_file.parent}: {exc}") from exc

    def load_all_rate_sets(self) -> List[ExchangeRateSet]:
        """
        Load and validate all rate-set records from the JSON cache file.
        
        Returns an empty list if cache file does not exist.
        Raises CacheError if file is corrupted or unreadable.
        """
        if not self.cache_file.exists():
            return []

        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                raw_data = json.loads(content)
        except (json.JSONDecodeError, OSError) as exc:
            raise CacheError(f"Error reading cache file {self.cache_file}: {exc}") from exc

        if not isinstance(raw_data, dict) or "rate_sets" not in raw_data:
            raise CacheError("Invalid cache structure: expected object with 'rate_sets' array.")

        raw_list = raw_data["rate_sets"]
        if not isinstance(raw_list, list):
            raise CacheError("Invalid cache structure: 'rate_sets' must be a list.")

        valid_sets: List[ExchangeRateSet] = []
        for item in raw_list:
            try:
                rate_set = dict_to_rate_set(item)
                valid_sets.append(rate_set)
            except Exception as exc:
                # If a record in the cache is malformed, log or raise CacheError
                raise CacheError(f"Malformed rate set in cache: {exc}") from exc

        return valid_sets

    def load_latest_rate_set(self) -> Optional[ExchangeRateSet]:
        """
        Retrieve the most recently retrieved valid exchange-rate set from cache.
        
        Returns None if cache does not exist or has no valid entries.
        """
        rate_sets = self.load_all_rate_sets()
        if not rate_sets:
            return None

        # Sort by retrieved_at descending (or effective_date if retrieved_at is equal)
        sorted_sets = sorted(rate_sets, key=lambda s: (s.retrieved_at, s.effective_date), reverse=True)
        return sorted_sets[0]

    def save_rate_set(self, new_rate_set: ExchangeRateSet) -> None:
        """
        Save a validated ExchangeRateSet to the JSON cache.
        
        Uses atomic file replacement via a temporary sibling file to guarantee
        that existing valid cache data is never truncated or corrupted on crash.
        """
        self._ensure_dir()

        # Load existing rate sets if cache file exists
        existing_sets: List[ExchangeRateSet] = []
        if self.cache_file.exists():
            try:
                existing_sets = self.load_all_rate_sets()
            except CacheError:
                # If existing cache is unreadable, preserve it as a backup rather than deleting
                backup_path = self.cache_file.with_suffix(".corrupt.bak")
                try:
                    self.cache_file.rename(backup_path)
                except OSError:
                    pass
                existing_sets = []

        # Remove previous entry for the same effective date if already present, to update with latest retrieval
        filtered_sets = [s for s in existing_sets if s.effective_date != new_rate_set.effective_date]
        filtered_sets.append(new_rate_set)

        payload = {
            "rate_sets": [rate_set_to_dict(s) for s in filtered_sets]
        }

        temp_file = self.cache_file.with_name(f"{self.cache_file.name}.tmp")

        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())

            # Atomic replace
            os.replace(temp_file, self.cache_file)
        except OSError as exc:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass
            raise CacheError(f"Failed to atomically write cache file: {exc}") from exc
