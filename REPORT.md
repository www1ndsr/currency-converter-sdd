# Implementation & Verification Report: Currency Converter

**Project**: Currency Converter (Spec-Driven Development)  
**Branch**: `lab3-implementation`  
**Date**: 2026-11-17  
**Status**: Core Implementation Complete (Testing tasks deferred to `lab3-tests` branch)

---

## 1. Executive Summary

The desktop Currency Converter has been implemented in strict adherence to the project constitution, feature specification (`spec.md`), technical plan (`plan.md`), and contracts (`contracts/`).

The application retrieves official exchange rates from the National Bank of Moldova (BNM), stores them in an atomic local JSON cache, performs high-precision financial conversions using `decimal.Decimal`, handles weekends/holidays with up to a 14-day backward search, and presents a responsive CustomTkinter GUI.

---

## 2. Delivered Components & File Structure

| File | Purpose | Specification Tracing |
|---|---|---|
| `currency_converter/models.py` | Strongly typed dataclasses (`Currency`, `ExchangeRateSet`, `ConversionRequest`, `ConversionResult`) | `data-model.md` |
| `currency_converter/errors.py` | Distinct domain exception hierarchy | Principle III, VII; `plan.md` |
| `currency_converter/serialization.py` | Decimal string & ISO-8601 serialization for JSON cache | `data-model.md` §Cached Rate Set |
| `currency_converter/bnm.py` | Official BNM XML client, all-or-nothing parser, rate normalizer | FR-004, FR-005, FR-006, FR-007, FR-021 |
| `currency_converter/conversion.py` | Pure Decimal conversion engine with `ROUND_HALF_UP` display quantization | FR-008, FR-009, FR-010, FR-011 |
| `currency_converter/validation.py` | Input validator for amount (period/comma, positives, finiteness) | FR-014, FR-015 |
| `currency_converter/cache.py` | Atomic JSON persistent storage with sibling temp file replacement | FR-017, FR-022, FR-023, FR-024, FR-025 |
| `currency_converter/orchestration.py` | Multi-day backward search, cache fallback, error translation | FR-016, FR-018, FR-019, FR-020, FR-026 |
| `currency_converter/ui.py` | Modern CustomTkinter desktop interface with responsive controls | FR-001, FR-002, FR-003, FR-027, FR-028, FR-029 |
| `currency_converter/app.py` | Application coordinator and background threading boundary | FR-030; `plan.md` |
| `currency_converter/__main__.py` | CLI entry point (`python -m currency_converter`) | `plan.md` |
| `requirements.txt` | Python 3.11+ dependencies (`customtkinter`, `requests`, `pytest`) | T002 |
| `pytest.ini` | Test discovery and offline configuration | T003 |
| `.gitignore` | Ignores cache files, virtualenvs, and pycache | T004 |
| `README.md` | Project documentation, setup, and launch instructions | Principle X, T041 |

---

## 3. Supported Resilience & Error Paths

1. **Network Failure with Existing Cache**:
   - The application catches network timeouts and HTTP errors.
   - Automatically loads the most recent valid rate set from `rates_cache.json`.
   - Visibly flags data provenance as `CACHED` and displays the cached rate date.
2. **Network Failure without Cache (Cold Start Offline)**:
   - Catches the offline condition gracefully.
   - Retains the base currency (`MDL`) in selectors.
   - Shows an understandable user error: *"Unable to retrieve exchange rates ... and no local cached rates are available."*
   - Same-currency conversion (e.g., MDL to MDL) remains fully functional without crashing.
3. **Weekends and Public Holidays (Empty Date Response)**:
   - When BNM returns an empty body or XML with no rates, the orchestrator searches backward day-by-day up to 14 calendar days.
   - Displays the effective date of the latest published rate found and informs the user of the date adjustment.
4. **Malformed or Partial XML**:
   - If XML is truncated, missing required elements (`ValCurs/@Date`, `CharCode`, `Nominal`, `Value`), or contains nonpositive values, the entire response is rejected.
   - Existing local cache is untouched and never overwritten by invalid data.
5. **Amount Validation Rejections**:
   - Rejects empty input, negative numbers, zero, text, NaNs, infinities, and multiple/mixed decimal separators (`1,234.56` or `10..5`).
   - Accepts either `.` or `,` as the sole decimal separator when followed by digits.

---

## 4. Verification and Testing Status

- **Automated Unit & Integration Tests**:
  Per project guidance, full unit and integration test implementations (T012, T013, T015–T018, T021, T023, T027, T028, T031, T034, T035, T039, T044–T046) are deferred to the dedicated `lab3-tests` branch.
- **Verification of Implemented Modules**:
  All implemented modules were verified for syntax, importability, headless instantiation, and core logical contracts (amount validation, conversion arithmetic, Decimal rounding, cache serialization, atomic writing, and button state management).

---

## 5. Specification Compliance Summary

| Requirement | Implementation Detail | Status |
|---|---|---|
| **FR-001** (Desktop GUI) | CustomTkinter single-window interface in `ui.py` | COMPLIANT |
| **FR-002** (Controls layout) | Amount entry, source/target dropdowns, Convert button, result label, date/source/status labels | COMPLIANT |
| **FR-003** (Button disabled rule) | `update_convert_button_state()` validates amount and selections dynamically | COMPLIANT |
| **FR-004** (BNM XML endpoint) | `BnmClient.build_url()` queries `https://www.bnm.md/en/official_exchange_rates?get_xml=1&date=DD.MM.YYYY` | COMPLIANT |
| **FR-005** (Parse XML fields) | Parses `Date`, `CharCode`, `Name`, `Nominal`, `Value` via `ElementTree` | COMPLIANT |
| **FR-006** (MDL base rate) | Explicitly adds `MDL` with normalized rate `Decimal("1")` | COMPLIANT |
| **FR-007** (Normalization) | Derived as `Decimal(Value) / Decimal(Nominal)` | COMPLIANT |
| **FR-008 & FR-009** (Conversion Formula) | `amount * source_rate / target_rate` in `conversion.py` | COMPLIANT |
| **FR-010** (Decimal Precision & Rounding) | `ROUND_HALF_UP` to 2 decimal places, Decimal throughout | COMPLIANT |
| **FR-011** (Same-currency) | Fast path returning quantized amount without network access | COMPLIANT |
| **FR-012 & FR-013** (Date & BNM Source) | Displays parsed XML date and `National Bank of Moldova (BNM)` | COMPLIANT |
| **FR-014 & FR-015** (Input Validation) | `parse_and_validate_amount()` in `validation.py` | COMPLIANT |
| **FR-016 & FR-018** (Network Resilience) | Catches timeouts/connection errors, no crash | COMPLIANT |
| **FR-017 & FR-023** (Cache Fallback & Restart) | Persistent JSON cache in `cache.py` loaded on startup/offline | COMPLIANT |
| **FR-019 & FR-020** (14-day Backward Search) | Multi-day sequential query loop in `orchestration.py` | COMPLIANT |
| **FR-021 & FR-025** (Invalid XML Safety) | Whole-response rejection, cache preserved | COMPLIANT |
| **FR-022 & FR-024** (Cache Attributes) | Retains `effective_date`, `retrieved_at`, `source`, `currencies` | COMPLIANT |
| **FR-026 & FR-029** (Live vs Cached Status) | Clear UI status badges: `LIVE (BNM)`, `CACHED`, `NOT APPLICABLE` | COMPLIANT |
| **FR-027** (Light Desktop Design) | Modern card-based UI with CustomTkinter light theme | COMPLIANT |
| **FR-028 & FR-030** (Responsive & Loading) | Background worker thread with `CTkProgressBar` | COMPLIANT |
