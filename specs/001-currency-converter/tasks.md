---
description: "Ordered implementation tasks for the Currency Converter feature"
---

# Tasks: Currency Converter

**Input**: Design documents from `specs/001-currency-converter/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`,
`quickstart.md`

**Tests**: Unit and integration tests are explicitly required by the specification and user.
All BNM HTTP tests use mocked responses; no automated test may depend on the live BNM service.

**Organization**: Setup and shared foundations first, then one implementation phase per
specification user story in priority order, followed by documentation and end-to-end acceptance.
The independent test notes describe a story-level demonstration; test tasks implement automated
coverage.

## Format

`[ ] Task ID [P?] [Story?] Action with expected outcome and exact path.`

- `[P]` indicates a task that can be performed in parallel because it changes distinct files and
  has no incomplete task dependency.
- `[US1]` through `[US5]` map to user stories in `spec.md`.
- Each task names a concrete expected result. Dependencies are stated explicitly where needed.
- Every implementation task touching a constrained data field cites the canonical field in
  `data-model.md`.

## Phase 1: Project Setup

**Purpose**: Create the application skeleton, dependencies, and test environment.

- [ ] T001 Create the `currency_converter/` package, `tests/unit/`, and `tests/integration/` directories as specified in `plan.md`; add `currency_converter/__init__.py` and an importable `currency_converter/__main__.py` scaffold for completion in T040.
- [ ] T002 Add `requirements.txt` with Python 3.11+ compatible CustomTkinter, requests, and pytest dependencies; do not list standard-library modules as dependencies.
- [ ] T003 Add `pytest.ini` at the repository root with test discovery for `tests/` and configuration that does not make live-network calls.
- [ ] T004 Add `.gitignore` entries for Python bytecode, virtual environments, pytest cache, and generated local rate-cache data.

## Phase 2: Foundational Shared Contracts

**Purpose**: Define shared domain and error boundaries used by the user-story implementations.

- [ ] T005 [P] Create the shared expected-failure types in `currency_converter/errors.py` for invalid input, network/timeout/HTTP errors, empty BNM dates, malformed or invalid rate data, unavailable currencies, and cache read/write failures.
- [ ] T006 Define validated currency and rate-set records in `currency_converter/models.py`; follow `data-model.md` for `Currency.code`, `Currency.name`, `Currency.nominal`, `Currency.value`, `Currency.rate_mdl_per_unit`, and `Exchange-Rate Set.effective_date`, `Exchange-Rate Set.retrieved_at`, `Exchange-Rate Set.source`, and `Exchange-Rate Set.currencies`.
- [ ] T007 Define shared provenance and conversion-result records in `currency_converter/models.py` after T006; follow `data-model.md` for `Conversion Result.amount_in_target`, `Conversion Result.source_code`, `Conversion Result.target_code`, `Conversion Result.effective_date`, `Conversion Result.source`, and `Conversion Result.rate_state`.
- [ ] T008 Add reusable Decimal string serialization and strict ISO/date timestamp conversion helpers in `currency_converter/serialization.py` for JSON cache boundaries; reject malformed values instead of accepting floats.

## Phase 3: User Story 1 - Convert an Amount (Priority: P1)

**Goal**: Retrieve a valid BNM rate set and convert MDL and foreign currencies accurately.

**Independent Test**: With a mocked BNM XML response containing EUR `Nominal=1`, `Value=20.1666`, and a second foreign rate, demonstrate EUR→MDL, MDL→EUR, foreign→foreign, and same-currency conversions, each with a predictable Decimal result and the used BNM date.

### BNM XML Integration and Parsing

- [ ] T009 [US1] Implement the date-specific BNM GET request, finite timeout, HTTP status handling, and response retrieval in `currency_converter/bnm.py` using `requests`; format the endpoint date as `DD.MM.YYYY` as defined in `contracts/bnm-xml-contract.md`.
- [ ] T010 [US1] Implement complete XML parsing in `currency_converter/bnm.py` after T009, using `xml.etree.ElementTree`; parse `ValCurs/@Date` and each required `Valute` field (`CharCode`, `Name`, `Nominal`, `Value`) as specified in `contracts/bnm-xml-contract.md`.
- [ ] T011 [US1] Normalize each parsed BNM currency as `Decimal(Value) / Decimal(Nominal)` after T010 and add MDL at exactly `Decimal("1")` in `currency_converter/bnm.py`; use canonical field rules for `Currency.nominal`, `Currency.value`, and `Currency.rate_mdl_per_unit` in `data-model.md`.
- [ ] T012 [P] [US1] Add mocked-response parser tests in `tests/unit/test_bnm.py` for valid XML, date extraction, nominal/value normalization (including nominal greater than one), MDL base rate, duplicate codes, and required currency metadata; cite `data-model.md` fields `Currency.code`, `Currency.name`, `Currency.nominal`, `Currency.value`, `Currency.rate_mdl_per_unit`, and `Exchange-Rate Set.effective_date`.
- [ ] T013 [P] [US1] Add mocked HTTP tests in `tests/unit/test_bnm.py` for URL/date formatting, finite timeout, status errors, connection errors, and timeouts; assert no test contacts BNM.

### Currency Conversion Logic

- [ ] T014 [US1] Implement Decimal conversion in `currency_converter/conversion.py` with formula `amount * source_rate / target_rate`; keep intermediate precision and quantize only the displayed amount using `ROUND_HALF_UP` to `0.01`; follow `data-model.md` fields `Conversion Request.source_code`, `Conversion Request.target_code`, and `Conversion Result.amount_in_target`.
- [ ] T015 [P] [US1] Add EUR-to-MDL conversion unit tests in `tests/unit/test_conversion.py` using fixed Decimal rates and expected two-place results; cite `data-model.md` fields `Currency.rate_mdl_per_unit` and `Conversion Result.amount_in_target`.
- [ ] T016 [P] [US1] Add MDL-to-EUR conversion unit tests in `tests/unit/test_conversion.py` using the inverse rate formula and expected two-place results; cite `data-model.md` fields `Currency.rate_mdl_per_unit` and `Conversion Result.amount_in_target`.
- [ ] T017 [P] [US1] Add foreign-currency-to-foreign-currency unit tests in `tests/unit/test_conversion.py` proving conversion is `amount * source_rate / target_rate`; cite `data-model.md` fields `Currency.rate_mdl_per_unit` and `Conversion Result.amount_in_target`.
- [ ] T018 [P] [US1] Add same-currency conversion tests in `tests/unit/test_conversion.py` proving amount validation and two-place `ROUND_HALF_UP` output require no rate set or HTTP call; cite `data-model.md` field `Conversion Result.amount_in_target`.
- [ ] T019 [US1] Include BNM source, effective date from the response, and live-rate state in successful rate-based conversion results in `currency_converter/conversion.py`; cite `data-model.md` fields `Exchange-Rate Set.effective_date`, `Exchange-Rate Set.source`, and `Conversion Result.rate_state`.

## Phase 4: User Story 2 - Receive Clear Input and Data Errors (Priority: P1)

**Goal**: Reject invalid amounts and surface expected data/network failures without terminating the application.

**Independent Test**: Submit empty, alphabetic, malformed, zero, negative, NaN, and infinity inputs and provide malformed/missing-field XML; confirm clear errors, intact prior state, and continued application operation.

- [ ] T020 [US2] Implement amount parsing and validation in `currency_converter/validation.py`; accept one comma or period decimal separator, parse directly to Decimal, and reject empty, invalid syntax, zero, negative, NaN, and infinity; follow `data-model.md` field `Conversion Request.amount`.
- [ ] T021 [P] [US2] Add unit tests in `tests/unit/test_validation.py` for valid period/comma inputs, whitespace handling, mixed/multiple separators, alphabetic text, empty input, zero, negatives, NaN, and positive/negative infinity; cite `data-model.md` field `Conversion Request.amount`.
- [ ] T022 [US2] Reject malformed XML, missing response date or required fields, invalid nominal/value, incomplete records, and partially valid BNM sets as whole-response failures in `currency_converter/bnm.py`; do not treat invalid responses as empty-date results or merge entries; cite `data-model.md` invariants for `Exchange-Rate Set`.
- [ ] T023 [P] [US2] Add mocked-response failure tests in `tests/unit/test_bnm.py` for truncated/malformed XML, missing fields/date, nonpositive or nonnumeric nominal/value, and one invalid record among valid records; assert the entire response is rejected.
- [ ] T024 [US2] Map expected validation, HTTP, network, XML, and missing-currency failures to user-readable recovery messages in `currency_converter/orchestration.py`; unexpected programming errors must not be reported as successful conversions.

## Phase 5: User Story 3 - Use Official Data Online or from Cache (Priority: P1)

**Goal**: Persist every valid response and transparently reuse valid data during network outages and after restart.

**Independent Test**: Save a mocked valid BNM response, construct a fresh cache service, then simulate network failure; verify the saved rate set can convert offline and is labeled cached with its original effective date.

- [ ] T025 [US3] Implement JSON cache read, full-record validation, and Decimal-string decoding in `currency_converter/cache.py` using an injectable `pathlib.Path`; follow `data-model.md` fields `Cached Rate Set.effective_date`, `Cached Rate Set.retrieved_at`, `Cached Rate Set.source`, and `Cached Rate Set.currencies`.
- [ ] T026 [US3] Implement cache writes in `currency_converter/cache.py` that preserve every successfully validated response, serialize Decimal values as strings, and atomically replace the JSON file only after a complete valid write; follow `data-model.md` entity `Cached Rate Set`.
- [ ] T027 [P] [US3] Add unit tests in `tests/unit/test_cache.py` for JSON round trips, Decimal strings, injected temporary paths, malformed/empty/unreadable cache handling, and multiple persisted effective dates; cite `data-model.md` fields `Cached Rate Set.effective_date`, `Cached Rate Set.retrieved_at`, `Cached Rate Set.source`, and `Cached Rate Set.currencies`.
- [ ] T028 [P] [US3] Add cache-preservation tests in `tests/unit/test_cache.py` proving failed validation or write does not truncate or overwrite the previous valid cache; cite `data-model.md` invariant that failed responses cannot invalidate prior valid data.
- [ ] T029 [US3] Implement application orchestration in `currency_converter/orchestration.py` to load BNM rates, persist each complete valid response, and expose live source/date/status to the UI; depend on T009-T011 and T025-T026; cite `data-model.md` fields `Exchange-Rate Set.effective_date`, `Exchange-Rate Set.retrieved_at`, `Exchange-Rate Set.source`, and `Exchange-Rate Set.currencies`.
- [ ] T030 [US3] Implement network-failure fallback in `currency_converter/orchestration.py` to automatically select the most recently retrieved valid cached rate set and mark it cached; when no valid cache exists, return a user-readable offline error without crashing; cite `data-model.md` fields `Conversion Result.effective_date`, `Conversion Result.source`, and `Conversion Result.rate_state`.
- [ ] T031 [P] [US3] Add orchestration tests in `tests/integration/test_offline_conversion_flow.py` for network failure with valid cache, network failure without cache, cache persistence across a newly constructed service/application, cached effective date, and cached/live status.

## Phase 6: User Story 4 - Use the Latest Available Previous Rate (Priority: P2)

**Goal**: On a valid empty-date response, find the most recent prior BNM rate within the 14-calendar-day search window.

**Independent Test**: Mock an empty weekend/holiday response followed by empty weekdays and a valid earlier response; verify the first valid previous rate set and its XML effective date are used.

- [ ] T032 [US4] Implement sequential previous-calendar-date requests in `currency_converter/orchestration.py` when BNM returns an empty response; check the requested date and then up to 14 prior calendar dates, stopping at the first valid rate set; do not continue the search on a network or malformed-XML failure.
- [ ] T033 [US4] Preserve the successful response's effective date and mark that the effective date differs from the requested weekend/holiday date in `currency_converter/orchestration.py`; cite `data-model.md` fields `Exchange-Rate Set.effective_date` and `Conversion Result.effective_date`.
- [ ] T034 [P] [US4] Add mocked HTTP tests in `tests/unit/test_bnm.py` covering empty response, valid no-rates XML, prior-date URL sequence, boundary of the 14-day search, and stop-at-first-valid response.
- [ ] T035 [P] [US4] Add orchestration tests in `tests/integration/test_offline_conversion_flow.py` for weekend/holiday previous-rate success, search-limit exhaustion with valid cache, and search-limit exhaustion without cache.

## Phase 7: User Story 5 - View a Clean Desktop Interface (Priority: P2)

**Goal**: Deliver the specified light desktop interface with clear controls, results, provenance, loading, and recoverable error states.

**Independent Test**: Launch the desktop entry point with mocked rate services and inspect enabled/disabled controls, live/cached source/date labels, loading/error/result states, and UI responsiveness during delayed requests.

- [ ] T036 [US5] Implement the CustomTkinter main window and required amount field, source/target selectors, conversion button, result area, effective-date label, and BNM source label in `currency_converter/ui.py`; populate selectors from available rates, and disable conversion while required selections or amount are absent.
- [ ] T037 [US5] Implement validation, loading, live/cache status, successful-result, and error presentation states in `currency_converter/ui.py`; identify a same-currency result's effective date as not applicable when no rate set was used.
- [ ] T038 [US5] Integrate the UI with `currency_converter/orchestration.py` in `currency_converter/app.py`; on startup request rates for the current date, keep HTTP and backward-search work off the UI event loop, and perform widget updates only on the UI thread.
- [ ] T039 [P] [US5] Add UI/orchestration tests in `tests/integration/test_offline_conversion_flow.py` for disabled-button conditions, loading feedback, live and cached provenance, no-cache errors, invalid input feedback, and same-currency without HTTP.
- [ ] T040 [US5] Verify the app entry point in `currency_converter/__main__.py` opens the desktop interface and leaves the application operational after all expected service errors.

## Phase 8: Documentation

**Purpose**: Provide setup, launch, data-source, calculation, and verification instructions.

- [ ] T041 [P] Update `README.md` with Python 3.11+ prerequisites, virtual-environment/dependency installation, desktop launch instructions, BNM source and XML endpoint, offline cache behavior, and Decimal conversion formula.
- [ ] T042 [P] Create `REPORT.md` with the delivered feature summary, supported error/offline paths, test command, test coverage summary, and manual acceptance results; leave results explicitly pending until testing is performed.
- [ ] T043 Update `specs/001-currency-converter/quickstart.md` after implementation so launch commands and validation steps match the actual entry point and dependency manifest.

## Phase 9: Final Acceptance Testing

**Purpose**: Validate all specified user-visible acceptance criteria end to end using deterministic fixtures and a live desktop session.

- [ ] T044 Run `pytest` from the repository root against `tests/` and resolve failures; verify all HTTP-dependent tests use mocked responses and no test contacts BNM.
- [ ] T045 [P] Run acceptance scenarios for EUR-to-MDL, MDL-to-EUR, foreign-to-foreign, same-currency offline conversion, decimal comma/period input, and invalid amounts using `tests/integration/test_offline_conversion_flow.py`.
- [ ] T046 [P] Run acceptance scenarios for mocked weekend/holiday fallback, the 14-day search boundary, network failure with and without cache, restart persistence, and invalid XML cache preservation using `tests/integration/test_offline_conversion_flow.py`.
- [ ] T047 Perform manual desktop acceptance review against `specs/001-currency-converter/contracts/desktop-ui-contract.md`; record results in `REPORT.md` for source/effective date, live/cache status, loading feedback, responsive interactions, validation, and recoverable errors.
- [ ] T048 Reconcile final results against every success criterion SC-001 through SC-011 in `specs/001-currency-converter/spec.md` and record pass/fail evidence and any remaining gaps in `REPORT.md`.

## Dependencies and Execution Order

### Phase Dependencies

- **Phase 1 Setup**: No dependencies; complete before application and test implementation.
- **Phase 2 Foundational**: Depends on Phase 1; defines shared models, error types, and serialization used by stories.
- **Phase 3 US1 Conversion**: Depends on Phase 2; delivers official rates and core conversion behavior.
- **Phase 4 US2 Validation/Errors**: Depends on shared errors and US1 BNM service; may be developed alongside independent cache work after Phase 2 if interfaces are agreed.
- **Phase 5 US3 Cache/Offline**: Depends on Phase 2 and US1 rate-set contract; completes persistent cache and offline fallback.
- **Phase 6 US4 Previous-Date Fallback**: Depends on US1 BNM service and US3 fallback behavior.
- **Phase 7 US5 Desktop GUI**: Depends on US1 conversion and rate contracts plus US2 validation/error mapping and US3/US4 status behavior.
- **Phase 8 Documentation**: README and REPORT can start after Phase 1; quickstart synchronization depends on application entry point.
- **Phase 9 Acceptance**: Depends on all implementation stories and documentation; acceptance results must be recorded before completion.

### User Story Dependencies

- **US1 (P1)**: First demonstrable slice; depends only on Phase 2.
- **US2 (P1)**: Uses US1's BNM response/errors; can proceed with US3 cache work once shared error and model contracts exist.
- **US3 (P1)**: Uses the US1 rate-set contract; independent cache tests can start after Phase 2.
- **US4 (P2)**: Extends US1 BNM retrieval and relies on US3 cache fallback when the search exhausts.
- **US5 (P2)**: Integrates all service outcomes from US1-US4; final end-to-end UI is dependent on those contracts.

### Task Dependencies

- T006 and T008 depend on T001; T007 depends on T006.
- T009 depends on T005-T008; T010 depends on T009; T011 depends on T010; T012-T013 depend on T009-T011.
- T014 depends on T006-T008; T015-T018 depend on T014.
- T020-T024 depend on shared failures and BNM service; T021 and T023 can run in parallel after interfaces stabilize.
- T025-T028 depend on T006-T008; T029-T031 depend on T009-T011 and T025-T028.
- T032-T035 depend on T009-T011; cache-exhaustion cases depend on T030.
- T036-T040 depend on orchestration and service contracts from US1-US4.
- T044-T048 depend on all required implementation tasks; T045 and T046 can execute in parallel after the integration harness is ready.

## Parallel Opportunities

- **Setup**: T002-T004 may be prepared in parallel after T001 establishes the repository layout.
- **US1 tests**: T012 and T013 are separate mocked BNM test concerns; T015-T018 are independent conversion test cases after T014 exists.
- **US2 tests**: T021 and T023 cover distinct validation and XML boundaries.
- **US3 tests**: T027 and T028 cover cache round-trip and preservation behavior and can be authored against the same interface.
- **US4 tests**: T034 and T035 cover BNM request sequencing and orchestration outcomes, respectively.
- **Documentation**: T041 and T042 can proceed in parallel; T043 follows actual launcher implementation.
- **Acceptance**: T045 and T046 can run in parallel after the mocked integration harness and application flows are complete.

## Implementation Strategy

1. Complete setup and shared models/errors.
2. Deliver an MVP with mocked-testable BNM parsing and all four conversion modes (US1).
3. Add validation and expected error behavior (US2).
4. Add persistent cache, restart support, and offline fallback (US3).
5. Add backward-date/weekend/holiday resolution (US4).
6. Integrate the complete desktop experience and asynchronous rate loading (US5).
7. Finish documentation and run automated plus manual acceptance against SC-001–SC-011.

No application implementation is performed by this task-generation artifact.
