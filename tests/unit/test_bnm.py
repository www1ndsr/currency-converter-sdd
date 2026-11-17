"""Unit tests for BNM client and XML parsing in currency_converter.bnm."""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest
import requests

from currency_converter.bnm import BnmClient, DEFAULT_BNM_URL
from currency_converter.errors import EmptyDateError, NetworkError, RateParsingError


VALID_BNM_XML = """<?xml version="1.0" encoding="utf-8"?>
<ValCurs Date="17.11.2026" name="Official exchange rates">
    <Valute ID="47">
        <NumCode>978</NumCode>
        <CharCode>EUR</CharCode>
        <Nominal>1</Nominal>
        <Name>Euro</Name>
        <Value>20.1666</Value>
    </Valute>
    <Valute ID="44">
        <NumCode>840</NumCode>
        <CharCode>USD</CharCode>
        <Nominal>1</Nominal>
        <Name>US Dollar</Name>
        <Value>18.5000</Value>
    </Valute>
    <Valute ID="40">
        <NumCode>392</NumCode>
        <CharCode>JPY</CharCode>
        <Nominal>100</Nominal>
        <Name>Japanese Yen</Name>
        <Value>12.2500</Value>
    </Valute>
</ValCurs>
"""


class TestBnmXmlParser:
    """Test suite for parsing and validating BNM XML responses."""

    def test_parse_valid_xml(self):
        client = BnmClient()
        rate_set = client.parse_rates_xml(VALID_BNM_XML)

        assert rate_set.effective_date == date(2026, 11, 17)
        assert rate_set.source == "National Bank of Moldova (BNM)"
        assert "EUR" in rate_set.currencies
        assert "USD" in rate_set.currencies
        assert "JPY" in rate_set.currencies
        assert "MDL" in rate_set.currencies

        eur = rate_set.currencies["EUR"]
        assert eur.code == "EUR"
        assert eur.name == "Euro"
        assert eur.nominal == Decimal("1")
        assert eur.value == Decimal("20.1666")
        assert eur.rate_mdl_per_unit == Decimal("20.1666")

    def test_parse_nominal_greater_than_one(self):
        client = BnmClient()
        rate_set = client.parse_rates_xml(VALID_BNM_XML)
        jpy = rate_set.currencies["JPY"]

        assert jpy.code == "JPY"
        assert jpy.nominal == Decimal("100")
        assert jpy.value == Decimal("12.2500")
        # 12.2500 / 100 = 0.1225
        assert jpy.rate_mdl_per_unit == Decimal("0.1225")

    def test_mdl_base_rate_included(self):
        client = BnmClient()
        rate_set = client.parse_rates_xml(VALID_BNM_XML)
        mdl = rate_set.currencies["MDL"]

        assert mdl.code == "MDL"
        assert mdl.rate_mdl_per_unit == Decimal("1")
        assert mdl.nominal == Decimal("1")
        assert mdl.value == Decimal("1")

    def test_empty_string_response_raises_empty_date_error(self):
        client = BnmClient()
        with pytest.raises(EmptyDateError, match="response body is empty"):
            client.parse_rates_xml("")
        with pytest.raises(EmptyDateError, match="response body is empty"):
            client.parse_rates_xml("   \n  ")

    def test_valid_xml_with_no_valute_records_raises_empty_date_error(self):
        xml_no_rates = """<?xml version="1.0" encoding="utf-8"?>
        <ValCurs Date="15.11.2026" name="Official exchange rates">
        </ValCurs>"""
        client = BnmClient()
        with pytest.raises(EmptyDateError, match="No currency rates found"):
            client.parse_rates_xml(xml_no_rates)

    def test_malformed_xml_raises_rate_parsing_error(self):
        truncated_xml = """<ValCurs Date="17.11.2026"><Valute><CharCode>EUR</Valute>"""
        client = BnmClient()
        with pytest.raises(RateParsingError, match="Malformed XML"):
            client.parse_rates_xml(truncated_xml)

    def test_wrong_root_tag_raises_rate_parsing_error(self):
        wrong_root = """<Rates Date="17.11.2026"><Valute><CharCode>EUR</CharCode></Valute></Rates>"""
        client = BnmClient()
        with pytest.raises(RateParsingError, match="Expected root tag 'ValCurs'"):
            client.parse_rates_xml(wrong_root)

    def test_missing_date_attribute_raises_rate_parsing_error(self):
        no_date = """<ValCurs name="Rates"><Valute><CharCode>EUR</CharCode></Valute></ValCurs>"""
        client = BnmClient()
        with pytest.raises(RateParsingError, match="Missing 'Date' attribute"):
            client.parse_rates_xml(no_date)

    def test_invalid_date_format_raises_rate_parsing_error(self):
        bad_date = """<ValCurs Date="2026-11-17"><Valute><CharCode>EUR</CharCode></Valute></ValCurs>"""
        client = BnmClient()
        with pytest.raises(RateParsingError, match="Invalid date format"):
            client.parse_rates_xml(bad_date)

    def test_missing_char_code_raises_rate_parsing_error(self):
        missing_code = """<ValCurs Date="17.11.2026">
            <Valute><Name>Euro</Name><Nominal>1</Nominal><Value>20.1666</Value></Valute>
        </ValCurs>"""
        client = BnmClient()
        with pytest.raises(RateParsingError, match="missing required CharCode"):
            client.parse_rates_xml(missing_code)

    def test_missing_name_raises_rate_parsing_error(self):
        missing_name = """<ValCurs Date="17.11.2026">
            <Valute><CharCode>EUR</CharCode><Nominal>1</Nominal><Value>20.1666</Value></Valute>
        </ValCurs>"""
        client = BnmClient()
        with pytest.raises(RateParsingError, match="missing required Name"):
            client.parse_rates_xml(missing_name)

    def test_missing_nominal_raises_rate_parsing_error(self):
        missing_nominal = """<ValCurs Date="17.11.2026">
            <Valute><CharCode>EUR</CharCode><Name>Euro</Name><Value>20.1666</Value></Valute>
        </ValCurs>"""
        client = BnmClient()
        with pytest.raises(RateParsingError, match="missing required Nominal"):
            client.parse_rates_xml(missing_nominal)

    def test_missing_value_raises_rate_parsing_error(self):
        missing_val = """<ValCurs Date="17.11.2026">
            <Valute><CharCode>EUR</CharCode><Name>Euro</Name><Nominal>1</Nominal></Valute>
        </ValCurs>"""
        client = BnmClient()
        with pytest.raises(RateParsingError, match="missing required Value"):
            client.parse_rates_xml(missing_val)

    def test_invalid_non_numeric_nominal_raises_rate_parsing_error(self):
        bad_nom = """<ValCurs Date="17.11.2026">
            <Valute><CharCode>EUR</CharCode><Name>Euro</Name><Nominal>ABC</Nominal><Value>20.16</Value></Valute>
        </ValCurs>"""
        client = BnmClient()
        with pytest.raises(RateParsingError, match="Cannot parse nominal"):
            client.parse_rates_xml(bad_nom)

    def test_zero_or_negative_nominal_raises_rate_parsing_error(self):
        zero_nom = """<ValCurs Date="17.11.2026">
            <Valute><CharCode>EUR</CharCode><Name>Euro</Name><Nominal>0</Nominal><Value>20.16</Value></Valute>
        </ValCurs>"""
        client = BnmClient()
        with pytest.raises(RateParsingError, match="Invalid nominal"):
            client.parse_rates_xml(zero_nom)

    def test_invalid_non_numeric_value_raises_rate_parsing_error(self):
        bad_val = """<ValCurs Date="17.11.2026">
            <Valute><CharCode>EUR</CharCode><Name>Euro</Name><Nominal>1</Nominal><Value>INVALID</Value></Valute>
        </ValCurs>"""
        client = BnmClient()
        with pytest.raises(RateParsingError, match="Cannot parse value"):
            client.parse_rates_xml(bad_val)

    def test_zero_or_negative_value_raises_rate_parsing_error(self):
        neg_val = """<ValCurs Date="17.11.2026">
            <Valute><CharCode>EUR</CharCode><Name>Euro</Name><Nominal>1</Nominal><Value>-20.16</Value></Valute>
        </ValCurs>"""
        client = BnmClient()
        with pytest.raises(RateParsingError, match="Invalid value"):
            client.parse_rates_xml(neg_val)

    def test_duplicate_currency_codes_raises_rate_parsing_error(self):
        dup_xml = """<ValCurs Date="17.11.2026">
            <Valute><CharCode>EUR</CharCode><Name>Euro</Name><Nominal>1</Nominal><Value>20.16</Value></Valute>
            <Valute><CharCode>EUR</CharCode><Name>Euro 2</Name><Nominal>1</Nominal><Value>20.20</Value></Valute>
        </ValCurs>"""
        client = BnmClient()
        with pytest.raises(RateParsingError, match="Duplicate currency code 'EUR'"):
            client.parse_rates_xml(dup_xml)


class TestBnmHttpClient:
    """Test suite for HTTP communication and error handling using mocks."""

    def test_build_url_date_formatting(self):
        client = BnmClient()
        test_date = date(2026, 5, 9)
        url = client.build_url(test_date)
        assert url == f"{DEFAULT_BNM_URL}?get_xml=1&date=09.05.2026"

    @patch("requests.get")
    def test_successful_fetch(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = VALID_BNM_XML
        mock_get.return_value = mock_response

        client = BnmClient(timeout=8.0)
        rate_set = client.fetch_rates_for_date(date(2026, 11, 17))

        assert rate_set.effective_date == date(2026, 11, 17)
        mock_get.assert_called_once_with(
            f"{DEFAULT_BNM_URL}?get_xml=1&date=17.11.2026",
            timeout=8.0,
        )

    @patch("requests.get")
    def test_http_status_error_raises_network_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_get.return_value = mock_response

        client = BnmClient()
        with pytest.raises(NetworkError, match="HTTP status 503"):
            client.fetch_rates_for_date(date(2026, 11, 17))

    @patch("requests.get")
    def test_network_timeout_raises_network_error(self, mock_get):
        mock_get.side_effect = requests.Timeout("Connection timed out")

        client = BnmClient()
        with pytest.raises(NetworkError, match="timed out"):
            client.fetch_rates_for_date(date(2026, 11, 17))

    @patch("requests.get")
    def test_connection_error_raises_network_error(self, mock_get):
        mock_get.side_effect = requests.ConnectionError("Name or service not known")

        client = BnmClient()
        with pytest.raises(NetworkError, match="Network error while connecting"):
            client.fetch_rates_for_date(date(2026, 11, 17))
