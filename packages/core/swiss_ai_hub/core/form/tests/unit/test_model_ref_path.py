import pytest

from swiss_ai_hub.core.form.all_form_options import ALL_FORM_OPTIONS  # noqa: F401 — rebuilds Group/Repeater
from swiss_ai_hub.core.form.elements.model_ref_path import ModelRefPath
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig


class TestResolve:
    def test_a_parent_step_leaves_the_declaring_form(self) -> None:
        assert ModelRefPath.resolve("../model_name", "llm.default_parameter.") == "llm.model_name"

    def test_a_path_without_parent_steps_is_taken_from_the_declaring_form(self) -> None:
        assert ModelRefPath.resolve("llm.model_name", "") == "llm.model_name"

    def test_several_parent_steps_climb_several_forms(self) -> None:
        assert ModelRefPath.resolve("../../model_name", "a.b.c.") == "a.model_name"

    def test_climbing_above_the_root_is_refused(self) -> None:
        with pytest.raises(ValueError, match="climbs above the form root"):
            ModelRefPath.resolve("../model_name", "")


class TestRenderedForm:
    def test_a_nested_sub_form_names_its_model_from_the_root(self) -> None:
        """`LLMParameter` sits one level deeper wherever `LLMConfig` is nested, and the frontend and API read
        the path from the form root."""
        nested_prefix = "llm."
        elements = LLMConfig.as_form().to_formkit_form(_id_prefix=nested_prefix)
        group = next(element for element in elements if element.name == "default_parameter")
        temperature = next(child for child in group.children if child.name == "temperature")

        assert temperature.model_ref == "llm.model_name"
