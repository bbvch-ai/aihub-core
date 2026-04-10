import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from redis.asyncio import Redis

from swiss_ai_hub.core.infrastructure.openwebui.online_agent import OnlineAgent
from swiss_ai_hub.core.infrastructure.openwebui.openwebui_client import OpenWebuiClient
from swiss_ai_hub.core.infrastructure.openwebui.openwebui_settings import OpenWebuiSettings

logger = logging.getLogger(__name__)

AIHUB_MODEL_PREFIX = "aihub-agent-"

_LOCK_TIMEOUT = 60


@asynccontextmanager
async def _sync_lock(redis: Redis, key: str) -> AsyncIterator[bool]:
    lock = redis.lock(key, timeout=_LOCK_TIMEOUT)
    if not await lock.acquire(blocking=False):
        logger.debug("OpenWebUI %s skipped: another instance is syncing", key.rsplit(":", 1)[-1])
        yield False
        return
    try:
        yield True
    finally:
        await lock.release()


class OpenWebuiProvisioner:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis
        self._settings = OpenWebuiSettings()
        self._openwebui = OpenWebuiClient(
            base_url=self._settings.BASE_URL,
            secret_key=self._settings.SECRET_KEY.get_secret_value(),
            service_account_id=self._settings.SERVICE_ACCOUNT_ID,
        )

    async def sync_agents(self, online_agents: list[OnlineAgent]) -> None:
        async with _sync_lock(self._redis, "openwebui:sync:agents") as acquired:
            if not acquired:
                return
            async with httpx.AsyncClient(timeout=30.0) as http:
                created, deleted = await self._sync_workspace_models(http, online_agents)

            logger.info("OpenWebUI sync: created %d, deleted %d workspace models", created, deleted)

    # ------------------------------------------------------------------
    # Workspace model sync
    # ------------------------------------------------------------------

    @staticmethod
    def _workspace_model_id(agent_class: str, agent_id: str) -> str:
        return f"{AIHUB_MODEL_PREFIX}{agent_class}-{agent_id}"

    @staticmethod
    def _base_model_id(agent_class: str, agent_id: str) -> str:
        return f"aihub-pipeline.{agent_class}.{agent_id}"

    @staticmethod
    def _compute_model_diff(
        online_agents: list[OnlineAgent], existing_model_ids: set[str]
    ) -> tuple[list[OnlineAgent], set[str]]:
        """Returns (models_to_create, model_ids_to_delete)."""
        desired_ids = {
            OpenWebuiProvisioner._workspace_model_id(agent.agent_class, agent.agent_id) for agent in online_agents
        }
        to_create = [
            agent
            for agent in online_agents
            if OpenWebuiProvisioner._workspace_model_id(agent.agent_class, agent.agent_id) not in existing_model_ids
        ]
        to_delete = existing_model_ids - desired_ids
        return to_create, to_delete

    async def _sync_workspace_models(
        self, http: httpx.AsyncClient, online_agents: list[OnlineAgent]
    ) -> tuple[int, int]:
        existing_models = await self._openwebui.list_models(http)
        existing_aihub = {m["id"] for m in existing_models if m.get("id", "").startswith(AIHUB_MODEL_PREFIX)}

        to_create, to_delete = self._compute_model_diff(online_agents, existing_aihub)

        for agent in to_create:
            model_data = {
                "id": self._workspace_model_id(agent.agent_class, agent.agent_id),
                "name": agent.display_name,
                "base_model_id": self._base_model_id(agent.agent_class, agent.agent_id),
                "meta": {"description": f"AI-Hub agent: {agent.agent_class}/{agent.agent_id}"},
            }
            await self._openwebui.create_model(http, model_data)
            logger.info("OpenWebUI: Created workspace model '%s'", model_data["id"])

        for model_id in to_delete:
            await self._openwebui.delete_model(http, model_id)
            logger.info("OpenWebUI: Deleted workspace model '%s'", model_id)

        return len(to_create), len(to_delete)
