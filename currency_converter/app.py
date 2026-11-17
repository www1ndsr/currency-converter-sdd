"""Application entry point and threading coordinator between UI and Orchestration."""

from decimal import Decimal
import threading
from typing import Optional

from currency_converter.bnm import BnmClient
from currency_converter.cache import CacheService
from currency_converter.errors import CurrencyConverterError
from currency_converter.models import RateState
from currency_converter.orchestration import ConversionOrchestrator, RateRetrievalResult
from currency_converter.ui import MainWindow
from currency_converter.validation import parse_and_validate_amount


class CurrencyConverterApp:
    """Main application manager coordinating the GUI and background services."""

    def __init__(
        self,
        bnm_client: Optional[BnmClient] = None,
        cache_service: Optional[CacheService] = None,
    ):
        self.orchestrator = ConversionOrchestrator(
            bnm_client=bnm_client,
            cache_service=cache_service,
        )

        self.window = MainWindow(
            on_convert_requested=self.handle_convert,
            on_refresh_requested=self.trigger_rate_refresh,
        )

    def start(self) -> None:
        """Initialize rates asynchronously and launch the desktop event loop."""
        # Initiate asynchronous initial rate retrieval
        self.trigger_rate_refresh()
        self.window.mainloop()

    def trigger_rate_refresh(self) -> None:
        """Launch background worker thread to load official exchange rates."""
        self.window.set_loading(True, "Contacting National Bank of Moldova (BNM)...")

        worker = threading.Thread(
            target=self._async_fetch_rates,
            daemon=True,
            name="BNM-Rate-Loader",
        )
        worker.start()

    def _async_fetch_rates(self) -> None:
        """Worker thread entry point for network rate loading."""
        result = self.orchestrator.load_rates()
        # Safe thread handoff to Tkinter main thread
        self.window.after(0, self._on_rates_loaded, result)

    def _on_rates_loaded(self, result: RateRetrievalResult) -> None:
        """Handle rate retrieval completion on the main GUI thread."""
        self.window.set_loading(False)

        # Populate currency dropdowns with the loaded rates
        currencies = self.orchestrator.get_available_currencies()
        self.window.populate_currencies(
            currencies=currencies,
            default_source="EUR",
            default_target="MDL",
        )

        if result.error_message:
            self.window.show_error(result.error_message)
        else:
            self.window.show_status(
                message=result.status_message,
                rate_state=result.rate_state,
                effective_date=result.effective_date,
            )

    def handle_convert(self, raw_amount: str, source_code: str, target_code: str) -> None:
        """Handle user conversion request triggered from GUI."""
        try:
            # Parse amount first for display in result info
            amount = parse_and_validate_amount(raw_amount)

            res = self.orchestrator.convert(
                raw_amount=raw_amount,
                source_code=source_code,
                target_code=target_code,
            )

            rate_info = None
            if res.source_rate and res.target_rate and res.source_code != res.target_code:
                # E.g. "1 EUR = 19.5000 MDL (BNM normalized rate)"
                rate_info = f"Rates: 1 {res.source_code} = {res.source_rate} MDL | 1 {res.target_code} = {res.target_rate} MDL"

            self.window.show_conversion_result(
                amount=amount,
                source_code=res.source_code,
                target_amount=res.amount_in_target,
                target_code=res.target_code,
                effective_date=res.effective_date,
                source=res.source,
                rate_state=res.rate_state,
                rate_info=rate_info,
            )

            # Clear any previous error in status banner
            if self.orchestrator.active_rate_state != RateState.NOT_APPLICABLE:
                self.window.show_status(
                    message=self.orchestrator.last_status_message or "Conversion completed successfully.",
                    rate_state=self.orchestrator.active_rate_state,
                    effective_date=res.effective_date,
                )

        except CurrencyConverterError as err:
            self.window.show_error(err.message)
        except Exception as exc:
            self.window.show_error(f"Unexpected error: {exc}")


def main() -> None:
    """Executable main function."""
    app = CurrencyConverterApp()
    app.start()


if __name__ == "__main__":
    main()
