"""
Langfuse Bootstrap Service.

Pre-configures Langfuse with AI-Hub LLM connections and default prompts
on API startup so users can run agent experiments from the Langfuse UI
without writing Python code.
"""

import logging
import re
from typing import Any

import httpx

from aihub_lib.infrastructure.langfuse.LangfuseBootstrapSettings import LangfuseBootstrapSettings
from aihub_lib.infrastructure.langfuse.LangfuseSettings import LangfuseSettings
from aihub_lib.infrastructure.litellm.LiteLLMProxySettings import LiteLLMProxySettings

logger = logging.getLogger(__name__)


class LangfuseBootstrap:
    """Pre-configures Langfuse with AI-Hub LLM connections and default prompts on startup."""

    def __init__(
        self,
        langfuse_settings: LangfuseSettings | None = None,
        bootstrap_settings: LangfuseBootstrapSettings | None = None,
    ) -> None:
        self.langfuse_settings = langfuse_settings or LangfuseSettings()
        self.bootstrap_settings = bootstrap_settings or LangfuseBootstrapSettings()

        self._base_url = self.langfuse_settings.BASEURL.rstrip("/")
        self._auth = (
            self.langfuse_settings.PUBLIC_KEY,
            self.langfuse_settings.SECRET_KEY.get_secret_value(),
        )

    async def bootstrap(self) -> None:
        """Run full bootstrap sequence on API startup."""
        if not self.bootstrap_settings.ENABLED:
            logger.info("Langfuse bootstrap disabled via LANGFUSE_BOOTSTRAP_ENABLED=false")
            return

        logger.info("Starting Langfuse bootstrap...")

        async with httpx.AsyncClient(timeout=30.0) as client:
            await self._register_aihub_connection(client)
            await self._register_litellm_connection(client)
            await self._register_model_definitions(client)
            await self._create_default_prompts(client)

        logger.info("Langfuse bootstrap completed")

    async def sync_agents(self, agent_models: list[str]) -> None:
        """Sync discovered agents to Langfuse so they appear in the experiment UI model dropdown."""
        if not self.bootstrap_settings.ENABLED:
            return

        if not agent_models:
            logger.debug("Langfuse sync: No agents to sync")
            return

        connection_data = self._build_aihub_connection_data(custom_models=agent_models)

        async with httpx.AsyncClient(timeout=30.0) as client:
            await self._upsert_llm_connection(client, connection_data, self.bootstrap_settings.AIHUB_CONNECTION_NAME)

        logger.info(f"Langfuse sync: Updated AI-Hub connection with {len(agent_models)} agents")

    async def _register_aihub_connection(self, client: httpx.AsyncClient) -> None:
        """Register AI-Hub's OpenAI-compatible endpoint as an LLM connection."""
        connection_data = self._build_aihub_connection_data(custom_models=[])
        await self._upsert_llm_connection(client, connection_data, self.bootstrap_settings.AIHUB_CONNECTION_NAME)

    async def _register_litellm_connection(self, client: httpx.AsyncClient) -> None:
        """Register LiteLLM proxy as an LLM connection for evaluators.

        Discovers available chat models by querying LiteLLM's /v1/model/info endpoint
        instead of relying on a static configuration list.
        """
        settings = self.bootstrap_settings

        if not settings.LITELLM_API_KEY:
            logger.info("Langfuse bootstrap: Skipping LiteLLM connection (no LANGFUSE_BOOTSTRAP_LITELLM_API_KEY)")
            return

        evaluator_models = await self._fetch_litellm_chat_models(client)

        connection_data = {
            "provider": "ai-hub-litellm",
            "adapter": "openai",
            "secretKey": settings.LITELLM_API_KEY.get_secret_value(),
            "baseURL": settings.LITELLM_BASE_URL,
            "customModels": evaluator_models,
            "withDefaultModels": False,
            "extraHeaders": {},
        }

        await self._upsert_llm_connection(client, connection_data, settings.LITELLM_CONNECTION_NAME)

    async def _register_model_definitions(self, client: httpx.AsyncClient) -> None:
        """Register model definitions with pricing in Langfuse for automatic cost calculation.

        Langfuse cannot auto-calculate costs for custom model names (e.g. 'text-generation/nano')
        because they don't match its built-in pricing database. By registering model definitions
        with per-token prices from LiteLLM, Langfuse uses existing usage_details on spans to
        calculate costs automatically.
        """
        try:
            litellm_settings = LiteLLMProxySettings()
        except Exception:
            logger.warning("Langfuse bootstrap: LiteLLM proxy not configured, skipping model definitions")
            return

        url = f"{litellm_settings.BASE_URL}/v1/model/info"
        api_key = litellm_settings.API_KEY.get_secret_value() if litellm_settings.API_KEY else ""
        headers = {"Authorization": f"Bearer {api_key}"}

        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
        except httpx.HTTPError:
            logger.warning("Langfuse bootstrap: Failed to fetch models from LiteLLM, skipping model definitions")
            return

        data = response.json().get("data", [])
        registered = 0

        for entry in data:
            model_name = entry.get("model_name")
            model_info = entry.get("model_info", {})
            input_cost = model_info.get("input_cost_per_token")
            output_cost = model_info.get("output_cost_per_token")

            if not model_name or input_cost is None or output_cost is None:
                continue

            if await self._create_model_definition(client, model_name, input_cost, output_cost):
                registered += 1

        logger.info(f"Langfuse bootstrap: Registered {registered} model definitions with pricing")

    async def _create_model_definition(
        self,
        client: httpx.AsyncClient,
        model_name: str,
        input_cost_per_token: float,
        output_cost_per_token: float,
    ) -> bool:
        """Create a single model definition with per-token pricing in Langfuse."""
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
            logger.warning(
                f"Langfuse bootstrap: Status {response.status_code} "
                f"when creating model definition '{model_name}': {response.text}"
            )
            return False

    async def _fetch_litellm_chat_models(self, client: httpx.AsyncClient) -> list[str]:
        """Fetch available chat models from LiteLLM's model info endpoint."""
        try:
            litellm_settings = LiteLLMProxySettings()
        except Exception:
            logger.warning("Langfuse bootstrap: LiteLLM proxy not configured, skipping model discovery")
            return []

        url = f"{litellm_settings.BASE_URL}/v1/model/info"
        api_key = litellm_settings.API_KEY.get_secret_value() if litellm_settings.API_KEY else ""
        headers = {"Authorization": f"Bearer {api_key}"}

        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
        except httpx.HTTPError:
            logger.warning("Langfuse bootstrap: Failed to fetch models from LiteLLM, using empty model list")
            return []

        data = response.json().get("data", [])
        models = [
            entry["model_name"]
            for entry in data
            if "model_name" in entry and entry.get("model_info", {}).get("mode") == "chat"
        ]

        logger.info(f"Langfuse bootstrap: Discovered {len(models)} chat models from LiteLLM: {models}")
        return models

    def _build_aihub_connection_data(self, *, custom_models: list[str]) -> dict[str, Any]:
        """Build the connection payload for the AI-Hub agents LLM connection."""
        settings = self.bootstrap_settings
        api_key = (
            settings.AIHUB_API_KEY.get_secret_value() if settings.AIHUB_API_KEY else "internal-network-no-auth-required"
        )

        return {
            "provider": "ai-hub-agents",
            "adapter": "openai",
            "secretKey": api_key,
            "baseURL": settings.AIHUB_BASE_URL,
            "customModels": custom_models,
            "withDefaultModels": False,
            "extraHeaders": {},
        }

    async def _upsert_llm_connection(self, client: httpx.AsyncClient, data: dict[str, Any], display_name: str) -> None:
        """Create or update an LLM connection in Langfuse."""
        url = f"{self._base_url}/api/public/llm-connections"
        response = await client.put(url, json=data, auth=self._auth)

        if response.status_code in (200, 201):
            logger.info(f"Langfuse LLM connection upserted: {display_name}")
        else:
            logger.warning(
                f"Langfuse bootstrap: Status {response.status_code} "
                f"when upserting connection '{display_name}': {response.text}"
            )

    async def _create_default_prompts(self, client: httpx.AsyncClient) -> None:
        """Create default prompt templates that define how dataset inputs are sent to agents."""
        await self._create_prompt(
            client,
            name="ai-hub-agent-question",
            messages=[{"role": "user", "content": "{{question}}"}],
            labels=["production"],
            tags=["ai-hub", "agent", "experiment"],
        )

        await self._create_prompt(
            client,
            name="ai-hub-agent-with-context",
            messages=[
                {"role": "system", "content": "{{system_prompt}}"},
                {"role": "user", "content": "{{question}}"},
            ],
            labels=["production"],
            tags=["ai-hub", "agent", "experiment", "with-context"],
        )

    async def _create_prompt(
        self,
        client: httpx.AsyncClient,
        name: str,
        messages: list[dict[str, str]],
        labels: list[str],
        tags: list[str],
    ) -> None:
        """Create a chat prompt template in Langfuse."""
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
            logger.warning(
                f"Langfuse bootstrap: Status {response.status_code} when creating prompt '{name}': {response.text}"
            )
