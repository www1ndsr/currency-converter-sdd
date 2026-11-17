"""Desktop graphical user interface using CustomTkinter."""

from datetime import date
from decimal import Decimal
from typing import Callable, List, Optional
import customtkinter as ctk

from currency_converter.models import BNM_SOURCE_NAME, Currency, RateState

# Theme and appearance per FR-027
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")


class MainWindow(ctk.CTk):
    """Main application window for the Currency Converter."""

    def __init__(
        self,
        on_convert_requested: Callable[[str, str, str], None],
        on_refresh_requested: Callable[[], None],
    ):
        super().__init__()

        self.on_convert_requested = on_convert_requested
        self.on_refresh_requested = on_refresh_requested

        # Window configuration
        self.title("BNM Currency Converter")
        self.geometry("640x720")
        self.minsize(560, 640)

        # UI state
        self._currencies: List[Currency] = []

        # Build UI layout
        self._create_widgets()
        self.update_convert_button_state()

    def _create_widgets(self) -> None:
        """Construct the modern light desktop layout."""
        # Main container with padding
        self.main_container = ctk.CTkFrame(self, corner_radius=12, fg_color="#F8FAFC")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        self.header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=20, pady=(15, 10))

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="Official Currency Converter",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#0F172A",
        )
        self.title_label.pack(anchor="w")

        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text="Exchange rates provided by the National Bank of Moldova (BNM)",
            font=ctk.CTkFont(size=13),
            text_color="#475569",
        )
        self.subtitle_label.pack(anchor="w", pady=(2, 0))

        # Input Card
        self.card_frame = ctk.CTkFrame(self.main_container, corner_radius=10, fg_color="#FFFFFF", border_width=1, border_color="#E2E8F0")
        self.card_frame.pack(fill="x", padx=20, pady=10)

        # Amount Input Section
        self.amount_label = ctk.CTkLabel(
            self.card_frame,
            text="Amount to Convert",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#1E293B",
        )
        self.amount_label.pack(anchor="w", padx=20, pady=(15, 5))

        self.amount_var = ctk.StringVar(value="")
        self.amount_var.trace_add("write", lambda *args: self.update_convert_button_state())

        self.amount_entry = ctk.CTkEntry(
            self.card_frame,
            textvariable=self.amount_var,
            placeholder_text="Enter positive amount (e.g. 100.00 or 100,00)",
            height=40,
            font=ctk.CTkFont(size=15),
        )
        self.amount_entry.pack(fill="x", padx=20, pady=(0, 15))

        # Currency Selectors Section
        self.currency_grid = ctk.CTkFrame(self.card_frame, fg_color="transparent")
        self.currency_grid.pack(fill="x", padx=20, pady=(0, 15))
        self.currency_grid.grid_columnconfigure((0, 2), weight=1)

        # Source Currency
        self.source_label = ctk.CTkLabel(
            self.currency_grid,
            text="From",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#334155",
        )
        self.source_label.grid(row=0, column=0, sticky="w", pady=(0, 5))

        self.source_var = ctk.StringVar(value="EUR")
        self.source_var.trace_add("write", lambda *args: self.update_convert_button_state())
        self.source_menu = ctk.CTkOptionMenu(
            self.currency_grid,
            variable=self.source_var,
            values=["EUR", "MDL", "USD"],
            height=38,
            font=ctk.CTkFont(size=14),
        )
        self.source_menu.grid(row=1, column=0, sticky="ew")

        # Swap Button
        self.swap_btn = ctk.CTkButton(
            self.currency_grid,
            text="⇄",
            width=42,
            height=38,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#F1F5F9",
            text_color="#0F172A",
            hover_color="#E2E8F0",
            command=self._swap_currencies,
        )
        self.swap_btn.grid(row=1, column=1, padx=10)

        # Target Currency
        self.target_label = ctk.CTkLabel(
            self.currency_grid,
            text="To",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#334155",
        )
        self.target_label.grid(row=0, column=2, sticky="w", pady=(0, 5))

        self.target_var = ctk.StringVar(value="MDL")
        self.target_var.trace_add("write", lambda *args: self.update_convert_button_state())
        self.target_menu = ctk.CTkOptionMenu(
            self.currency_grid,
            variable=self.target_var,
            values=["MDL", "EUR", "USD"],
            height=38,
            font=ctk.CTkFont(size=14),
        )
        self.target_menu.grid(row=1, column=2, sticky="ew")

        # Action Buttons Section
        self.button_frame = ctk.CTkFrame(self.card_frame, fg_color="transparent")
        self.button_frame.pack(fill="x", padx=20, pady=(5, 20))
        self.button_frame.grid_columnconfigure(0, weight=3)
        self.button_frame.grid_columnconfigure(1, weight=1)

        self.convert_button = ctk.CTkButton(
            self.button_frame,
            text="Convert",
            height=44,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self._on_convert_clicked,
        )
        self.convert_button.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.refresh_button = ctk.CTkButton(
            self.button_frame,
            text="Reload Rates",
            height=44,
            font=ctk.CTkFont(size=13),
            fg_color="#64748B",
            hover_color="#475569",
            command=self.on_refresh_requested,
        )
        self.refresh_button.grid(row=0, column=1, sticky="ew")

        # Loading / Progress Bar
        self.progress_bar = ctk.CTkProgressBar(self.main_container, mode="indeterminate", height=4)
        self.progress_bar.pack(fill="x", padx=20, pady=(2, 6))
        self.progress_bar.pack_forget()  # Hidden by default

        # Result Display Card
        self.result_card = ctk.CTkFrame(self.main_container, corner_radius=10, fg_color="#FFFFFF", border_width=1, border_color="#E2E8F0")
        self.result_card.pack(fill="x", padx=20, pady=10)

        self.result_header = ctk.CTkLabel(
            self.result_card,
            text="Conversion Result",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#64748B",
        )
        self.result_header.pack(anchor="w", padx=20, pady=(15, 2))

        self.result_value_label = ctk.CTkLabel(
            self.result_card,
            text="—",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#0F172A",
        )
        self.result_value_label.pack(anchor="w", padx=20, pady=(0, 5))

        self.rate_info_label = ctk.CTkLabel(
            self.result_card,
            text="",
            font=ctk.CTkFont(size=13),
            text_color="#475569",
        )
        self.rate_info_label.pack(anchor="w", padx=20, pady=(0, 15))

        # Status and Provenance Frame
        self.provenance_frame = ctk.CTkFrame(self.main_container, corner_radius=8, fg_color="#F1F5F9")
        self.provenance_frame.pack(fill="both", expand=True, padx=20, pady=(5, 10))

        # Metadata grid
        self.meta_grid = ctk.CTkFrame(self.provenance_frame, fg_color="transparent")
        self.meta_grid.pack(fill="x", padx=15, pady=(12, 6))
        self.meta_grid.grid_columnconfigure((0, 1, 2), weight=1)

        # Source
        self.source_title = ctk.CTkLabel(self.meta_grid, text="Source", font=ctk.CTkFont(size=11, weight="bold"), text_color="#64748B")
        self.source_title.grid(row=0, column=0, sticky="w")
        self.source_val_label = ctk.CTkLabel(self.meta_grid, text=BNM_SOURCE_NAME, font=ctk.CTkFont(size=12, weight="bold"), text_color="#0F172A")
        self.source_val_label.grid(row=1, column=0, sticky="w")

        # Effective Date
        self.date_title = ctk.CTkLabel(self.meta_grid, text="Effective Date", font=ctk.CTkFont(size=11, weight="bold"), text_color="#64748B")
        self.date_title.grid(row=0, column=1, sticky="w")
        self.date_val_label = ctk.CTkLabel(self.meta_grid, text="Loading...", font=ctk.CTkFont(size=12, weight="bold"), text_color="#0F172A")
        self.date_val_label.grid(row=1, column=1, sticky="w")

        # Rate State Status Badge
        self.state_title = ctk.CTkLabel(self.meta_grid, text="Rate Status", font=ctk.CTkFont(size=11, weight="bold"), text_color="#64748B")
        self.state_title.grid(row=0, column=2, sticky="w")
        self.state_val_label = ctk.CTkLabel(
            self.meta_grid,
            text="INITIALIZING",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#2563EB",
        )
        self.state_val_label.grid(row=1, column=2, sticky="w")

        # Status / Feedback Message Banner
        self.status_msg_label = ctk.CTkLabel(
            self.provenance_frame,
            text="Initializing exchange rates...",
            font=ctk.CTkFont(size=12),
            text_color="#334155",
            wraplength=520,
            justify="left",
        )
        self.status_msg_label.pack(fill="x", padx=15, pady=(4, 12), anchor="w")

    def _swap_currencies(self) -> None:
        """Swap selected source and target currencies."""
        src = self.source_var.get()
        tgt = self.target_var.get()
        self.source_var.set(tgt)
        self.target_var.set(src)

    def _on_convert_clicked(self) -> None:
        """Trigger conversion callback."""
        amount = self.amount_var.get()
        source = self.source_var.get()
        target = self.target_var.get()
        self.on_convert_requested(amount, source, target)

    def update_convert_button_state(self) -> None:
        """
        Enforce FR-003: The conversion button MUST remain disabled until
        the amount field is non-empty and both currency selectors have a selection.
        """
        amount_text = self.amount_var.get().strip()
        source_sel = self.source_var.get().strip()
        target_sel = self.target_var.get().strip()

        if amount_text and source_sel and target_sel:
            self.convert_button.configure(state="normal")
        else:
            self.convert_button.configure(state="disabled")

    def set_loading(self, loading: bool, message: str = "Loading exchange rates from BNM...") -> None:
        """Display loading feedback without blocking GUI interactions (FR-028, FR-030)."""
        if loading:
            self.progress_bar.pack(fill="x", padx=20, pady=(2, 6))
            self.progress_bar.start()
            self.refresh_button.configure(state="disabled")
            self.status_msg_label.configure(text=message, text_color="#2563EB")
        else:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
            self.refresh_button.configure(state="normal")

    def populate_currencies(self, currencies: List[Currency], default_source: str = "EUR", default_target: str = "MDL") -> None:
        """Populate source and target dropdown selectors with available currencies."""
        self._currencies = currencies
        options = [c.code for c in currencies]

        if not options:
            options = ["MDL"]

        self.source_menu.configure(values=options)
        self.target_menu.configure(values=options)

        # Set default selections if valid
        if default_source in options:
            self.source_var.set(default_source)
        elif options:
            self.source_var.set(options[0])

        if default_target in options:
            self.target_var.set(default_target)
        elif len(options) > 1:
            self.target_var.set(options[1])
        elif options:
            self.target_var.set(options[0])

        self.update_convert_button_state()

    def show_conversion_result(
        self,
        amount: Decimal,
        source_code: str,
        target_amount: Decimal,
        target_code: str,
        effective_date: Optional[date],
        source: str,
        rate_state: RateState,
        rate_info: Optional[str] = None,
    ) -> None:
        """Render successful conversion result formatted to two decimal places."""
        formatted_result = f"{target_amount:,.2f} {target_code}"
        self.result_value_label.configure(
            text=formatted_result,
            text_color="#0F172A",
        )

        if rate_info:
            self.rate_info_label.configure(text=rate_info, text_color="#475569")
        else:
            self.rate_info_label.configure(
                text=f"{amount:,.2f} {source_code} = {target_amount:,.2f} {target_code}",
                text_color="#475569",
            )

        self.source_val_label.configure(text=source)

        # Display effective date
        if effective_date is not None:
            self.date_val_label.configure(text=effective_date.strftime("%d.%m.%Y"))
        else:
            self.date_val_label.configure(text="Not Applicable")

        # Rate status badge
        self._update_rate_state_badge(rate_state)

    def show_error(self, message: str) -> None:
        """Display an understandable error message in the status banner."""
        self.status_msg_label.configure(
            text=f"⚠️ {message}",
            text_color="#DC2626",
        )

    def show_status(self, message: str, rate_state: RateState, effective_date: Optional[date]) -> None:
        """Update status message and metadata labels."""
        self.status_msg_label.configure(text=message, text_color="#334155")

        if effective_date is not None:
            self.date_val_label.configure(text=effective_date.strftime("%d.%m.%Y"))
        else:
            self.date_val_label.configure(text="Not Applicable")

        self._update_rate_state_badge(rate_state)

    def _update_rate_state_badge(self, rate_state: RateState) -> None:
        """Render rate state badge with distinct color."""
        if rate_state == RateState.LIVE:
            self.state_val_label.configure(text="LIVE (BNM)", text_color="#16A34A")
        elif rate_state == RateState.CACHED:
            self.state_val_label.configure(text="CACHED", text_color="#D97706")
        else:
            self.state_val_label.configure(text="NOT APPLICABLE", text_color="#64748B")
