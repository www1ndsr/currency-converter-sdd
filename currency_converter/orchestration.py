"""Application orchestration layer coordinating BNM client, cache, conversion, and validation."""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional

from currency_converter.bnm import BnmClient
from currency_converter.cache import CacheService
from currency_converter.conversion import convert_currency
from currency_converter.errors import (
    CacheError,
    CurrencyConverterError,
    CurrencyUnavailableError,
    EmptyDateError,
    NetworkError,
    RateParsingError,
    ValidationError,
)
from currency_converter.models import (
    BNM_SOURCE_NAME,
    MDL_CURRENCY_CODE,
    ConversionRequest,
    ConversionResult,
    Currency,
    ExchangeRateSet,
    RateState,
)
from currency_converter.validation import parse_and_validate_amount, validate_currency_code

MAX_BACKWARD_SEARCH_DAYS = 14


@dataclass
class RateRetrievalResult:
    """Encapsulates the outcome of an exchange-rate loading operation."""
    rate_set: Optional[ExchangeRateSet]
    rate_state: RateState
    requested_date: date
    effective_date: Optional[date]
    date_differs: bool = False
    status_message: str = ""
    error_message: Optional[str] = None


class ConversionOrchestrator:
    """Coordinates business logic across BNM retrieval, cache, and conversions."""

    def __init__(
        self,
        bnm_client: Optional[BnmClient] = None,
        cache_service: Optional[CacheService] = None,
    ):
        self.bnm_client = bnm_client or BnmClient()
        self.cache_service = cache_service or CacheService()
        self.active_rate_set: Optional[ExchangeRateSet] = None
        self.active_rate_state: RateState = RateState.NOT_APPLICABLE
        self.last_status_message: str = ""

    def load_rates(self, target_date: Optional[date] = None) -> RateRetrievalResult:
        """
        Load exchange rates for target_date (default: today).
        
        Attempts live BNM retrieval with up to 14-calendar-day backward search
        for empty dates (weekends/holidays).
        
        Falls back to local cache upon network failure.
        Rejects malformed XML without overwriting or corrupting cache.
        """
        req_date = target_date or date.today()

        # Step 1: Attempt live BNM fetch with backward search for empty dates
        try:
            return self._fetch_live_with_backward_search(req_date)
        except NetworkError as net_err:
            # Network failed; attempt fallback to local cache
            return self._fallback_to_cache(req_date, reason=f"Network error: {net_err.message}")
        except RateParsingError as parse_err:
            # BNM returned malformed XML or invalid rates
            # Spec: Do not overwrite cache; show clear error; can fallback to cache if available
            return self._fallback_to_cache(
                req_date,
                reason=f"Official rate data from BNM was invalid or malformed: {parse_err.message}",
            )
        except Exception as exc:
            return self._fallback_to_cache(req_date, reason=f"Unexpected error loading rates: {exc}")

    def _fetch_live_with_backward_search(self, req_date: date) -> RateRetrievalResult:
        """Search backward up to 14 calendar days if BNM returns an empty response."""
        curr_date = req_date
        days_searched = 0

        while days_searched <= MAX_BACKWARD_SEARCH_DAYS:
            try:
                rate_set = self.bnm_client.fetch_rates_for_date(curr_date)

                # Successfully parsed a valid rate set
                # Save to local persistent cache
                try:
                    self.cache_service.save_rate_set(rate_set)
                except CacheError:
                    # Cache write failure should not crash or stop application
                    pass

                self.active_rate_set = rate_set
                self.active_rate_state = RateState.LIVE

                date_differs = (rate_set.effective_date != req_date)
                if date_differs:
                    msg = (
                        f"Live rates loaded for {rate_set.effective_date.strftime('%d.%m.%Y')} "
                        f"(No rates published for {req_date.strftime('%d.%m.%Y')}; "
                        f"searched backward {days_searched} day{'s' if days_searched != 1 else ''})."
                    )
                else:
                    msg = f"Live official exchange rates loaded for {rate_set.effective_date.strftime('%d.%m.%Y')}."

                self.last_status_message = msg
                return RateRetrievalResult(
                    rate_set=rate_set,
                    rate_state=RateState.LIVE,
                    requested_date=req_date,
                    effective_date=rate_set.effective_date,
                    date_differs=date_differs,
                    status_message=msg,
                )

            except EmptyDateError:
                # BNM returned empty body or no rates for this date; try previous day
                days_searched += 1
                curr_date = req_date - timedelta(days=days_searched)
                continue
            # NetworkError and RateParsingError are re-raised to stop backward search

        # If we exhausted 14 days with empty responses, fall back to cache
        return self._fallback_to_cache(
            req_date,
            reason=f"No official rates found within {MAX_BACKWARD_SEARCH_DAYS} days of {req_date.strftime('%d.%m.%Y')}.",
        )

    def _fallback_to_cache(self, req_date: date, reason: str) -> RateRetrievalResult:
        """Attempt to load the latest valid cached exchange-rate set."""
        cached_set: Optional[ExchangeRateSet] = None
        try:
            cached_set = self.cache_service.load_latest_rate_set()
        except CacheError as cache_err:
            # Cache is corrupted or unreadable
            err_msg = f"{reason}. Local cache could not be read: {cache_err.message}"
            self.last_status_message = err_msg
            return RateRetrievalResult(
                rate_set=None,
                rate_state=RateState.NOT_APPLICABLE,
                requested_date=req_date,
                effective_date=None,
                date_differs=False,
                status_message=err_msg,
                error_message=err_msg,
            )

        if cached_set is not None:
            self.active_rate_set = cached_set
            self.active_rate_state = RateState.CACHED
            msg = (
                f"Offline / Cached rates in use for {cached_set.effective_date.strftime('%d.%m.%Y')} "
                f"({reason})."
            )
            self.last_status_message = msg
            return RateRetrievalResult(
                rate_set=cached_set,
                rate_state=RateState.CACHED,
                requested_date=req_date,
                effective_date=cached_set.effective_date,
                date_differs=(cached_set.effective_date != req_date),
                status_message=msg,
            )

        # No cache available
        err_msg = (
            f"Unable to retrieve exchange rates ({reason}) and no local cached rates are available. "
            "Please check your network connection."
        )
        self.last_status_message = err_msg
        return RateRetrievalResult(
            rate_set=None,
            rate_state=RateState.NOT_APPLICABLE,
            requested_date=req_date,
            effective_date=None,
            date_differs=False,
            status_message=err_msg,
            error_message=err_msg,
        )

    def convert(
        self,
        raw_amount: Optional[str],
        source_code: Optional[str],
        target_code: Optional[str],
    ) -> ConversionResult:
        """
        Validate inputs and perform currency conversion.
        
        Same-currency conversion operates without rate data if no rates are loaded.
        Cross-currency conversion requires an active rate set.
        """
        amount = parse_and_validate_amount(raw_amount)
        src = validate_currency_code(source_code, "Source currency")
        tgt = validate_currency_code(target_code, "Target currency")

        req = ConversionRequest(amount=amount, source_code=src, target_code=tgt)
        return convert_currency(
            request=req,
            rate_set=self.active_rate_set,
            rate_state=self.active_rate_state,
        )

    def get_available_currencies(self) -> List[Currency]:
        """
        Get sorted list of available currencies for the UI dropdowns.
        
        MDL, EUR, USD are ordered first, followed by alphabetical order.
        If no rates are loaded, returns at least MDL.
        """
        if self.active_rate_set is None:
            return [
                Currency(
                    code=MDL_CURRENCY_CODE,
                    name="Moldovan Leu",
                    nominal=Decimal("1"),
                    value=Decimal("1"),
                    rate_mdl_per_unit=Decimal("1"),
                )
            ]

        preferred = [MDL_CURRENCY_CODE, "EUR", "USD", "RON", "UAH", "GBP"]
        currencies = list(self.active_rate_set.currencies.values())

        def sort_key(c: Currency):
            try:
                idx = preferred.index(c.code)
                return (0, idx, c.code)
            except ValueError:
                return (1, 0, c.code)

        return sorted(currencies, key=sort_key)
