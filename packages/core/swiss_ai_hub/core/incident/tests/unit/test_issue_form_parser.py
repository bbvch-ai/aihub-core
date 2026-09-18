import pytest
from pydantic import ValidationError

from swiss_ai_hub.core.form.base.html_element import HtmlElement
from swiss_ai_hub.core.form.elements.input_text import InputText
from swiss_ai_hub.core.form.elements.multi_select import MultiSelect
from swiss_ai_hub.core.form.elements.select import Select
from swiss_ai_hub.core.form.elements.textarea import Textarea
from swiss_ai_hub.core.incident.incident_context import IncidentContext
from swiss_ai_hub.core.incident.issue_form_parser import IssueFormParser

MINIMAL_DEFINITION = """
title: '[INC] '
labels: [incident]
body:
  - type: markdown
    attributes:
      value: Some prose
  - type: textarea
    id: what_went_wrong
    attributes:
      label: What went wrong?
      description: Help text
    validations:
      required: true
  - type: dropdown
    id: impact
    attributes:
      label: Impact
      options: [High, Low]
    validations:
      required: true
  - type: dropdown
    id: areas
    attributes:
      label: Areas
      multiple: true
      options: [Chat, Search]
  - type: input
    id: tenant
    attributes:
      label: Tenant
"""


def test_should_map_each_entry_type_to_its_element_when_definition_is_valid() -> None:
    form = IssueFormParser.parse(MINIMAL_DEFINITION)

    assert [type(element) for element in form.elements] == [HtmlElement, Textarea, Select, MultiSelect, InputText]


def test_should_expose_title_and_labels_when_definition_declares_them() -> None:
    form = IssueFormParser.parse(MINIMAL_DEFINITION)

    assert form.title_prefix == "[INC] "
    assert form.labels == ["incident"]


def test_should_skip_prose_when_collecting_answerable_fields() -> None:
    form = IssueFormParser.parse(MINIMAL_DEFINITION)

    assert [field.id for field in form.fields] == ["what_went_wrong", "impact", "areas", "tenant"]


def test_should_carry_required_flag_and_options_onto_the_field() -> None:
    form = IssueFormParser.parse(MINIMAL_DEFINITION)
    by_id = {field.id: field for field in form.fields}

    assert by_id["what_went_wrong"].required is True
    assert by_id["tenant"].required is False
    assert by_id["impact"].options == ["High", "Low"]
    assert by_id["areas"].multiple is True


def test_should_turn_description_into_help_text_on_the_element() -> None:
    form = IssueFormParser.parse(MINIMAL_DEFINITION)

    assert form.elements[1].help == "Help text"


@pytest.mark.parametrize(
    ("definition", "expected_message"),
    [
        ("body: not-a-list", "must be a mapping with a 'body' list"),
        ("body:\n  - type: slider\n    id: x\n    attributes:\n      label: X", "unsupported type 'slider'"),
        ("body:\n  - type: input\n    attributes:\n      label: X", "needs an id"),
        ("body:\n  - type: input\n    id: x\n    attributes: {}", "needs a label"),
        ("body:\n  - type: dropdown\n    id: x\n    attributes:\n      label: X", "has no options"),
        ("body:\n  - type: markdown\n    attributes: {}", "markdown without a value"),
        (
            "body:\n  - type: input\n    id: x\n    attributes:\n      label: A\n"
            "  - type: input\n    id: x\n    attributes:\n      label: B",
            "Duplicate question id 'x'",
        ),
    ],
)
def test_should_reject_a_broken_definition_loudly(definition: str, expected_message: str) -> None:
    with pytest.raises(ValueError, match=expected_message):
        IssueFormParser.parse(definition)


def test_should_accept_a_submission_that_answers_every_required_question() -> None:
    model = IssueFormParser.parse(MINIMAL_DEFINITION).submission_model()

    submission = model(what_went_wrong="It broke", impact="High", areas=["Chat"], tenant="acme")

    assert submission.impact == "High"


def test_should_reject_a_submission_missing_a_required_answer() -> None:
    model = IssueFormParser.parse(MINIMAL_DEFINITION).submission_model()

    with pytest.raises(ValidationError):
        model(impact="High")


def test_should_reject_a_submission_naming_an_option_the_form_does_not_offer() -> None:
    model = IssueFormParser.parse(MINIMAL_DEFINITION).submission_model()

    with pytest.raises(ValidationError):
        model(what_went_wrong="It broke", impact="Catastrophic")


def test_should_allow_an_optional_question_to_go_unanswered() -> None:
    model = IssueFormParser.parse(MINIMAL_DEFINITION).submission_model()

    submission = model(what_went_wrong="It broke", impact="Low")

    assert submission.tenant is None


def test_should_put_known_values_into_the_matching_elements_when_prefilling() -> None:
    form = IssueFormParser.parse(MINIMAL_DEFINITION)

    prefilled = form.with_prefill({"tenant": "Acme (68c1)"})

    assert prefilled.elements[4].value == "Acme (68c1)"


def test_should_leave_an_element_untouched_when_no_value_is_known_for_it() -> None:
    form = IssueFormParser.parse(MINIMAL_DEFINITION)

    prefilled = form.with_prefill({"tenant": "Acme (68c1)"})

    assert prefilled.elements[1].value is None


def test_should_drop_empty_context_values_so_they_do_not_overwrite_defaults() -> None:
    context = IncidentContext(tenant="Acme", conversation_id="")

    assert context.as_prefill() == {"tenant": "Acme"}


def test_should_load_the_shipped_definition() -> None:
    """Guards the file QC edits: a broken definition fails here, not at a user's click."""
    form = IssueFormParser.load()

    assert form.labels == ["incident"]
    assert {field.id for field in form.fields} >= set(IncidentContext.model_fields)


def test_should_prefill_every_context_field_from_the_shipped_definition() -> None:
    """Every IncidentContext field must name a question, or it silently never appears."""
    form = IssueFormParser.load()

    missing = set(IncidentContext.model_fields) - form.field_ids()

    assert missing == set()
