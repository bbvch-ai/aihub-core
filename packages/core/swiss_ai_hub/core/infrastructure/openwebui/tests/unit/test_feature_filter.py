"""Unit tests for the OpenWebUI inlet filter ``aihub_feature_filter``.

The filter lives under ``infra/`` as an OpenWebUI function, outside any Python package, so it is loaded from its
file path. The generated copy is the one the stack registers; the drift test keeps it equal to the template.
"""

import importlib.util
from pathlib import Path
from typing import Any

import pytest

from swiss_ai_hub.core.events.agent.user.chat_feature import ChatFeature

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[8]
GENERATED_FILTER = REPO_ROOT / "infra/configs/openwebui/functions/aihub_feature_filter.py"
TEMPLATE_FILTER = REPO_ROOT / "infra/deployment/templates/openwebui_functions/aihub_feature_filter.py"
PIPE = REPO_ROOT / "infra/deployment/templates/openwebui_functions/aihub_pipeline.py"


def _model(**capabilities: bool) -> dict[str, Any]:
    return {"id": "aihub-pipeline.RAGAgent.hr", "info": {"meta": {"capabilities": capabilities}}}


@pytest.fixture
def feature_filter() -> Any:
    spec = importlib.util.spec_from_file_location("aihub_feature_filter", GENERATED_FILTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def _run(feature_filter: Any, features: dict[str, bool], model: dict[str, Any], metadata: dict) -> dict:
    return await feature_filter.Filter().inlet({"features": features}, __metadata__=metadata, __model__=model)


class TestFeatureFilter:
    @pytest.mark.asyncio
    async def test_supported_toggle_reaches_the_pipe(self, feature_filter: Any) -> None:
        metadata: dict = {}

        await _run(feature_filter, {"web_search": True}, _model(web_search=True), metadata)

        assert metadata[feature_filter.REQUESTED_FEATURES_METADATA_KEY] == ["web_search"]

    @pytest.mark.asyncio
    async def test_toggle_off_is_not_requested(self, feature_filter: Any) -> None:
        metadata: dict = {}

        await _run(feature_filter, {"web_search": False}, _model(web_search=True), metadata)

        assert metadata[feature_filter.REQUESTED_FEATURES_METADATA_KEY] == []

    @pytest.mark.asyncio
    async def test_toggle_left_on_under_another_model_is_dropped(self, feature_filter: Any) -> None:
        """OpenWebUI sends a toggle's state even when the selected model hides it."""
        metadata: dict = {}

        await _run(feature_filter, {"code_interpreter": True}, _model(code_interpreter=False), metadata)

        assert metadata[feature_filter.REQUESTED_FEATURES_METADATA_KEY] == []

    @pytest.mark.asyncio
    async def test_missing_capability_counts_as_unsupported(self, feature_filter: Any) -> None:
        """OpenWebUI itself treats a missing capability as enabled; the filter must not."""
        metadata: dict = {}

        await _run(feature_filter, {"image_generation": True}, _model(), metadata)

        assert metadata[feature_filter.REQUESTED_FEATURES_METADATA_KEY] == []

    @pytest.mark.asyncio
    async def test_openwebui_never_sees_a_toggle_it_would_act_on(self, feature_filter: Any) -> None:
        features = {"web_search": True, "image_generation": True, "code_interpreter": True, "memory": True}
        model = _model(web_search=True, image_generation=True, code_interpreter=True)

        body = await _run(feature_filter, features, model, {})

        assert body["features"] == {}

    @pytest.mark.asyncio
    async def test_unrelated_features_are_left_to_openwebui(self, feature_filter: Any) -> None:
        body = await _run(feature_filter, {"voice": True, "web_search": True}, _model(web_search=True), {})

        assert body["features"] == {"voice": True}

    @pytest.mark.asyncio
    async def test_keeps_features_added_by_toggle_filters(self, feature_filter: Any) -> None:
        metadata = {"aihub_requested_features": ["deep_research"]}

        await _run(feature_filter, {"web_search": True}, _model(web_search=True), metadata)

        assert metadata[feature_filter.REQUESTED_FEATURES_METADATA_KEY] == ["deep_research", "web_search"]

    def test_native_features_match_the_chat_feature_contract(self, feature_filter: Any) -> None:
        native = {feature.value for feature in ChatFeature if feature.openwebui_capability}

        assert set(feature_filter.NATIVE_FEATURES) == native

    def test_pipe_reads_the_key_the_filter_writes(self, feature_filter: Any) -> None:
        expected = f'REQUESTED_FEATURES_METADATA_KEY = "{feature_filter.REQUESTED_FEATURES_METADATA_KEY}"'

        assert expected in PIPE.read_text()

    def test_generated_copy_matches_template(self) -> None:
        assert GENERATED_FILTER.read_text() == TEMPLATE_FILTER.read_text()

    def test_registered_for_agent_models_only(self) -> None:
        assert "\nglobal: false\n" in TEMPLATE_FILTER.read_text()
