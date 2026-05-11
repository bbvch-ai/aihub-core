from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.form import Checkbox
from swiss_ai_hub.core.form.form import Form

from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString


class UserMemoryConfig(Form):
    """
    Configuration for user-scoped memory in RAG workflows.

    Supports duality pattern for form rendering and data validation.
    """

    enable_user_memory_retrieval: Annotated[
        bool | Checkbox,
        Field(description="Whether to retrieve user-specific memories for personalized context."),
    ] = True
    rerank_user_memory: Annotated[
        bool | Checkbox,
        Field(description="Whether to rerank user memory search results via the configured reranker."),
    ] = True
    enable_user_memory_storage: Annotated[
        bool | Checkbox,
        Field(description="Whether to store new memories from conversations for future retrieval."),
    ] = True

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode UserMemoryConfig."""
        return cls(
            enable_user_memory_retrieval=Checkbox(
                label=AgentLocaleString.from_i18n_path("agent.rag_agent.config.enable_user_memory_retrieval.label"),
                help=AgentLocaleString.from_i18n_path("agent.rag_agent.config.enable_user_memory_retrieval.help"),
                ref="check_user_memory_retrieval_enabled",
            ),
            rerank_user_memory=Checkbox(
                label=AgentLocaleString.from_i18n_path("agent.rag_agent.config.rerank_user_memory.label"),
                help=AgentLocaleString.from_i18n_path("agent.rag_agent.config.rerank_user_memory.help"),
                condition_if="$get(check_user_memory_retrieval_enabled).value",
            ),
            enable_user_memory_storage=Checkbox(
                label=AgentLocaleString.from_i18n_path("agent.rag_agent.config.enable_user_memory_storage.label"),
                help=AgentLocaleString.from_i18n_path("agent.rag_agent.config.enable_user_memory_storage.help"),
            ),
        )
