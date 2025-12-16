from typing import Annotated

from pydantic import Field

from aihub_agent.agents.RagAgent.configs.ExpertEscalationConfig import ExpertEscalationConfig
from aihub_agent.agents.RagAgent.configs.RAGAgentConfig import RAGAgentConfig


class ExpertRAGAgentConfig(RAGAgentConfig):
    """
    Configuration for an ExpertRAGAgent with expert escalation capability.

    Extends RAGAgentConfig with expert escalation when context is insufficient.
    The expert escalation workflow allows the agent to consult human experts
    when the retrieved context is insufficient to answer the user's question.
    """

    expert_escalation: Annotated[
        ExpertEscalationConfig,
        Field(description="Expert escalation config. Required for ExpertRAGAgent."),
    ]
