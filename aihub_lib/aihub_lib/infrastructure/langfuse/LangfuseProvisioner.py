"""Provisions Langfuse with LLM connections, model pricing, and a default prompt on API startup."""

import logging
import re
from collections.abc import Coroutine
from typing import Any

import httpx

from aihub_lib.auth.dependencies.SuperuserAuthHandler.SuperuserSettings import SuperuserSettings
from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.infrastructure.langfuse.LangfuseSettings import LangfuseSettings
from aihub_lib.infrastructure.litellm.LiteLLMProxySettings import LiteLLMProxySettings

logger = logging.getLogger(__name__)

AIHUB_CONNECTION_NAME = "AI-Hub Agents"
LITELLM_CONNECTION_NAME = "AI-Hub LLM (Evaluators)"


class LangfuseProvisioner:
    def __init__(self, langfuse_settings: LangfuseSettings | None = None) -> None:
        self.langfuse_settings = langfuse_settings or LangfuseSettings()
        self._base_url = self.langfuse_settings.BASEURL.rstrip("/")

    @property
    def _auth(self) -> tuple[str, str]:
        return (
            self.langfuse_settings.PUBLIC_KEY,
            self.langfuse_settings.SECRET_KEY.get_secret_value(),
        )

    async def provision(self) -> None:
        """Each step is independent — a failure in one does not prevent subsequent steps."""
        logger.info("Starting Langfuse provisioning...")

        async with httpx.AsyncClient(timeout=30.0) as client:
            litellm_models = await self._run_step("LiteLLM model discovery", self._fetch_litellm_models(client)) or []
            await self._run_step("AI-Hub connection", self._register_aihub_connection(client))
            await self._run_step("LiteLLM connection", self._register_litellm_connection(client, litellm_models))
            await self._run_step("model definitions", self._register_model_definitions(client, litellm_models))
            await self._run_step("default prompt", self._create_default_prompt(client))

        logger.info("Langfuse provisioning completed")

    async def sync_agents(self, agent_models: list[str]) -> None:
        """Update the AI-Hub LLM connection with current agent models for the experiment UI."""
        if not agent_models:
            return

        connection_data = self._build_aihub_connection_data(custom_models=agent_models)

        async with httpx.AsyncClient(timeout=30.0) as client:
            await self._upsert_llm_connection(client, connection_data, AIHUB_CONNECTION_NAME)

        logger.info(f"Langfuse sync: Updated AI-Hub connection with {len(agent_models)} agents")

    # ------------------------------------------------------------------
    # Provisioning steps
    # ------------------------------------------------------------------

    @staticmethod
    async def _run_step(name: str, coro: Coroutine[Any, Any, Any]) -> Any:
        try:
            return await coro
        except Exception as e:
            logger.warning(f"Langfuse provisioning: '{name}' failed — {e}")
            return None

    async def _register_aihub_connection(self, client: httpx.AsyncClient) -> None:
        connection_data = self._build_aihub_connection_data(custom_models=[])
        await self._upsert_llm_connection(client, connection_data, AIHUB_CONNECTION_NAME)

    async def _register_litellm_connection(
        self, client: httpx.AsyncClient, litellm_models: list[dict[str, Any]]
    ) -> None:
        try:
            litellm_settings = LiteLLMProxySettings()
        except Exception:
            logger.info("Langfuse provisioning: Skipping LiteLLM connection (not configured)")
            return

        if not litellm_settings.API_KEY:
            logger.info("Langfuse provisioning: Skipping LiteLLM connection (no API key)")
            return

        chat_models = [
            entry["model_name"]
            for entry in litellm_models
            if "model_name" in entry and entry.get("model_info", {}).get("mode") == "chat"
        ]

        connection_data = {
            "provider": "ai-hub-litellm",
            "adapter": "openai",
            "secretKey": litellm_settings.API_KEY.get_secret_value(),
            "baseURL": litellm_settings.BASE_URL,
            "customModels": chat_models,
            "withDefaultModels": False,
            "extraHeaders": {},
        }

        await self._upsert_llm_connection(client, connection_data, LITELLM_CONNECTION_NAME)
        logger.info(f"Langfuse provisioning: Discovered {len(chat_models)} chat models from LiteLLM: {chat_models}")

    async def _register_model_definitions(
        self, client: httpx.AsyncClient, litellm_models: list[dict[str, Any]]
    ) -> None:
        """Langfuse can't auto-calculate costs for custom model names (e.g. 'text-generation/nano')
        since they don't match its built-in pricing database. We register per-token prices from LiteLLM.
        """
        registered = 0

        for entry in litellm_models:
            model_name = entry.get("model_name")
            model_info = entry.get("model_info", {})
            input_cost = model_info.get("input_cost_per_token")
            output_cost = model_info.get("output_cost_per_token")

            if not model_name or input_cost is None or output_cost is None:
                continue

            if await self._create_model_definition(client, model_name, input_cost, output_cost):
                registered += 1

        logger.info(f"Langfuse provisioning: Registered {registered} model definitions with pricing")

    async def _create_default_prompt(self, client: httpx.AsyncClient) -> None:
        """Maps dataset ``question`` field to a user message for the OpenAI-compatible agent endpoint."""
        await self._create_prompt(
            client,
            name="ai-hub-agent",
            messages=[{"role": "user", "content": "{{question}}"}],
            labels=["production"],
            tags=["ai-hub", "agent", "experiment"],
        )

    # ------------------------------------------------------------------
    # LiteLLM model discovery
    # ------------------------------------------------------------------

    @staticmethod
    async def _fetch_litellm_models(client: httpx.AsyncClient) -> list[dict[str, Any]]:
        try:
            litellm_settings = LiteLLMProxySettings()
        except Exception:
            logger.info("Langfuse provisioning: LiteLLM not configured, skipping model discovery")
            return []

        url = f"{litellm_settings.BASE_URL}/v1/model/info"
        api_key = litellm_settings.API_KEY.get_secret_value() if litellm_settings.API_KEY else ""
        headers = {"Authorization": f"Bearer {api_key}"}

        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
        except httpx.HTTPError:
            logger.warning("Langfuse provisioning: Failed to fetch models from LiteLLM")
            return []

        return response.json().get("data", [])

    # ------------------------------------------------------------------
    # Langfuse API helpers
    # ------------------------------------------------------------------

    def _build_aihub_connection_data(self, *, custom_models: list[str]) -> dict[str, Any]:
        return {
            "provider": "ai-hub-agents",
            "adapter": "openai",
            "secretKey": SuperuserSettings().TOKEN.get_secret_value(),
            "baseURL": AIHubSettings().OPENAI_API_BASE_URL,
            "customModels": custom_models,
            "withDefaultModels": False,
            "extraHeaders": {},
        }

    async def _upsert_llm_connection(self, client: httpx.AsyncClient, data: dict[str, Any], display_name: str) -> None:
        url = f"{self._base_url}/api/public/llm-connections"
        response = await client.put(url, json=data, auth=self._auth)

        if response.status_code in (200, 201):
            logger.info(f"Langfuse LLM connection upserted: {display_name}")
        else:
            response.raise_for_status()

    async def _create_model_definition(
        self,
        client: httpx.AsyncClient,
        model_name: str,
        input_cost_per_token: float,
        output_cost_per_token: float,
    ) -> bool:
        url = f"{self._base_url}/api/public/models"
        match_pattern = f"(?i)^({re.escape(model_name)})$"

        model_data = {
            "modelName": model_name,
            "matchPattern": match_pattern,
            "unit": "TOKENS",
            "inputPrice": input_cost_per_token,
            "outputPrice": output_cost_per_token,
        }

        response = await client.post(url, json=model_data, auth=self._auth)

        if response.status_code in (200, 201):
            logger.info(f"Langfuse model definition created: {model_name}")
            return True
        elif response.status_code == 409:
            logger.debug(f"Langfuse model definition already exists: {model_name}")
            return False
        else:
            response.raise_for_status()
            return False

    async def _create_prompt(
        self,
        client: httpx.AsyncClient,
        name: str,
        messages: list[dict[str, str]],
        labels: list[str],
        tags: list[str],
    ) -> None:
        url = f"{self._base_url}/api/public/v2/prompts"

        prompt_data = {
            "name": name,
            "type": "chat",
            "prompt": messages,
            "labels": labels,
            "tags": tags,
        }

        response = await client.post(url, json=prompt_data, auth=self._auth)

        if response.status_code in (200, 201):
            logger.info(f"Langfuse prompt created: {name}")
        elif response.status_code == 409:
            logger.debug(f"Langfuse prompt already exists: {name}")
        else:
            response.raise_for_status()
