"""A precondition may only ask for events its own step declares.

`AgentDispatcher.check_and_trigger_steps` builds the event map from the **step's** `_input_events` and hands that
same map to the precondition. So a precondition parameter typed as an event the step does not consume is never
bound, and because `_build_event_kwargs` simply omits a kwarg it cannot fill, a *required* one raises
`TypeError: <precondition>() missing 1 required positional argument` — inside the dispatcher, on every run of that
agent, long after the code looked correct in review.

That is not hypothetical: adding `start_event` to `ready_for_stop` broke every RAG and Expert-RAG run exactly this
way. The steps whose preconditions read a start event happen to declare one, so the mistake looks fine right up
until it is made on a step that does not.

Identity is the usual reason to want one, and `UserIdentity | None` is the answer — the dispatcher fills it from
`RunContext`, independent of any step's event declarations.
"""

import inspect

import pytest

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.agents.email_classification_agent import EmailClassificationAgent
from swiss_ai_hub.agent.agents.expert_asking_agent.expert_asking_agent import ExpertAskingAgent
from swiss_ai_hub.agent.agents.expert_rag_agent.expert_rag_agent import ExpertRAGAgent
from swiss_ai_hub.agent.agents.few_shot_agent.few_shot_agent import FewShotAgent
from swiss_ai_hub.agent.agents.imap_agent.imap_agent import ImapAgent
from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent import LLMWrappingAgent
from swiss_ai_hub.agent.agents.namespace_selection_agent.namespace_selection_agent import NamespaceSelectionAgent
from swiss_ai_hub.agent.agents.rag_agent.rag_agent import RAGAgent
from swiss_ai_hub.agent.agents.retrieval_agent.retrieval_agent import RetrievalAgent

_AGENTS = [
    EmailClassificationAgent,
    ExpertAskingAgent,
    ExpertRAGAgent,
    FewShotAgent,
    ImapAgent,
    LLMWrappingAgent,
    NamespaceSelectionAgent,
    RAGAgent,
    RetrievalAgent,
]


def _steps_with_preconditions(agent: type[Agent]):
    for step_method in agent.get_steps():
        precondition_fn = getattr(step_method, Agent.PRECONDITION_FUNCTION_ANNOTATION, None)
        if precondition_fn is not None:
            yield step_method, precondition_fn


@pytest.mark.parametrize("agent", _AGENTS, ids=lambda agent: agent.__name__)
def test_no_precondition_asks_for_an_event_its_step_does_not_declare(agent: type[Agent]):
    for step_method, precondition_fn in _steps_with_preconditions(agent):
        step_events = getattr(step_method, Agent.INPUT_EVENTS_ANNOTATION, set())
        precondition_events = getattr(precondition_fn, Agent.INPUT_EVENTS_ANNOTATION, set())

        unreachable = precondition_events - step_events
        assert not unreachable, (
            f"{agent.__name__}.{step_method.__name__}'s precondition {precondition_fn.__name__} asks for "
            f"{sorted(event.__name__ for event in unreachable)}, which the step does not consume — the dispatcher "
            f"builds the event map from the step's inputs, so those parameters are never bound. Declare the event on "
            f"the step, or take what you need from RunContext (e.g. `user: UserIdentity | None`)."
        )


@pytest.mark.parametrize("agent", _AGENTS, ids=lambda agent: agent.__name__)
def test_every_required_precondition_parameter_can_actually_be_filled(agent: type[Agent]):
    """The failure mode is a `TypeError` inside the dispatcher, so an unfillable *required* parameter is the sharp
    edge — an optional one merely stays `None`."""
    for step_method, precondition_fn in _steps_with_preconditions(agent):
        step_events = getattr(step_method, Agent.INPUT_EVENTS_ANNOTATION, set())
        mapping = getattr(precondition_fn, Agent.INPUT_EVENT_MAPPING_ANNOTATION, {})

        for name, parameter in inspect.signature(precondition_fn).parameters.items():
            if parameter.default is not inspect.Parameter.empty or name not in mapping:
                continue
            assert mapping[name] & step_events, (
                f"{agent.__name__}.{step_method.__name__}'s precondition {precondition_fn.__name__} requires "
                f"'{name}', but none of {sorted(event.__name__ for event in mapping[name])} is consumed by the step "
                f"— every run of this agent would raise TypeError before the precondition could decide anything."
            )
