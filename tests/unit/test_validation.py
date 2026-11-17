"""Unit tests for input validation in currency_converter.validation."""

from decimal import Decimal
import pytest

from currency_converter.errors import ValidationError
from currency_converter.validation import parse_and_validate_amount, validate_currency_code


class TestAmountValidation:
    """Test suite for amount parsing and validation rules."""

    def test_valid_integer_amount(self):
        result = parse_and_validate_amount("100")
        assert result == Decimal("100")
        assert isinstance(result, Decimal)

    def test_valid_decimal_with_period(self):
        result = parse_and_validate_amount("123.45")
        assert result == Decimal("123.45")
        assert isinstance(result, Decimal)

    def test_valid_decimal_with_comma(self):
        result = parse_and_validate_amount("123,45")
        assert result == Decimal("123.45")
        assert isinstance(result, Decimal)

    def test_valid_with_surrounding_whitespace(self):
        result = parse_and_validate_amount("   50.75   ")
        assert result == Decimal("50.75")
        result_comma = parse_and_validate_amount("   50,75   ")
        assert result_comma == Decimal("50.75")

    def test_valid_leading_decimal_separator(self):
        assert parse_and_validate_amount(".75") == Decimal("0.75")
        assert parse_and_validate_amount(",75") == Decimal("0.75")

    def test_empty_string_rejected(self):
        with pytest.raises(ValidationError, match="Amount is required"):
            parse_and_validate_amount("")

    def test_whitespace_only_rejected(self):
        with pytest.raises(ValidationError, match="Amount is required"):
            parse_and_validate_amount("   ")

    def test_none_input_rejected(self):
        with pytest.raises(ValidationError, match="Amount is required"):
            parse_and_validate_amount(None)

    def test_alphabetic_characters_rejected(self):
        with pytest.raises(ValidationError, match="Invalid amount format"):
            parse_and_validate_amount("abc")

    def test_alphanumeric_mixed_rejected(self):
        with pytest.raises(ValidationError, match="Invalid amount format"):
            parse_and_validate_amount("100EUR")
        with pytest.raises(ValidationError, match="Invalid amount format"):
            parse_and_validate_amount("12a.34")

    def test_zero_amount_rejected(self):
        with pytest.raises(ValidationError, match="Amount must be greater than zero"):
            parse_and_validate_amount("0")
        with pytest.raises(ValidationError, match="Amount must be greater than zero"):
            parse_and_validate_amount("0.00")
        with pytest.raises(ValidationError, match="Amount must be greater than zero"):
            parse_and_validate_amount("0,0")

    def test_negative_amount_rejected(self):
        with pytest.raises(ValidationError, match="Negative numbers are not accepted"):
            parse_and_validate_amount("-10")
        with pytest.raises(ValidationError, match="Negative numbers are not accepted"):
            parse_and_validate_amount("-0.01")
        with pytest.raises(ValidationError, match="Negative numbers are not accepted"):
            parse_and_validate_amount("-50,25")

    def test_multiple_period_separators_rejected(self):
        with pytest.raises(ValidationError, match="Multiple or mixed decimal separators"):
            parse_and_validate_amount("1.2.3")
        with pytest.raises(ValidationError, match="Multiple or mixed decimal separators"):
            parse_and_validate_amount("10..5")

    def test_multiple_comma_separators_rejected(self):
        with pytest.raises(ValidationError, match="Multiple or mixed decimal separators"):
            parse_and_validate_amount("1,2,3")
        with pytest.raises(ValidationError, match="Multiple or mixed decimal separators"):
            parse_and_validate_amount("10,,5")

    def test_mixed_separators_thousand_formatting_rejected(self):
        # 1,234.50 or 1.234,50 are rejected per specification
        with pytest.raises(ValidationError, match="Multiple or mixed decimal separators"):
            parse_and_validate_amount("1,234.50")
        with pytest.raises(ValidationError, match="Multiple or mixed decimal separators"):
            parse_and_validate_amount("1.234,50")

    def test_trailing_separator_without_digits_rejected(self):
        with pytest.raises(ValidationError, match="followed by one or more digits"):
            parse_and_validate_amount("100.")
        with pytest.raises(ValidationError, match="followed by one or more digits"):
            parse_and_validate_amount("100,")

    def test_nan_rejected(self):
        with pytest.raises(ValidationError, match="valid finite number"):
            parse_and_validate_amount("NaN")
        with pytest.raises(ValidationError, match="valid finite number"):
            parse_and_validate_amount("nan")

    def test_infinity_rejected(self):
        with pytest.raises(ValidationError, match="valid finite number"):
            parse_and_validate_amount("Infinity")
        with pytest.raises(ValidationError, match="valid finite number"):
            parse_and_validate_amount("inf")
        with pytest.raises(ValidationError, match="valid finite number"):
            parse_and_validate_amount("-inf")

    def test_explicit_plus_sign_rejected(self):
        with pytest.raises(ValidationError, match="Invalid amount format"):
            parse_and_validate_amount("+100")

    def test_amount_exceeding_max_limit_rejected(self):
        with pytest.raises(ValidationError, match="exceeds the maximum supported"):
            parse_and_validate_amount("1000000000000001")


class TestCurrencyCodeValidation:
    """Test suite for currency code validation."""

    def test_valid_code_uppercase(self):
        assert validate_currency_code("EUR") == "EUR"

    def test_valid_code_lowercase_normalized(self):
        assert validate_currency_code("usd") == "USD"

    def test_valid_code_with_whitespace(self):
        assert validate_currency_code("  mdl  ") == "MDL"

    def test_empty_currency_code_rejected(self):
        with pytest.raises(ValidationError, match="must be selected"):
            validate_currency_code("")

    def test_none_currency_code_rejected(self):
        with pytest.raises(ValidationError, match="must be selected"):
            validate_currency_code(None)
