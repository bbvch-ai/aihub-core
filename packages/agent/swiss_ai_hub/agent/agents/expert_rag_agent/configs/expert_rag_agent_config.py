from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.generative_ai import MemorySettings

from swiss_ai_hub.agent.agents.rag_agent.configs.expert_escalation_config import ExpertEscalationConfig
from swiss_ai_hub.agent.agents.rag_agent.configs.rag_agent_config import RAGAgentConfig


class ExpertRAGAgentConfig(RAGAgentConfig):
    """
    Configuration for an ExpertRAGAgent with expert escalation capability.

    Extends RAGAgentConfig with expert escalation when context is insufficient.
    The expert escalation workflow allows the agent to consult human experts
    when the retrieved context is insufficient to answer the user's question.

    Supports duality pattern for form rendering and data validation.
    """

    expert_escalation: Annotated[
        ExpertEscalationConfig,
        Field(description="Expert escalation config. Required for ExpertRAGAgent.", title="Expert Escalation"),
    ]
    tenant_namespace: Annotated[
        str | None,
        Field(
            description=(
                "Namespace passed to the downstream ExpertAsking agent for storing expert-conversation memories. "
                "None defers to ExpertAsking's own `tenant_namespace`."
            ),
        ),
    ] = Field(default_factory=lambda: MemorySettings().DEFAULT_TENANT_NAMESPACE)

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode ExpertRAGAgentConfig."""
        base_form = RAGAgentConfig.as_form()

        return cls(
            name=base_form.name,
            description=base_form.description,
            icon=base_form.icon,
            agent_id=base_form.agent_id,
            llm=base_form.llm,
            retrievers=base_form.retrievers,
            number_of_input_tokens=base_form.number_of_input_tokens,
            context_sufficient_guard=base_form.context_sufficient_guard,
            reranking_config=base_form.reranking_config,
            few_shot_guard_examples=base_form.few_shot_guard_examples,
            system_prompt=base_form.system_prompt,
            context_prompt=base_form.context_prompt,
            memory=base_form.memory,
            expert_escalation=ExpertEscalationConfig.as_form(),
        )
