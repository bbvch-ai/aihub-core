"""How the OpenWebUI pipe shows an agent's question in Open WebUI's dialog: the dialog cannot scroll, so a long tool
input sits in a capped box that keeps the buttons on screen, and the input is shown exactly as the model wrote it."""

import html
import importlib.util
import re
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[8]
TEMPLATE_PIPE = REPO_ROOT / "infra/deployment/templates/openwebui_functions/aihub_pipeline.py"
OPEN_WEBUI_MODULES = ["open_webui", "open_webui.models", "open_webui.models.chats", "open_webui.models.files"]
OPEN_WEBUI_MODULES += ["open_webui.models.users"]
OPEN_WEBUI_MODULES += ["open_webui.utils", "open_webui.utils.chat_id"]

TRICKY_LINES = [
    "# load the workbook",
    "import pandas as pd",
    "",
    "df = pd.read_excel('Billing.xlsx')  # <img src=x onerror=alert(1)>",
    "print(f'`{df.shape}` & $x$ costs')",
    "html = '</pre><b>hidden</b>'",
]


@pytest.fixture
def pipe(monkeypatch: pytest.MonkeyPatch) -> Any:
    for name in OPEN_WEBUI_MODULES:
        monkeypatch.setitem(sys.modules, name, MagicMock())
    spec = importlib.util.spec_from_file_location("aihub_pipeline", TEMPLATE_PIPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _context(pipe: Any, answer: Any) -> Any:
    return pipe.EventContext(
        state_manager=pipe.StreamingStateManager(),
        emitter=AsyncMock(),
        caller=AsyncMock(return_value=answer),
        headers={},
        agent_class="UniversalAgent",
        agent_id="assistant",
        thread_id="t1",
        stream_service=MagicMock(send_hitl_response=AsyncMock()),
    )


def _approval(question: str) -> dict[str, Any]:
    return {
        "_event_name": "ToolApprovalRequestEvent",
        "_parent_event_names": [
            "HumanInTheLoopConfirmationRequestEvent",
            "HumanInTheLoopRequestEvent",
            "SemanticEvent",
        ],
        "event_id": "e1",
        "hitl_type": "confirmation",
        "question": question,
        "topic": {"event_name": "ToolApprovalResponseEvent", "display_id": "d1"},
    }


def _hitl(hitl_type: str, question: str) -> dict[str, Any]:
    return {
        "_event_name": "HumanInTheLoopConfirmationRequestEvent",
        "_parent_event_names": ["HumanInTheLoopRequestEvent", "SemanticEvent"],
        "event_id": "e2",
        "hitl_type": hitl_type,
        "question": question,
        "topic": {},
    }


def _run_command_question(command: str) -> str:
    return f'The assistant wants to use "Run Command": Run in the code sandbox:\n{command}\nAllow it?'


async def _dialog_message(pipe: Any, event: dict[str, Any], answer: Any = True) -> tuple[str, Any]:
    context = _context(pipe, answer)
    await pipe.EventProcessorFactory.create_chain().process(event, context)
    dialog = context.caller.await_args.args[0]
    return dialog["data"]["message"], context


@pytest.mark.asyncio
async def test_a_long_command_sits_escaped_in_one_scroll_box_between_lead_and_ask(pipe: Any) -> None:
    command = "\n".join(TRICKY_LINES * 10)

    message, _ = await _dialog_message(pipe, _approval(_run_command_question(command)))

    assert message.count("<pre") == 1
    assert message.count("</pre>") == 1
    lead, box, ask = re.fullmatch(
        r"<p>(.*)</p>\n\n<pre style=\"([^\"]*)\">(.*)</pre>\n\n<p>(.*)</p>", message, re.S
    ).group(1, 3, 4)
    assert lead == "The assistant wants to use &quot;Run Command&quot;: Run in the code sandbox:"
    assert ask == "Allow it?"
    assert box.split("\n") == [html.escape(line) for line in TRICKY_LINES * 10]


@pytest.mark.asyncio
async def test_the_box_caps_its_height_and_keeps_the_indentation(pipe: Any) -> None:
    message, _ = await _dialog_message(pipe, _approval(_run_command_question("for row in rows:\n    print(row)")))

    style = re.search(r'<pre style="([^"]*)"', message).group(1)
    assert "max-height:50vh" in style
    assert "overflow:auto" in style
    assert "white-space:pre;" in style
    assert "monospace" in style
    assert "\n    print(row)</pre>" in message


@pytest.mark.asyncio
async def test_a_one_line_approval_is_boxed_and_wraps(pipe: Any) -> None:
    message, _ = await _dialog_message(pipe, _approval('Allow "Write File" to write <report>.md?'))

    assert re.fullmatch(r'<pre style="[^"]*white-space:pre-wrap;[^"]*">[^<]*</pre>', message)
    assert "&lt;report&gt;.md" in message


@pytest.mark.asyncio
async def test_another_confirmation_keeps_its_markdown_in_a_capped_wrapper(pipe: Any) -> None:
    question = "Search these knowledge bases?\n\n- **Contracts**\n- **Invoices**"

    message, _ = await _dialog_message(pipe, _hitl("confirmation", question))

    assert message == f'<div style="max-height:60vh;overflow-y:auto">\n\n{question}\n\n</div>'


@pytest.mark.asyncio
async def test_the_input_dialog_question_is_capped_too(pipe: Any) -> None:
    message, context = await _dialog_message(pipe, _hitl("input", "Which **year**?"), answer={"value": "2025"})

    assert message == '<div style="max-height:60vh;overflow-y:auto">\n\nWhich **year**?\n\n</div>'
    assert context.stream_service.send_hitl_response.await_args.args[1]["response"] == "2025"


@pytest.mark.asyncio
async def test_cancel_is_still_sent_back_to_the_agent(pipe: Any) -> None:
    event = _approval(_run_command_question("rm -rf build"))

    _, context = await _dialog_message(pipe, event, answer=False)

    name, payload, display_id, *_ = context.stream_service.send_hitl_response.await_args.args
    assert (name, payload["response"], display_id) == ("ToolApprovalResponseEvent", False, "d1")
