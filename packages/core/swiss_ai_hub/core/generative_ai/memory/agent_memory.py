from datetime import datetime

from llama_index.core.base.llms.types import ChatMessage, MessageRole

from swiss_ai_hub.core.agents.agent_config import AgentConfig
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.infrastructure.mem0.mem0_service import Mem0Service
from swiss_ai_hub.core.infrastructure.mem0.mem0_settings import Mem0Settings
from swiss_ai_hub.core.infrastructure.mem0.types.memory_added import MemoryAdded
from swiss_ai_hub.core.infrastructure.mem0.types.memory_search_result import MemorySearchResult
from swiss_ai_hub.core.infrastructure.mem0.types.memory_type import MemoryType


class AgentMemory:
    """
    Manages user and organization memories for agents, integrating mem0 for persistent context across conversations.

    This class provides agents with long-term memory capabilities by wrapping mem0's memory management with
    agent-specific context. It customizes memory extraction prompts based on each agent's identity and purpose,
    ensuring that learned facts are relevant to the agent's domain.

    Why agent-scoped memory? Different agents serve different purposes (e.g., RAG for documents, code assistant
    for programming). Memories should be stored with agent context so retrieval is filtered by which agent
    interacted with the user, enabling specialized memory banks per agent type.
    """

    def __init__(self, agent_config: AgentConfig, agent_class: str, t: LocaleHandler):
        """
        Initialize agent memory with customized fact extraction prompts.

        Configures mem0 with agent-specific prompts that guide the LLM on what facts to extract from
        conversations. This personalization ensures memories are relevant to the agent's domain and includes
        temporal context (current date) for time-sensitive information.
        """
        self._agent_class = agent_class
        custom_fact_extraction_prompt = t(
            "lib.prompt.memory.fact_extraction",
            agent_name=t.extract(agent_config.name),
            agent_description=t.extract(agent_config.description),
            current_date=datetime.now().strftime("%Y-%m-%d"),
        )
        custom_update_memory_prompt = t(
            "lib.prompt.memory.memory_update",
            agent_name=t.extract(agent_config.name),
            agent_description=t.extract(agent_config.description),
        )

        self._agent_config = agent_config
        self._t = t
        self._config = Mem0Settings().get_config(
            custom_fact_extraction_prompt=custom_fact_extraction_prompt,
            custom_update_memory_prompt=custom_update_memory_prompt,
        )
        self.mem0service = Mem0Service(
            self._config,
            t=self._t,
        )

    @property
    def agent_id(self):
        """
        Returns agent identifier in format 'agent_class/agent_id'.

        This composite ID is used as the 'name' field in conversation history for mem0, distinguishing
        agent messages from user messages and enabling memory filtering by which agent was involved.
        """
        return f"{self._agent_class}/{self._agent_config.agent_id}"

    def messages_to_dict(
        self, messages: list[ChatMessage], user_id: str, remove_system_message: bool = True
    ) -> list[dict[str, str]]:
        """
        Converts LlamaIndex ChatMessage objects to mem0-compatible dict format.

        System messages are removed by default because they contain transient context (retrieval results,
        injected memories) rather than conversational content worth persisting. We only want to store
        the actual user-agent dialogue for memory extraction.
        """
        conversation: list[dict[str, str]] = []
        for msg in messages:
            name = user_id if msg.role == MessageRole.USER else self.agent_id
            if remove_system_message and msg.role == MessageRole.SYSTEM:
                continue
            conversation.append({"role": msg.role.value, "content": msg.content, "name": name})
        return conversation

    async def add_user_memory(
        self,
        messages: list[ChatMessage],
        user_id: str,
        thread_id: str,
        display_id: str,
        run_id: str,
    ) -> MemoryAdded:
        """
        Extracts and stores user-scoped memories from conversation messages.

        Memories are scoped to individual users, ensuring privacy - one user's memories never leak to another.
        The thread/display/run IDs are preserved in metadata for traceability (knowing which conversation
        generated which memory) and potential future filtering.
        """
        return await self.mem0service.add_memory(
            messages=self.messages_to_dict(messages, user_id),
            owner_id=user_id,
            memory_type=MemoryType.USER_MEMORY,
            user_id=user_id,
            agent_id=self.agent_id,
            thread_id=thread_id,
            display_id=display_id,
            run_id=run_id,
        )

    async def add_organization_memory(
        self,
        memory: str,
        user_id: str,
        thread_id: str,
        display_id: str,
        run_id: str,
        tenant_id: str,
        tenant_namespace: str,
    ) -> MemoryAdded:
        """
        Extracts and stores tenant-scoped memories shared across users.

        Tenant memories enable knowledge sharing within a company/team. Unlike user memories (private),
        these are accessible to all users within the tenant namespace. Use this for shared facts like
        company policies, project details, or team conventions that should inform all agents serving that tenant.

        Note that for tenant memories, the caller of the function is responsible for creating a clean
        memory, it is NOT inferred from the chat history.
        """
        messages = [{"role": MessageRole.USER, "content": memory, "name": user_id}]
        return await self.mem0service.add_memory(
            messages=messages,
            owner_id=tenant_id,
            memory_type=MemoryType.ORGANIZATION_MEMORY,
            user_id=user_id,
            agent_id=self.agent_id,
            thread_id=thread_id,
            display_id=display_id,
            run_id=run_id,
            tenant_id=tenant_id,
            tenant_namespace=tenant_namespace,
            infer=False,
        )

    async def search_user_memory(
        self,
        query: str,
        user_id: str,
        thread_id: str | None = None,
        display_id: str | None = None,
        run_id: str | None = None,
        limit: int = 100,
        threshold: float | None = None,
        rerank: bool = True,
    ) -> MemorySearchResult:
        """
        Retrieves relevant user memories via semantic search.

        Reranking is enabled by default to improve relevance - the initial vector search returns candidates,
        then a more sophisticated reranker (typically cross-encoder) refines the ordering. The threshold
        filters low-relevance results, ensuring only sufficiently related memories are returned.
        """
        return await self.mem0service.search(
            query=query,
            owner_id=user_id,
            thread_id=thread_id,
            display_id=display_id,
            run_id=run_id,
            memory_type=MemoryType.USER_MEMORY,
            user_id=user_id,
            agent_id=self.agent_id,
            limit=limit,
            threshold=threshold,
            rerank=rerank,
        )

    async def search_organization_memory(
        self,
        query: str,
        tenant_id: str,
        tenant_namespaces: list[str] | None = None,
        user_id: str | None = None,
        thread_id: str | None = None,
        display_id: str | None = None,
        run_id: str | None = None,
        limit: int = 100,
        threshold: float | None = None,
        rerank: bool = True,
    ) -> MemorySearchResult:
        """
        Retrieves relevant tenant memories via semantic search.

        Tenant namespace provides additional scoping for multi-tenant scenarios (e.g., different
        departments within a company). If not provided, searches across all memories for the tenant.
        This enables both broad tenant-wide knowledge and department-specific context.

        Organization memory is tenant-scoped and shared across agents within the tenant. Filtering
        by the searching agent (`self.agent_id`) is intentionally NOT applied — otherwise a memory
        written by one agent would be invisible to another. The writer's `_agent_id` remains on
        the stored memory's metadata as trace information, but does not partition reads.

        The caller controls `user_id` scoping: pass `None` (the default) for fully shared
        tenant-wide retrieval; pass a concrete `user_id` only if the caller wants to restrict
        results to memories written on behalf of that user.
        """
        return await self.mem0service.search(
            query=query,
            owner_id=tenant_id,
            thread_id=thread_id,
            display_id=display_id,
            run_id=run_id,
            memory_type=MemoryType.ORGANIZATION_MEMORY,
            user_id=user_id,
            agent_id=None,
            tenant_namespaces=tenant_namespaces,
            tenant_id=tenant_id,
            limit=limit,
            threshold=threshold,
            rerank=rerank,
        )
