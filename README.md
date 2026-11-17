# Currency Converter (BNM)

A modern, resilient desktop currency converter application using official daily exchange rates from the **National Bank of Moldova (BNM)**. Built in accordance with Spec-Driven Development principles and precise financial calculation standards.

---

## Features

- **Official BNM Rates**: Automatically loads official exchange rates from BNM's XML service (`https://www.bnm.md/en/official_exchange_rates`).
- **Precise Financial Arithmetic**: Employs `decimal.Decimal` throughout parsing, normalization, conversion, and rounding. No binary floating-point math is used.
- **Deterministic Rounding**: Quantizes displayed results to two decimal places using Decimal `ROUND_HALF_UP`. Intermediate calculations maintain full Decimal precision.
- **Weekend & Holiday Resilience**: Automatically searches backward up to 14 calendar days when an official rate is not published on a weekend or public holiday, informing the user of the effective date.
- **Offline Cache**: Automatically persists every validated BNM rate response to local storage (`rates_cache.json`) via atomic replacement. Gracefully falls back to cached rates if the network is unavailable, clearly labeling the data as cached.
- **Robust Input Validation**: Accepts amounts with either period (`.`) or comma (`,`) decimal separators. Rejects negative numbers, zero, text, non-finite values (NaN/Infinity), and multiple/mixed separators with clear user feedback.
- **Same-Currency Fast Path**: Converts identical currencies (e.g., USD to USD or MDL to MDL) instantly without requiring network access or exchange rates.
- **Responsive GUI**: Developed with CustomTkinter. All network and backward-search calls run asynchronously on background worker threads, keeping the desktop interface fluid and responsive.

---

## Architecture Overview

The application follows a clean layered architecture with unidirectional dependencies:

```text
currency_converter/
├── __init__.py           # Package definition
├── __main__.py           # Command-line entry point
├── app.py                # Main application coordinator & thread boundaries
├── bnm.py                # BNM HTTP client & XML parser (all-or-nothing validation)
├── cache.py              # Persistent local JSON cache with atomic file replacement
├── conversion.py         # Decimal calculation engine & rounding rules
├── errors.py             # Custom domain and infrastructure exceptions
├── models.py             # Strongly typed dataclasses (Currency, ExchangeRateSet, etc.)
├── orchestration.py      # Business workflows, multi-day fallback, error mapping
├── serialization.py      # Decimal string & ISO date serialization helpers
├── ui.py                 # CustomTkinter modern desktop presentation
└── validation.py         # Strict amount and currency input validation
```

---

## Prerequisites

- **Python**: Version 3.11 or newer
- **Operating System**: Windows, macOS, or Linux with desktop graphical support

---

## Installation

1. **Clone or navigate to the repository**:
   ```bash
   cd currency-converter-sdd
   ```

2. **Create and activate a virtual environment**:
   - On Windows (PowerShell):
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - On Linux / macOS:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Running the Application

Launch the desktop application via:

```bash
python -m currency_converter
```

Or execute directly:
```bash
python currency_converter/app.py
```

---

## Conversion Formulas & Precision Policy

- **Rate Normalization**:
  $$\text{rate\_mdl\_per\_unit} = \frac{\text{Value}}{\text{Nominal}}$$
  *(For example, 100 JPY at 12.50 MDL produces 0.1250 MDL per JPY).*
  MDL is the base currency with an exact rate of `1`.

- **Cross-Currency Conversion**:
  $$\text{target\_amount} = \text{amount} \times \frac{\text{source\_rate}}{\text{target\_rate}}$$

- **Quantization**:
  The final displayed amount is rounded to two decimal places:
  `result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)`.

---

## Data Provenance & Transparency

Every rate-based conversion explicitly displays:
1. **Source**: `National Bank of Moldova (BNM)`
2. **Effective Date**: The official publication date parsed from the BNM XML `Date` attribute.
3. **Status**:
   - `LIVE (BNM)`: Fresh official data retrieved directly from BNM.
   - `CACHED`: Network unavailable; retrieved from local persistent storage.
   - `NOT APPLICABLE`: Used for same-currency conversions when no exchange rate was required.

---

## Running Tests

Automated testing is configured with `pytest`. All tests isolate network boundaries using mocks:

```bash
pytest
```
