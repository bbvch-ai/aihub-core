import asyncio
import hashlib
import logging
from copy import deepcopy
from datetime import datetime
from typing import override

import pytz
from mem0 import AsyncMemory

logger = logging.getLogger(__name__)


class PatchedAsyncMemory(AsyncMemory):
    """
    Patches mem0's AsyncMemory to preserve custom metadata during updates.

    mem0's default _update_memory() method only preserves a hardcoded set of fields
    (user_id, agent_id, run_id, actor_id, role) and deletes all other metadata.
    This patch ensures ALL metadata (especially underscore-prefixed fields like
    _thread_id, _user_id, etc.) is preserved during memory updates.
    """

    @override
    async def _update_memory(self, memory_id: str, data: str, existing_embeddings, metadata=None):
        """
        Update memory data while preserving ALL metadata fields.

        This overrides mem0's _update_memory to preserve ALL fields from existing memory,
        not just the hardcoded set (user_id, agent_id, run_id, actor_id, role).
        """
        try:
            existing_memory = await asyncio.to_thread(self.vector_store.get, vector_id=memory_id)
        except Exception:
            logger.error(f"Error getting memory with ID {memory_id} during update.")
            raise ValueError(f"Error getting memory with ID {memory_id}. Please provide a valid 'memory_id'")

        prev_value = existing_memory.payload.get("data")

        new_metadata = deepcopy(existing_memory.payload)

        if metadata is not None:
            new_metadata.update(deepcopy(metadata))

        new_metadata["data"] = data
        new_metadata["hash"] = hashlib.md5(data.encode()).hexdigest()
        new_metadata["created_at"] = existing_memory.payload.get("created_at")
        new_metadata["updated_at"] = datetime.now(pytz.timezone("US/Pacific")).isoformat()

        if data in existing_embeddings:
            embeddings = existing_embeddings[data]
        else:
            embeddings = await asyncio.to_thread(self.embedding_model.embed, data, "update")

        await asyncio.to_thread(
            self.vector_store.update,
            vector_id=memory_id,
            vector=embeddings,
            payload=new_metadata,
        )

        await asyncio.to_thread(
            self.db.add_history,
            memory_id,
            prev_value,
            data,
            "UPDATE",
            is_deleted=0,
        )
