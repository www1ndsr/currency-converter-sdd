# BNM XML Data Contract

## Request

- **Provider**: National Bank of Moldova (BNM)
- **Endpoint**:
  `https://www.bnm.md/en/official_exchange_rates?get_xml=1&date=DD.MM.YYYY`
- **Method**: HTTP GET
- **Date parameter**: Requested date formatted as `DD.MM.YYYY`
- **Timeout**: The request must have a finite timeout. The exact timeout value is an implementation
  configuration decision and must be documented.

## Successful Response Shape

The observed official response is XML with a `ValCurs` root, a `Date` attribute identifying the
effective rate date, and one or more `Valute` child records. Each usable `Valute` includes:

| XML element/attribute | Meaning | Required validation |
|---|---|---|
| `ValCurs/@Date` | Effective date | Required and parseable as a calendar date |
| `Valute/@ID` | BNM record identifier | Not used as the user-facing currency key |
| `Valute/CharCode` | Currency code | Required, non-empty, unique |
| `Valute/Name` | Currency name | Required, non-empty |
| `Valute/Nominal` | Units represented by `Value` | Required finite positive decimal |
| `Valute/Value` | Published MDL value for the nominal quantity | Required finite positive decimal |

`NumCode` may be present but is not required for conversion. MDL is supplied by the application as
the base currency with a rate of exactly one.

## Rate Interpretation

Each BNM value is denominated in MDL for the stated nominal number of foreign currency units.
Normalize a currency rate to MDL per one unit:

```text
rate_mdl_per_unit = Decimal(Value) / Decimal(Nominal)
```

Example: `Nominal=10`, `Value=2.2237` yields `0.22237` MDL per one unit.

For two selected currencies:

```text
amount_in_target = amount * source_rate_mdl_per_unit / target_rate_mdl_per_unit
```

Do not round intermediate rates or calculations. Quantize the displayed result to two decimal
places using the plan's documented `ROUND_HALF_UP` policy.

## Empty, Invalid, and Failure Responses

- An empty body or a valid response with no rate records means no rate was published for that
  requested date; the application may request previous calendar dates, up to 14 calendar days
  earlier.
- HTTP errors, timeouts, connection failures, malformed XML, missing effective date, duplicate
  currency codes, missing required fields, invalid/nonpositive nominal or value, or partial
  invalidity are not empty-date responses. They fail the complete request and must not be cached.
- A response is accepted and cached only if the entire rate set is valid. Do not combine entries
  from separate response dates or fill invalid records from cache.
- The result's effective date must come from the successful response's `ValCurs/@Date`.
- The source label is `National Bank of Moldova (BNM)`.

## Mocking Requirements

Tests must substitute the HTTP response boundary and cover status codes, timeout/connection
failure, empty body, valid XML, malformed/truncated XML, missing fields, invalid decimal values,
partial records, and conflicting dates. Tests must not call the live BNM service.
