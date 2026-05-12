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
