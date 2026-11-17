# Implementation Plan: Currency Converter

**Branch**: `001-currency-converter` | **Date**: 2026-11-17 | **Spec**:
[spec.md](./spec.md)

**Input**: Approved feature specification in `specs/001-currency-converter/spec.md`

## Summary

Build a desktop currency converter that retrieves official daily exchange rates from the National
Bank of Moldova (BNM), normalizes them to MDL per currency unit, and performs precise Decimal
conversions. Keep the graphical interface, BNM integration, conversion rules, persistent JSON
cache, and orchestration independent enough to test without network access. The interface remains
responsive during retrieval and always distinguishes live and cached rate data.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: CustomTkinter, requests, xml.etree.ElementTree, decimal.Decimal,
pathlib, json

**Storage**: Local JSON cache in the user's application data directory; cache path is injectable
for tests.

**Testing**: pytest; unittest.mock or pytest monkeypatch for HTTP and filesystem boundaries

**Target Platform**: Desktop environments supported by Python and CustomTkinter

**Project Type**: Desktop application

**Performance Goals**: Keep the UI event loop responsive during network access; show loading
feedback immediately; no hard conversion latency target is specified.

**Constraints**: Use Decimal throughout parsing, normalization, calculation, and rounding.
Network timeouts and expected HTTP, XML, validation, and cache failures must be surfaced as
recoverable user-facing states. HTTP calls must not execute on the UI event loop. Cache writes
must preserve the last valid data if a new response cannot be validated or saved.

**Scale/Scope**: Single-user desktop application; one conversion window; BNM rate set with a small
number of currencies; local persistent cache; no user account, server, or multi-device sync.

## Constitution Check

| Principle | Design evidence | Gate |
|---|---|---|
| Specification-first | This plan traces requirements to the approved spec; implementation follows tasks derived from it. | PASS |
| Precise financial calculations | Decimal-only amount, rate, normalization, calculation, and defined display quantization. | PASS |
| Failure resilience | Typed expected failures and UI states for network, response, XML, and cache errors. | PASS |
| Data transparency | Every rate-based result carries BNM source, effective date, and live/cache state; a same-currency result with no rate set says date is not applicable. | PASS |
| Offline resilience | Validated rate sets persist locally and remain loadable after restart. | PASS |
| Input validation | A dedicated validation boundary rejects invalid or non-finite amounts before calculation. | PASS |
| Maintainable architecture | UI, orchestration, BNM access, conversion, and cache responsibilities are separated. | PASS |
| Testability | HTTP and cache paths are injectable; automated tests do not require live BNM access. | PASS |
| User experience | Desktop UI includes disabled/loading/error/result states and stays responsive. | PASS |
| Documentation | README and REPORT are required implementation deliverables; quickstart is defined here. | PASS |

No constitution violations or unresolved technical choices block design.

## Architecture

Use a single Python application with one-way dependency flow:

1. **Presentation** owns the CustomTkinter window, amount and currency controls, result, provenance,
   loading indication, and user-facing errors. It delegates actions to orchestration and renders
   returned state; it does not parse XML, perform HTTP requests, or calculate rates.
2. **Application orchestration** coordinates input validation, rate loading, cache fallback,
   conversion, and presentation state. It owns the network-worker lifecycle and returns
   completions to the UI thread through a thread-safe handoff.
3. **BNM data service** builds the date-specific request, enforces an HTTP timeout, checks the
   response, parses and validates the complete XML rate set, and returns the effective date and
   normalized Decimal rates. It has no GUI or cache responsibilities.
4. **Conversion service** accepts a validated amount and rate set and applies the same-currency
   fast path or `amount * source_rate / target_rate`. It rounds only the displayed result to two
   decimal places using `ROUND_HALF_UP`; intermediate calculations remain Decimal.
5. **Cache service** reads and writes JSON at an injected `pathlib.Path`. It validates loaded
   records, serializes Decimals as strings, and appends every fully validated response as a
   rate-set record. Use a temporary sibling file and atomic replacement for writes so interruption
   cannot truncate the last valid cache. For offline fallback, select the most recently retrieved
   valid record.

Expected failures are represented distinctly at service boundaries (network/timeout, HTTP status,
empty response, invalid XML or rate set, unsupported currency, invalid amount, and cache
unavailable/corrupt). Orchestration maps them to plain-language UI messages and appropriate
fallback behavior. Unexpected programming errors are not disguised as successful results.

### Rate Retrieval Flow

For a selected/requested date, request BNM data and validate the response. An empty response causes
backward requests one calendar day at a time, checking the requested day and then previous days up
to 14 calendar days earlier. A malformed or partially valid response is an error, not an empty
date, and is not merged with any other response. On a network failure, automatically use the
latest valid cached rate set if available and label it as cached; otherwise show an offline error.
Only a fully valid response is saved. The effective date comes from the `Date` attribute of the
successful BNM XML document.

### Concurrency and UI State

Network calls, including backward-date checks, run on a worker thread. Only the UI thread updates
widgets. While a request is active, show loading feedback and keep the window interactive. A
completed request returns a single coherent rate set and provenance state; do not show results
assembled from different requests. Same-currency conversion validates the amount but does not wait
for or initiate network access.

## Project Structure

### Documentation (this feature)

```text
specs/001-currency-converter/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── bnm-xml-contract.md
    └── desktop-ui-contract.md
```

### Source Code (planned; not created by this command)

```text
currency_converter/
├── __init__.py
├── __main__.py
├── models.py
├── serialization.py
├── app.py
├── ui.py
├── orchestration.py
├── bnm.py
├── conversion.py
├── cache.py
├── validation.py
└── errors.py

tests/
├── unit/
│   ├── test_validation.py
│   ├── test_conversion.py
│   ├── test_bnm.py
│   └── test_cache.py
└── integration/
    └── test_offline_conversion_flow.py

README.md
REPORT.md
requirements.txt
```

**Structure Decision**: Use one small Python package and focused test suites. Do not introduce a
web backend, database, general-purpose framework, or extra architectural layers; inject only the
HTTP and filesystem boundaries needed for testability.

## Verification Strategy

- Unit-test accepted and rejected amount formats, separator handling, finiteness, and positivity.
- Test normalization, MDL base rate, same-currency behavior, cross-currency formula, and rounding
  using known Decimal fixtures.
- Test BNM request URL/date formatting, timeout and HTTP failures, empty body, XML parse errors,
  missing fields, invalid nominal/value, effective-date extraction, and complete rate-set results.
- Test cache persistence across a new cache-service instance, injected temporary paths, malformed
  cache handling, Decimal string round-trips, and preservation of old valid data after failed
  refreshes.
- Test orchestration with mocked BNM and cache services for live success, backward-date success,
  cached offline fallback, no-cache failure, and UI loading/completion/error states.
- Run all unit and integration tests with `pytest`; no test makes a live HTTP request.
- Manually verify desktop layout, loading feedback, enabled/disabled states, result provenance,
  recoverable errors, and responsiveness while a mocked slow request is active.

## Complexity Tracking

No constitution violations. The worker-thread boundary is necessary to satisfy the specified
responsive desktop behavior; no additional process, service, or persistence framework is planned.
