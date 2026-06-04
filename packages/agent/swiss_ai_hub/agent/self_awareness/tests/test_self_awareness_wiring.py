"""
Self-awareness wiring contract.

A blueprint becomes self-aware by defining the self-awareness steps explicitly (detect/answer/stop).
Two invariants protect that design:

1. The three self-awareness steps are defined together or not at all — a partial set is a wiring bug.
2. A self-aware blueprint must gate every raw `UserMessageEvent` entry step with `NotAMetaQuestionEvent`,
   otherwise detection would race the normal pipeline (the §4 race condition). This gating cannot be
   automated, so this test is the guardrail that forces every present and future self-aware blueprint
   to wire it.
"""

from collections.abc import Callable

import pytest
from swiss_ai_hub.core.events.agent import NotAMetaQuestionEvent, StartEvent, UserMessageEvent
from swiss_ai_hub.core.workflow import DispatchableWorkflow

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.agents.expert_asking_agent.expert_asking_agent import ExpertAskingAgent
from swiss_ai_hub.agent.agents.expert_rag_agent.expert_rag_agent import ExpertRAGAgent
from swiss_ai_hub.agent.agents.few_shot_agent.few_shot_agent import FewShotAgent
from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent import LLMWrappingAgent
from swiss_ai_hub.agent.agents.mcp_react_agent.mcp_react_agent import McpReactAgent
from swiss_ai_hub.agent.agents.namespace_selection_agent.namespace_selection_agent import NamespaceSelectionAgent
from swiss_ai_hub.agent.agents.rag_agent.rag_agent import RAGAgent
from swiss_ai_hub.agent.agents.retrieval_agent.retrieval_agent import RetrievalAgent
from swiss_ai_hub.agent.self_awareness.meta_question_workflow_summary import SELF_AWARENESS_STEP_NAMES

PRODUCTION_AGENTS: list[type[Agent]] = [
    RAGAgent,
    ExpertRAGAgent,
    ExpertAskingAgent,
    FewShotAgent,
    LLMWrappingAgent,
    McpReactAgent,
    NamespaceSelectionAgent,
    RetrievalAgent,
]


def _step_names(agent: type[Agent]) -> set[str]:
    return {step.__name__ for step in agent.get_steps()}


def _is_self_aware(agent: type[Agent]) -> bool:
    """A blueprint is self-aware when it defines the detection step explicitly."""
    return "detect_meta_question_step" in _step_names(agent)


def _is_raw_chat_entry_step(step: Callable) -> bool:
    """
    True when this step fires directly on a raw chat message: it accepts `UserMessageEvent` and every
    required (non-optional) event parameter accepts only start events, so the start event alone triggers
    it. Steps with a required upstream event (e.g. condense, which needs `LimitChatHistoryEvent`) are
    not entry steps and are downstream of the gate, so they need no gating.
    """
    mapping: dict[str, set[type]] = getattr(step, DispatchableWorkflow.INPUT_EVENT_MAPPING_ANNOTATION)
    optional: dict[str, bool] = getattr(step, DispatchableWorkflow.PARAMETER_OPTIONAL_MAP_ANNOTATION)

    if not any(UserMessageEvent in events for events in mapping.values()):
        return False
    for name, events in mapping.items():
        if optional.get(name, False):
            continue
        if not all(issubclass(event, StartEvent) for event in events):
            return False
    return True


@pytest.mark.parametrize("agent", PRODUCTION_AGENTS)
def test_self_awareness_steps_are_all_or_nothing(agent: type[Agent]):
    """A blueprint defines the full set of self-awareness steps or none — a partial set is a wiring bug."""
    present = _step_names(agent) & SELF_AWARENESS_STEP_NAMES
    assert present in (set(), SELF_AWARENESS_STEP_NAMES), (
        f"{agent.__name__} defines a partial self-awareness step set: {present}. Define "
        "detect_meta_question_step, answer_meta_question_step and stop_after_meta_answer_step together."
    )


@pytest.mark.parametrize("agent", PRODUCTION_AGENTS)
def test_self_aware_agents_gate_their_chat_entry_steps(agent: type[Agent]):
    """A self-aware blueprint must gate every raw chat entry step with NotAMetaQuestionEvent."""
    if not _is_self_aware(agent):
        pytest.skip(f"{agent.__name__} does not define the self-awareness steps")

    for step in agent.get_steps():
        if step.__name__ in SELF_AWARENESS_STEP_NAMES:
            continue
        if not _is_raw_chat_entry_step(step):
            continue
        inputs = getattr(step, DispatchableWorkflow.INPUT_EVENTS_ANNOTATION)
        assert NotAMetaQuestionEvent in inputs, (
            f"{agent.__name__}.{step.__name__} fires on a raw UserMessageEvent but is not gated with "
            "NotAMetaQuestionEvent — self-awareness detection would race the normal pipeline. Add "
            "`_clear: NotAMetaQuestionEvent | None = None` and combine its precondition with "
            "check_passed_meta_question_gate."
        )
