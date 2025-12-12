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

        # DEBUG: Log what we're getting from the vector store
        logger.info(f"[METADATA DEBUG 1] existing_memory type: {type(existing_memory)}")
        logger.info(f"[METADATA DEBUG 2] existing_memory.payload type: {type(existing_memory.payload)}")
        logger.info(f"[METADATA DEBUG 3] existing_memory.payload keys: {list(existing_memory.payload.keys())}")
        logger.info(f"[METADATA DEBUG 4] existing_memory.payload content: {existing_memory.payload}")

        # Check if there are any other attributes that might contain metadata
        logger.info(f"[METADATA DEBUG 5] existing_memory attributes: {dir(existing_memory)}")

        # Start with ALL existing payload fields (this preserves custom metadata)
        new_metadata = deepcopy(existing_memory.payload)
        logger.info(f"[METADATA DEBUG 6] new_metadata after deepcopy: {new_metadata}")

        # Override with new metadata if provided
        if metadata is not None:
            logger.info(f"[METADATA DEBUG 7] Overriding with metadata: {metadata}")
            new_metadata.update(deepcopy(metadata))
            logger.info(f"[METADATA DEBUG 8] new_metadata after override: {new_metadata}")

        # Update standard fields
        new_metadata["data"] = data
        new_metadata["hash"] = hashlib.md5(data.encode()).hexdigest()
        new_metadata["created_at"] = existing_memory.payload.get("created_at")
        new_metadata["updated_at"] = datetime.now(pytz.timezone("US/Pacific")).isoformat()

        logger.info(f"[METADATA DEBUG 9] new_metadata before vector store update: {new_metadata}")
        logger.info(
            f"[METADATA DEBUG 10] Underscore fields present: {[k for k in new_metadata.keys() if k.startswith('_')]}"
        )

        # Get embeddings
        if data in existing_embeddings:
            embeddings = existing_embeddings[data]
        else:
            embeddings = await asyncio.to_thread(self.embedding_model.embed, data, "update")

        # Update vector store with preserved metadata
        await asyncio.to_thread(
            self.vector_store.update,
            vector_id=memory_id,
            vector=embeddings,
            payload=new_metadata,
        )
        logger.info("[METADATA DEBUG 11] Vector store update completed")
        logger.info(f"Updating memory with ID {memory_id=} with {data=}")

        # Add history record
        await asyncio.to_thread(
            self.db.add_history,
            memory_id,
            prev_value,
            data,
            "UPDATE",
            is_deleted=0,
        )
