from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.form import Checkbox, LocaleInput
from swiss_ai_hub.core.form.constraints import Ge
from swiss_ai_hub.core.generative_ai import FewShotGuardExample, KnowledgeRetrieverConfig
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.agents.rag_agent.configs.reranking_config import RerankingConfig
from swiss_ai_hub.agent.capabilities.attached_files.attached_files_fields import AttachedFilesFields
from swiss_ai_hub.agent.capabilities.conversation.conversation_fields import ConversationFields
from swiss_ai_hub.agent.capabilities.memory.memory_fields import MemoryFields
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.steps.guards.context_sufficient_guard_step.context_sufficient_guard_step_config import (
    ContextSufficientGuardStepConfig,
)


class RAGAgentConfig(MemoryFields, AttachedFilesFields, ConversationFields, AgentConfig):
    """
    Configuration for a RAGAgent with multiple retrieval sources.

    The conversational and memory fields come from the capability mixins; what is declared here is
    retrieval: sources, reranking, the guards and the prompts that frame retrieved context.

    Note: For expert escalation functionality, use ExpertRAGAgentConfig instead.

    Supports duality pattern for form rendering and data validation.
    """

    system_prompt: Annotated[
        LocaleString | LocaleInput | None,
        Field(description="System prompt to guide the agent's behavior and responses.", title="System Prompt"),
    ] = AgentLocaleString.from_i18n_path("agent.rag_agent.config.system_prompt.default")
    context_prompt: Annotated[
        LocaleString | LocaleInput | None,
        Field(
            description="Prompt template for providing context (e.g., retrieved documents) to the LLM.",
            title="Context Prompt",
        ),
    ] = AgentLocaleString.from_i18n_path("agent.rag_agent.config.context_prompt.default")
    condense_question: Annotated[
        bool | Checkbox,
        Field(description="Retrieval embeds one standalone question, so RAG condenses by default."),
    ] = True
    context_sufficient_guard: Annotated[
        ContextSufficientGuardStepConfig,
        Field(
            description="Configuration for the context-sufficient guard step.",
            title="Context Sufficient Guard",
        ),
    ] = ContextSufficientGuardStepConfig()
    retrievers: Annotated[
        list[KnowledgeRetrieverConfig],
        Field(description="List of knowledge retriever configurations.", title="Retrievers"),
    ]
    reranking_config: Annotated[
        RerankingConfig | None,
        Field(description="Configuration for reranking retrieved documents to improve relevance.", title="Reranking"),
    ] = None
    retrieved_tokens_per_node: Annotated[
        int,
        Field(
            description="A retrieved node's size in tokens for reserving room, on the generous side: ingestion chunks "
            "are shorter, but neighbour and summary nodes ride along with them."
        ),
        Ge(1),
    ] = 800
    restrict_to_user_access: Annotated[
        bool | Checkbox,
        Field(description="Retrieve only from the configured collections the asking user may read."),
    ] = False
    few_shot_guard_examples: Annotated[
        list[FewShotGuardExample],
        Field(
            description="Examples for the few-shot guard to define which user requests are accepted.",
            title="Few-Shot Guard Examples",
        ),
    ] = []

    def retrieved_context_reserve(self) -> int:
        """Tokens to keep free for the knowledge this profile retrieves, so attached files cannot crowd it out.

        An estimate, not a count: retrieval runs after the files are sized. It covers every retrieved node with its
        neighbours, narrowed to the reranker's top_n when reranking is on, and never more than half the budget.
        """
        nodes = sum(
            retriever.retrieve_k
            * (1 + 2 * retriever.retrieve_prev_next.num_nodes if retriever.retrieve_prev_next else 1)
            for retriever in self.retrievers
        )
        if self.reranking_config is not None:
            nodes = min(nodes, self.reranking_config.reranking_model.top_n)
        return min(nodes * self.retrieved_tokens_per_node, self.input_budget() // 2)

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode RAGAgentConfig."""
        base = AgentConfig.as_form()

        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            **cls.conversation_form_elements(),
            **cls.memory_form_elements(),
            **cls.attached_files_form_elements(),
            retrievers=[KnowledgeRetrieverConfig.as_form()],
            context_sufficient_guard=ContextSufficientGuardStepConfig.as_form(),
            reranking_config=RerankingConfig.as_form(),
            few_shot_guard_examples=[FewShotGuardExample.as_form()],
            restrict_to_user_access=Checkbox(
                label=AgentLocaleString.from_i18n_path("agent.rag_agent.config.restrict_to_user_access.label"),
                help=AgentLocaleString.from_i18n_path("agent.rag_agent.config.restrict_to_user_access.help"),
                value=True,
            ),
            system_prompt=LocaleString.as_form(
                label=AgentLocaleString.from_i18n_path("agent.rag_agent.config.system_prompt.label"),
                help_text=AgentLocaleString.from_i18n_path("agent.rag_agent.config.system_prompt.help"),
                input_type="textarea",
            ),
            context_prompt=LocaleString.as_form(
                label=AgentLocaleString.from_i18n_path("agent.rag_agent.config.context_prompt.label"),
                help_text=AgentLocaleString.from_i18n_path("agent.rag_agent.config.context_prompt.help"),
                input_type="textarea",
            ),
        )
