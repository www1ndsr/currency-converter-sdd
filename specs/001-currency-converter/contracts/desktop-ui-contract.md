# Desktop UI Contract

## Main Window

The primary window presents:

- A positive amount input field.
- Source and target currency selectors populated from the active complete rate set.
- A conversion button disabled while the amount is empty or either currency is unselected.
- A result area for the target amount, formatted to two decimal places.
- The effective rate date and the `National Bank of Moldova (BNM)` source.
- A visible rate status distinguishing live BNM data from local cached data.
- Loading and clear validation, network, invalid-data, and missing-rate feedback.

The light desktop interface must use readable labels and retain an understandable state after
expected errors. Network operations must not block interaction with the window.

## User Input

- Amount text accepts one decimal separator, either comma or period.
- A decimal separator must be followed by one or more digits. Mixed/multiple separators,
  alphabetic text, empty input, zero, negative values, NaN, and infinity are rejected.
- Accepted amount text is converted directly to Decimal; it is never parsed through binary
  floating point.
- Same-currency conversion validates the amount, returns it rounded to two places, and does not
  trigger a rate request.
- For a same-currency conversion performed before any rate data has been loaded, show that the
  effective date is not applicable because no exchange rate was used.

## Rate Load and Conversion States

| State | Required visible behavior |
|---|---|
| Loading | Show loading feedback; keep the window responsive |
| Live rates available | Identify BNM, effective date from the response, and live status |
| Empty date, prior date found | Use the first valid earlier response; identify its effective date and explain the date differs from the requested date |
| Network failure, valid cache | Automatically use the valid cache; identify cached status and its effective date |
| Network failure, no valid cache | Show an understandable error and remain operational |
| Malformed or partially valid response | Reject the whole response, preserve existing valid cache, show an understandable failure |
| Invalid amount | Show a validation message; do not display a newly calculated result |
| Missing selected currency | Explain that the selected currency is unavailable; do not calculate with a missing rate |

Every displayed conversion using a rate set must retain and show that same set's effective date,
source, and live/cache state.
