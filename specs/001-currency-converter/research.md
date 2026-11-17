# Research: Currency Converter

## Decisions

### Desktop UI

- **Decision**: Use CustomTkinter for the single-window graphical desktop UI.
- **Rationale**: It is the user-selected toolkit and provides the required desktop controls without
  introducing a separate web stack.
- **Alternatives considered**: A console interface is explicitly prohibited. A browser-based UI
  would add an unnecessary server/client architecture.

### HTTP and XML

- **Decision**: Use requests for BNM HTTP access and `xml.etree.ElementTree` for XML parsing.
- **Rationale**: Both are specified. The official endpoint's observed XML uses a `ValCurs` root
  with a `Date` attribute and child `Valute` records containing `CharCode`, `Nominal`, `Name`, and
  `Value`. See [BNM XML endpoint](https://www.bnm.md/en/official_exchange_rates?get_xml=1&date=17.11.2026).
- **Alternatives considered**: No alternative HTTP client or XML library is needed.
- **Boundary**: Treat the endpoint's XML as untrusted input. Validate the full document and all
  required records before returning or caching it.

### Decimal and Rounding

- **Decision**: Use `decimal.Decimal` for input amounts, parsed nominal/value, normalized rates,
  and conversion arithmetic. Parse XML numeric text from strings and never route values through
  binary floating point. Quantize only the displayed result to `0.01` with `ROUND_HALF_UP`.
- **Rationale**: This preserves exact decimal source values and gives deterministic two-place
  presentation consistent with the financial correctness principle.
- **Alternatives considered**: Binary floats are prohibited. Rounding intermediate rates would
  accumulate unnecessary error.

### Persistent Cache

- **Decision**: Store every validated response as a rate-set record in a JSON file using Decimal
  strings and an injectable path. Use atomic replacement when saving and choose the latest
  retrieved valid record for offline fallback.
- **Rationale**: JSON and pathlib are specified; atomic replacement protects the previous valid
  cache from partial writes and application interruption.
- **Alternatives considered**: A database is unnecessary for the small local data set and would
  add operational complexity.

### Responsive Network Access

- **Decision**: Run all HTTP operations and backward-date requests away from the GUI event loop;
  marshal resulting state back to the UI thread.
- **Rationale**: CustomTkinter widgets must be updated by the GUI thread, while FR-030 requires
  network operations not to block interaction.
- **Alternatives considered**: Synchronous requests on the GUI thread would freeze the interface.
  A process pool or async framework is unnecessary for this application.

### Backward Search

- **Decision**: On an empty BNM response, check the requested date and then each prior calendar
  date, stopping at the first valid official response or after reaching 14 calendar days earlier.
- **Rationale**: This implements the clarified specification and selects the most recent prior
  rate available within the limit. Network and malformed-response failures are not interpreted as
  a date with no publication.
- **Alternatives considered**: Searching beyond the limit is not specified and could make retrieval
  latency unpredictable.

## Resolved Inputs

- Product behavior and acceptance criteria: `spec.md`.
- Project principles: `.specify/memory/constitution.md`.
- Required runtime, GUI, transport, parsing, arithmetic, storage, and test tools: user-provided
  technology choices.
- No framework or package version pinning is specified; implementation must select versions
  compatible with Python 3.11+ and document them in the dependency manifest.
