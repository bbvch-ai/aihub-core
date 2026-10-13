"""The My Files chat toggle: OpenWebUI runs it only while switched on, and running adds the feature for the agent."""

import filecmp
import importlib.util
from pathlib import Path
from typing import Any

import pytest

from swiss_ai_hub.core.events.agent.user.chat_feature import ChatFeature

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[8]
GENERATED_FILTER = REPO_ROOT / "infra/configs/openwebui/functions/aihub_feature_user_files.py"
TEMPLATE_FILTER = REPO_ROOT / "infra/deployment/templates/openwebui_functions/aihub_feature_user_files.py"


@pytest.fixture
def toggle() -> Any:
    spec = importlib.util.spec_from_file_location("aihub_feature_user_files", GENERATED_FILTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_it_is_registered_under_the_id_the_provisioner_attaches() -> None:
    assert GENERATED_FILTER.stem.replace("_", "-") == ChatFeature.USER_FILES.openwebui_toggle_filter_id
    assert ChatFeature.USER_FILES.openwebui_capability is None


def test_it_is_a_toggle_with_an_icon(toggle: Any) -> None:
    instance = toggle.Filter()

    assert instance.toggle is True
    assert instance.icon.startswith("data:image/svg+xml;base64,")


@pytest.mark.asyncio
async def test_running_adds_the_feature_next_to_the_others(toggle: Any) -> None:
    metadata = {toggle.REQUESTED_FEATURES_METADATA_KEY: ["code_interpreter"]}

    body = await toggle.Filter().inlet({"messages": []}, __metadata__=metadata)

    assert body == {"messages": []}
    assert metadata[toggle.REQUESTED_FEATURES_METADATA_KEY] == ["code_interpreter", ChatFeature.USER_FILES.value]


def test_the_template_copy_matches() -> None:
    assert filecmp.cmp(GENERATED_FILTER, TEMPLATE_FILTER, shallow=False)
