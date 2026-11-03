"""`ModelLimitValidator`: a save may not set a model-bound field beyond what the model picked on the same form serves.

The form is the real `LLMConfig` sub-form a conversational blueprint announces, round-tripped through the stored
dict shape the API reads back, next to a model-bound input-token budget like `ConversationFields` declares.
"""

from typing import Annotated, Any
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from pydantic import Field, TypeAdapter
from swiss_ai_hub.core.form import ALL_FORM_OPTIONS, Form, FormkitElement, ModelBoundInputNumber
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.api.i18n.api_locale_handler import ApiLocaleHandler
from swiss_ai_hub.api.routes.model.dto.model_dto import ModelDTO
from swiss_ai_hub.api.util.model_limit_validator import ModelLimitValidator

SMALL_MODEL = "text-generation/small"
TEXT_ONLY_MODEL = "text-generation/text-only"


class _ChatBlueprintConfig(Form):
    llm: Annotated[LLMConfig, Field(description="The answering model")]
    number_of_input_tokens: Annotated[int | ModelBoundInputNumber, Field(description="Input budget")] = 128000


def _elements(fill_factor: float | None = None) -> list[FormkitElement]:
    form = _ChatBlueprintConfig(
        llm=LLMConfig.as_form(),
        number_of_input_tokens=ModelBoundInputNumber(
            label=LocaleString(en="Input tokens"),
            model_ref="llm.model_name",
            max_from="max_input_tokens",
            fill_factor=fill_factor,
            min=1024,
        ),
    )
    stored = [element.model_dump(by_alias=True) for element in form.to_formkit_form()]
    return TypeAdapter(list[ALL_FORM_OPTIONS]).validate_python(stored)


_MODELS = [
    ModelDTO.model_validate(
        {"model_name": SMALL_MODEL, "model_info": {"mode": "chat", "max_input_tokens": 8192, "supports_vision": True}}
    ),
    ModelDTO.model_validate(
        {
            "model_name": TEXT_ONLY_MODEL,
            "model_info": {"mode": "chat", "max_input_tokens": 8192, "supports_vision": False},
        }
    ),
]


def _config(model: str, tokens: int = 4096, accept_images: bool = False) -> dict[str, Any]:
    return {
        "llm": {"model_name": model, "default_parameter": {"accept_images": accept_images}},
        "number_of_input_tokens": tokens,
    }


async def _reject(config: dict[str, Any], fill_factor: float | None = None) -> None:
    with patch(
        "swiss_ai_hub.api.util.model_limit_validator.ModelService.get_model_list", AsyncMock(return_value=_MODELS)
    ):
        await ModelLimitValidator.reject_values_beyond_model_limits(
            _elements(fill_factor), config, fake_user(), ApiLocaleHandler(locale="en")
        )


@pytest.mark.asyncio
async def test_a_budget_within_the_model_window_is_saved():
    await _reject(_config(SMALL_MODEL, tokens=8192))


@pytest.mark.asyncio
async def test_a_budget_above_the_model_window_is_refused_naming_the_field():
    with pytest.raises(HTTPException) as raised:
        await _reject(_config(SMALL_MODEL, tokens=8193))

    assert raised.value.status_code == 400
    assert "number_of_input_tokens" in raised.value.detail
    assert "8192" in raised.value.detail


@pytest.mark.asyncio
async def test_a_field_filling_a_share_of_the_window_is_bounded_at_that_share():
    """A value between the share and the window would behave exactly like the share, so it is not offered."""
    await _reject(_config(SMALL_MODEL, tokens=6963), fill_factor=0.85)

    with pytest.raises(HTTPException) as raised:
        await _reject(_config(SMALL_MODEL, tokens=6964), fill_factor=0.85)

    assert "6963" in raised.value.detail


@pytest.mark.asyncio
async def test_an_unknown_model_is_not_held_against_the_save():
    await _reject(_config("text-generation/not-listed", tokens=10_000_000))


@pytest.mark.asyncio
async def test_images_cannot_be_accepted_for_a_model_that_declares_no_vision():
    with pytest.raises(HTTPException) as raised:
        await _reject(_config(TEXT_ONLY_MODEL, accept_images=True))

    assert "llm.default_parameter.accept_images" in raised.value.detail


@pytest.mark.asyncio
async def test_images_can_be_accepted_for_a_vision_model():
    await _reject(_config(SMALL_MODEL, accept_images=True))


@pytest.mark.asyncio
async def test_a_form_without_model_bound_fields_never_asks_for_the_models():
    with patch(
        "swiss_ai_hub.api.util.model_limit_validator.ModelService.get_model_list", AsyncMock(return_value=_MODELS)
    ) as get_model_list:
        await ModelLimitValidator.reject_values_beyond_model_limits([], {"x": 1}, fake_user(), ApiLocaleHandler())

    get_model_list.assert_not_called()
