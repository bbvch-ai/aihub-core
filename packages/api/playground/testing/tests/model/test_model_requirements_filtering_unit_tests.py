"""`GET /models/mode/{mode}` narrowed by a picker's requirements, over one fake model per way of failing them."""

from unittest.mock import AsyncMock, patch

import pytest
from swiss_ai_hub.core.infrastructure import HostingLocation, ModelCapability, ModelRequirements
from swiss_ai_hub.core.testing.auth_utils.test_identity import fake_user

from playground.testing.tests.model.fake_models import FAKE_MODELS
from swiss_ai_hub.api.routes.model.model_service import ModelService

TODAYS_CHAT_SET_WITHOUT_OCR = {
    "text-generation/fake-swiss",
    "text-generation/fake-eu",
    "text-generation/fake-no-tools",
    "text-generation/fake-undeclared",
}


async def _listed(requirements: ModelRequirements | None = None, include_special_purpose: bool = False) -> set[str]:
    with patch.object(ModelService, "get_model_list", AsyncMock(return_value=FAKE_MODELS)):
        models = await ModelService.get_models_by_mode(fake_user(), "chat", requirements, include_special_purpose)
    return {model.model_name for model in models}


@pytest.mark.asyncio
async def test_no_requirements_list_todays_chat_models_without_the_ocr_model():
    """The undeclared model stays: operators add models through the LiteLLM UI without our keys."""
    assert await _listed() == TODAYS_CHAT_SET_WITHOUT_OCR


@pytest.mark.asyncio
async def test_include_special_purpose_brings_the_ocr_model_back():
    assert await _listed(include_special_purpose=True) == TODAYS_CHAT_SET_WITHOUT_OCR | {"text-generation/fake-ocr"}


@pytest.mark.asyncio
async def test_a_vision_requirement_still_leaves_out_the_ocr_model():
    """The OCR model reads images, but no general chat picker may offer it, whatever it requires."""
    assert await _listed(ModelRequirements(capabilities={ModelCapability.VISION})) == {
        "text-generation/fake-swiss",
        "text-generation/fake-eu",
        "text-generation/fake-no-tools",
    }


@pytest.mark.asyncio
async def test_tool_calling_leaves_out_models_without_it_and_undeclared_ones():
    assert await _listed(ModelRequirements(capabilities={ModelCapability.TOOL_CALLING})) == {
        "text-generation/fake-swiss",
        "text-generation/fake-eu",
    }


@pytest.mark.asyncio
async def test_a_location_requirement_keeps_only_models_hosted_there():
    assert await _listed(ModelRequirements(hosting_locations={HostingLocation.SWISS_CLOUD})) == {
        "text-generation/fake-swiss",
        "text-generation/fake-no-tools",
    }


@pytest.mark.asyncio
async def test_several_locations_are_alternatives():
    requirements = ModelRequirements(hosting_locations={HostingLocation.SWISS_CLOUD, HostingLocation.EU})
    assert await _listed(requirements) == {
        "text-generation/fake-swiss",
        "text-generation/fake-eu",
        "text-generation/fake-no-tools",
    }


@pytest.mark.asyncio
async def test_capabilities_and_location_must_both_hold():
    requirements = ModelRequirements(
        capabilities={ModelCapability.TOOL_CALLING}, hosting_locations={HostingLocation.SWISS_CLOUD}
    )
    assert await _listed(requirements) == {"text-generation/fake-swiss"}


@pytest.mark.asyncio
async def test_a_location_nobody_offers_lists_nothing():
    assert await _listed(ModelRequirements(hosting_locations={HostingLocation.LOCAL})) == set()


@pytest.mark.asyncio
async def test_include_special_purpose_does_not_bypass_requirements():
    requirements = ModelRequirements(capabilities={ModelCapability.TOOL_CALLING})
    assert "text-generation/fake-ocr" not in await _listed(requirements, include_special_purpose=True)
