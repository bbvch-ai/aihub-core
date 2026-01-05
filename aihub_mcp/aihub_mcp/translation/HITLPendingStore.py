import logging
import time
from typing import Any

from aihub_lib.nats.dispatcher.stores.StoreBase import StoreBase
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

DEFAULT_HITL_TTL_SECONDS = 60 * 10  # 10 minutes


class HITLPendingStore(StoreBase):
    """
    Valkey-backed store for pending Human-in-the-Loop requests.

    When MCP elicitation is not supported by the client, this store holds the execution
    context so that the submit_hitl_response tool can resume agent execution.

    Key format: pending_hitl:{request_id}:context

    Context includes:
    - Agent routing info (agent_class, thread_id, display_id, run_id)
    - Original HITL request event
    - Accumulated content from before the HITL request
    - Timestamp for debugging
    """

    def __init__(self, redis: Redis, ttl_seconds: int = DEFAULT_HITL_TTL_SECONDS) -> None:
        super().__init__(redis, prefix="pending_hitl", default_ttl=ttl_seconds)

    async def store_pending(
        self,
        request_id: str,
        agent_class: str,
        thread_id: str,
        display_id: str,
        run_id: str,
        request_event: dict[str, Any],
        hitl_type: str,
        accumulated_content: list[str],
    ) -> bool:
        """Store pending HITL context for later retrieval by submit_hitl_response."""
        context = {
            "request_id": request_id,
            "agent_class": agent_class,
            "thread_id": thread_id,
            "display_id": display_id,
            "run_id": run_id,
            "request_event": request_event,
            "hitl_type": hitl_type,
            "accumulated_content": accumulated_content,
            "created_at": time.time(),
        }

        success = await self.put_json_value(request_id, "context", context)
        if success:
            logger.info(f"Stored pending HITL request: {request_id}")
        else:
            logger.error(f"Failed to store pending HITL request: {request_id}")
        return success

    async def get_pending(self, request_id: str) -> dict[str, Any] | None:
        """Retrieve pending HITL context by request_id, or None if not found or expired."""
        context = await self.get_json_value(request_id, "context")
        if context:
            logger.debug(f"Retrieved pending HITL request: {request_id}")
        else:
            logger.debug(f"Pending HITL request not found or expired: {request_id}")
        return context

    async def remove_pending(self, request_id: str) -> None:
        """Remove pending request after it has been processed."""
        await self.delete_all(request_id)
        logger.info(f"Removed pending HITL request: {request_id}")
