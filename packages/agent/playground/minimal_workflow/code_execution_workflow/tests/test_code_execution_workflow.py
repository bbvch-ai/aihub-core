"""Code execution without a tool loop: the message's Python blocks run as written and their output comes back as a
file, the same way every time."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from swiss_ai_hub.core.events.agent import SandboxFileDisplayedEvent

from playground.minimal_workflow.code_execution_workflow.code_execution_playground_config import (
    CodeExecutionPlaygroundConfig,
)
from playground.minimal_workflow.code_execution_workflow.python_block_agent import PythonBlockAgent
from playground.minimal_workflow.code_execution_workflow.python_blocks import PythonBlocks

MESSAGE = """Please run these:

```python
print(6 * 7)
```

and

```python
import sys
print(sys.version_info.major)
```

```bash
echo not python
```"""


def _workspace() -> Any:
    workspace = MagicMock()
    workspace.folder = "conversations/t1"
    workspace.path = lambda path: f"conversations/t1/{path}"
    workspace.client.write_file = AsyncMock()
    workspace.client.execute = AsyncMock(
        side_effect=[
            {"exit_code": 0, "output": [{"data": "42\r\n"}]},
            {"exit_code": 0, "output": [{"data": "3\r\n"}]},
        ]
    )
    workspace.keep = AsyncMock(
        return_value=SandboxFileDisplayedEvent(
            path="conversations/t1/python_output.txt",
            filename="python_output.txt",
            content_type="text/plain",
            size=40,
            bucket="agent-files",
            key="k",
        )
    )
    return workspace


def test_the_blueprint_validates_without_a_tool_loop():
    PythonBlockAgent.validate_workflow(CodeExecutionPlaygroundConfig)

    assert PythonBlockAgent.tool_sets() == []
    assert PythonBlockAgent.supported_features() == set()


def test_only_the_python_blocks_are_found():
    assert PythonBlocks.in_text(MESSAGE) == ["print(6 * 7)", "import sys\nprint(sys.version_info.major)"]


def test_a_message_without_python_has_nothing_to_run():
    assert PythonBlocks.in_text("What does `print(1)` do?") == []


@pytest.mark.asyncio
async def test_each_block_runs_as_its_own_script_and_the_output_is_kept_as_a_file():
    workspace = _workspace()

    report, kept = await PythonBlocks.run(workspace, PythonBlocks.in_text(MESSAGE), "en")

    assert [call.args for call in workspace.client.write_file.await_args_list[:2]] == [
        ("conversations/t1/python_block_1.py", "print(6 * 7)"),
        ("conversations/t1/python_block_2.py", "import sys\nprint(sys.version_info.major)"),
    ]
    assert [call.args[0] for call in workspace.client.execute.await_args_list] == [
        "python3 python_block_1.py",
        "python3 python_block_2.py",
    ]
    assert report == "Block 1 (exit code 0):\n42\n\nBlock 2 (exit code 0):\n3\n"
    workspace.client.write_file.assert_awaited_with("conversations/t1/python_output.txt", report)
    workspace.keep.assert_awaited_once_with("python_output.txt")
    assert kept.filename == "python_output.txt"


@pytest.mark.asyncio
async def test_a_block_still_running_after_the_wait_is_stopped_before_the_next_runs():
    workspace = _workspace()
    workspace.client.kill = AsyncMock()
    workspace.client.execute = AsyncMock(
        side_effect=[
            {"status": "running", "id": "p1", "output": [{"data": "working\n"}]},
            {"exit_code": 0, "output": [{"data": "3\n"}]},
        ]
    )

    report, _ = await PythonBlocks.run(workspace, ["while True: pass", "print(3)"], "en")

    workspace.client.kill.assert_awaited_once_with("p1", force=True)
    assert report == "Block 1 (stopped after 60 seconds):\nworking\n\nBlock 2 (exit code 0):\n3\n"


@pytest.mark.asyncio
async def test_the_report_is_written_in_the_run_locale():
    report, _ = await PythonBlocks.run(_workspace(), ["print(6 * 7)", "print(3)"], "de")

    assert report.startswith("Block 1 (Exit-Code 0):\n42")


@pytest.mark.asyncio
async def test_the_reply_is_shown_and_completes_the_turn_like_a_model_answer():
    displayer = MagicMock()
    displayer.display_chunk = AsyncMock()

    answer = await PythonBlocks.reply(displayer, "done")

    displayer.display_chunk.assert_awaited_once_with("done", model_name="python")
    assert [(message.role, message.content) for message in answer.output_messages] == [("assistant", "done")]
