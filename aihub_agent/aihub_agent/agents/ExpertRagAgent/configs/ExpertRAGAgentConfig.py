from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.prompting.few_shot.FewShotGuardExample import FewShotGuardExample
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from pydantic import Field, model_validator

from aihub_agent.agents.ExpertRagAgent.configs.ExpertEscalationConfig import ExpertEscalationConfig
from aihub_agent.agents.RagAgent.configs.RerankingConfig import RerankingConfig
from aihub_agent.agents.RagAgent.configs.RetrievalAgentReference import RetrievalAgentReference


class ExpertRAGAgentConfig(AgentConfig):
    """
    Configuration for ExpertRAGAgent with mandatory expert escalation.

    Supports:
    - Multi-agent retrieval (1-n agents by ID) - requires at least one insight retrieval agent
    - Multi-hop retrieval for context sufficiency
    - MANDATORY expert escalation when context is insufficient
    - Explicit write_insight_namespace for storing new insights

    Note: At least one insight retrieval agent is REQUIRED since ExpertRAGAgent
    needs an insight agent for retrieving and storing insights from expert answers.

    Important: For insights to be retrievable, at least one configured InsightRetrievalAgent
    must have a source matching (write_insight_namespace, agent_class, agent_id) where
    agent_class and agent_id are from this config (or overridden via RAGUserMessageEvent).
    """

    llm: Annotated[
        LLMConfig,
        Field(description="The LLM configuration for the agent."),
    ]

    # Unified retrieval agents - requires at least one insight retrieval agent
    retrieval_agents: Annotated[
        list[RetrievalAgentReference],
        Field(description="List of retrieval agents. REQUIRED: at least one must be an insight retrieval agent."),
    ]

    # Where new insights are stored (REQUIRED)
    write_insight_namespace: Annotated[
        str,
        Field(description="Namespace where new insights from expert answers will be stored."),
    ]

    # Expert escalation (REQUIRED)
    expert_escalation: Annotated[
        ExpertEscalationConfig,
        Field(description="Expert escalation config. REQUIRED for ExpertRAGAgent."),
    ]

    # Shared reranking (applied after combining all results)
    reranking_config: Annotated[
        RerankingConfig,
        Field(description="Configuration for reranking combined results to improve relevance."),
    ] = RerankingConfig()

    number_of_input_tokens: Annotated[
        int, Field(description="Maximum tokens allowed in input to manage context size or cost.")
    ]
    condense_question_prompt: Annotated[
        LocaleString | None,
        Field(description="Prompt template for transforming a user query into a standalone question."),
    ] = None
    few_shot_guard_examples: Annotated[
        list[FewShotGuardExample],
        Field(description="Examples for the few-shot guard to define which user requests are accepted."),
    ] = []
    check_context_sufficiency: Annotated[
        bool | None,
        Field(
            description="Whether or not to check if the retrieved context is sufficient for generating a response.",
        ),
    ] = False
    max_hops: Annotated[
        int,
        Field(
            description="Maximum number of retrieval hops to perform if context is insufficient.",
            ge=1,
        ),
    ] = 1
    system_prompt: Annotated[
        LocaleString | None,
        Field(description="System prompt to guide the agent's behavior and responses."),
    ] = None

    @model_validator(mode="after")
    def validate_retrieval_agents_required(self) -> "ExpertRAGAgentConfig":
        """Validate that at least one retrieval agent is configured."""
        if not self.retrieval_agents:
            raise ValueError("ExpertRAGAgent requires at least one retrieval agent (including insight retrieval)")
        return self
