import warnings
from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.knowledge.KnowledgeRetrieverConfig import KnowledgeRetrieverConfig
from aihub_lib.generative_ai.knowledge.RetrieverFactory import RetrieverConfig
from aihub_lib.generative_ai.prompting.few_shot.FewShotGuardExample import FewShotGuardExample
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from pydantic import Field, model_validator

from aihub_agent.agents.RagAgent.configs.ExpertWorkflowConfig import ExpertWorkflowConfig
from aihub_agent.agents.RagAgent.configs.RerankingConfig import RerankingConfig
from aihub_agent.agents.RagAgent.configs.RetrieveStepConfig import RetrieveStepConfig


class RAGAgentConfig(AgentConfig):
    """
    Configuration for a RAGAgent with multiple retrieval sources and optional expert workflow.

    Supports:
    - Multiple retrievers (knowledge base + insights)
    - Optional expert escalation when context is insufficient
    - Backward compatibility with legacy retrieve_step_config
    """

    llm: Annotated[
        LLMConfig,
        Field(description="The LLM configuration for the agent."),
    ]

    # New: Multiple retrievers
    retrievers: Annotated[
        list[RetrieverConfig],
        Field(description="List of retriever configurations (knowledge, insight)."),
    ] = []

    # Legacy: Single retriever config (deprecated, auto-migrated)
    retrieve_step_config: Annotated[
        RetrieveStepConfig | None,
        Field(description="DEPRECATED: Use 'retrievers' instead."),
    ] = None

    number_of_input_tokens: Annotated[
        int,
        Field(description="Maximum tokens allowed in input to manage context size or cost."),
    ]
    condense_question_prompt: Annotated[
        LocaleString | None,
        Field(description="Prompt template for transforming a user query into a standalone question."),
    ] = None
    context_prompt: Annotated[
        LocaleString | None,
        Field(description="Prompt template for providing context (e.g., retrieved documents) to the LLM."),
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
    reranking_config: Annotated[
        RerankingConfig,
        Field(description="Configuration for reranking retrieved documents to improve relevance."),
    ] = RerankingConfig()

    # New: Optional expert workflow
    expert_workflow_config: Annotated[
        ExpertWorkflowConfig | None,
        Field(description="Optional config to enable expert escalation when context is insufficient."),
    ] = None

    @model_validator(mode="after")
    def migrate_legacy_config(self) -> "RAGAgentConfig":
        """Auto-migrate legacy retrieve_step_config to retrievers list."""
        if self.retrieve_step_config and not self.retrievers:
            warnings.warn(
                "retrieve_step_config is deprecated. Use 'retrievers' list instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            self.retrievers = [
                KnowledgeRetrieverConfig(
                    retriever_type="knowledge",
                    name="Primary Knowledge Base",
                    embed_model=self.retrieve_step_config.embed_model,
                    vector_store=self.retrieve_step_config.vector_store,
                    index_namespaces=self.retrieve_step_config.index_namespaces,
                    retrieve_k=self.retrieve_step_config.retrieve_k,
                    query_mode=self.retrieve_step_config.query_mode,
                    node_types=self.retrieve_step_config.node_types,
                    retrieve_prev_next=self.retrieve_step_config.retrieve_prev_next,
                )
            ]
        return self
