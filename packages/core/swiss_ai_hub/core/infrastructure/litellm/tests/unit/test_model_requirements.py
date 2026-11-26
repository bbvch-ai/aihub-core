"""`ModelRequirements`: which models one model picker may offer and save.

Stricter than `ModelGatedCheckbox` on purpose: a flag LiteLLM reports as null, or does not report, is unsupported, and
a location that is missing or unknown fails a location requirement.
"""

import pytest
from pydantic import ValidationError

from swiss_ai_hub.core.infrastructure.litellm.hosting_location import HostingLocation
from swiss_ai_hub.core.infrastructure.litellm.model_capability import ModelCapability
from swiss_ai_hub.core.infrastructure.litellm.model_requirements import ModelRequirements

TOOLS_AND_VISION = ModelRequirements(capabilities={ModelCapability.TOOL_CALLING, ModelCapability.VISION})
SWISS_OR_LOCAL = ModelRequirements(hosting_locations={HostingLocation.SWISS_CLOUD, HostingLocation.LOCAL})


def test_no_requirements_admit_any_model():
    assert ModelRequirements().admits({})


def test_every_capability_must_be_supported():
    model_info = {"supports_function_calling": True, "supports_vision": True}
    assert TOOLS_AND_VISION.admits(model_info)


def test_one_missing_capability_is_enough_to_fail():
    model_info = {"supports_function_calling": True, "supports_vision": False}
    assert TOOLS_AND_VISION.unmet_by(model_info) == ["vision"]


@pytest.mark.parametrize("model_info", [{"supports_function_calling": None}, {}], ids=["null", "missing"])
def test_a_flag_that_is_not_set_counts_as_unsupported(model_info):
    assert ModelRequirements(capabilities={ModelCapability.TOOL_CALLING}).unmet_by(model_info) == ["tool_calling"]


@pytest.mark.parametrize(
    ("capability", "key"),
    [
        (ModelCapability.VISION, "supports_vision"),
        (ModelCapability.TOOL_CALLING, "supports_function_calling"),
        (ModelCapability.STRUCTURED_OUTPUT, "supports_response_schema"),
        (ModelCapability.REASONING, "supports_reasoning"),
    ],
)
def test_each_capability_reads_its_litellm_flag(capability, key):
    assert ModelRequirements(capabilities={capability}).admits({key: True})


def test_an_allowed_location_is_admitted():
    assert SWISS_OR_LOCAL.admits({"aihub_hosting_location": "swiss_cloud"})


@pytest.mark.parametrize("location", ["eu", "mars", None], ids=["not-allowed", "unknown", "null"])
def test_any_other_location_fails(location):
    assert SWISS_OR_LOCAL.unmet_by({"aihub_hosting_location": location}) == ["hosting_location"]


def test_a_model_without_a_location_fails_a_location_requirement():
    assert SWISS_OR_LOCAL.unmet_by({}) == ["hosting_location"]


def test_capabilities_are_reported_before_the_location():
    requirements = ModelRequirements(
        capabilities={ModelCapability.TOOL_CALLING}, hosting_locations={HostingLocation.LOCAL}
    )
    assert requirements.unmet_by({"aihub_hosting_location": "eu"}) == ["tool_calling", "hosting_location"]


def test_an_empty_location_set_is_rejected():
    """It would admit no model at all; leaving the field unset is how a picker allows every location."""
    with pytest.raises(ValidationError):
        ModelRequirements(hosting_locations=set())


def test_serialises_as_sorted_lists_and_round_trips():
    requirements = ModelRequirements(
        capabilities={ModelCapability.VISION, ModelCapability.REASONING},
        hosting_locations={HostingLocation.SWISS_CLOUD, HostingLocation.EU},
    )
    dumped = requirements.model_dump(mode="json")
    assert dumped == {"capabilities": ["reasoning", "vision"], "hosting_locations": ["eu", "swiss_cloud"]}
    assert ModelRequirements.model_validate(dumped) == requirements
