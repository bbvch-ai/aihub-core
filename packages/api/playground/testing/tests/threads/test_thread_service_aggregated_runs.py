from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

from swiss_ai_hub.api.routes.agent.dto.agent_identifier import AgentIdentifier
from swiss_ai_hub.api.routes.thread.dto.statistics.intermediate_display_stats import IntermediateDisplayStats
from swiss_ai_hub.api.routes.thread.dto.statistics.run_statistics import RunStatistics
from swiss_ai_hub.api.routes.thread.thread_service import ThreadService


def _run(run_id: str, display_id: str | None, start_agent: tuple[str, str], *participants: dict) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "display_id": display_id,
        "start_agent_class": start_agent[0],
        "start_agent_id": start_agent[1],
        "participating_agents_in_run": list(participants),
    }


@pytest.fixture
def isolated_statistics():
    """Agents `RAGAgent/*` resolve, any other agent does not; run statistics are tagged by run id."""
    fetch = AsyncMock(
        side_effect=lambda agent_class, agent_id, t: f"agent:{agent_id}" if agent_class == "RAGAgent" else None
    )
    added: list[tuple[str, str]] = []
    with (
        patch.object(ThreadService, "_fetch_minimal_agent_dto", fetch),
        patch.object(IntermediateDisplayStats, "update_from_run_data"),
        patch.object(
            IntermediateDisplayStats, "add_run_dto", lambda self, run: added.append((self.display_id, run)), create=True
        ),
        patch.object(
            RunStatistics, "from_run_data", side_effect=lambda run_data, agent: f"{run_data['run_id']}+{agent}"
        ),
    ):
        yield fetch, added


@pytest.mark.asyncio
async def test_runs_are_grouped_by_display_and_carry_their_starting_agent(isolated_statistics):
    _, added = isolated_statistics
    runs = [
        _run("r1", "d1", ("RAGAgent", "hr")),
        _run("r2", "d1", ("RAGAgent", "hr")),
        _run("r3", "d2", ("RAGAgent", "fi")),
    ]

    results = await ThreadService._process_aggregated_runs(runs, Mock())

    assert list(results.display_aggregates) == ["d1", "d2"]
    assert added == [("d1", "r1+agent:hr"), ("d1", "r2+agent:hr"), ("d2", "r3+agent:fi")]


@pytest.mark.asyncio
async def test_a_run_without_display_is_skipped(isolated_statistics):
    fetch, added = isolated_statistics

    results = await ThreadService._process_aggregated_runs([_run("r1", None, ("RAGAgent", "hr"))], Mock())

    assert results.display_aggregates == {}
    assert added == []
    fetch.assert_not_awaited()


@pytest.mark.asyncio
async def test_a_run_whose_agent_cannot_be_resolved_keeps_its_display_without_statistics(isolated_statistics):
    _, added = isolated_statistics

    results = await ThreadService._process_aggregated_runs([_run("r1", "d1", ("DeletedAgent", "gone"))], Mock())

    assert list(results.display_aggregates) == ["d1"]
    assert added == []


@pytest.mark.asyncio
async def test_a_run_whose_statistics_fail_to_build_does_not_stop_the_others(isolated_statistics):
    _, added = isolated_statistics
    runs = [_run("broken", "d1", ("RAGAgent", "hr")), _run("r2", "d1", ("RAGAgent", "hr"))]

    def build(run_data: dict, agent: str) -> str:
        if run_data["run_id"] == "broken":
            raise ValueError("invalid run")
        return f"{run_data['run_id']}+{agent}"

    with patch.object(RunStatistics, "from_run_data", side_effect=build):
        await ThreadService._process_aggregated_runs(runs, Mock())

    assert added == [("d1", "r2+agent:hr")]


@pytest.mark.asyncio
async def test_participating_agents_are_collected_without_the_user_or_incomplete_entries(isolated_statistics):
    runs = [
        _run(
            "r1",
            "d1",
            ("RAGAgent", "hr"),
            {"agent_class": "RAGAgent", "agent_id": "hr"},
            {"agent_class": "UserAgent", "agent_id": "alice"},
            {"agent_class": "RAGAgent"},
            {"agent_id": "orphan"},
        ),
        _run("r2", "d2", ("RAGAgent", "fi"), {"agent_class": "RAGAgent", "agent_id": "hr"}),
    ]

    results = await ThreadService._process_aggregated_runs(runs, Mock())

    assert results.participating_agent_ids == {AgentIdentifier(agent_class="RAGAgent", agent_id="hr")}
