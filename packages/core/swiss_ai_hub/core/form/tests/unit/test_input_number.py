from swiss_ai_hub.core.form.elements.input_number import InputNumber
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class TestInputNumberValidation:
    def test_integer_bounds_render_without_decimal(self) -> None:
        element = InputNumber(label=LocaleString(en="Age"), min=0, max=120)
        assert "min:0" in element.validation
        assert "max:120" in element.validation

    def test_float_bounds_strip_trailing_zeros(self) -> None:
        element = InputNumber(label=LocaleString(en="Temperature"), min=0.5, max=1.0)
        assert "min:0.5" in element.validation
        assert "max:1" in element.validation

    def test_large_bounds_do_not_use_scientific_notation(self) -> None:
        element = InputNumber(label=LocaleString(en="Big"), min=1_000_000, max=10_000_000)
        assert "min:1000000|" in element.validation + "|"
        assert "max:10000000" in element.validation
        assert "1e+" not in element.validation
        assert "1E+" not in element.validation

    def test_small_fractional_bounds_do_not_use_scientific_notation(self) -> None:
        element = InputNumber(label=LocaleString(en="Tiny"), min=0.00001, max=0.0001)
        assert "min:0.00001" in element.validation
        assert "max:0.0001" in element.validation
        assert "1e-" not in element.validation
        assert "1E-" not in element.validation

    def test_sub_micro_bounds_keep_full_precision(self) -> None:
        # Regression: format(1e-7, "f").rstrip("0").rstrip(".") returned "0",
        # silently widening the bound. Verify sub-1e-6 values keep their decimals.
        element = InputNumber(label=LocaleString(en="Sub-micro"), min=1e-7, max=1e-6)
        assert "min:0.0000001" in element.validation
        assert "max:0.000001" in element.validation
        assert "min:0|" not in element.validation + "|"
        assert "max:0|" not in element.validation + "|"
        assert "e-" not in element.validation
        assert "E-" not in element.validation


class TestInputNumberFractionDigits:
    """PrimeVue InputNumber is integer-only unless fraction digits are configured, so a
    fractional field must auto-enable decimals (otherwise the decimal point is rejected)."""

    def test_fractional_step_enables_decimals(self) -> None:
        element = InputNumber(label=LocaleString(en="Temperature"), min=0.0, max=2.0, step=0.1, value=0.1)
        assert element.max_fraction_digits == 1
        assert element.min_fraction_digits == 0

    def test_finer_step_allows_more_decimals(self) -> None:
        element = InputNumber(label=LocaleString(en="Score"), step=0.05)
        assert element.max_fraction_digits == 2

    def test_integer_field_stays_integer(self) -> None:
        element = InputNumber(label=LocaleString(en="Tokens"), min=0, max=128_000, step=1024, value=128_000)
        assert element.max_fraction_digits is None
        assert element.min_fraction_digits is None

    def test_explicit_fraction_digits_are_respected(self) -> None:
        element = InputNumber(label=LocaleString(en="Custom"), step=0.1, max_fraction_digits=4)
        assert element.max_fraction_digits == 4
