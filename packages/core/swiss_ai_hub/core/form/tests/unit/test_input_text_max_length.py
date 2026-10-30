import pytest

from swiss_ai_hub.core.agents.agent_config import AgentConfig
from swiss_ai_hub.core.form.base.prime_vue_element import PrimeVueElement
from swiss_ai_hub.core.form.elements.input_text import InputText
from swiss_ai_hub.core.form.elements.textarea import Textarea
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler

ELEMENT_TYPES = [InputText, Textarea]


@pytest.mark.parametrize("element_type", ELEMENT_TYPES)
def test_max_length_emits_length_rule_and_maxlength_attribute(element_type: type[PrimeVueElement]):
    element = element_type(label="Title", required=True, max_length=10)
    assert element.validation == "required|length:0,10"
    assert element.model_dump(by_alias=True)["maxlength"] == 10


@pytest.mark.parametrize("element_type", ELEMENT_TYPES)
def test_without_max_length_no_length_rule_is_emitted(element_type: type[PrimeVueElement]):
    assert element_type(label="Title").validation == ""


@pytest.mark.parametrize("element_type", ELEMENT_TYPES)
def test_validate_value_rejects_text_over_the_limit(element_type: type[PrimeVueElement]):
    element = element_type(label="Title", max_length=3)
    assert element.validate_value("title", "abcd", LocaleHandler(locale="en")) == ["must be at most 3 characters"]
    assert element.validate_value("title", "abc", LocaleHandler(locale="en")) == []


def test_agent_id_carries_the_id_length_limit():
    validations = {element.name: element.validation for element in AgentConfig.as_form().to_formkit_form()}
    assert validations["agent_id"] == f"required|length:0,{AgentConfig.ID_MAX_LENGTH}"
