from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.form import Checkbox
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.i18n import LocaleString

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
    enable_async_memory_storage: Annotated[
        bool | Checkbox,
        Field(
            description="When storage is enabled, persist user memory in an independent MemoryWriterAgent run "
            "instead of inline on the chat run's critical path (issue #1179). Off = current inline+blocking "
            "behavior; on = the run finalizes as soon as the answer is ready and memory persists in the "
            "background."
        ),
    ] = False

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
                ref="check_user_memory_storage_enabled",
            ),
            enable_async_memory_storage=Checkbox(
                label=LocaleString(
                    de="Speicher asynchron schreiben",
                    en="Store memory asynchronously",
                    fr="Enregistrer la mémoire de manière asynchrone",
                    it="Salva la memoria in modo asincrono",
                ),
                help=LocaleString(
                    de="Persistiert Nutzerspeicher ausserhalb des kritischen Pfads über den Memory-Writer-Agenten.",
                    en="Persist user memory off the chat critical path via the memory-writer agent.",
                    fr="Persiste la mémoire utilisateur hors du chemin critique via l'agent d'écriture mémoire.",
                    it="Persiste la memoria utente fuori dal percorso critico tramite l'agente di scrittura memoria.",
                ),
                condition_if="$get(check_user_memory_storage_enabled).value",
            ),
        )
