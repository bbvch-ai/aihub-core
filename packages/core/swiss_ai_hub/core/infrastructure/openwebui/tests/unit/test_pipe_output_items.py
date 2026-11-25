"""How the OpenWebUI pipe hands a finished answer to Open WebUI: as output items, each thought a reasoning item apart
from the answer text, so editing an answer never shows the agent's thinking as answer text."""

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


def _answered_after_thinking(pipe: Any) -> Any:
    state = pipe.StreamingStateManager()
    state.start_thinking_block("Checking whether this is a question about me\n")
    state.append_to_current_block("Thinking of a title for this conversation\n")
    state.start_text_block("Hello Thu! I'm your rose flower specialist.")
    state.finalize_all_blocks()
    return state


def _texts(item: dict[str, Any]) -> str:
    return "".join(part["text"] for part in item["content"])


def test_a_thought_becomes_a_reasoning_item_apart_from_the_answer(pipe: Any) -> None:
    items = _answered_after_thinking(pipe).to_output_items()

    assert [item["type"] for item in items] == ["reasoning", "message"]
    assert _texts(items[0]) == "Checking whether this is a question about me\nThinking of a title for this conversation"
    assert items[0]["status"] == "completed"
    assert _texts(items[1]) == "Hello Thu! I'm your rose flower specialist."
    assert "<details" not in _texts(items[1])


def test_tool_calls_stay_in_the_answer_in_the_order_they_ran(pipe: Any) -> None:
    state = pipe.StreamingStateManager()
    state.start_thinking_block("Looking up the weather")
    state.start_tool_block("c1", "get_weather", {"city": "Zurich"})
    state.complete_tool_block("c1", "Sunny")
    state.start_text_block("It is sunny in Zurich.")
    state.finalize_all_blocks()

    items = state.to_output_items()

    assert [item["type"] for item in items] == ["reasoning", "message"]
    answer = _texts(items[1])
    assert answer.index('<details type="tool_calls"') < answer.index("It is sunny in Zurich.")
    assert 'type="reasoning"' not in answer


def test_text_between_two_thoughts_keeps_its_place(pipe: Any) -> None:
    state = pipe.StreamingStateManager()
    state.start_thinking_block("First thought")
    state.start_tool_block("c1", "search", {})
    state.start_thinking_block("Second thought")
    state.start_text_block("Answer")
    state.finalize_all_blocks()

    items = state.to_output_items()

    assert [item["type"] for item in items] == ["reasoning", "message", "reasoning", "message"]
    assert [_texts(item) for item in items][2:] == ["Second thought", "Answer"]


def test_an_answer_without_thinking_is_one_message(pipe: Any) -> None:
    state = pipe.StreamingStateManager()
    state.start_text_block("Just the answer")
    state.finalize_all_blocks()

    assert [(item["type"], _texts(item)) for item in state.to_output_items()] == [("message", "Just the answer")]


@pytest.mark.asyncio
async def test_a_streamed_answer_reaches_open_webui_as_indexed_output_items(pipe: Any) -> None:
    state = _answered_after_thinking(pipe)

    events = [event async for event in pipe.Pipe._finished_answer(state, True)]

    assert [event["type"] for event in events] == ["response.output_item.done"] * 2
    assert [event["output_index"] for event in events] == [0, 1]
    assert [event["item"]["type"] for event in events] == ["reasoning", "message"]


def test_an_unstreamed_answer_stays_html(pipe: Any) -> None:
    state = _answered_after_thinking(pipe)

    assert pipe.Pipe._finished_answer(state, False) == state.serialize_to_html()
