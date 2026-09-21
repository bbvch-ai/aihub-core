import logging

from redis.asyncio import Redis

from swiss_ai_hub.core.dispatcher.stores.store_base import StoreBase

logger = logging.getLogger(__name__)


class TraceStore(StoreBase):
    """
    Run-scoped store for tracing metadata used by OpenTelemetry/Langfuse integration.

    Stores W3C trace context carriers, user input/output, and AITL parent context
    so that distributed step spans can be re-parented under the correct trace even
    across HITL/BITL interruptions and agent-in-the-loop delegation.
    """

    def __init__(self, redis: Redis):
        super().__init__(redis, prefix="traces")

    async def store_run_context_carrier(self, execution_context_id: str, carrier: dict[str, str]) -> bool:
        """Stores the W3C trace context carrier captured at run start."""
        return await self.put_json_value(execution_context_id, "run_context", carrier)

    async def get_run_context_carrier(self, execution_context_id: str) -> dict[str, str] | None:
        return await self.get_json_value(execution_context_id, "run_context")

    async def store_user_input(self, execution_context_id: str, user_input: str) -> bool:
        return await self.put_json_value(execution_context_id, "input", user_input)

    async def get_user_input(self, execution_context_id: str) -> str:
        return await self.get_json_value(execution_context_id, "input", "")

    async def store_user_id(self, execution_context_id: str, user_id: str) -> bool:
        return await self.put_json_value(execution_context_id, "user_id", user_id)

    async def get_user_id(self, execution_context_id: str) -> str:
        return await self.get_json_value(execution_context_id, "user_id", "")

    async def store_tenant_id(self, execution_context_id: str, tenant_id: str) -> bool:
        return await self.put_json_value(execution_context_id, "tenant_id", tenant_id)

    async def get_tenant_id(self, execution_context_id: str) -> str:
        return await self.get_json_value(execution_context_id, "tenant_id", "")

    async def store_output(self, execution_context_id: str, output: str) -> bool:
        return await self.put_json_value(execution_context_id, "output", output)

    async def get_output(self, execution_context_id: str) -> str:
        return await self.get_json_value(execution_context_id, "output", "")

    async def store_aitl_parent_context(
        self, execution_context_id: str, carrier: dict[str, str], target_agent_class: str
    ) -> bool:
        """Stores AITL wrapper span context and target agent class for re-parenting."""
        success = await self.put_json_value(execution_context_id, "aitl_parent_context", carrier)
        return success and await self.put_json_value(
            execution_context_id, "aitl_target_agent_class", target_agent_class
        )

    async def get_aitl_parent_context(self, execution_context_id: str) -> dict[str, str] | None:
        return await self.get_json_value(execution_context_id, "aitl_parent_context")

    async def get_aitl_target_agent_class(self, execution_context_id: str) -> str | None:
        return await self.get_json_value(execution_context_id, "aitl_target_agent_class")
