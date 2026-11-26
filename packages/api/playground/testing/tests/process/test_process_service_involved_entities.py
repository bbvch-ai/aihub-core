from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock, patch

import pytest

from swiss_ai_hub.api.routes.agent.dto.minimal_agent_instance_dto import MinimalAgentInstanceDTO
from swiss_ai_hub.api.routes.process.process_service import ProcessService
from swiss_ai_hub.api.routes.user.dto.minimal_user_dto import MinimalUserDTO

AGENT_WORK = ["AgentBWork", "AgentWorkEvent", "WorkEvent", "ProcessEvent"]
HUMAN_WORK = ["ReviewWork", "HumanWorkEvent", "WorkEvent", "ProcessEvent"]
AGENT_WORK_REQUEST = ["AgentWorkRequestEvent", "WorkRequestEvent", "ProcessEvent"]
# The classes the caller loaded up front; `MissingAgent` is not among them.
CLASSES = {"AgentB": Mock(name="AgentB"), "AgentC": Mock(name="AgentC")}


def _event(parents: list[str], submitted_by: Any) -> dict[str, Any]:
    return {"event_parents": parents, "event_data": {"submitted_by": submitted_by}}


def _agent(agent_class: str, agent_id: str) -> dict[str, str]:
    return {"agent_class": agent_class, "agent_id": agent_id}


@pytest.fixture(autouse=True)
def tagged_dtos():
    """DTOs are tagged with their profile so the test can tell them apart."""
    with patch.object(
        MinimalAgentInstanceDTO,
        "from_class_and_config",
        side_effect=lambda class_entity, config_entity, t: f"dto:{config_entity}",
    ):
        yield


def test_each_agent_that_did_work_is_listed_once():
    configs = {("AgentB", "b"): "config-b", ("AgentC", "c"): "config-c"}
    events = [
        _event(AGENT_WORK, _agent("AgentB", "b")),
        _event(AGENT_WORK, _agent("AgentC", "c")),
        _event(AGENT_WORK, _agent("AgentB", "b")),
    ]

    agents, humans = ProcessService._extract_involved_entities(events, Mock(), configs, CLASSES)

    assert agents == ["dto:config-b", "dto:config-c"]
    assert humans == []


def test_an_agent_without_its_profile_or_class_is_left_out():
    configs = {("MissingAgent", "m"): "config-m"}
    events = [
        _event(AGENT_WORK, _agent("AgentB", "no-profile")),
        _event(AGENT_WORK, _agent("AgentB", "no-profile")),
        _event(AGENT_WORK, _agent("MissingAgent", "m")),
    ]

    agents, _ = ProcessService._extract_involved_entities(events, Mock(), configs, CLASSES)

    assert agents == []


def test_requests_and_other_events_name_nobody():
    events = [
        _event(AGENT_WORK_REQUEST, _agent("AgentB", "b")),
        {"event_parents": ["ProcessStartEvent", "ProcessEvent"], "event_data": {}},
        {"event_data": {}},
    ]

    assert ProcessService._extract_involved_entities(events, Mock(), {("AgentB", "b"): "config-b"}, CLASSES) == ([], [])


def test_each_human_that_did_work_is_listed_once_from_a_dict_or_an_object():
    alice = {"id": "alice", "name": "Alice", "email": "alice@example.com", "profile_image": "img"}
    bob = SimpleNamespace(id="bob", name="Bob", email="bob@example.com")
    events = [_event(HUMAN_WORK, alice), _event(HUMAN_WORK, bob), _event(HUMAN_WORK, alice)]

    _, humans = ProcessService._extract_involved_entities(events, Mock(), {}, CLASSES)

    assert humans == [
        MinimalUserDTO(id="alice", name="Alice", email="alice@example.com", profile_image="img"),
        MinimalUserDTO(id="bob", name="Bob", email="bob@example.com", profile_image=None),
    ]


def test_a_human_without_an_id_is_left_out():
    events = [_event(HUMAN_WORK, {"name": "Nobody", "email": "x@example.com"}), _event(HUMAN_WORK, SimpleNamespace())]

    assert ProcessService._extract_involved_entities(events, Mock(), {}, CLASSES) == ([], [])


def test_agents_and_humans_are_collected_from_one_walkthrough():
    events = [
        _event(HUMAN_WORK, {"id": "alice", "name": "Alice", "email": "alice@example.com"}),
        _event(AGENT_WORK, _agent("AgentB", "b")),
    ]

    agents, humans = ProcessService._extract_involved_entities(events, Mock(), {("AgentB", "b"): "config-b"}, CLASSES)

    assert agents == ["dto:config-b"]
    assert [human.id for human in humans] == ["alice"]
