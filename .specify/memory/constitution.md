<!--
Sync Impact Report:
- Version change: template placeholders -> 1.0.0
- Modified principles: none (initial constitution)
- Added sections: Specification-First Development; Precise Financial Calculations;
  Failure Resilience; Data Transparency; Offline Resilience; Input Validation;
  Maintainable Architecture; Testability; User Experience; Documentation
- Removed sections: none
- Follow-up TODOs: none
-->

# Currency Converter Constitution

## Core Principles

### I. Specification-First Development
Requirements MUST be fully specified and approved before implementation begins. Specifications
MUST describe observable behavior, inputs, outputs, errors, rate provenance, and acceptance
criteria. Application implementation is performed only from generated specifications by an
external coding agent.

### II. Precise Financial Calculations
All currency amounts, exchange rates, and conversion results MUST use precise decimal arithmetic.
Binary floating-point arithmetic MUST NOT be used for currency calculations or financial
comparisons. Calculations MUST define and apply a deterministic rounding policy.

### III. Failure Resilience
Network failures, empty API responses, malformed XML, unavailable caches, read/write failures,
and missing exchange-rate entries MUST NOT crash the application. The application MUST handle
these cases by returning clear errors or safely reusing the latest valid cached data.

### IV. Data Transparency
The application MUST identify the National Bank of Moldova (BNM) as the exchange-rate source and
MUST display the effective date of the rates used for every conversion. Cached or calculated
results MUST remain explicit about their source and effective date.

### V. Offline Resilience
The application MUST persist the last successfully retrieved and validated BNM exchange-rate data
locally. When the network is unavailable or fresh data cannot be retrieved, the application MUST
reuse the latest valid cache and clearly indicate that cached rates are in use.

### VI. Input Validation
Every amount MUST be validated before calculation. Empty, non-numeric, zero, negative, NaN, and
infinite amounts MUST be rejected. Validation errors MUST identify the invalid input and explain
the accepted format.

### VII. Maintainable Architecture
The application MUST separate user interface, business logic, external BNM data access, and local
cache access into distinct modules or components. Dependencies MUST follow toward stable,
domain-focused abstractions rather than concrete UI or infrastructure implementations.

### VIII. Testability
External HTTP requests MUST be mockable through explicit interfaces or dependency injection.
Unit and integration tests MUST NOT require a live BNM service or external network access.
Conversion rules, validation, XML parsing, error handling, and cache fallback MUST have
automated test coverage.

### IX. User Experience
The desktop interface MUST be clean and modern, with clear labels, predictable navigation,
accessible feedback, and responsive controls. Errors MUST be written in plain language, identify
the problem, and suggest a valid next action.

### X. Documentation
The repository MUST maintain README.md with setup and usage instructions and REPORT.md with the
implementation and verification report. Documentation MUST be updated whenever behavior,
configuration, data handling, or verification requirements change.

## Product Constraints
The application MUST obtain official exchange rates from the National Bank of Moldova.
The application MUST operate as a desktop application. The application MUST preserve the user's
rate source and effective date when converting currencies. The application MUST NOT present
freshness, source provenance, or calculation results ambiguously.

## Development Workflow
Changes MUST follow specification, plan, task, implementation, and verification stages.
Constitution compliance MUST be checked during specification review and implementation review.
The external coding agent MUST receive only generated specifications and approved implementation
tasks. Direct application implementation is deferred until specifications are complete.

Quality gates MUST verify decimal arithmetic, input rejection, BNM source provenance, effective
dates, cache fallback, malformed-response handling, test isolation from live HTTP services,
documentation completeness, and desktop UI behavior.

## Governance
This constitution supersedes other project practices where they conflict. Amendments require a
documented proposal, a semantic-version increment, and explicit approval by the project owner.
All pull requests and reviews MUST verify compliance with these principles.

Semantics of the version are:

- MAJOR for incompatible governance or principle removals or redefinitions.
- MINOR for new principles or materially expanded sections.
- PATCH for clarifications, wording fixes, or non-semantic refinements.

The compliance review MUST confirm that specifications are complete before implementation,
financial calculations use decimal arithmetic, error and cache paths are tested, source and date
provenance are visible, architecture boundaries are preserved, and documentation is current.

**Version**: 1.0.0 | **Ratified**: 2026-11-17 | **Last Amended**: 2026-11-17
