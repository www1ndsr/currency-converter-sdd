# Quickstart and Validation: Currency Converter

This guide is for implementation and verification after the application is built. It does not
implement or install the application.

## Prerequisites

- Python 3.11 or newer
- Access to the official BNM exchange-rate XML service for live-rate checks
- A desktop environment supported by CustomTkinter

## Install

From the repository root, create and activate a virtual environment using the platform's standard
Python commands, then install the project dependencies from its dependency manifest. The manifest
must include CustomTkinter, requests, and pytest; standard-library modules such as Decimal, JSON,
pathlib, and ElementTree must not be installed separately.

## Run

Launch the desktop application using the entry point documented in the project README. The main
window should appear without requiring a console-only interaction. The first rate load should
show loading feedback and then identify BNM, the actual effective date, and whether the rate set is
live or cached.

## Automated Tests

Run the unit and integration suite from the repository root:

```text
pytest
```

The test suite must use mocked HTTP responses and temporary/injected cache paths; it must not
contact the live BNM service.

## Validation Scenarios

1. **Live EUR to MDL**: Load a valid fixture with EUR nominal `1` and value `20.1666`; convert
   `100` EUR to MDL. Expect `2016.66` MDL, subject to the source fixture and two-place display
   rounding. Show the fixture's BNM effective date and live status.
2. **MDL to EUR**: With the same fixture, convert `100` MDL to EUR. Expect calculation by
   `100 * 1 / 20.1666`, rounded to two decimal places.
3. **Foreign to foreign**: With rates for two currencies, verify the result is
   `amount * source_rate / target_rate`, rounded only for display.
4. **Same currency offline**: Disable network and provide no cache. Convert `12,34` USD to USD.
   Expect `12.34` without a network request.
5. **Invalid input**: Confirm empty, alphabetic, mixed-separator, zero, negative, NaN, and
   infinity values are rejected with clear feedback.
6. **Unavailable date**: Mock an empty requested-date response and earlier empty responses followed
   by a valid response. Verify search stops at the first valid prior day and exposes that response's
   XML effective date.
7. **Offline cache after restart**: Save a valid rate set, construct a fresh application/cache
   service with network unavailable, then verify the cached result works and remains labeled
   cached.
8. **Offline without cache**: Mock a network failure and an empty cache. Verify an understandable
   error appears and the application remains open and responsive.
9. **Invalid XML safety**: Test malformed XML, missing response date, absent fields, nonpositive
   nominal/value, and partially invalid currency entries. Each whole response must be rejected and
   an existing valid cache must remain unchanged.
10. **UI responsiveness**: Hold a mocked HTTP response open while exercising the window. Verify
    loading feedback is visible and the UI remains interactive until the result is delivered.

For the full data and UI expectations, see `data-model.md` and `contracts/`.
