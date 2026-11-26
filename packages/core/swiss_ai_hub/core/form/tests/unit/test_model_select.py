"""`ModelSelect.requirements`: announced with the form and read back from the stored form unchanged."""

import json

from pydantic import BaseModel, TypeAdapter

from swiss_ai_hub.core.form.all_form_options import ALL_FORM_OPTIONS
from swiss_ai_hub.core.form.elements.group import Group
from swiss_ai_hub.core.form.elements.model_select import ModelSelect
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.infrastructure.litellm.hosting_location import HostingLocation
from swiss_ai_hub.core.infrastructure.litellm.model_capability import ModelCapability
from swiss_ai_hub.core.infrastructure.litellm.model_requirements import ModelRequirements

REQUIREMENTS = ModelRequirements(
    capabilities={ModelCapability.VISION, ModelCapability.TOOL_CALLING},
    hosting_locations={HostingLocation.LOCAL},
)


def _picker(requirements: ModelRequirements | None = None) -> ModelSelect:
    if requirements is None:
        return ModelSelect(label=LocaleString(en="Model"))
    return ModelSelect(label=LocaleString(en="Model"), requirements=requirements)


def test_requires_nothing_by_default():
    assert _picker().requirements == ModelRequirements()


def test_requirements_are_announced_with_the_element():
    dumped = _picker(REQUIREMENTS).model_dump(by_alias=True, mode="json")
    assert dumped["requirements"] == {"capabilities": ["tool_calling", "vision"], "hosting_locations": ["local"]}


def test_requirements_survive_the_stored_form():
    stored = _picker(REQUIREMENTS).model_dump(by_alias=True, mode="json")
    restored = TypeAdapter(ALL_FORM_OPTIONS).validate_python(stored)
    assert isinstance(restored, ModelSelect)
    assert restored.requirements == REQUIREMENTS


def test_requirements_serialise_as_sorted_lists_when_dumped_as_any():
    """Events dump with `serialize_as_any`, which skips staticmethod field serializers in Pydantic 2.13: the set then
    reached the event's JSON as its Python repr, and the API rejected the whole announced form."""

    class _Announcement(BaseModel):
        form: list[BaseModel]

    group = Group(name="llm", label=LocaleString(en="LLM"), children=[_picker(REQUIREMENTS)])
    dumped = _Announcement(form=[group]).model_dump(serialize_as_any=True, mode="python")

    requirements = dumped["form"][0]["children"][0]["requirements"]
    assert requirements == {"capabilities": ["tool_calling", "vision"], "hosting_locations": ["local"]}
    assert json.loads(json.dumps(dumped, default=str))["form"][0]["children"][0]["requirements"] == requirements
