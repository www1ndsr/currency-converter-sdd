"""Currency conversion calculation engine using precise Decimal arithmetic."""

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from currency_converter.errors import CurrencyUnavailableError, ValidationError
from currency_converter.models import (
    BNM_SOURCE_NAME,
    ConversionRequest,
    ConversionResult,
    ExchangeRateSet,
    RateState,
)

TWO_PLACES = Decimal("0.01")


def quantize_amount(amount: Decimal) -> Decimal:
    """Quantize an amount to two decimal places using ROUND_HALF_UP."""
    if not isinstance(amount, Decimal) or not amount.is_finite():
        raise ValidationError("Amount to quantize must be a finite Decimal.")
    return amount.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def convert_currency(
    request: ConversionRequest,
    rate_set: Optional[ExchangeRateSet] = None,
    rate_state: RateState = RateState.LIVE,
) -> ConversionResult:
    """
    Execute conversion for request.
    
    If source_code == target_code:
        Returns entered amount rounded to 2 decimal places without requiring rate data.
        If rate_set is provided, preserves its provenance; otherwise rate_state is NOT_APPLICABLE.
        
    If cross-currency:
        Requires valid rate_set containing both currencies.
        Formula: amount * source_rate / target_rate.
        Quantized to 2 decimal places using ROUND_HALF_UP.
    """
    src_code = request.source_code.upper().strip()
    tgt_code = request.target_code.upper().strip()

    # Same-currency conversion fast path
    if src_code == tgt_code:
        quantized_result = quantize_amount(request.amount)
        if rate_set is not None:
            curr = rate_set.get_currency(src_code)
            src_rate = curr.rate_mdl_per_unit if curr else None
            return ConversionResult(
                amount_in_target=quantized_result,
                source_code=src_code,
                target_code=tgt_code,
                rate_state=rate_state,
                effective_date=rate_set.effective_date,
                source=rate_set.source,
                source_rate=src_rate,
                target_rate=src_rate,
            )
        return ConversionResult(
            amount_in_target=quantized_result,
            source_code=src_code,
            target_code=tgt_code,
            rate_state=RateState.NOT_APPLICABLE,
            effective_date=None,
            source=BNM_SOURCE_NAME,
            source_rate=None,
            target_rate=None,
        )

    # Cross-currency conversion requires a rate set
    if rate_set is None:
        raise CurrencyUnavailableError(
            f"Cannot convert from {src_code} to {tgt_code}: No exchange rates loaded."
        )

    source_curr = rate_set.get_currency(src_code)
    if source_curr is None:
        raise CurrencyUnavailableError(
            f"Source currency '{src_code}' is unavailable in the loaded exchange rates."
        )

    target_curr = rate_set.get_currency(tgt_code)
    if target_curr is None:
        raise CurrencyUnavailableError(
            f"Target currency '{tgt_code}' is unavailable in the loaded exchange rates."
        )

    # Formula: amount * source_rate / target_rate
    raw_converted = (request.amount * source_curr.rate_mdl_per_unit) / target_curr.rate_mdl_per_unit
    quantized_result = quantize_amount(raw_converted)

    return ConversionResult(
        amount_in_target=quantized_result,
        source_code=src_code,
        target_code=tgt_code,
        rate_state=rate_state,
        effective_date=rate_set.effective_date,
        source=rate_set.source,
        source_rate=source_curr.rate_mdl_per_unit,
        target_rate=target_curr.rate_mdl_per_unit,
    )
