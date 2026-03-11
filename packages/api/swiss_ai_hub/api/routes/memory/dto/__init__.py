"""Data Transfer Objects for memory management."""

from swiss_ai_hub.api.routes.memory.dto.delete_memory_response import DeleteAllMemoriesResponse, DeleteMemoryResponse
from swiss_ai_hub.api.routes.memory.dto.memories_response import MemoriesResponse
from swiss_ai_hub.api.routes.memory.dto.memory_dto import MemoryDTO
from swiss_ai_hub.api.routes.memory.dto.memory_graph_response import MemoryGraphResponse
from swiss_ai_hub.api.routes.memory.dto.memory_relation_dto import MemoryRelationDTO
from swiss_ai_hub.api.routes.memory.dto.memory_search_response import MemorySearchResponse
from swiss_ai_hub.api.routes.memory.dto.update_memory_request import UpdateMemoryRequest
from swiss_ai_hub.api.routes.memory.dto.update_memory_response import UpdateMemoryResponse

__all__ = [
    "DeleteAllMemoriesResponse",
    "DeleteMemoryResponse",
    "MemoriesResponse",
    "MemoryDTO",
    "MemoryGraphResponse",
    "MemoryRelationDTO",
    "MemorySearchResponse",
    "UpdateMemoryRequest",
    "UpdateMemoryResponse",
]
