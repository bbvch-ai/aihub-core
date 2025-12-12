from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.prompting.few_shot.FewShotGuardExample import FewShotGuardExample
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from pydantic import Field, model_validator

from aihub_agent.agents.ExpertRagAgent.configs.ExpertEscalationConfig import ExpertEscalationConfig
from aihub_agent.agents.RagAgent.configs.RerankingConfig import RerankingConfig


class ExpertRAGAgentConfig(AgentConfig):
    """
    Configuration for ExpertRAGAgent with mandatory expert escalation and insight retrieval.

    Supports:
    - Multi-agent knowledge retrieval (0-n agents by ID)
    - Multi-agent insight retrieval (1-n agents by ID, REQUIRED)
    - Multi-hop retrieval for context sufficiency
    - MANDATORY expert escalation when context is insufficient
    - Explicit write_insight_namespace for storing new insights

    Note: insight_retrieval_agents is REQUIRED (at least 1) since ExpertRAGAgent
    needs an insight agent for retrieving and storing insights from expert answers.

    Important: For insights to be retrievable, at least one configured InsightRetrievalAgent
    must have a source matching (write_insight_namespace, agent_class, agent_id) where
    agent_class and agent_id are from this config (or overridden via RAGUserMessageEvent).
    """

    llm: Annotated[
        LLMConfig,
        Field(description="The LLM configuration for the agent."),
    ]

    # Knowledge retrieval agents by ID (0-n)
    knowledge_retrieval_agents: Annotated[
        list[str],
        Field(description="List of KnowledgeRetrievalAgent IDs to invoke for retrieval."),
    ] = []

    # Insight retrieval agents by ID (1-n, REQUIRED)
    insight_retrieval_agents: Annotated[
        list[str],
        Field(description="List of InsightRetrievalAgent IDs. REQUIRED for ExpertRAGAgent."),
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
    def validate_insight_retrieval_agents_required(self) -> "ExpertRAGAgentConfig":
        """Validate that at least one insight retrieval agent is configured."""
        if not self.insight_retrieval_agents:
            raise ValueError("ExpertRAGAgent requires at least one insight retrieval agent")
        return self
