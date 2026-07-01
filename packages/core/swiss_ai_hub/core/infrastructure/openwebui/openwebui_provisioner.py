import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
from redis.asyncio import Redis
from redis.exceptions import LockError
from scim2_client.engines.httpx import AsyncSCIMClient
from scim2_models import Group, User

from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_proxy_settings import LiteLLMProxySettings
from swiss_ai_hub.core.infrastructure.openwebui.access_grant import AccessGrant
from swiss_ai_hub.core.infrastructure.openwebui.available_model import AvailableModel
from swiss_ai_hub.core.infrastructure.openwebui.online_agent import OnlineAgent
from swiss_ai_hub.core.infrastructure.openwebui.openwebui_client import OpenWebuiClient
from swiss_ai_hub.core.infrastructure.openwebui.openwebui_settings import OpenWebuiSettings
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity
from swiss_ai_hub.core.persistence.agents.agent_class_entity import AgentClassEntity
from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument
from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity

logger = logging.getLogger(__name__)

AIHUB_GROUP_PREFIX = "aihub:"
AIHUB_AGENT_PREFIX = "aihub-agent-"
AIHUB_LLM_MODEL_PREFIX = "aihub-model-"

_LOCK_TIMEOUT = 60
# The group critical section lists all SCIM groups/users + all Keycloak users and then issues one
# membership update per group, so it can run for a while on large tenants. Its lock TTL must comfortably
# exceed that worst case, otherwise the lock auto-expires mid-run and a second sync can race it.
_GROUPS_LOCK_TTL = 600

type AiHubToOwuiUserIdMapping = dict[str, str]
"""Maps AI-Hub user IDs (keys) to OpenWebUI user IDs (values), matched by email."""

type TenantAccessRules = dict[str, list[str]]
"""Maps tenant name to its access rule strings."""

type RoleAccessRules = dict[tuple[str, str], list[str]]
"""Maps (tenant display name, role name) to that role's access rule strings.

Keyed by the pair because role names are only unique per tenant (index ``(tenant_id, name)``):
the same name (``AIHubUser``, a shared ``TestRole``, …) exists in every tenant with its own rules,
so a name-only key would collapse them and let one tenant's rules mask another's."""


class OpenWebuiProvisioner:
    def __init__(self, *, redis: Redis) -> None:
        self._settings = OpenWebuiSettings()
        self._openwebui = OpenWebuiClient(
            base_url=self._settings.BASE_URL,
            secret_key=self._settings.SECRET_KEY.get_secret_value(),
            scim_token=self._settings.SCIM_TOKEN.get_secret_value(),
            service_account_id=self._settings.SERVICE_ACCOUNT_ID,
        )
        self._redis = redis

    @asynccontextmanager
    async def _sync_lock(
        self, key: str, *, blocking: bool = False, ttl: int = _LOCK_TIMEOUT, wait: int = _LOCK_TIMEOUT
    ) -> AsyncIterator[bool]:
        """Acquires a Redis lock for the given key.

        ``blocking=False`` (default): skip the work if another instance holds it — used for whole-sync
        operations that are safe to drop because the holder already covers the same work.
        ``blocking=True``: wait up to ``wait`` seconds for the holder to finish — used for the group
        critical section, which must run rather than be skipped, but must never run concurrently.

        ``ttl`` is the lock's auto-expiry and must exceed the worst-case runtime of the protected work,
        otherwise the lock expires mid-run and a second caller can acquire it. ``wait`` only bounds how
        long a blocking caller waits, so the two are decoupled.
        """
        lock = self._redis.lock(key, timeout=ttl)
        blocking_timeout = wait if blocking else None
        if not await lock.acquire(blocking=blocking, blocking_timeout=blocking_timeout):
            logger.debug("OpenWebUI %s skipped: another instance is syncing", key.rsplit(":", 1)[-1])
            yield False
            return
        try:
            yield True
        finally:
            try:
                await lock.release()
            except LockError:
                # The lock auto-expired (work outran its TTL) and may now be held by another caller;
                # don't let the release failure mask the outcome of the work we just did.
                logger.warning("OpenWebUI sync lock '%s' expired before release; consider raising its TTL", key)

    async def provision(self) -> None:
        async with self._sync_lock("openwebui:sync:provision") as acquired:
            if not acquired:
                return
            logger.info("Starting OpenWebUI provisioning...")

            async with httpx.AsyncClient(timeout=30.0) as http:
                await self._sync_groups()
                await self._sync_workspace_models(http, self._get_known_online_agents())
                await self._sync_llm_workspace_models(http, await self._get_available_llm_models())
                await self._sync_access_grants(http)

            logger.info("OpenWebUI provisioning completed")

    async def sync_agents(self, online_agents: list[OnlineAgent]) -> None:
        async with self._sync_lock("openwebui:sync:agents") as acquired:
            if not acquired:
                return
            async with httpx.AsyncClient(timeout=30.0) as http:
                await self._sync_workspace_models(http, online_agents)
                await self._sync_access_grants(http)

            logger.info(f"OpenWebUI sync: Updated {len(online_agents)} agent workspace models")

    async def sync_access(self) -> None:
        async with self._sync_lock("openwebui:sync:access") as acquired:
            if not acquired:
                return
            async with httpx.AsyncClient(timeout=30.0) as http:
                await self._sync_groups()
                await self._sync_access_grants(http)

    @property
    def model_name_locale(self) -> str:
        """Locale used to render the single name OpenWebUI stores per workspace model."""
        return self._settings.MODEL_NAME_LOCALE

    def _resolve_display_name(self, name: LocaleStringEntity, agent_id: str) -> str:
        if not (name.de or name.en or name.fr or name.it):
            return agent_id
        return LocaleHandler(self.model_name_locale).extract(name)

    def _get_known_online_agents(self) -> list[OnlineAgent]:
        """Queries the DB for agent instances whose class was recently discovered."""
        class_entities = AgentClassEntity.get_online_conversational()
        if not class_entities:
            return []

        agent_classes = [ce.agent_class for ce in class_entities]
        all_configs = AgentConfigEntityDocument.find_for_classes(agent_classes)

        return [
            OnlineAgent(
                agent_class=config.agent_class,
                agent_id=config.agent_id,
                display_name=self._resolve_display_name(config.name, config.agent_id),
            )
            for config in all_configs
        ]

    async def _get_available_llm_models(self) -> list[AvailableModel]:
        """Queries LiteLLM for chat-capable models eligible to appear in the OpenWebUI picker.

        Filters on ``mode == "chat"`` rather than the capability prefix so non-chat models
        (embedding/rerank/transcription/image) never reach the chat picker.
        """
        async with LiteLLMProxySettings().httpx_aclient as client:
            response = await client.get("/v1/model/info")
            response.raise_for_status()
            data = response.json()["data"]

        models: list[AvailableModel] = []
        for entry in data:
            if entry.get("model_info", {}).get("mode") != "chat":
                continue
            capability, _, name = entry["model_name"].partition("/")
            if not name:
                continue
            models.append(AvailableModel(capability=capability, name=name, display_name=name))
        return models

    # ------------------------------------------------------------------
    # Group sync
    # ------------------------------------------------------------------

    @staticmethod
    def _build_desired_groups(
        tenants: list[dict[str, Any]], roles_by_tenant: dict[str, list[dict[str, Any]]]
    ) -> set[str]:
        groups: set[str] = set()
        for tenant in tenants:
            tenant_name = tenant["name"]
            for role in roles_by_tenant.get(tenant_name, []):
                groups.add(f"{AIHUB_GROUP_PREFIX}{tenant_name}:{role['name']}")
        return groups

    @staticmethod
    def _build_user_id_mapping(aihub_users: list[dict[str, str]], owui_users: list[User]) -> AiHubToOwuiUserIdMapping:
        """Maps AI-Hub user IDs to OpenWebUI user IDs via email."""
        owui_by_email = {u.user_name: u.id for u in owui_users if u.user_name and u.id}
        mapping: AiHubToOwuiUserIdMapping = {}
        for user in aihub_users:
            owui_id = owui_by_email.get(user["email"])
            if owui_id:
                mapping[user["id"]] = owui_id
        return mapping

    @staticmethod
    async def _get_active_user_ids(tenant_id: str) -> set[str]:
        return await KeycloakAdminService.get_user_ids_with_active_tenant(tenant_id)

    async def _sync_group_memberships(
        self,
        tenants: list[dict[str, Any]],
        roles_by_tenant: dict[str, list[dict[str, Any]]],
        aihub_groups: dict[str, Group],
        user_id_mapping: AiHubToOwuiUserIdMapping,
        scim: AsyncSCIMClient | None = None,
    ) -> None:
        for tenant in tenants:
            tenant_id = tenant["id"]
            active_user_ids = await self._get_active_user_ids(tenant_id)

            for role_data in roles_by_tenant.get(tenant["name"], []):
                group_name = f"{AIHUB_GROUP_PREFIX}{tenant['name']}:{role_data['name']}"
                if group_name not in aihub_groups:
                    continue

                all_utr = UserTenantRoleEntity.objects(tenant_id=tenant_id, roles=role_data["name"])
                aihub_user_ids = [utr.user_id for utr in all_utr if utr.user_id in active_user_ids]
                owui_member_ids = [user_id_mapping[uid] for uid in aihub_user_ids if uid in user_id_mapping]

                await self._openwebui.update_group_members(aihub_groups[group_name].id, owui_member_ids, scim=scim)

    async def _sync_groups(self) -> None:
        """Serializes group reconciliation across all callers (``provision`` and ``sync_access``).

        ``create_group`` is not atomic at the SCIM layer, so two concurrent ``_sync_groups`` runs would
        both observe a group as missing and each create it, yielding duplicate same-named groups. This
        dedicated blocking lock guarantees the create/delete section runs one-at-a-time across processes.
        """
        async with self._sync_lock("openwebui:sync:groups", blocking=True, ttl=_GROUPS_LOCK_TTL) as acquired:
            if not acquired:
                logger.warning("OpenWebUI group sync skipped: timed out waiting for the group-sync lock")
                return
            await self._sync_groups_locked()

    async def _sync_groups_locked(self) -> None:
        tenants = [
            {"name": t.name, "id": str(t.id), "access_rules": t.access_rules} for t in TenantMetadataEntity.objects()
        ]

        roles_by_tenant: dict[str, list[dict[str, Any]]] = {}
        for tenant in tenants:
            roles = RoleEntity.get_roles_for_tenant(tenant["id"])
            roles_by_tenant[tenant["name"]] = [{"name": r.name, "access_rules": r.access_rules} for r in roles]

        desired = self._build_desired_groups(tenants, roles_by_tenant)

        async with self._openwebui.scim_session() as scim:
            existing_groups = await self._openwebui.list_groups(scim=scim)
            aihub_groups: dict[str, Group] = {
                g.display_name: g for g in existing_groups if (g.display_name or "").startswith(AIHUB_GROUP_PREFIX)
            }

            for name in desired - set(aihub_groups.keys()):
                created = await self._openwebui.create_group(name, scim=scim)
                aihub_groups[name] = created
                logger.info(f"OpenWebUI: Created group '{name}'")

            for name in set(aihub_groups.keys()) - desired:
                await self._openwebui.delete_group(aihub_groups.pop(name).id, scim=scim)
                logger.info(f"OpenWebUI: Deleted orphaned group '{name}'")

            owui_users = await self._openwebui.list_users(scim=scim)
            keycloak_users = await KeycloakAdminService.get_all_users()
            aihub_users = [{"id": u.id, "email": u.email} for u in keycloak_users]
            user_id_mapping = self._build_user_id_mapping(aihub_users, owui_users)

            await self._sync_group_memberships(tenants, roles_by_tenant, aihub_groups, user_id_mapping, scim=scim)

    # ------------------------------------------------------------------
    # Workspace model sync
    # ------------------------------------------------------------------

    @staticmethod
    def _workspace_model_id(agent_class: str, agent_id: str) -> str:
        return f"{AIHUB_AGENT_PREFIX}{agent_class}-{agent_id}"

    @staticmethod
    def _base_model_id(agent_class: str, agent_id: str) -> str:
        return f"aihub-pipeline.{agent_class}.{agent_id}"

    def _build_model_data(self, agent: OnlineAgent) -> dict[str, Any]:
        return {
            "id": self._workspace_model_id(agent.agent_class, agent.agent_id),
            "name": agent.display_name,
            "base_model_id": self._base_model_id(agent.agent_class, agent.agent_id),
            "meta": {"description": f"AI-Hub agent: {agent.agent_class}/{agent.agent_id}"},
        }

    @staticmethod
    def _compute_model_diff(
        online_agents: list[OnlineAgent], existing_models: dict[str, dict[str, Any]]
    ) -> tuple[list[OnlineAgent], list[OnlineAgent], set[str]]:
        """Returns (models_to_create, models_to_update, model_ids_to_delete).

        An agent is updated when its workspace model exists but the stored name drifted from the
        current agent name (e.g. after a rename) — the only field this diff reconciles. Access
        grants are reconciled separately by _sync_access_grants.
        """
        desired_ids: set[str] = set()
        to_create: list[OnlineAgent] = []
        to_update: list[OnlineAgent] = []
        for agent in online_agents:
            model_id = OpenWebuiProvisioner._workspace_model_id(agent.agent_class, agent.agent_id)
            desired_ids.add(model_id)
            existing = existing_models.get(model_id)
            if existing is None:
                to_create.append(agent)
            elif existing.get("name") != agent.display_name:
                to_update.append(agent)
        to_delete = set(existing_models) - desired_ids
        return to_create, to_update, to_delete

    async def _sync_workspace_models(self, http: httpx.AsyncClient, online_agents: list[OnlineAgent]) -> None:
        existing_models = await self._openwebui.list_models(http)
        existing_aihub = {m["id"]: m for m in existing_models if m.get("id", "").startswith(AIHUB_AGENT_PREFIX)}

        to_create, to_update, to_delete = self._compute_model_diff(online_agents, existing_aihub)

        for agent in to_create:
            model_data = self._build_model_data(agent)
            await self._openwebui.create_model(http, model_data)
            logger.info(f"OpenWebUI: Created workspace model '{model_data['id']}'")

        for agent in to_update:
            model_data = self._build_model_data(agent)
            await self._openwebui.update_model(http, model_data)
            logger.info(f"OpenWebUI: Updated workspace model '{model_data['id']}' name to '{agent.display_name}'")

        for model_id in to_delete:
            await self._openwebui.delete_model(http, model_id)
            logger.info(f"OpenWebUI: Deleted workspace model '{model_id}'")

    # ------------------------------------------------------------------
    # LLM model sync
    # ------------------------------------------------------------------

    @staticmethod
    def _llm_workspace_model_id(model: AvailableModel) -> str:
        return f"{AIHUB_LLM_MODEL_PREFIX}{model.capability}-{model.name}"

    def _build_llm_model_data(self, model: AvailableModel) -> dict[str, Any]:
        """Points ``base_model_id`` at the raw LiteLLM connection model so chat routes through it.

        That base has no OpenWebUI registry entry, so ``has_base_model_access`` treats it as a raw
        provider model and lets granted users through — gating happens via this entry's access grants.
        """
        return {
            "id": self._llm_workspace_model_id(model),
            "name": model.display_name,
            "base_model_id": model.litellm_name,
            "meta": {"description": f"AI-Hub model: {model.litellm_name}"},
        }

    async def _sync_llm_workspace_models(self, http: httpx.AsyncClient, models: list[AvailableModel]) -> None:
        existing_models = await self._openwebui.list_models(http)
        existing_aihub = {m["id"]: m for m in existing_models if m.get("id", "").startswith(AIHUB_LLM_MODEL_PREFIX)}

        desired = {self._llm_workspace_model_id(model): model for model in models}

        for model_id, model in desired.items():
            existing = existing_aihub.get(model_id)
            if existing is None:
                await self._openwebui.create_model(http, self._build_llm_model_data(model))
                logger.info(f"OpenWebUI: Created LLM workspace model '{model_id}'")
            elif existing.get("name") != model.display_name:
                await self._openwebui.update_model(http, self._build_llm_model_data(model))
                logger.info(f"OpenWebUI: Updated LLM workspace model '{model_id}' name to '{model.display_name}'")

        for model_id in set(existing_aihub) - set(desired):
            await self._openwebui.delete_model(http, model_id)
            logger.info(f"OpenWebUI: Deleted LLM workspace model '{model_id}'")

    # ------------------------------------------------------------------
    # Access grant computation
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_access_for_model(
        agent_class: str,
        agent_id: str,
        groups: list[Group],
        tenant_rules: TenantAccessRules,
        role_rules: RoleAccessRules,
    ) -> list[AccessGrant]:
        """Computes which groups should have read access to a given agent workspace model."""
        grants: list[AccessGrant] = []

        for group in groups:
            group_name = group.display_name or ""
            if not group_name.startswith(AIHUB_GROUP_PREFIX):
                continue

            parts = group_name[len(AIHUB_GROUP_PREFIX) :].rsplit(":", 1)
            if len(parts) != 2:
                continue

            tenant_name, role_name = parts
            t_rules = tenant_rules.get(tenant_name, [])
            r_rules = role_rules.get((tenant_name, role_name), [])

            checker = AccessChecker(user_access_rules=r_rules, tenant_access_rules=t_rules)
            if checker.has_access_to_agent(agent_class, agent_id):
                grants.append(AccessGrant(principal_type="group", principal_id=group.id, permission="read"))

        return grants

    @staticmethod
    def _compute_access_for_llm_model(
        capability: str,
        name: str,
        groups: list[Group],
        tenant_rules: TenantAccessRules,
        role_rules: RoleAccessRules,
    ) -> list[AccessGrant]:
        """Computes which groups should have read access to a given LLM workspace model."""
        grants: list[AccessGrant] = []

        for group in groups:
            group_name = group.display_name or ""
            if not group_name.startswith(AIHUB_GROUP_PREFIX):
                continue

            parts = group_name[len(AIHUB_GROUP_PREFIX) :].rsplit(":", 1)
            if len(parts) != 2:
                continue

            tenant_name, role_name = parts
            t_rules = tenant_rules.get(tenant_name, [])
            r_rules = role_rules.get((tenant_name, role_name), [])

            checker = AccessChecker(user_access_rules=r_rules, tenant_access_rules=t_rules)
            if checker.has_access_to_model(capability, name):
                grants.append(AccessGrant(principal_type="group", principal_id=group.id, permission="read"))

        return grants

    @staticmethod
    def _parse_agent_from_model(model: dict[str, Any]) -> tuple[str, str] | None:
        """Extracts (agent_class, agent_id) from a workspace model via its base_model_id."""
        base_model_id = model.get("base_model_id", "")
        if not base_model_id.startswith("aihub-pipeline."):
            return None
        parts = base_model_id[len("aihub-pipeline.") :].split(".", 1)
        return (parts[0], parts[1]) if len(parts) == 2 else None

    @staticmethod
    def _parse_llm_from_model(model: dict[str, Any]) -> tuple[str, str] | None:
        """Extracts (capability, name) from an LLM workspace model via its base_model_id."""
        capability, _, name = model.get("base_model_id", "").partition("/")
        return (capability, name) if capability and name else None

    def _compute_grants_for_managed_model(
        self,
        model: dict[str, Any],
        groups: list[Group],
        tenant_rules: TenantAccessRules,
        role_rules: RoleAccessRules,
    ) -> list[AccessGrant] | None:
        """Dispatches grant computation by managed-model prefix; returns None for unparseable models."""
        model_id = model.get("id", "")
        if model_id.startswith(AIHUB_AGENT_PREFIX):
            parsed = self._parse_agent_from_model(model)
            return self._compute_access_for_model(*parsed, groups, tenant_rules, role_rules) if parsed else None
        if model_id.startswith(AIHUB_LLM_MODEL_PREFIX):
            parsed = self._parse_llm_from_model(model)
            return self._compute_access_for_llm_model(*parsed, groups, tenant_rules, role_rules) if parsed else None
        return None

    @staticmethod
    def _build_role_rules() -> RoleAccessRules:
        """Keys rules by (tenant display name, role name) so same-named roles in different tenants
        stay distinct. The tenant display name matches the ``aihub:{tenant}:{role}`` group naming and
        the ``tenant_rules`` keying, so the lookup in ``_compute_access_for_*`` lines up."""
        tenant_name_by_id = {str(tenant.id): tenant.name for tenant in TenantMetadataEntity.objects()}
        return {
            (tenant_name_by_id[role.tenant_id], role.name): list(role.access_rules)
            for role in RoleEntity.objects()
            if role.tenant_id in tenant_name_by_id
        }

    async def _sync_access_grants(self, http: httpx.AsyncClient) -> None:
        existing_models = await self._openwebui.list_models(http)
        aihub_models = [
            m for m in existing_models if m.get("id", "").startswith((AIHUB_AGENT_PREFIX, AIHUB_LLM_MODEL_PREFIX))
        ]

        if not aihub_models:
            return

        async with self._openwebui.scim_session() as scim:
            all_groups = await self._openwebui.list_groups(scim=scim)
        aihub_groups = [g for g in all_groups if (g.display_name or "").startswith(AIHUB_GROUP_PREFIX)]

        if not aihub_groups:
            return

        tenant_rules: TenantAccessRules = {t.name: t.access_rules for t in TenantMetadataEntity.objects()}
        role_rules = self._build_role_rules()

        # Limit concurrent HTTP requests to avoid overwhelming OpenWebUI
        semaphore = asyncio.Semaphore(5)

        async def update_single(model: dict[str, Any]) -> None:
            async with semaphore:
                access_control = self._compute_grants_for_managed_model(model, aihub_groups, tenant_rules, role_rules)
                if access_control is None:
                    return
                await self._openwebui.update_model_access(http, model["id"], access_control)

        await asyncio.gather(*[update_single(m) for m in aihub_models])
