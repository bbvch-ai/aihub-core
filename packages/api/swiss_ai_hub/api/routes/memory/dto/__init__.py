"""Data Transfer Objects for memory management."""

from swiss_ai_hub.api.routes.memory.dto.DeleteMemoryResponse import DeleteAllMemoriesResponse, DeleteMemoryResponse
from swiss_ai_hub.api.routes.memory.dto.MemoriesResponse import MemoriesResponse
from swiss_ai_hub.api.routes.memory.dto.MemoryDTO import MemoryDTO
from swiss_ai_hub.api.routes.memory.dto.MemoryGraphResponse import MemoryGraphResponse
from swiss_ai_hub.api.routes.memory.dto.MemoryRelationDTO import MemoryRelationDTO
from swiss_ai_hub.api.routes.memory.dto.MemorySearchResponse import MemorySearchResponse
from swiss_ai_hub.api.routes.memory.dto.UpdateMemoryRequest import UpdateMemoryRequest
from swiss_ai_hub.api.routes.memory.dto.UpdateMemoryResponse import UpdateMemoryResponse

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
