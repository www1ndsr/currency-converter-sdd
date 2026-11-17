"""BNM (National Bank of Moldova) exchange-rate client and XML parser."""

from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Dict, Optional
import xml.etree.ElementTree as ET

import requests

from currency_converter.errors import EmptyDateError, NetworkError, RateParsingError
from currency_converter.models import (
    BNM_SOURCE_NAME,
    MDL_CURRENCY_CODE,
    MDL_CURRENCY_NAME,
    Currency,
    ExchangeRateSet,
)

DEFAULT_BNM_URL = "https://www.bnm.md/en/official_exchange_rates"
DEFAULT_TIMEOUT_SECONDS = 10.0


class BnmClient:
    """Client for fetching and parsing official exchange rates from BNM."""

    def __init__(self, base_url: str = DEFAULT_BNM_URL, timeout: float = DEFAULT_TIMEOUT_SECONDS):
        self.base_url = base_url
        self.timeout = timeout

    def build_url(self, target_date: date) -> str:
        """Format the date as DD.MM.YYYY and construct the request URL."""
        date_str = target_date.strftime("%d.%m.%Y")
        return f"{self.base_url}?get_xml=1&date={date_str}"

    def fetch_rates_for_date(
        self,
        target_date: date,
        session: Optional[requests.Session] = None,
    ) -> ExchangeRateSet:
        """
        Request official exchange rates for target_date from BNM.
        
        Raises:
            NetworkError: On connection failure, timeout, or HTTP error.
            EmptyDateError: If response body is empty or contains no currency records.
            RateParsingError: If XML is malformed, missing fields, or contains invalid rates.
        """
        url = self.build_url(target_date)
        http = session or requests

        try:
            response = http.get(url, timeout=self.timeout)
        except requests.Timeout as exc:
            raise NetworkError(f"Request to BNM timed out for date {target_date.strftime('%d.%m.%Y')}", str(exc)) from exc
        except requests.RequestException as exc:
            raise NetworkError(f"Network error while connecting to BNM for date {target_date.strftime('%d.%m.%Y')}", str(exc)) from exc

        if response.status_code != 200:
            raise NetworkError(f"BNM returned HTTP status {response.status_code} for date {target_date.strftime('%d.%m.%Y')}")

        return self.parse_rates_xml(response.text)

    def parse_rates_xml(self, xml_text: str) -> ExchangeRateSet:
        """
        Parse raw BNM XML response into a validated ExchangeRateSet.
        
        Strict whole-response validation: any missing field, malformed XML,
        duplicate code, or invalid decimal invalidates the entire response.
        """
        if not xml_text or not xml_text.strip():
            raise EmptyDateError("BNM response body is empty.")

        try:
            root = ET.fromstring(xml_text.strip())
        except ET.ParseError as exc:
            raise RateParsingError("Malformed XML received from BNM", str(exc)) from exc

        if root.tag != "ValCurs":
            raise RateParsingError(f"Expected root tag 'ValCurs', found '{root.tag}'")

        date_attr = root.attrib.get("Date")
        if not date_attr or not date_attr.strip():
            raise RateParsingError("Missing 'Date' attribute on ValCurs root element.")

        try:
            effective_date = datetime.strptime(date_attr.strip(), "%d.%m.%Y").date()
        except ValueError as exc:
            raise RateParsingError(f"Invalid date format '{date_attr}' on ValCurs (expected DD.MM.YYYY)", str(exc)) from exc

        valute_elements = root.findall("Valute")
        if not valute_elements:
            raise EmptyDateError(f"No currency rates found in BNM response for date {date_attr}")

        currencies: Dict[str, Currency] = {}

        for valute in valute_elements:
            char_code_el = valute.find("CharCode")
            name_el = valute.find("Name")
            nominal_el = valute.find("Nominal")
            value_el = valute.find("Value")

            if char_code_el is None or not (char_code_el.text or "").strip():
                raise RateParsingError("Valute entry missing required CharCode element.")
            if name_el is None or not (name_el.text or "").strip():
                raise RateParsingError("Valute entry missing required Name element.")
            if nominal_el is None or not (nominal_el.text or "").strip():
                raise RateParsingError("Valute entry missing required Nominal element.")
            if value_el is None or not (value_el.text or "").strip():
                raise RateParsingError("Valute entry missing required Value element.")

            code = char_code_el.text.strip().upper()
            if code in currencies:
                raise RateParsingError(f"Duplicate currency code '{code}' in BNM response.")

            name = name_el.text.strip()

            try:
                # Nominal is usually integer or decimal
                nominal_str = nominal_el.text.strip().replace(",", ".")
                nominal = Decimal(nominal_str)
                if not nominal.is_finite() or nominal <= Decimal("0"):
                    raise RateParsingError(f"Invalid nominal '{nominal_el.text}' for currency {code}.")
            except (InvalidOperation, ValueError) as exc:
                raise RateParsingError(f"Cannot parse nominal '{nominal_el.text}' for currency {code}", str(exc)) from exc

            try:
                value_str = value_el.text.strip().replace(",", ".")
                value = Decimal(value_str)
                if not value.is_finite() or value <= Decimal("0"):
                    raise RateParsingError(f"Invalid value '{value_el.text}' for currency {code}.")
            except (InvalidOperation, ValueError) as exc:
                raise RateParsingError(f"Cannot parse value '{value_el.text}' for currency {code}", str(exc)) from exc

            rate_mdl_per_unit = value / nominal

            currencies[code] = Currency(
                code=code,
                name=name,
                nominal=nominal,
                value=value,
                rate_mdl_per_unit=rate_mdl_per_unit,
            )

        # Ensure base currency MDL is present with rate exactly 1
        currencies[MDL_CURRENCY_CODE] = Currency(
            code=MDL_CURRENCY_CODE,
            name=MDL_CURRENCY_NAME,
            nominal=Decimal("1"),
            value=Decimal("1"),
            rate_mdl_per_unit=Decimal("1"),
        )

        return ExchangeRateSet(
            effective_date=effective_date,
            retrieved_at=datetime.now(timezone.utc),
            currencies=currencies,
            source=BNM_SOURCE_NAME,
        )
