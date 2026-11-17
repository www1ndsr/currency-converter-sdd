# Data Model: Currency Converter

## Currency

Represents one BNM currency or the MDL base currency.

| Field | Type/format | Validation |
|---|---|---|
| `code` | ISO-like currency code string | Non-empty, normalized consistently (uppercase); unique within a rate set |
| `name` | String | Non-empty for BNM currencies; MDL may use `Moldovan Leu` |
| `nominal` | Positive Decimal | Required for BNM entries; greater than zero |
| `value` | Positive Decimal | Required for BNM entries; finite and greater than zero |
| `rate_mdl_per_unit` | Positive Decimal | `value / nominal`; MDL is exactly `1` |

The original BNM nominal and value are retained as decimal strings in persistent data so the
published values can be inspected without floating-point conversion. The normalized rate is
derived using Decimal arithmetic.

## Exchange-Rate Set

An internally consistent set of rates from one complete, successfully parsed BNM XML response.

| Field | Type/format | Validation |
|---|---|---|
| `effective_date` | Date (`YYYY-MM-DD` internally) | Parsed from the BNM document's `Date` attribute |
| `retrieved_at` | Timestamp with timezone | Time the complete response was retrieved successfully |
| `source` | String | `National Bank of Moldova (BNM)` |
| `currencies` | Map keyed by currency code | Complete valid parsed entries plus MDL base rate |

Rates from distinct XML responses are never combined. An empty response is not a rate set.

## Cached Rate Set

Persistent JSON collection of validated rate sets. Each successful response is appended as a
record containing rates as decimal strings, effective date, retrieval timestamp, and source. Cache
loading validates records before making rates available. Cache writes use atomic replacement and
occur only after a complete new rate set has passed validation. Offline fallback selects the most
recently retrieved valid record. Entries are not expired by this feature specification.

## Conversion Request

| Field | Type/format | Validation |
|---|---|---|
| `amount` | Positive finite Decimal | Reject empty, invalid syntax, zero, negative, NaN, and infinity |
| `source_code` | Currency code | Must be selected; must exist in the rate set except on the same-currency fast path |
| `target_code` | Currency code | Must be selected; must exist in the rate set except on the same-currency fast path |

Input accepts one decimal separator: comma or period. The parsing boundary converts accepted
decimal text to Decimal without passing through float; invalid/mixed separators are rejected.

## Conversion Result

| Field | Type/format | Description |
|---|---|---|
| `amount_in_target` | Decimal | `amount * source_rate / target_rate`, quantized for display to two decimal places |
| `source_code`, `target_code` | Currency codes | Currency pair selected by the user |
| `effective_date` | Date | Rate set date actually used; absent only for network-independent same-currency results if no rate set has ever been loaded |
| `source` | String | National Bank of Moldova (BNM) |
| `rate_state` | `live` or `cached` | How the rate set was obtained |

Same-currency requests return the entered positive amount rounded to two decimal places without
requiring rate data or a network request. If no rate set was used, the UI identifies the effective
rate date as not applicable for that conversion. When rate data is used, each result retains its
exact rate-set provenance.

## State and Validation Invariants

- Every rate set is all-or-nothing: invalid XML or any invalid required currency entry rejects that
  response.
- A failed response or failed cache save cannot invalidate or truncate the prior valid cache.
- MDL has an exact rate of `1` in every usable rate set.
- Currency codes are unique within each set; duplicate or conflicting codes invalidate the set.
- All amounts, nominal values, exchange values, and normalized rates remain Decimal values in
  calculations.
- A displayed result is never labeled live unless derived from the successful response used for
  that conversion.
