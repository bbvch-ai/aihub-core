import logging
import time
from typing import ClassVar

import httpx
from pydantic import ValidationError
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.generative_ai import IngestedNode, MetadataFilterPair, RetrievalRuntimeConfig
from swiss_ai_hub.core.network import PublicHostGuard

from swiss_ai_hub.agent.agents.rag_agent.access.external_access_answer import ExternalAccessAnswer
from swiss_ai_hub.agent.agents.rag_agent.access.external_access_filter_settings import ExternalAccessFilterSettings
from swiss_ai_hub.agent.agents.rag_agent.configs.external_access_filter_config import ExternalAccessFilterConfig

logger = logging.getLogger(__name__)


class ExternalAccessFilters:
    """Narrows a run's retrievers to the documents an external system lets the asking user see.

    Whatever goes wrong - no user, a slow or failing resolver, an unreadable answer - ends in no access, never in an
    unfiltered search: the resolver is the only authority on these documents.
    """

    USER_EMAIL_HEADER: ClassVar[str] = "X-AIHub-User-Email"
    TENANT_HEADER: ClassVar[str] = "X-AIHub-Tenant"

    _answers: ClassVar[dict[tuple[str, str, str], tuple[float, list[str]]]] = {}

    @staticmethod
    async def apply(
        runtime_configs: list[RetrievalRuntimeConfig],
        config: ExternalAccessFilterConfig,
        user: UserIdentity | None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> list[RetrievalRuntimeConfig]:
        values = await ExternalAccessFilters.visible_values(config, user, transport)
        if not values:
            return []
        access_filter = MetadataFilterPair(key=config.metadata_key, value=values)
        return [
            runtime_config.model_copy(
                update={"additional_metadata_filters": [*runtime_config.additional_metadata_filters, access_filter]}
            )
            for runtime_config in runtime_configs
        ]

    @staticmethod
    async def still_visible(
        nodes: list[IngestedNode],
        config: ExternalAccessFilterConfig,
        user: UserIdentity | None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> list[IngestedNode]:
        """Nodes carried over from an earlier turn were released then, not necessarily now; they stay only if their
        value is released for this turn too."""
        if not nodes:
            return []
        values = set(await ExternalAccessFilters.visible_values(config, user, transport))
        return [node for node in nodes if ExternalAccessFilters._values_of(node, config.metadata_key) & values]

    @staticmethod
    def _values_of(node: IngestedNode, metadata_key: str) -> set[str]:
        value = node.record_fields.get(metadata_key)
        if isinstance(value, list):
            return {str(item) for item in value}
        return {str(value)} if value is not None else set()

    @staticmethod
    async def visible_values(
        config: ExternalAccessFilterConfig,
        user: UserIdentity | None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> list[str]:
        if user is None or not user.email:
            logger.warning("External access filter: the run has no user with an e-mail, nothing is retrieved")
            return []
        key = ExternalAccessFilters._cache_key(config, user)
        cached = ExternalAccessFilters._answers.get(key)
        if cached and cached[0] > time.monotonic():
            return cached[1]
        values = await ExternalAccessFilters._ask_resolver(config, user, transport)
        if values is not None and config.cache_ttl_seconds > 0:
            ExternalAccessFilters._answers[key] = (time.monotonic() + config.cache_ttl_seconds, values)
        return values or []

    @staticmethod
    def forget_answers() -> None:
        ExternalAccessFilters._answers.clear()

    @staticmethod
    def _tenant_of(user: UserIdentity) -> str:
        return user.acting_within_tenant.id if user.acting_within_tenant else ""

    @staticmethod
    def _cache_key(config: ExternalAccessFilterConfig, user: UserIdentity) -> tuple[str, str, str]:
        return (str(config.resolver_url), ExternalAccessFilters._tenant_of(user), user.id)

    @staticmethod
    def _headers(config: ExternalAccessFilterConfig, user: UserIdentity) -> dict[str, str]:
        headers = {
            ExternalAccessFilters.USER_EMAIL_HEADER: user.email,
            ExternalAccessFilters.TENANT_HEADER: ExternalAccessFilters._tenant_of(user),
        }
        if config.api_key:
            headers["Authorization"] = f"Bearer {config.api_key}"
        return headers

    @staticmethod
    async def _ask_resolver(
        config: ExternalAccessFilterConfig, user: UserIdentity, transport: httpx.AsyncBaseTransport | None
    ) -> list[str] | None:
        """None is a failure and is not cached, so the next question asks again; an empty list is an answer.

        Only public hosts, or those named in ``EXTERNAL_ACCESS_FILTER_ALLOWED_PRIVATE_HOSTS``, are called, and redirects
        are not followed (httpx's default): a profile editor sets the URL, and the API key goes with the request.
        """
        try:
            await PublicHostGuard.require_public_async(
                str(config.resolver_url),
                ExternalAccessFilterSettings().private_host_allow_list(),
                "EXTERNAL_ACCESS_FILTER_ALLOWED_PRIVATE_HOSTS",
            )
            async with httpx.AsyncClient(timeout=float(config.timeout_seconds), transport=transport) as client:
                response = await client.get(
                    str(config.resolver_url), headers=ExternalAccessFilters._headers(config, user)
                )
            response.raise_for_status()
            return ExternalAccessAnswer.model_validate(response.json()).values
        except (httpx.HTTPError, ValueError, ValidationError) as resolver_error:
            logger.warning("External access filter: resolver failed, nothing is retrieved: %s", type(resolver_error).__name__)
            return None
