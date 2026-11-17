# Feature Specification: Currency Converter

**Feature Branch**: `001-currency-converter`

**Created**: 2026-11-17

**Status**: Draft

**Input**: User description: "A desktop currency conversion application using official exchange rates from the National Bank of Moldova."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Convert an Amount (Priority: P1)

A target user enters a positive amount, chooses source and target currencies, and starts a
conversion. The application calculates and displays the converted amount, effective rate date,
source, and whether the rates are live or cached.

**Why this priority**: Conversion is the application's primary value and must be independently
usable.

**Independent Test**: Enter 100 EUR, select EUR to MDL, and verify the result uses the normalized
BNM EUR rate and displays the effective date and source.

**Acceptance Scenarios**:

1. **Given** valid rates and a positive amount, **When** the user selects EUR as source and MDL as
   target and converts, **Then** the displayed result follows `amount * EUR rate / 1` and is shown
   rounded to two decimal places.
2. **Given** valid rates and a positive amount, **When** the user selects MDL as source and EUR as
   target and converts, **Then** the displayed result follows `amount * 1 / EUR rate` and is shown
   rounded to two decimal places.
3. **Given** valid rates and a positive amount, **When** the user selects two different non-MDL
   currencies and converts, **Then** the result follows `amount * source rate / target rate`.
4. **Given** valid rates, **When** the source and target currencies are identical, **Then** the
   result equals the entered amount rounded to two decimal places without an error.

---

### User Story 2 - Receive Clear Input and Data Errors (Priority: P1)

A target user sees understandable feedback when an amount is invalid or official rates cannot be
loaded, while the application remains usable.

**Why this priority**: Clear validation and resilient failure behavior prevent incorrect financial
results and application crashes.

**Independent Test**: Submit empty, alphabetic, negative, zero, NaN, and infinite values, then
repeat with network and cache unavailable; verify clear messages and continued operation.

**Acceptance Scenarios**:

1. **Given** an empty amount field, **When** conversion is attempted or validation is displayed,
   **Then** the application shows a clear amount-required message and leaves conversion disabled.
2. **Given** an alphabetic, malformed, zero, negative, NaN, or infinite amount, **When** conversion
   is attempted, **Then** the application rejects it with a clear validation message.
3. **Given** a network failure and no valid cache, **When** rates are requested, **Then** the
   application shows an understandable offline error and remains operational.
4. **Given** malformed XML or missing or invalid rate fields, **When** rates are processed, **Then**
   the application rejects the response and does not overwrite a previously valid cache.

---

### User Story 3 - Use Official Data Online or from Cache (Priority: P1)

A target user obtains exchange rates from BNM or, when offline, reuses the last successfully
validated rate response without mistaking it for current data.

**Why this priority**: The application must remain useful during outages and must preserve
transparency about rate age and source.

**Independent Test**: Retrieve valid rates, restart the application with network disabled, and
verify that the latest cache is offered or used and its effective date is displayed.

**Acceptance Scenarios**:

1. **Given** BNM returns a valid response, **When** rates are loaded, **Then** currency codes,
   names, nominal values, normalized rates, source, effective date, and retrieval state are
   available for conversion.
2. **Given** network is unavailable and a valid cache exists, **When** rates are requested, **Then**
   the application offers or automatically uses the cache and visibly labels it as cached.
3. **Given** a valid cache exists, **When** the application is restarted, **Then** cached rates
   remain available for conversion without a live network request.
4. **Given** live rates are displayed, **When** the rate state is shown, **Then** the application
   clearly identifies the data as live from BNM.

---

### User Story 4 - Use the Latest Available Previous Rate (Priority: P2)

A target user requests rates for a date with no newly published official rate. The application
searches backward through a reasonable documented period and uses the most recent valid previous
rate while informing the user.

**Why this priority**: BNM rates are unavailable on weekends and public holidays, and users need
the latest valid official rate rather than an error.

**Independent Test**: Request a known weekend or holiday date whose response is empty, then verify
that the application searches backward and displays the effective date of the returned rate.

**Acceptance Scenarios**:

1. **Given** BNM returns an empty response for the requested date, **When** the backward search
   reaches a valid prior official date, **Then** the application uses that response and displays
   the prior effective date.
2. **Given** the requested date is a weekend or public holiday, **When** no current response exists,
   **Then** the application uses the latest available previous rate and informs the user that the
   displayed date differs from the requested date.
3. **Given** no valid response is found within the documented backward-search limit, **When** a valid
   cache exists, **Then** the application may use the cache and clearly label it as cached.
4. **Given** no valid response or cache exists within the search period, **When** data loading
   finishes, **Then** the application shows a clear error without crashing.

---

### User Story 5 - View a Clean Desktop Interface (Priority: P2)

A target user can operate the converter in a responsive, modern, light desktop interface that
shows all required conversion and rate context.

**Why this priority**: A complete desktop experience makes financial results understandable and
trustworthy.

**Independent Test**: Start the application and inspect the main window, loading feedback,
validation feedback, result area, effective date, source, and cache/live state.

**Acceptance Scenarios**:

1. **Given** the application is open, **When** the main window is shown, **Then** it contains an
   amount field, source selector, target selector, conversion button, result display, effective
   rate date, and data source name.
2. **Given** the amount is empty or a currency is not selected, **When** the user views the
   conversion button, **Then** the button is disabled.
3. **Given** a network operation is in progress, **When** the operation is active, **Then** loading
   feedback is visible and the interface remains responsive.
4. **Given** conversion succeeds, **When** the result is displayed, **Then** labels and values are
   readable, the result has two decimal places, and rate provenance is visible.

---

### Edge Cases

- The amount contains surrounding whitespace; leading or trailing whitespace is accepted only if
  the remaining text is a valid numeric amount.
- The amount uses an invalid decimal separator or contains mixed separators; it is rejected with
  an understandable format message.
- The amount is extremely large or exceeds the supported calculation range; it is rejected without
  crashing or losing precision.
- The same currency is selected; no exchange operation or error occurs beyond normal amount
  validation.
- BNM omits MDL or another supported currency; the application handles the missing entry safely.
- BNM returns zero, negative, malformed, or non-finite nominal or exchange values; the application
  rejects those values.
- BNM XML is truncated or contains missing required elements; the application rejects the response
  without changing the cache.
- The cache is missing, unreadable, empty, expired, or invalid; the application reports the
  appropriate offline state and remains operational.
- A valid cache exists but does not contain the selected currency; the application reports that the
  requested currency is unavailable rather than presenting a misleading result.
- The user changes currencies or amount while network loading is in progress; loading completion
  must not produce stale or inconsistent results.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The application MUST provide a graphical desktop interface; a console-only interface
  is not acceptable.
- **FR-002**: The main window MUST contain an amount input field, source currency selector, target
  currency selector, conversion button, result display, effective exchange-rate date, and data
  source name.
- **FR-003**: The conversion button MUST remain disabled until the amount field is non-empty and
  both currency selectors have a selection.
- **FR-004**: The application MUST obtain official currency rates from BNM using the documented
  XML endpoint.
- **FR-005**: The application MUST parse currency code, currency name, nominal, and value from the
  XML response.
- **FR-006**: The application MUST include MDL as a base currency with a normalized rate of 1.
- **FR-007**: The application MUST normalize each official rate as `value divided by nominal`.
- **FR-008**: The application MUST support conversion in both directions and between any two
  currencies included in a valid loaded rate set.
- **FR-009**: The application MUST calculate conversions as
  `amount_in_target = amount * source_rate / target_rate`.
- **FR-010**: The application MUST use precise decimal arithmetic and display the converted result
  rounded to two decimal places.
- **FR-011**: The application MUST return the entered amount, rounded consistently to two decimal
  places, for same-currency conversion without an error.
- **FR-012**: The application MUST display the effective date of the rate set actually used.
- **FR-013**: The application MUST identify the National Bank of Moldova as the data source.
- **FR-014**: The application MUST reject an empty amount with a clear validation message.
- **FR-015**: The application MUST reject alphabetic text, invalid numeric formats, zero, negative
  values, NaN, and infinity.
- **FR-016**: A network failure MUST NOT crash the application.
- **FR-017**: When network access is unavailable and a previously successful rate response is
  cached, the application MUST offer or automatically use it and clearly display its effective
  date.
- **FR-018**: When network access is unavailable and no valid cache exists, the application MUST
  display an understandable error and remain operational.
- **FR-019**: If BNM returns an empty response for the requested date, the application MUST search
  backward for the most recent available official rate date within 14 calendar days.
- **FR-020**: The application MUST use the latest available previous official rate for weekends or
  public holidays and inform the user that the effective date differs from the requested date.
- **FR-021**: The application MUST safely handle malformed XML, missing required fields, invalid
  nominal values, invalid exchange rates, and missing selected currencies.
- **FR-022**: The application MUST save every successfully parsed and validated BNM response locally.
- **FR-023**: Cached rates MUST remain available after application restarts.
- **FR-024**: Each cache entry MUST retain the effective rate date, retrieval timestamp, source,
  and currency rates.
- **FR-025**: Failed or malformed responses MUST NOT overwrite a previously valid cache.
- **FR-026**: The application MUST NOT present cached rates as live or current rates.
- **FR-027**: The interface MUST use a clean, modern, light desktop design with clear labels and
  readable results.
- **FR-028**: The application MUST show loading feedback while retrieving exchange rates.
- **FR-029**: The application MUST show whether displayed rates are live or taken from the local
  cache.
- **FR-030**: Network operations MUST NOT block the application from processing user interactions.

### Key Entities

- **Amount**: A user-entered financial value; valid values are positive finite decimal numbers.
- **Currency**: A supported currency code and name associated with a normalized BNM rate.
- **Exchange-Rate Set**: A validated collection of normalized currency rates for one effective
  date.
- **Rate Provenance**: Source name, effective date, retrieval state, and retrieval timestamp that
  describe how a rate set was obtained.
- **Cached Rate Set**: The last successfully validated exchange-rate set persisted across
  application restarts.
- **Conversion Result**: Target amount, source currency, target currency, normalized rates used,
  effective date, source, and retrieval state.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can complete EUR-to-MDL conversion within the normal desktop interaction
  flow and receive a result rounded to two decimal places.
- **SC-002**: A user can complete MDL-to-EUR conversion and a conversion between two non-MDL
  currencies using the documented formula.
- **SC-003**: Same-currency conversion returns the entered positive amount consistently rounded to
  two decimal places in 100% of tested valid cases.
- **SC-004**: Empty, alphabetic, malformed, zero, negative, NaN, and infinite amounts are rejected
  in 100% of tested cases with clear feedback.
- **SC-005**: Network failure does not terminate the application or prevent it from showing an
  understandable error or cache state.
- **SC-006**: A valid cache remains usable after application restart and is visibly identified as
  cached with its effective date.
- **SC-007**: A weekend or holiday request finds the latest valid official rate within the 14-day
  search limit and visibly identifies the effective date used.
- **SC-008**: The main window always exposes the effective rate date and National Bank of Moldova
  source for conversions.
- **SC-009**: Loading, validation, and rate-provenance feedback remain visible without freezing
  desktop interactions during network operations.

## Assumptions

- The application requests the BNM XML data for the user's relevant date, with the current date as
  the initial startup default.
- The backward search limit of 14 calendar days is a reasonable default and is documented to users
  or maintainers through specification and behavior.
- BNM XML and currency values use formats accepted by the application's precise decimal
  calculation rules; locale-specific display formatting does not alter stored precision.
- Desktop operating-system availability and permission for local cache storage are assumed.
- No account, authentication, personalization, or historical rate-search user interface is added
  beyond loading rates for the effective date relevant to conversion.
- Mobile and web interfaces are outside the scope of this desktop application.
