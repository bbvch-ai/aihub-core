"""How the OpenWebUI pipe shows a table a model extracted in its tool loop: as a block of the answer that stays where
it arrived, capped inline, with its summary below; and how an earlier table shrinks to a line on the way back."""

import importlib.util
import re
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from swiss_ai_hub.core.generative_ai.structured_extraction.extracted_table_markup import ExtractedTableMarkup

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
    )


def _table(rows: int) -> str:
    body = "\n".join(f"| invoices/a.pdf | a.pdf | item {index} [s1a2b3c] |" for index in range(rows))
    return ExtractedTableMarkup.wrap(f"| Path | File | item |\n| --- | --- | --- |\n{body}", rows)


def _extracted(rows: int = 3, tool_call_id: str | None = "c1") -> dict[str, Any]:
    return {
        "_event_name": "RecordsExtractedEvent",
        "_parent_event_names": ["RecordsExtractedEvent", "ControlAndDisplayEvent"],
        "event_id": "e9",
        "extraction_id": "x1",
        "table": _table(rows) if rows else "",
        "summary": "**Files:** 1 · **Rows found:** 3",
        "row_count": rows,
        "tool_call_id": tool_call_id,
    }


def _tool_call(call_id: str = "c1") -> dict[str, Any]:
    return {
        "_event_name": "ToolEvent",
        "_parent_event_names": ["ToolEvent", "SemanticEvent"],
        "event_id": "e1",
        "tool_call_id": call_id,
        "name": "extract_records",
        "label": "Extract a Table",
        "parameters": {"fields": "item"},
    }


def _chunk(text: str) -> dict[str, Any]:
    return {"_event_name": "ChunkEvent", "_parent_event_names": ["ChunkEvent", "DisplayEvent"], "content": text}


async def _process(pipe: Any, context: Any, *events: dict[str, Any]) -> None:
    chain = pipe.EventProcessorFactory.create_chain()
    for event in events:
        await chain.process(event, context)


@pytest.mark.asyncio
async def test_a_table_extracted_for_a_tool_call_stays_in_the_answer_with_its_summary(pipe: Any):
    context = _context(pipe)

    await _process(pipe, context, _tool_call(), _extracted(), _chunk("The table lists three items."))

    html = context.state_manager.serialize_to_html()
    assert html.index('type="tool_calls"') < html.index("| invoices/a.pdf | a.pdf | item 0") < html.index("**Files:**")
    assert html.rstrip().endswith("The table lists three items.")
    assert '<details type="reasoning"' not in html


@pytest.mark.asyncio
async def test_a_table_is_never_turned_into_a_thought_by_a_later_tool_call(pipe: Any):
    context = _context(pipe)

    await _process(pipe, context, _tool_call("c1"), _extracted(), _tool_call("c2"), _chunk("Done."))

    html = context.state_manager.serialize_to_html()
    outside_collapsed_blocks = re.sub(r"<details\b[^>]*>[\s\S]*?</details>", "", html)
    assert "| invoices/a.pdf | a.pdf | item 2" in outside_collapsed_blocks
    assert html.count('type="tool_calls"') == 2


@pytest.mark.asyncio
async def test_citation_rewriting_leaves_table_cells_alone(pipe: Any):
    context = _context(pipe)

    await _process(pipe, context, _extracted())

    assert "item 0 [s1a2b3c]" in context.state_manager.serialize_to_html()


@pytest.mark.asyncio
async def test_a_blueprints_own_table_and_an_empty_one_are_not_shown_twice(pipe: Any):
    context = _context(pipe)

    await _process(pipe, context, _extracted(tool_call_id=None), _extracted(rows=0))

    assert "invoices/a.pdf" not in context.state_manager.serialize_to_html()


@pytest.mark.asyncio
async def test_a_large_table_is_capped_inline_and_says_so(pipe: Any):
    context = _context(pipe)

    await _process(pipe, context, _extracted(rows=250))

    html = context.state_manager.serialize_to_html()
    assert "item 99 " in html
    assert "item 100 " not in html
    assert "Showing the first 100 of 250 rows here." in html
    assert '[aihub-extracted-table]: # "rows=250"' in html


def test_a_table_cut_inline_condenses_to_its_real_row_count(pipe: Any):
    shown = pipe.RecordsExtractedEventHandler()._inline(_extracted(rows=250))

    condensed = pipe.MessageConverter.strip_agent_markup(shown)

    assert condensed.startswith("[A table of 250 extracted rows was shown here.]")


def test_a_cell_quoting_the_end_marker_does_not_end_the_table(pipe: Any):
    quoting = ExtractedTableMarkup.wrap(
        "| Path | Clause |\n| --- | --- |\n| a.pdf | see [/aihub-extracted-table]: # in the annex |\n| b.pdf | b |", 2
    )

    converted = pipe.MessageConverter.convert_to_event_format([{"role": "assistant", "content": quoting}])

    assert converted[0]["blocks"][0]["text"] == "[A table of 2 extracted rows was shown here.]"


def test_an_earlier_table_shrinks_to_a_line_on_the_way_back(pipe: Any):
    answer = f"{_table(3)}\n\n**Files:** 1"

    converted = pipe.MessageConverter.convert_to_event_format([{"role": "assistant", "content": answer}])

    assert converted[0]["blocks"][0]["text"] == "[A table of 3 extracted rows was shown here.]\n\n**Files:** 1"
