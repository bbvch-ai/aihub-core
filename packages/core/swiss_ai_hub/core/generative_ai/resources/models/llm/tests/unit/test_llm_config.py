"""Tests for the LLMConfig form factory and its task-model variant."""

from swiss_ai_hub.core.form.all_form_options import ALL_FORM_OPTIONS  # noqa: F401 — rebuilds Group/Repeater
from swiss_ai_hub.core.form.elements.model_select import ModelSelect
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig, LLMParameter

MAIN_MODEL = "text-generation/main-model"
TASK_MODEL = "text-generation/task-model"


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
