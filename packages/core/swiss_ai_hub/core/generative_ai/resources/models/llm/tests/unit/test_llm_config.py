"""Tests for the LLMConfig form factory, its task-model variant, and llama-index construction."""

from typing import Annotated
from unittest.mock import Mock, patch

import pytest
from pydantic import Field, ValidationError

from swiss_ai_hub.core.form.all_form_options import ALL_FORM_OPTIONS  # noqa: F401 — rebuilds Group/Repeater
from swiss_ai_hub.core.form.elements.model_bound_input_number import ModelBoundInputNumber
from swiss_ai_hub.core.form.elements.model_gated_checkbox import ModelGatedCheckbox
from swiss_ai_hub.core.form.elements.model_select import ModelSelect
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import DEFAULT_TEMPERATURE, LLMConfig, LLMParameter
from swiss_ai_hub.core.i18n.locale_string import LocaleString

MAIN_MODEL = "text-generation/main-model"
TASK_MODEL = "text-generation/task-model"

_FAKE_MODEL_INFO = {
    "model_info": {
        "max_input_tokens": 8192,
        "mode": "chat",
        "supports_function_calling": True,
        "max_output_tokens": 2048,
        "supports_response_schema": True,
        "input_cost_per_token": 0.000001,
        "output_cost_per_token": 0.000002,
    }
}


def _build_llm(config: LLMConfig | None = None, model_info: dict | None = None):
    config = config or LLMConfig(model_name="text-generation/gemma-4-31B-it")

    fake_settings = Mock(BASE_URL="http://litellm-test/v1", API_KEY=Mock(get_secret_value=Mock(return_value="key")))
    with (
        patch.object(LLMConfig, "get_model_info", return_value=model_info or _FAKE_MODEL_INFO),
        patch(
            "swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config.LiteLLMProxySettings",
            return_value=fake_settings,
        ),
    ):
        llm, cost_tracker = config.to_llama_index()

    return llm, cost_tracker


class TestAsForm:
    def test_the_default_form_offers_the_generation_parameters(self) -> None:
        elements = LLMConfig.as_form().to_formkit_form()

        assert [element.name for element in elements] == ["model_name", "default_parameter"]

    def test_the_model_picker_can_be_rendered_alone(self) -> None:
        form = LLMConfig.as_form(include_default_parameter=False)

        assert isinstance(form.model_name, ModelSelect)
        assert [element.name for element in form.to_formkit_form()] == ["model_name"]


class TestAsTaskLlm:
    def test_generation_parameters_are_taken_from_the_source_config(self) -> None:
        main = LLMConfig(
            model_name=MAIN_MODEL,
            default_parameter=LLMParameter(temperature=0.7, timeout=42.0),
        )

        task = main.as_task_llm(TASK_MODEL)

        assert task.model_name == TASK_MODEL
        assert task.default_parameter.temperature == 0.7
        assert task.default_parameter.timeout == 42.0

    def test_an_unset_temperature_pins_the_task_variant_to_the_deterministic_default(self) -> None:
        """Auxiliary steps classify and condense; a model's chat-tuned default (1.0 for gemma) must not reach them."""
        main = LLMConfig(model_name=MAIN_MODEL)

        task = main.as_task_llm(TASK_MODEL)

        assert main.default_parameter.temperature is None
        assert task.default_parameter.temperature == DEFAULT_TEMPERATURE

    def test_the_task_variant_ignores_the_task_models_default_temperature(self) -> None:
        task = LLMConfig(model_name=MAIN_MODEL).as_task_llm(TASK_MODEL)

        llm, _ = _build_llm(task, _with_curated(default_temperature=1.0))

        assert llm.temperature == DEFAULT_TEMPERATURE

    def test_the_main_config_still_samples_at_the_model_default(self) -> None:
        llm, _ = _build_llm(LLMConfig(model_name=MAIN_MODEL), _with_curated(default_temperature=1.0))

        assert llm.temperature == 1.0

    def test_top_p_and_image_acceptance_are_taken_from_the_source_config(self) -> None:
        main = LLMConfig(model_name=MAIN_MODEL, default_parameter=LLMParameter(top_p=0.4, accept_images=False))

        task = main.as_task_llm(TASK_MODEL)

        assert task.default_parameter.top_p == 0.4
        assert task.default_parameter.accept_images is False

    def test_log_probabilities_are_always_off(self) -> None:
        main = LLMConfig(
            model_name=MAIN_MODEL,
            default_parameter=LLMParameter(logprobs=True, top_logprobs=5),
        )

        task = main.as_task_llm(TASK_MODEL)

        assert task.default_parameter.logprobs is False
        assert task.default_parameter.top_logprobs == 0

    def test_the_source_config_is_not_mutated(self) -> None:
        main = LLMConfig(model_name=MAIN_MODEL, default_parameter=LLMParameter(temperature=0.7))

        task = main.as_task_llm(TASK_MODEL)
        task.default_parameter.temperature = 1.5

        assert main.model_name == MAIN_MODEL
        assert main.default_parameter.temperature == 0.7


class TestToLlamaIndex:
    def test_usage_reporting_is_not_baked_into_every_request(self) -> None:
        """
        ``stream_options`` is requested per streamed call by ``ResilientOpenAILike``, which can retry
        without it. Baking it into ``additional_kwargs`` here would make that retry impossible, since
        ``additional_kwargs`` wins over per-call kwargs in ``_get_model_kwargs``.
        """
        llm, _ = _build_llm()

        assert "stream_options" not in llm.additional_kwargs
        assert "stream_options" not in llm._get_model_kwargs(stream=True)


class TestTheDeclaredContextWindow:
    """Callers that bound a prompt need the window before building one. `None` rather than a raise: a guard
    must not turn a model with an incomplete LiteLLM entry into a failing run."""

    def test_the_window_is_read_from_the_litellm_entry(self):
        config = LLMConfig(model_name=MAIN_MODEL)

        with patch.object(LLMConfig, "get_model_info", return_value=_FAKE_MODEL_INFO):
            assert config.max_input_tokens == 8192

    def test_a_model_declaring_no_window_yields_none(self):
        config = LLMConfig(model_name=MAIN_MODEL)

        with patch.object(LLMConfig, "get_model_info", return_value={"model_info": {"mode": "chat"}}):
            assert config.max_input_tokens is None


def _with_curated(**curated: object) -> dict:
    return {"model_info": {**_FAKE_MODEL_INFO["model_info"], **curated}}


class TestSamplingDefaults:
    """An unset temperature or top_p is the model's curated default, not one constant shared by every model."""

    def test_an_unset_temperature_uses_the_model_default(self) -> None:
        llm, _ = _build_llm(model_info=_with_curated(default_temperature=0.7))

        assert llm.temperature == 0.7

    def test_a_configured_temperature_wins_over_the_model_default(self) -> None:
        config = LLMConfig(model_name=MAIN_MODEL, default_parameter=LLMParameter(temperature=0.0))

        llm, _ = _build_llm(config, _with_curated(default_temperature=0.7))

        assert llm.temperature == 0.0

    def test_a_model_without_a_curated_temperature_keeps_the_previous_default(self) -> None:
        llm, _ = _build_llm()

        assert llm.temperature == DEFAULT_TEMPERATURE

    def test_an_unset_top_p_uses_the_model_default(self) -> None:
        llm, _ = _build_llm(model_info=_with_curated(default_top_p=0.8))

        assert llm.additional_kwargs["top_p"] == 0.8

    def test_a_configured_top_p_wins_over_the_model_default(self) -> None:
        config = LLMConfig(model_name=MAIN_MODEL, default_parameter=LLMParameter(top_p=0.3))

        llm, _ = _build_llm(config, _with_curated(default_top_p=0.8))

        assert llm.additional_kwargs["top_p"] == 0.3

    def test_top_p_is_left_to_the_provider_when_nothing_sets_it(self) -> None:
        llm, _ = _build_llm()

        assert "top_p" not in llm.additional_kwargs

    def test_top_p_above_one_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            LLMParameter(top_p=1.5)

    def test_deterministic_configs_ignore_the_model_default(self) -> None:
        llm, _ = _build_llm(LLMConfig.deterministic(MAIN_MODEL), _with_curated(default_temperature=1.0))

        assert llm.temperature == DEFAULT_TEMPERATURE


class TestModelBoundParameters:
    def test_sampling_fields_reference_the_sibling_model_picker(self) -> None:
        group = next(e for e in LLMConfig.as_form().to_formkit_form() if e.name == "default_parameter")
        by_name = {child.name: child for child in group.children}

        assert isinstance(by_name["temperature"], ModelBoundInputNumber)
        assert by_name["temperature"].model_ref == "model_name"
        assert by_name["top_p"].default_from == "default_top_p"
        assert isinstance(by_name["accept_images"], ModelGatedCheckbox)
        assert by_name["accept_images"].requires == "supports_vision"

    def test_sampling_fields_offer_their_own_override_instead_of_the_generic_toggle(self) -> None:
        """The generic enable toggle hides the input while off, so the model's default would only show after the
        admin had already decided to override it."""
        group = next(e for e in LLMConfig.as_form().to_formkit_form() if e.name == "default_parameter")
        by_name = {child.name: child for child in group.children}

        for name in ("temperature", "top_p"):
            assert by_name[name].nullable is False
            assert by_name[name].required is False
            assert by_name[name].override_label is not None

    def test_the_temperature_shows_the_platform_fallback_and_top_p_leaves_it_to_the_provider(self) -> None:
        group = next(e for e in LLMConfig.as_form().to_formkit_form() if e.name == "default_parameter")
        by_name = {child.name: child for child in group.children}

        assert by_name["temperature"].fallback_default == DEFAULT_TEMPERATURE
        assert by_name["top_p"].fallback_default is None

    def test_a_model_bound_field_without_override_label_keeps_the_generic_toggle(self) -> None:
        class _Budget(Form):
            budget: Annotated[float | None | ModelBoundInputNumber, Field(description="Budget")] = None

        budget = ModelBoundInputNumber(label=LocaleString(en="Budget"), model_ref="model", default_from="x")
        element = _Budget(budget=budget).to_formkit_form()[0]

        assert element.nullable is True

    def test_vision_and_image_limit_are_read_from_the_litellm_entry(self) -> None:
        config = LLMConfig(model_name=MAIN_MODEL)

        with patch.object(LLMConfig, "get_model_info", return_value=_with_curated(supports_vision=True, max_images=8)):
            assert config.supports_vision is True
            assert config.max_images == 8
