import logging
from collections.abc import Callable
from functools import cached_property

from llama_index.core.utils import get_tokenizer
from mem0.configs.base import MemoryConfig

from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config import EmbeddingModelConfig
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.infrastructure.mem0.graph.patched_memory_graph import PatchedMemoryGraph
from swiss_ai_hub.core.infrastructure.mem0.patched_async_memory import PatchedAsyncMemory
from swiss_ai_hub.core.infrastructure.mem0.patched_milvus_db import PatchedMilvusDB
from swiss_ai_hub.core.infrastructure.mem0.patched_open_ai_embedding import PatchedOpenAIEmbedding
from swiss_ai_hub.core.infrastructure.mem0.patched_open_aillm import PatchedOpenAILLM
from swiss_ai_hub.core.infrastructure.mem0.types.memory import Memory
from swiss_ai_hub.core.infrastructure.mem0.types.memory_added import MemoryAdded
from swiss_ai_hub.core.infrastructure.mem0.types.memory_search_result import MemorySearchResult
from swiss_ai_hub.core.infrastructure.mem0.types.memory_type import MemoryType

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_MAX_INPUT_TOKENS = 8192

# We can only count tiktoken tokens locally, but the budget is spent in the embedder's own tokenizer, and
# tiktoken undercounts. Measured against a live bge-m3: English 1.60x (8101 -> 12963), French 1.00x, German
# and Chinese below 1. The factor has to cover the worst case, so it tolerates a 2x undercount. Deliberately
# not the 0.85 that markdown_structural_node_parser uses for chunking: at the measured English ratio 0.85
# leaves a full-size input at ~1.9x its real budget. Raising this needs the same measurement against
# whatever model the deployment runs.
SEARCH_QUERY_BUDGET_SAFETY_FACTOR = 0.5

# Smallest window we assume any deployed embedder accepts. Only used to decide when a query is short enough
# to skip resolving the real window, so it must never exceed a configured model's actual window.
MINIMUM_EMBEDDING_MAX_INPUT_TOKENS = 512


class Mem0Service:
    def __init__(
        self,
        config: MemoryConfig,
        t: LocaleHandler,
        max_search_query_tokens: int | None = None,
    ):
        self._config = config
        self._max_search_query_tokens = max_search_query_tokens
        self._memory = PatchedAsyncMemory(config=config)
        self._memory.vector_store = PatchedMilvusDB.from_milvus(self._memory.vector_store)
        self._memory.llm = PatchedOpenAILLM.from_llm(self._memory.llm)
        self._memory.embedding_model = PatchedOpenAIEmbedding.from_embedding(self._memory.embedding_model)
        # When the graph store is disabled, mem0 sets enable_graph=False and self.graph=None — nothing to wrap.
        if self._memory.enable_graph:
            self._memory.graph = PatchedMemoryGraph.from_graph(self._memory.graph, t=t)

    @property
    def config(self):
        return self._config

    @cached_property
    def _effective_query_token_limit(self) -> int:
        window = self._max_search_query_tokens or (
            EmbeddingModelConfig(model_name=self._config.embedder.config["model"])
            .get_model_info()["model_info"]
            .get("max_input_tokens")
            or DEFAULT_EMBEDDING_MAX_INPUT_TOKENS
        )
        return max(1, int(window * SEARCH_QUERY_BUDGET_SAFETY_FACTOR))

    @staticmethod
    def _longest_fitting_tail(query: str, limit: int, tokenizer: Callable[[str], list[int]]) -> str:
        """
        Keep a long suffix within the budget: chat clients inline documents before the user's question, so
        the tail is where the question lives.

        Safety does not rest on suffix token counts being monotonic — under BPE they are not
        ("unbelievable" measures [3, 3, 2, 3, ...]). It rests on `high` only ever being assigned an index
        that measured as fitting, so the returned suffix was measured, never inferred. Non-monotonicity
        costs optimality alone: a slightly longer suffix may also have fit.

        Chosen over a sentence splitter because sentence boundaries buy an embedding vector nothing while
        this hits the budget exactly. It also avoids NLTK punkt, whose corpus loader rejects files with
        st_nlink > 1 — which is what a `uv` venv installs by default, though not what the images ship
        (every app Dockerfile sets UV_LINK_MODE=copy), so that failure is a dev-machine one.
        """
        low, high = 0, len(query)
        while low < high:
            middle = (low + high) // 2
            if len(tokenizer(query[middle:])) <= limit:
                high = middle
            else:
                low = middle + 1
        return query[low:] or query[-1:]

    def _clamp_query(self, query: str) -> str:
        """
        The cheap check counts tokens rather than characters: a character is not an upper bound on tokens
        (a ZWJ emoji sequence costs 7). It compares against the smallest window we support so a query that
        fits any model returns without resolving the real, possibly remote, limit.
        """
        tokenizer = get_tokenizer()
        original_tokens = len(tokenizer(query))
        resolution_free_budget = int(
            (self._max_search_query_tokens or MINIMUM_EMBEDDING_MAX_INPUT_TOKENS) * SEARCH_QUERY_BUDGET_SAFETY_FACTOR
        )
        if original_tokens <= resolution_free_budget:
            return query
        limit = self._effective_query_token_limit
        if original_tokens <= limit:
            return query
        clamped = self._longest_fitting_tail(query, limit, tokenizer)
        logger.warning(
            "Search query exceeds the embedding budget, truncating: %d -> %d tokens (%d -> %d characters, limit %d)",
            original_tokens,
            len(tokenizer(clamped)),
            len(query),
            len(clamped),
            limit,
        )
        return clamped

    async def add_memory(
        self,
        messages: list[dict[str, str]],
        owner_id: str,
        memory_type: MemoryType,
        user_id: str,
        agent_id: str,
        thread_id: str,
        display_id: str,
        run_id: str,
        tenant_id: str | None = None,
        tenant_namespace: str | None = None,
        infer: bool = True,
    ) -> MemoryAdded:
        metadata = {
            "_type": memory_type.value,
            "_user_id": user_id,
            "_agent_id": agent_id,
            "_thread_id": thread_id,
            "_display_id": display_id,
            "_run_id": run_id,
            "_tenant_id": tenant_id,
            "_tenant_namespace": tenant_namespace,
        }
        # Filter out None values and empty strings
        metadata = {k: str(v) for k, v in metadata.items() if v is not None and v != ""}
        # Native agent_id scopes mem0's infer-time reconciliation (its ADD/UPDATE/DELETE search over
        # existing memories) to the writing agent, so one agent's write can no longer rewrite or delete
        # another agent's user memories. mem0 reconciles on native keys, not on our `_agent_id` metadata.
        # Org memory is left unscoped (infer=False, intentionally tenant-shared). Reads stay cross-agent
        # shared — the read path passes agent_id=None deliberately.
        native_agent_id = agent_id if memory_type == MemoryType.USER_MEMORY else None
        added_memory = await self._memory.add(
            messages,
            user_id=owner_id,
            agent_id=native_agent_id,
            metadata=metadata,
            infer=infer,
        )

        # mem0 omits the "relations" key entirely when the graph store is disabled (main.py returns only
        # {"results": ...}); default to an empty structure so graph-off writes don't KeyError.
        relations = added_memory.get("relations") or {}
        added_entities, deleted_entities = [], []
        for relation in relations.get("added_entities", []):
            if isinstance(relation, list):
                added_entities.extend(relation)
            else:
                added_entities.append(relation)
        for relation in relations.get("deleted_entities", []):
            if isinstance(relation, list):
                deleted_entities.extend(relation)
            else:
                deleted_entities.append(relation)

        added_memory["relations"] = {"added_entities": added_entities, "deleted_entities": deleted_entities}

        return MemoryAdded.model_validate(
            {
                **added_memory,
                "owner_id": owner_id,
                "_user_id": user_id,
                "_agent_id": agent_id,
                "_thread_id": thread_id,
                "_display_id": display_id,
                "_run_id": run_id,
                "_tenant_id": tenant_id,
                "_tenant_namespace": tenant_namespace,
                "_type": memory_type.value,
                # Only an inferring write runs the LLM; a verbatim write reports no model because none ran.
                "llm_model_name": self._config.llm.config["model"] if infer else None,
            }
        )

    async def get_memory(self, memory_id: str) -> Memory:
        memory = await self._memory.get(memory_id)
        return Memory.model_validate(memory)

    async def delete_memory(self, memory_id: str):
        await self._memory.delete(memory_id)

    async def update_memory(self, memory_id: str, data: str):
        await self._memory.update(memory_id=memory_id, data=data)

    async def search(
        self,
        query: str,
        owner_id: str,
        thread_id: str | None = None,
        display_id: str | None = None,
        run_id: str | None = None,
        memory_type: MemoryType | None = None,
        user_id: str | None = None,
        agent_id: str | None = None,
        tenant_id: str | None = None,
        tenant_namespaces: list[str] | None = None,
        limit: int = 100,
        threshold: float | None = None,
        rerank: bool = True,
    ) -> MemorySearchResult:
        query = self._clamp_query(query)
        scalar_filters = {
            "_type": memory_type.value,
            "_user_id": user_id,
            "_agent_id": agent_id,
            "_thread_id": thread_id,
            "_display_id": display_id,
            "_run_id": run_id,
            "_tenant_id": tenant_id,
        }
        filters: dict[str, str | dict[str, list[str]]] = {
            k: str(v) for k, v in scalar_filters.items() if v is not None and v != ""
        }
        if tenant_namespaces:
            filters["_tenant_namespace"] = (
                tenant_namespaces[0] if len(tenant_namespaces) == 1 else {"in": list(tenant_namespaces)}
            )
        memories = await self._memory.search(
            query=query,
            user_id=owner_id,
            limit=limit,
            filters=filters,
            threshold=threshold,
            rerank=rerank,
        )
        return MemorySearchResult.model_validate(memories)

    async def delete_all(
        self,
        owner_id: str,
    ):
        await self._memory.delete_all(user_id=owner_id)

    async def get_all(
        self,
        owner_id: str,
    ) -> MemorySearchResult:
        memories = await self._memory.get_all(user_id=owner_id, limit=10_000)
        return MemorySearchResult.model_validate(memories)
