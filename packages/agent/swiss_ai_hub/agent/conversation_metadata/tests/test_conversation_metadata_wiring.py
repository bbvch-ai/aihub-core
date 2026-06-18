"""Wiring test for conversation-metadata step adoption (analogous to test_self_awareness_wiring).

Conversation metadata (title + follow-up questions) is adopted as explicit per-agent ``@step``
wrappers — there is no base-class mixin (see the ADR). This test pins which agents adopt the steps so
a newly added conversational agent cannot silently forget to, and the excluded agents cannot silently
gain them.
"""

from swiss_ai_hub.agent.agents.expert_asking_agent.expert_asking_agent import ExpertAskingAgent
from swiss_ai_hub.agent.agents.expert_rag_agent.expert_rag_agent import ExpertRAGAgent
from swiss_ai_hub.agent.agents.few_shot_agent.few_shot_agent import FewShotAgent
from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent import LLMWrappingAgent
from swiss_ai_hub.agent.agents.mcp_react_agent.mcp_react_agent import McpReactAgent
from swiss_ai_hub.agent.agents.namespace_selection_agent.namespace_selection_agent import NamespaceSelectionAgent
from swiss_ai_hub.agent.agents.rag_agent.rag_agent import RAGAgent
from swiss_ai_hub.agent.agents.retrieval_agent.retrieval_agent import RetrievalAgent

CONVERSATION_METADATA_STEPS = {"generate_conversation_title_step", "generate_follow_up_questions_step"}

# Answer-owning conversational agents that currently adopt the metadata steps. Their final answer is a
# non-terminal LLMEvent the steps can hook on.
ADOPTING_AGENTS = [RAGAgent, ExpertRAGAgent]

# Conversational agents that are intended to adopt but are blocked: their answer is a stop event
# (LLMStopEvent / StopEvent) and the dispatcher returns on stop events before dispatching waiting
# steps, so a step cannot consume the answer. Adopting them requires restructuring their terminal step
# (tracked with the issue owner). They must NOT silently adopt half-working steps in the meantime.
ADOPTION_BLOCKED_AGENTS = [LLMWrappingAgent, FewShotAgent, McpReactAgent]

# Non-answer-owning or non-conversational agents that must never adopt the steps.
EXCLUDED_AGENTS = [RetrievalAgent, NamespaceSelectionAgent, ExpertAskingAgent]


def _step_names(agent_type) -> set[str]:
    return {step.__name__ for step in agent_type.get_steps()}


def test_adopting_agents_define_both_metadata_steps():
    for agent_type in ADOPTING_AGENTS:
        assert CONVERSATION_METADATA_STEPS.issubset(_step_names(agent_type)), (
            f"{agent_type.__name__} must define both conversation-metadata steps"
        )


def test_excluded_and_blocked_agents_do_not_define_metadata_steps():
    for agent_type in EXCLUDED_AGENTS + ADOPTION_BLOCKED_AGENTS:
        assert not (CONVERSATION_METADATA_STEPS & _step_names(agent_type)), (
            f"{agent_type.__name__} must not define conversation-metadata steps"
        )
