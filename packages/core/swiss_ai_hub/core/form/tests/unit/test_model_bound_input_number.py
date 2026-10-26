"""`ModelBoundInputNumber.maximum_for`: the bound a model's limit puts on the field, shared by the API and the form."""

from swiss_ai_hub.core.form.elements.model_bound_input_number import ModelBoundInputNumber
from swiss_ai_hub.core.i18n.locale_string import LocaleString


def _element(fill_factor: float | None) -> ModelBoundInputNumber:
    return ModelBoundInputNumber(
        label=LocaleString(en="Input tokens"),
        model_ref="llm.model_name",
        max_from="max_input_tokens",
        fill_factor=fill_factor,
    )


def test_without_a_fill_factor_the_bound_is_the_models_limit():
    assert _element(None).maximum_for(155_648) == 155_648


def test_with_a_fill_factor_the_bound_is_the_share_the_runtime_fills():
    """A value above it would behave exactly like it, so the field never offers one."""
    assert _element(0.85).maximum_for(155_648) == 132_300
