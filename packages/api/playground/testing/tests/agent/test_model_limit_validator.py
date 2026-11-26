"""`ModelLimitValidator`: a save may not set a model-bound field beyond what the model picked on the same form serves.

The form is the real `LLMConfig` sub-form a conversational blueprint announces, round-tripped through the stored
dict shape the API reads back, next to a model-bound input-token budget like `ConversationFields` declares.
"""

from typing import Annotated, Any
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from pydantic import Field, TypeAdapter
from swiss_ai_hub.core.form import (
    ALL_FORM_OPTIONS,
    Form,
    FormkitElement,
    ModelBoundInputNumber,
    ModelSelect,
    Repeater,
)
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import HostingLocation, ModelCapability, ModelRequirements
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


TOOL_CALLING = ModelRequirements(capabilities={ModelCapability.TOOL_CALLING})
TOOLS_MODEL = "text-generation/tools"
OCR_MODEL = "text-generation/ocr"
_PICKER_MODELS = [
    *_MODELS,
    ModelDTO.model_validate(
        {
            "model_name": TOOLS_MODEL,
            "model_info": {"mode": "chat", "supports_function_calling": True, "aihub_hosting_location": "eu"},
        }
    ),
    ModelDTO.model_validate(
        {"model_name": OCR_MODEL, "model_info": {"mode": "chat", "aihub_general_purpose": False}},
    ),
]


def _picker_elements(requirements: ModelRequirements | None) -> list[FormkitElement]:
    form = _ChatBlueprintConfig(llm=LLMConfig.as_form(requirements=requirements))
    stored = [element.model_dump(by_alias=True) for element in form.to_formkit_form()]
    return TypeAdapter(list[ALL_FORM_OPTIONS]).validate_python(stored)


async def _reject_pick(model: str, requirements: ModelRequirements | None = None) -> None:
    with patch(
        "swiss_ai_hub.api.util.model_limit_validator.ModelService.get_model_list",
        AsyncMock(return_value=_PICKER_MODELS),
    ):
        await ModelLimitValidator.reject_values_beyond_model_limits(
            _picker_elements(requirements), {"llm": {"model_name": model}}, fake_user(), ApiLocaleHandler(locale="en")
        )


@pytest.mark.asyncio
async def test_a_model_meeting_the_pickers_requirements_is_saved():
    await _reject_pick(TOOLS_MODEL, TOOL_CALLING)


@pytest.mark.asyncio
async def test_a_model_failing_the_pickers_requirements_is_refused_naming_what_it_lacks():
    """A stored profile from before the requirement keeps running, but its next save has to pick another model."""
    with pytest.raises(HTTPException) as raised:
        await _reject_pick(SMALL_MODEL, TOOL_CALLING)

    assert raised.value.status_code == 400
    assert "llm.model_name" in raised.value.detail
    assert "(tool calling)" in raised.value.detail


@pytest.mark.asyncio
async def test_a_location_requirement_is_enforced():
    with pytest.raises(HTTPException) as raised:
        await _reject_pick(TOOLS_MODEL, ModelRequirements(hosting_locations={HostingLocation.SWISS_CLOUD}))

    assert "(hosting location)" in raised.value.detail


@pytest.mark.asyncio
async def test_a_picker_without_requirements_accepts_any_general_purpose_model():
    await _reject_pick(SMALL_MODEL)


@pytest.mark.asyncio
async def test_a_model_built_for_one_job_is_refused_even_without_requirements():
    with pytest.raises(HTTPException) as raised:
        await _reject_pick(OCR_MODEL)

    assert "llm.model_name" in raised.value.detail
    assert OCR_MODEL in raised.value.detail


@pytest.mark.asyncio
async def test_an_unknown_picked_model_is_not_held_against_the_save():
    await _reject_pick("text-generation/not-listed", TOOL_CALLING)


class _RetrieverConfig(Form):
    embed_model: Annotated[str | ModelSelect, Field(description="Embedding model")]


class _RepeatedPickerConfig(Form):
    retrievers: Annotated[list[_RetrieverConfig], Field(description="Retrievers")]


def _repeated_picker_elements() -> list[FormkitElement]:
    form = _RepeatedPickerConfig(
        retrievers=[_RetrieverConfig(embed_model=ModelSelect(label=LocaleString(en="Embedding"), mode="embedding"))]
    )
    stored = [element.model_dump(by_alias=True) for element in form.to_formkit_form()]
    return TypeAdapter(list[ALL_FORM_OPTIONS]).validate_python(stored)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "retrievers",
    [
        [{"embed_model": SMALL_MODEL}, {"embed_model": OCR_MODEL}],
        {"0": {"embed_model": SMALL_MODEL}, "1": {"embed_model": OCR_MODEL}},
    ],
    ids=["list", "formkit-numbered-dict"],
)
async def test_a_picker_in_a_repeater_is_checked_per_entry(retrievers):
    with (
        patch(
            "swiss_ai_hub.api.util.model_limit_validator.ModelService.get_model_list",
            AsyncMock(return_value=_PICKER_MODELS),
        ),
        pytest.raises(HTTPException) as raised,
    ):
        await ModelLimitValidator.reject_values_beyond_model_limits(
            _repeated_picker_elements(), {"retrievers": retrievers}, fake_user(), ApiLocaleHandler(locale="en")
        )

    assert "retrievers.1.embed_model" in raised.value.detail
    assert "retrievers.0" not in raised.value.detail


def test_only_pickers_are_collected_from_repeater_entries():
    """A field bound to another field's model names it without the entry's index, so it cannot be resolved there."""
    tokens = ModelBoundInputNumber(
        name="tokens", label=LocaleString(en="Tokens"), model_ref="model_name", max_from="max_input_tokens"
    )
    repeater = Repeater(
        name="entries",
        label=LocaleString(en="Entries"),
        children=[tokens, ModelSelect(name="model_name", label=LocaleString(en="Model"))],
    )

    bound = ModelLimitValidator.bound_elements(
        [repeater], {"entries": [{"tokens": 10_000_000, "model_name": SMALL_MODEL}]}, ""
    )

    assert [(path, type(element).__name__) for path, element, _ in bound] == [("entries.0.model_name", "ModelSelect")]
