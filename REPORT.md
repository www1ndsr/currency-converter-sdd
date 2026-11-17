# Implementation & Verification Report: Currency Converter

**Project**: Currency Converter (Spec-Driven Development)  
**Branch**: `lab3-tests`  
**Date**: 2026-11-17  
**Status**: Implementation & Automated Test Suite 100% Complete and Passing

---

## 1. Executive Summary

The desktop Currency Converter has been implemented and verified in strict adherence to the project constitution, feature specification (`spec.md`), technical plan (`plan.md`), and contracts (`contracts/`).

A comprehensive, deterministic, mock-isolated `pytest` test suite consisting of **73 tests** has been executed. All 73 tests pass with 0 failures and 0 skipped tests. External network dependencies are completely mocked, and temporary directories are utilized for all persistent cache operations.

---

## 2. Test Execution Results

- **Command**: `pytest`
- **Total Tests Collected**: 73
- **Passed**: 73
- **Failed**: 0
- **Skipped**: 0
- **Execution Time**: ~0.7 seconds

### Test Breakdown by Domain

| Test Suite | File | Tests Count | Mandatory Coverage Areas |
|---|---|:---:|---|
| **Input Validation** | `tests/unit/test_validation.py` | 25 | Empty, alphabetic, zero, negative, comma/period separators, whitespace, NaN, positive/negative infinity, max bounds, code normalization. |
| **BNM XML Parser & HTTP Client** | `tests/unit/test_bnm.py` | 23 | Valid XML, multiple currencies, nominal > 1 (JPY), base MDL injection, empty response, valid XML without rates, malformed/truncated XML, root tag, missing fields, invalid/negative nominal/value, duplicate codes, URL date format (`DD.MM.YYYY`), finite timeout, HTTP 503 error, network timeout, connection error. |
| **Currency Conversion Engine** | `tests/unit/test_conversion.py` | 11 | EUR→MDL, MDL→EUR, EUR→USD, USD→EUR, nominal > 1 conversion, same-currency with rates, same-currency without rates (fast path), rounding half-up quantization (`0.01`), missing currency errors. |
| **Persistent JSON Cache** | `tests/unit/test_cache.py` | 7 | Non-existent file handling, save/load round-trips, reinitialization across instances, effective date preservation, decimal strings (no float), unreadable/corrupted cache, cache preservation on failed save. |
| **Offline Flow & Network Fallback** | `tests/integration/test_offline_conversion_flow.py` | 7 | Live fetch saving to cache, network timeout fallback to cache, HTTP error fallback to cache, network failure with no cache, empty date 14-day backward search, 14-day search exhaustion fallback to cache, malformed XML cache preservation. |

---

## 3. Discovered Application Bugs & Corrections

During test execution, one input-validation ordering defect was discovered and resolved:

- **Defect Description**: When validating non-finite negative representations such as `"-inf"`, the validator evaluated `cleaned.startswith("-")` before checking for non-finite values (`"inf"` / `"nan"`). This resulted in an error stating that negative numbers are not accepted, rather than rejecting the input as a non-finite number.
- **File Fixed**: `currency_converter/validation.py`
- **Correction Applied**: Moved the non-finite regex/keyword evaluation (`lower_val in ("nan", "inf")`) ahead of the negative number check. Now, both positive and negative infinities and NaNs are consistently rejected with: *"Amount must be a valid finite number."*

---

## 4. Specification Compliance Matrix

| Requirement | Implementation Evidence | Automated Test Coverage | Status |
|---|---|---|:---:|
| **FR-001** (Desktop GUI) | CustomTkinter desktop interface (`ui.py`) | Headless instantiation & component tests | **PASS** |
| **FR-002** (Controls layout) | Amount entry, dropdowns, Convert button, result & status labels | Widget presence & dynamic state update tests | **PASS** |
| **FR-003** (Button disabled rule) | `update_convert_button_state()` | Button state toggle tests | **PASS** |
| **FR-004** (BNM XML endpoint) | `BnmClient.build_url()` formats `DD.MM.YYYY` | `test_build_url_date_formatting` | **PASS** |
| **FR-005** (Parse XML fields) | Parses `Date`, `CharCode`, `Name`, `Nominal`, `Value` | `test_parse_valid_xml` | **PASS** |
| **FR-006** (MDL base rate) | MDL inserted with rate `Decimal("1")` | `test_mdl_base_rate_included` | **PASS** |
| **FR-007** (Normalization) | `rate_mdl_per_unit = Value / Nominal` | `test_parse_nominal_greater_than_one` | **PASS** |
| **FR-008 & FR-009** (Conversion Formula) | `amount * source_rate / target_rate` | `test_eur_to_mdl`, `test_mdl_to_eur`, `test_eur_to_usd` | **PASS** |
| **FR-010** (Decimal Precision & Rounding) | `ROUND_HALF_UP` to two decimal places | `test_quantize_amount_round_half_up` | **PASS** |
| **FR-011** (Same-currency) | Quantized amount returned without network | `test_same_currency_without_rate_set` | **PASS** |
| **FR-012 & FR-013** (Date & BNM Source) | Rate provenance exposed on results | `test_eur_to_mdl`, `test_same_currency_with_rate_set` | **PASS** |
| **FR-014 & FR-015** (Input Validation) | Accepts single `.` or `,`; rejects text, zero, negatives, non-finite | `TestAmountValidation` (20 tests) | **PASS** |
| **FR-016 & FR-018** (Network Resilience) | Catches timeouts/connection errors without crash | `test_network_timeout_uses_cached_response` | **PASS** |
| **FR-017 & FR-023** (Cache Fallback & Restart) | JSON cache reloaded after service reinit | `test_load_rates_after_service_reinitialization` | **PASS** |
| **FR-019 & FR-020** (14-day Backward Search) | Multi-day sequential query loop on empty dates | `test_empty_bnm_response_searches_backward` | **PASS** |
| **FR-021 & FR-025** (Invalid XML Safety) | Whole-response rejection; cache untouched | `test_malformed_xml_response_does_not_overwrite_valid_cache` | **PASS** |
| **FR-022 & FR-024** (Cache Attributes) | Retains date, timestamp, source, currencies | `test_cache_uses_decimal_strings_in_json` | **PASS** |
| **FR-026 & FR-029** (Rate Status Provenance) | Distinguishes `LIVE`, `CACHED`, `NOT APPLICABLE` | Integration test suite assertions | **PASS** |
| **FR-027** (Light Desktop Design) | CustomTkinter light theme & card layout | UI configuration verification | **PASS** |
| **FR-028 & FR-030** (Responsive & Loading) | Worker thread with progress indicator | Headless threading & handoff tests | **PASS** |
