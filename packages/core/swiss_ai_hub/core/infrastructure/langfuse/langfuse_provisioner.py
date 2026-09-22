"""Provisions Langfuse with LLM connections, model pricing, and a default prompt on API startup."""

import ipaddress
import logging
import re
from collections.abc import Coroutine
from typing import Any
from urllib.parse import urlparse

import httpx

from swiss_ai_hub.core.auth.superuser_settings import SuperuserSettings
from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.langfuse.langfuse_settings import LangfuseSettings
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_proxy_settings import LiteLLMProxySettings

logger = logging.getLogger(__name__)

AIHUB_CONNECTION_NAME = "AI-Hub Agents"
LITELLM_CONNECTION_NAME = "AI-Hub LLM (Evaluators)"

OCR_MODEL_NAME_PREFIXES: tuple[str, ...] = ("mineru", "olmocr", "lightonocr")

LOOPBACK_HOSTNAMES: frozenset[str] = frozenset({"localhost", "0.0.0.0", "::", "[::]"})

ALLOWLIST_SETTING = "LANGFUSE_LLM_CONNECTION_WHITELISTED_HOST"
LANGFUSE_SERVICES = "langfuse-web and langfuse-worker"


class LangfuseProvisioner:
    def __init__(self, langfuse_settings: LangfuseSettings | None = None) -> None:
        self.langfuse_settings = langfuse_settings or LangfuseSettings()
        self._base_url = self.langfuse_settings.BASE_URL.rstrip("/")

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
            logger.error(f"Langfuse provisioning: '{name}' failed — {e}")
            return None

    async def _register_aihub_connection(self, client: httpx.AsyncClient) -> None:
        connection_data = self._build_aihub_connection_data(custom_models=[])
        await self._upsert_llm_connection(client, connection_data, AIHUB_CONNECTION_NAME)

    async def _register_litellm_connection(
        self, client: httpx.AsyncClient, litellm_models: list[dict[str, Any]]
    ) -> None:
        litellm_settings = LiteLLMProxySettings()

        if not litellm_settings.API_KEY:
            raise ValueError("LITE_LLM_PROXY_API_KEY is required to register the Langfuse evaluator connection")

        base_url = litellm_settings.internal_base_url
        self._assert_dialable_from_langfuse(base_url, "LITE_LLM_PROXY_INTERNAL_BASE_URL")

        chat_models = self._judge_models(litellm_models)

        connection_data = {
            "provider": "ai-hub-litellm",
            "adapter": "openai",
            "secretKey": litellm_settings.API_KEY.get_secret_value(),
            "baseURL": base_url,
            "customModels": chat_models,
            "withDefaultModels": False,
            "extraHeaders": {},
        }

        await self._upsert_llm_connection(client, connection_data, LITELLM_CONNECTION_NAME)
        logger.info(f"Langfuse provisioning: Registered {len(chat_models)} judge models from LiteLLM: {chat_models}")

    @staticmethod
    def _assert_dialable_from_langfuse(url: str, setting_name: str) -> None:
        """Langfuse dials this URL from its own container, so a loopback address can only ever reach Langfuse itself."""
        hostname = urlparse(url).hostname or ""

        is_loopback = hostname.lower() in LOOPBACK_HOSTNAMES
        if not is_loopback:
            try:
                is_loopback = ipaddress.ip_address(hostname).is_loopback
            except ValueError:
                is_loopback = False

        if is_loopback:
            raise ValueError(
                f"{setting_name} is '{url}', which resolves to the loopback interface. Langfuse dials this "
                f"connection from its own container, where loopback is Langfuse itself, so every call would fail. "
                f"Set it to an address {LANGFUSE_SERVICES} can reach."
            )

    @staticmethod
    def _judge_models(litellm_models: list[dict[str, Any]]) -> list[str]:
        """OCR/VLM models are served as ``mode: chat`` but cannot grade text, so they must not reach the judge list."""
        return [
            entry["model_name"]
            for entry in litellm_models
            if "model_name" in entry
            and entry.get("model_info", {}).get("mode") == "chat"
            and not entry["model_name"].rsplit("/", maxsplit=1)[-1].lower().startswith(OCR_MODEL_NAME_PREFIXES)
        ]

    async def _register_model_definitions(
        self, client: httpx.AsyncClient, litellm_models: list[dict[str, Any]]
    ) -> None:
        """Langfuse can't auto-calculate costs for custom model names.

        We register per-token prices from LiteLLM since custom names don't match the built-in pricing database.
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
        """Discovery stays on the in-cluster URL; only the connection Langfuse dials needs the public one."""
        litellm_settings = LiteLLMProxySettings()

        url = f"{litellm_settings.BASE_URL}/v1/model/info"
        api_key = litellm_settings.API_KEY.get_secret_value() if litellm_settings.API_KEY else ""
        headers = {"Authorization": f"Bearer {api_key}"}

        response = await client.get(url, headers=headers)
        response.raise_for_status()

        return response.json().get("data", [])

    # ------------------------------------------------------------------
    # Langfuse API helpers
    # ------------------------------------------------------------------

    def _build_aihub_connection_data(self, *, custom_models: list[str]) -> dict[str, Any]:
        base_url = AIHubSettings().OPENAI_API_BASE_URL
        self._assert_dialable_from_langfuse(base_url, "AIHUB_OPENAI_API_BASE_URL")

        return {
            "provider": "ai-hub-agents",
            "adapter": "openai",
            "secretKey": SuperuserSettings().TOKEN.get_secret_value(),
            "baseURL": base_url,
            "customModels": custom_models,
            "withDefaultModels": False,
            "extraHeaders": {},
        }

    async def _upsert_llm_connection(self, client: httpx.AsyncClient, data: dict[str, Any], display_name: str) -> None:
        url = f"{self._base_url}/api/public/llm-connections"
        response = await client.put(url, json=data, auth=self._auth)

        if response.status_code in (200, 201):
            logger.info(f"Langfuse LLM connection upserted: {display_name}")
            return

        if response.status_code == 400 and "blocked ip address" in response.text.lower():
            hostname = urlparse(data["baseURL"]).hostname or data["baseURL"]
            raise ValueError(
                f"Langfuse rejected the '{display_name}' baseURL '{data['baseURL']}' as a private address. "
                f"Add '{hostname}' to {ALLOWLIST_SETTING} on {LANGFUSE_SERVICES} — Langfuse validates the "
                f"hostname both when the connection is written and on every call it makes through it."
            )

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
        elif response.status_code == 409 or (response.status_code == 400 and "already exists" in response.text.lower()):
            logger.debug(f"Langfuse model definition already exists: {model_name}")
            return False
        else:
            logger.warning(
                f"Langfuse model definition failed for '{model_name}': {response.status_code} — {response.text}"
            )
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
