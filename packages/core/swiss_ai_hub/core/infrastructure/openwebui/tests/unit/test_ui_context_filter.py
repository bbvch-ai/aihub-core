"""The UI-context filter tells the AI-Hub shell which agent or model a turn uses, and must never hold the turn up.

OpenWebUI runs this inlet before every turn reaches a pipe or a model. It used to send its script as an event call,
which waits until the browser answers; a tab that had switched chats or lost its socket never answered, so the turn
spun forever before any agent saw it (aihub-core-private#338). The filter imports OpenWebUI's own modules, which only
exist inside that container, so they are stubbed to load it from its file path.
"""

import asyncio
import filecmp
import importlib.util
import inspect
import json
import logging
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[8]
GENERATED_FILTER = REPO_ROOT / "infra/configs/openwebui/functions/aihub_ui_context_filter.py"
TEMPLATE_FILTER = REPO_ROOT / "infra/deployment/templates/openwebui_functions/aihub_ui_context_filter.py"
OPEN_WEBUI_MODULES = ["open_webui", "open_webui.models", "open_webui.models.models"]
AGENT_MODEL = "aihub-pipeline.RAGAgent.my-profile"


@pytest.fixture
def ui_context(monkeypatch: pytest.MonkeyPatch) -> Any:
    for name in OPEN_WEBUI_MODULES:
        monkeypatch.setitem(sys.modules, name, MagicMock())
    sys.modules["open_webui.models.models"].Models.get_model_by_id = AsyncMock(return_value=None)
    spec = importlib.util.spec_from_file_location("aihub_ui_context_filter", GENERATED_FILTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def _never_answer(_event: dict[str, Any]) -> Any:
    """An event call whose browser never answers, like a tab that switched chats right after sending."""
    await asyncio.Event().wait()


async def _run_inlet(ui_context: Any, body: dict[str, Any], offered: dict[str, Any]) -> dict[str, Any]:
    """OpenWebUI hands a filter only the extras its signature names (``utils/filter.py`` ``get_filter_params``)."""
    instance = ui_context.Filter()
    accepted = inspect.signature(instance.inlet).parameters
    return await instance.inlet(body, **{name: value for name, value in offered.items() if name in accepted})


@pytest.mark.asyncio
async def test_an_agent_turn_publishes_its_class_and_profile(ui_context: Any) -> None:
    emitter = AsyncMock()

    body = await _run_inlet(
        ui_context,
        {"model": AGENT_MODEL},
        {"__event_emitter__": emitter, "__metadata__": {"message_id": "msg-1"}, "__model__": {"name": "My RAG"}},
    )

    assert body == {"model": AGENT_MODEL}
    emitter.assert_awaited_once()
    event = emitter.await_args.args[0]
    assert event["type"] == "execute"
    code = event["data"]["code"]
    assert "set-model-context" in code
    assert f"agent_class: {json.dumps('RAGAgent')}" in code
    assert f"agent_name: {json.dumps('my-profile')}" in code
    assert f"display_id: {json.dumps(ui_context.Filter()._display_id('msg-1'))}" in code


@pytest.mark.asyncio
async def test_a_browser_that_never_answers_cannot_hold_the_turn(ui_context: Any) -> None:
    event_call = AsyncMock(side_effect=_never_answer)
    emitter = AsyncMock()

    body = await asyncio.wait_for(
        _run_inlet(ui_context, {"model": AGENT_MODEL}, {"__event_call__": event_call, "__event_emitter__": emitter}),
        timeout=1,
    )

    assert body == {"model": AGENT_MODEL}
    event_call.assert_not_awaited()
    emitter.assert_awaited_once()


@pytest.mark.asyncio
async def test_without_an_emitter_the_turn_passes_unchanged(ui_context: Any) -> None:
    body = await _run_inlet(ui_context, {"model": AGENT_MODEL}, {})

    assert body == {"model": AGENT_MODEL}


@pytest.mark.asyncio
async def test_a_failed_publish_still_lets_the_turn_through(ui_context: Any, caplog: pytest.LogCaptureFixture) -> None:
    emitter = AsyncMock(side_effect=RuntimeError("socket gone"))

    with caplog.at_level(logging.WARNING):
        body = await _run_inlet(ui_context, {"model": AGENT_MODEL}, {"__event_emitter__": emitter})

    assert body == {"model": AGENT_MODEL}
    assert "Failed to publish UI context: socket gone" in caplog.text


def test_the_template_copy_matches() -> None:
    assert filecmp.cmp(GENERATED_FILTER, TEMPLATE_FILTER, shallow=False)
