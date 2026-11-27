"""An agent the model asked as a tool shows in OpenWebUI under that tool call: each step as a status while it runs,
and the steps listed above its answer in the tool's block."""

import html
import importlib.util
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[8]
TEMPLATE_PIPE = REPO_ROOT / "infra/deployment/templates/openwebui_functions/aihub_pipeline.py"
OPEN_WEBUI_MODULES = ["open_webui", "open_webui.models", "open_webui.models.chats", "open_webui.models.files"]
OPEN_WEBUI_MODULES += ["open_webui.models.users", "open_webui.utils", "open_webui.utils.chat_id"]


@pytest.fixture
def pipe(monkeypatch: pytest.MonkeyPatch) -> Any:
    for name in OPEN_WEBUI_MODULES:
        monkeypatch.setitem(sys.modules, name, MagicMock())
    spec = importlib.util.spec_from_file_location("aihub_pipeline", TEMPLATE_PIPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Recorder:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    async def __call__(self, event: dict[str, Any]) -> None:
        self.events.append(event)


def _context(pipe: Any) -> Any:
    return pipe.EventContext(
        state_manager=pipe.StreamingStateManager(),
        emitter=_Recorder(),
        caller=MagicMock(),
        headers={},
        agent_class="UniversalAgent",
        agent_id="assistant",
        thread_id="t1",
        stream_service=MagicMock(),
        chat_id="chat-1",
        message_id="msg-1",
    )


def _progress(step: str) -> dict[str, Any]:
    return {
        "_event_name": "DelegatedProgressEvent",
        "_parent_event_names": ["DelegatedProgressEvent", "DisplayEvent"],
        "tool_call_id": "call-1",
        "request_event_id": "request-1",
        "agent_class": "RAGAgent",
        "agent_id": "law",
        "step": step,
    }


@pytest.mark.asyncio
async def test_each_step_shows_as_status_and_is_listed_with_the_answer(pipe: Any) -> None:
    context = _context(pipe)
    await pipe.ToolEventHandler().handle(
        {"_parent_event_names": ["ToolEvent"], "tool_call_id": "call-1", "label": "Law Agent", "parameters": {}},
        context,
    )

    handler = pipe.DelegatedProgressEventHandler()
    assert await handler.can_handle(_progress("Retrieve"))
    await handler.handle(_progress("Retrieve"), context)
    await handler.handle(_progress("Answer"), context)
    await pipe.ToolResultEventHandler().handle({"tool_call_id": "call-1", "content": "Yes."}, context)

    statuses = [event["data"]["description"] for event in context.emitter.events if event["type"] == "status"]
    assert "Law Agent: Retrieve" in statuses and "Law Agent: Answer" in statuses
    assert html.escape('"Steps: Retrieve → Answer\\n\\nYes."') in context.state_manager.serialize_to_html()


@pytest.mark.asyncio
async def test_a_step_of_an_unknown_call_only_shows_as_status(pipe: Any) -> None:
    context = _context(pipe)

    await pipe.DelegatedProgressEventHandler().handle(_progress("Retrieve"), context)

    assert context.emitter.events[-1]["data"]["description"] == "Retrieve"
