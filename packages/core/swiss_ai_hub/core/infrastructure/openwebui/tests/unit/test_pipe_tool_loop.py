"""How the OpenWebUI pipe shows an agent's tool loop: each chosen tool as Open WebUI's own collapsible tool block
with its result, the model's preamble out of the answer, and a status while the loop works in the background."""

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
OPEN_WEBUI_MODULES += ["open_webui.models.users"]


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

    @property
    def statuses(self) -> list[dict[str, Any]]:
        return [event["data"] for event in self.events if event["type"] == "status"]


def _context(pipe: Any, emitter: _Recorder) -> Any:
    return pipe.EventContext(
        state_manager=pipe.StreamingStateManager(),
        emitter=emitter,
        caller=MagicMock(),
        headers={},
        agent_class="ToolLoopAgent",
        agent_id="assistant",
        thread_id="t1",
        stream_service=MagicMock(),
    )


def _tool_call(call_id: str = "c1") -> dict[str, Any]:
    return {
        "_event_name": "ToolEvent",
        "_parent_event_names": ["ToolEvent", "SemanticEvent"],
        "event_id": "e1",
        "tool_call_id": call_id,
        "name": "get_weather",
        "label": "Weather",
        "description": "get_weather(city: str) -> str\nWeather and forecast for a city.",
        "parameters": {"city": "Zurich"},
    }


async def _process(pipe: Any, context: Any, *events: dict[str, Any]) -> None:
    chain = pipe.EventProcessorFactory.create_chain()
    for event in events:
        await chain.process(event, context)


@pytest.mark.asyncio
async def test_a_chosen_tool_shows_under_its_label_with_its_result(pipe: Any) -> None:
    emitter = _Recorder()
    context = _context(pipe, emitter)
    result = {"_event_name": "ToolResultEvent", "tool_call_id": "c1", "name": "get_weather", "content": "Sunny, 21°C"}

    await _process(pipe, context, _tool_call(), result)

    html = context.state_manager.serialize_to_html()
    assert 'type="tool_calls" done="true" id="c1" name="Weather"' in html
    assert "Sunny, 21°C" in html
    assert emitter.statuses[0]["description"] == "Weather"


@pytest.mark.asyncio
async def test_a_result_finds_its_block_after_other_calls_started(pipe: Any) -> None:
    context = _context(pipe, _Recorder())
    first_result = {"_event_name": "ToolResultEvent", "tool_call_id": "c1", "name": "get_weather", "content": "Rain"}

    await _process(pipe, context, _tool_call("c1"), _tool_call("c2"), first_result)

    html = context.state_manager.serialize_to_html()
    assert html.index("Rain") < html.index('id="c2"')


@pytest.mark.asyncio
async def test_a_failed_call_reads_as_an_error(pipe: Any) -> None:
    context = _context(pipe, _Recorder())
    failed = {"_event_name": "ToolResultEvent", "tool_call_id": "c1", "content": "timeout", "is_error": True}

    await _process(pipe, context, _tool_call(), failed)

    assert "Error: timeout" in context.state_manager.serialize_to_html()


@pytest.mark.asyncio
async def test_a_result_is_shown_as_the_model_received_it(pipe: Any) -> None:
    context = _context(pipe, _Recorder())
    result = {"_event_name": "ToolResultEvent", "tool_call_id": "c1", "content": "Cite it as [s3f9a1c]."}

    await _process(pipe, context, _tool_call(), result)

    assert "[s3f9a1c]" in context.state_manager.serialize_to_html()


@pytest.mark.asyncio
async def test_text_streamed_before_a_tool_call_moves_out_of_the_answer(pipe: Any) -> None:
    context = _context(pipe, _Recorder())
    preamble = {"_parent_event_names": ["ChunkEvent"], "content": "Let me check the weather."}
    answer = {"_parent_event_names": ["ChunkEvent"], "content": "Take an umbrella."}

    await _process(pipe, context, preamble, _tool_call(), answer)

    html = context.state_manager.serialize_to_html()
    assert '<details type="reasoning" done="true">\nLet me check the weather.' in html
    assert html.rstrip().endswith("Take an umbrella.")


@pytest.mark.asyncio
async def test_the_loop_says_what_it_does_while_nothing_else_shows(pipe: Any) -> None:
    emitter = _Recorder()
    status = {"_event_name": "ToolLoopStatusEvent", "loop": "tools", "description": "Deciding", "done": False}

    await _process(pipe, _context(pipe, emitter), status)

    assert emitter.statuses == [{"action": None, "description": "Deciding", "done": False}]


@pytest.mark.asyncio
async def test_condensing_shows_as_a_finished_status(pipe: Any) -> None:
    emitter = _Recorder()
    condensed = {
        "_event_name": "ToolLoopCondensedEvent",
        "loop": "tools",
        "description": "Condensed earlier results to fit the conversation",
    }

    await _process(pipe, _context(pipe, emitter), condensed)

    assert emitter.statuses == [
        {"action": None, "description": "Condensed earlier results to fit the conversation", "done": True}
    ]


def test_an_earlier_answer_reaches_the_agent_without_its_tool_blocks(pipe: Any) -> None:
    """A model handed its own earlier tool blocks writes one as text instead of calling the tool."""
    answer = (
        '<details type="reasoning" done="true"><summary>Thought</summary>\n&gt; plan</details>\n'
        '<details type="tool_calls" done="true" id="c1" name="Run Command" arguments="{&quot;command&quot;: '
        '&quot;python3 run.py&quot;}" result="&quot;Exit code 0.&quot;"><summary>Tool Executed</summary></details>\n'
        "The chart is attached."
    )
    question = 'Keep <details type="note">this</details> as I wrote it.'

    converted = pipe.MessageConverter.convert_to_event_format(
        [{"role": "assistant", "content": answer}, {"role": "user", "content": question}]
    )

    assert [block["text"].strip() for block in converted[0]["blocks"]] == ["The chart is attached."]
    assert converted[1]["blocks"] == [{"block_type": "text", "text": question}]


def test_an_earlier_answer_keeps_a_details_block_it_wrote_itself(pipe: Any) -> None:
    answer = 'Here are the steps:\n<details type="note"><summary>Steps</summary>Open the file.</details>'

    converted = pipe.MessageConverter.convert_to_event_format([{"role": "assistant", "content": answer}])

    assert "Open the file." in converted[0]["blocks"][0]["text"]
