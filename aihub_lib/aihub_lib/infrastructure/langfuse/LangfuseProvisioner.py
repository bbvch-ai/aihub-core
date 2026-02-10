"""
Langfuse Provisioner.

Pre-configures Langfuse with AI-Hub LLM connections, model pricing definitions,
and a default prompt template on API startup so users can run agent experiments
from the Langfuse UI without writing Python code. Also syncs discovered agents
periodically so they appear in the experiment model dropdown.
"""

import logging
import re
from collections.abc import Coroutine
from typing import Any

import httpx

from aihub_lib.infrastructure.langfuse.LangfuseBootstrapSettings import LangfuseBootstrapSettings
from aihub_lib.infrastructure.langfuse.LangfuseSettings import LangfuseSettings
from aihub_lib.infrastructure.litellm.LiteLLMProxySettings import LiteLLMProxySettings

logger = logging.getLogger(__name__)


class LangfuseProvisioner:
    """Provisions Langfuse with AI-Hub LLM connections, model pricing, and a prompt template."""

    def __init__(
        self,
        langfuse_settings: LangfuseSettings | None = None,
        bootstrap_settings: LangfuseBootstrapSettings | None = None,
    ) -> None:
        self.langfuse_settings = langfuse_settings or LangfuseSettings()
        self.bootstrap_settings = bootstrap_settings or LangfuseBootstrapSettings()
        self._base_url = self.langfuse_settings.BASEURL.rstrip("/")

    @property
    def _auth(self) -> tuple[str, str]:
        return (
            self.langfuse_settings.PUBLIC_KEY,
            self.langfuse_settings.SECRET_KEY.get_secret_value(),
        )

    async def provision(self) -> None:
        """Run full provisioning sequence on API startup.

        Each step is independent — a failure in one step does not prevent subsequent steps.
        This method never raises; all errors are logged as warnings.
        """
        if not self.bootstrap_settings.ENABLED:
            logger.info("Langfuse provisioning disabled via LANGFUSE_BOOTSTRAP_ENABLED=false")
            return

        logger.info("Starting Langfuse provisioning...")

        async with httpx.AsyncClient(timeout=30.0) as client:
            litellm_models = await self._run_step("LiteLLM model discovery", self._fetch_litellm_models(client)) or []
            await self._run_step("AI-Hub connection", self._register_aihub_connection(client))
            await self._run_step("LiteLLM connection", self._register_litellm_connection(client, litellm_models))
            await self._run_step("model definitions", self._register_model_definitions(client, litellm_models))
            await self._run_step("default prompt", self._create_default_prompt(client))

        logger.info("Langfuse provisioning completed")

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

    # ------------------------------------------------------------------
    # Provisioning steps
    # ------------------------------------------------------------------

    @staticmethod
    async def _run_step(name: str, coro: Coroutine[Any, Any, Any]) -> Any:
        """Run a provisioning step, logging and swallowing errors so subsequent steps still execute."""
        try:
            return await coro
        except Exception as e:
            logger.warning(f"Langfuse provisioning: '{name}' failed — {e}")
            return None

    async def _register_aihub_connection(self, client: httpx.AsyncClient) -> None:
        """Register AI-Hub's OpenAI-compatible endpoint as an LLM connection."""
        connection_data = self._build_aihub_connection_data(custom_models=[])
        await self._upsert_llm_connection(client, connection_data, self.bootstrap_settings.AIHUB_CONNECTION_NAME)

    async def _register_litellm_connection(
        self, client: httpx.AsyncClient, litellm_models: list[dict[str, Any]]
    ) -> None:
        """Register LiteLLM proxy as an LLM connection for evaluators."""
        settings = self.bootstrap_settings

        if not settings.LITELLM_API_KEY:
            logger.info("Langfuse provisioning: Skipping LiteLLM connection (no LANGFUSE_BOOTSTRAP_LITELLM_API_KEY)")
            return

        chat_models = [
            entry["model_name"]
            for entry in litellm_models
            if "model_name" in entry and entry.get("model_info", {}).get("mode") == "chat"
        ]

        connection_data = {
            "provider": "ai-hub-litellm",
            "adapter": "openai",
            "secretKey": settings.LITELLM_API_KEY.get_secret_value(),
            "baseURL": settings.LITELLM_BASE_URL,
            "customModels": chat_models,
            "withDefaultModels": False,
            "extraHeaders": {},
        }

        await self._upsert_llm_connection(client, connection_data, settings.LITELLM_CONNECTION_NAME)
        logger.info(f"Langfuse provisioning: Discovered {len(chat_models)} chat models from LiteLLM: {chat_models}")

    async def _register_model_definitions(
        self, client: httpx.AsyncClient, litellm_models: list[dict[str, Any]]
    ) -> None:
        """Register model definitions with pricing in Langfuse for automatic cost calculation.

        Langfuse cannot auto-calculate costs for custom model names (e.g. 'text-generation/nano')
        because they don't match its built-in pricing database. By registering model definitions
        with per-token prices from LiteLLM, Langfuse uses existing usage_details on spans to
        calculate costs automatically.
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
        """Create the default prompt template for running experiments against AI-Hub agents.

        The prompt maps the dataset's ``question`` field to a user message, which is
        how AI-Hub agents expect input via the OpenAI-compatible endpoint.
        Select this prompt when configuring an experiment run in the Langfuse UI.
        """
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
        """Fetch all model entries from LiteLLM's model info endpoint.

        Returns raw model dicts so callers can extract what they need
        (chat model names, pricing, etc.) without a second HTTP call.
        """
        try:
            litellm_settings = LiteLLMProxySettings()
        except Exception:
            logger.info("Langfuse provisioning: LiteLLM proxy not configured, skipping model discovery")
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
        """Create or update an LLM connection in Langfuse. Raises on non-2xx responses."""
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
            response.raise_for_status()
            return False  # unreachable, but keeps the return type explicit

    async def _create_prompt(
        self,
        client: httpx.AsyncClient,
        name: str,
        messages: list[dict[str, str]],
        labels: list[str],
        tags: list[str],
    ) -> None:
        """Create a chat prompt template in Langfuse. Skips if it already exists (409)."""
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
