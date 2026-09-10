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

# Pre-0.11.3 preset id prefixes. OpenWebUI 0.11.3 made an unregistered base_model_id admin-only
# (see _build_model_data / _build_llm_model_data below), so provisioning switched to registering the
# raw pipe/LiteLLM id directly as a base row instead of a preset pointing at it from one hop above.
# Kept only so _delete_legacy_preset_models can clean up presets created by prior versions of this
# provisioner — remove both the constants and that method once every deployment has synced past the
# change (one release after this ships).
AIHUB_AGENT_PREFIX = "aihub-agent-"
AIHUB_LLM_MODEL_PREFIX = "aihub-model-"

# Marks a base-registry row (base_model_id is None) as managed by this provisioner, so a sync can
# tell it apart from a base row a human created directly in the OpenWebUI workspace. See
# _build_model_data / _build_llm_model_data.
AIHUB_MANAGED_META_KEY = "aihub_managed"

# The function-calling mode _build_model_data / _build_llm_model_data provision onto every managed
# row (see their docstrings for why). Shared with _compute_model_diff and _sync_llm_workspace_models
# so a row already synced under a prior value of this constant is treated as drifted and updated —
# without that check, only brand-new rows would ever pick up a changed default, since name is
# otherwise the sole field either diff reconciles for an already-existing row.
_MANAGED_FUNCTION_CALLING = "legacy"

# Prefix of an agent's own base-registry id (e.g. "aihub-pipeline.RAGAgent.picasso-2"), as opposed
# to an LLM model's (e.g. "text-generation/Kimi-K2.6") — the two managed-row shapes base-row syncs
# and grant parsing need to tell apart now that both live in the same base-model registry.
AGENT_PIPE_ID_PREFIX = "aihub-pipeline."

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

    async def sync_known_agents(self) -> None:
        """Reconciles workspace models against the currently-known online agents in the DB.

        Lets agent-config mutations (create/rename/delete) reflect in the OpenWebUI model picker
        immediately instead of waiting for the next periodic discovery cycle.
        """
        await self.sync_agents(self._get_known_online_agents())

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
        response = await LiteLLMProxySettings().httpx_aclient.get("/v1/model/info")
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
    def _base_model_id(agent_class: str, agent_id: str) -> str:
        return f"{AGENT_PIPE_ID_PREFIX}{agent_class}.{agent_id}"

    def _build_model_data(self, agent: OnlineAgent) -> dict[str, Any]:
        """Registers the raw agent pipe id directly as a base-registry row (no base_model_id).

        OpenWebUI 0.11.3 made ``has_base_model_access`` deny everyone but admins through a
        ``base_model_id`` with no registry row of its own — the opposite of 0.9.x, which treated an
        unregistered base as a gate-free raw provider model. A preset pointing at the pipe id from one
        hop above no longer routes for non-admins, so the pipe id itself must carry the grant instead.

        ``function_calling: "legacy"`` — see ``_build_llm_model_data`` for why. The agent pipe never
        read OpenWebUI's ``tools``/builtins in the first place, so this is pure upside here: it just
        makes OpenWebUI perform image generation/web search/code interpreter itself again instead of
        handing the agent's LLM a tool spec it has nothing to invoke.
        """
        return {
            "id": self._base_model_id(agent.agent_class, agent.agent_id),
            "name": agent.display_name,
            "meta": {
                "description": f"AI-Hub agent: {agent.agent_class}/{agent.agent_id}",
                AIHUB_MANAGED_META_KEY: True,
            },
            "params": {"function_calling": _MANAGED_FUNCTION_CALLING},
        }

    @staticmethod
    def _compute_model_diff(
        online_agents: list[OnlineAgent], existing_models: dict[str, dict[str, Any]]
    ) -> tuple[list[OnlineAgent], list[OnlineAgent], set[str]]:
        """Returns (models_to_create, models_to_update, model_ids_to_delete).

        An agent is updated when its workspace model exists but the stored name drifted from the
        current agent name (e.g. after a rename), or its stored function-calling mode drifted from
        ``_MANAGED_FUNCTION_CALLING`` (e.g. this provisioner's own default changed since the row was
        last synced) — the two fields this diff reconciles. Access grants are reconciled separately
        by _sync_access_grants.
        """
        desired_ids: set[str] = set()
        to_create: list[OnlineAgent] = []
        to_update: list[OnlineAgent] = []
        for agent in online_agents:
            model_id = OpenWebuiProvisioner._base_model_id(agent.agent_class, agent.agent_id)
            desired_ids.add(model_id)
            existing = existing_models.get(model_id)
            if existing is None:
                to_create.append(agent)
            elif (
                existing.get("name") != agent.display_name
                or existing.get("params", {}).get("function_calling") != _MANAGED_FUNCTION_CALLING
            ):
                to_update.append(agent)
        to_delete = set(existing_models) - desired_ids
        return to_create, to_update, to_delete

    async def _sync_workspace_models(self, http: httpx.AsyncClient, online_agents: list[OnlineAgent]) -> None:
        """Reconciles agent pipe ids in the base-model registry (see ``_build_model_data``).

        Reads ``list_base_models`` rather than ``list_models``: a managed row has no
        ``base_model_id``, which is exactly what ``list_models``'s search filters out (and what makes
        it invisible to the Workspace UI too — see ``OpenWebuiClient.list_base_models``).
        """
        existing_rows = await self._openwebui.list_base_models(http)
        existing_aihub = {
            m["id"]: m
            for m in existing_rows
            if m.get("id", "").startswith(AGENT_PIPE_ID_PREFIX) and m.get("meta", {}).get(AIHUB_MANAGED_META_KEY)
        }

        to_create, to_update, to_delete = self._compute_model_diff(online_agents, existing_aihub)

        if not online_agents and to_delete:
            logger.warning(
                f"OpenWebUI: Skipping deletion of {len(to_delete)} workspace models — no agent class is "
                f"online, which reads as agent downtime rather than deprovisioning"
            )
            to_delete = set()

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

    def _build_llm_model_data(self, model: AvailableModel) -> dict[str, Any]:
        """Registers the raw LiteLLM model id directly as a base-registry row (no base_model_id).

        See ``_build_model_data`` for why: 0.11.3 denies non-admins through any unregistered
        ``base_model_id``, so the raw id itself must carry the grant now instead of a preset above it.

        ``function_calling: "legacy"`` — 0.11.3 defaults every row to Native, where OpenWebUI's
        built-in image generation/web search/code interpreter stop running server-side and instead
        get offered to the model as a ``generate_image``/``search_web``/``execute_code`` tool, on the
        hope it chooses to call it. That hope doesn't hold reliably: verified against this deployment's
        own chat history that the same model (gemma) both succeeded and failed at spontaneously calling
        ``generate_image`` across otherwise-identical requests, with zero code-side difference between
        the two — see issue aihub-core-private#240. Legacy restores the pre-0.11.3 behavior where
        OpenWebUI performs the action itself rather than trusting the model's tool-calling judgment.
        Costs Open Terminal (registered as a direct tool server) its native ``tool_calls`` fidelity,
        falling back to single-tool-per-turn, task-model-JSON-parsed invocation instead — the one
        capability this deployment's own history shows is actually exercised via native mode today.
        A user who needs native tool orchestration for one conversation can still override this in
        that chat's own Advanced Params, which takes precedence over this row-level default.
        """
        return {
            "id": model.litellm_name,
            "name": model.display_name,
            "meta": {
                "description": f"AI-Hub model: {model.litellm_name}",
                AIHUB_MANAGED_META_KEY: True,
            },
            "params": {"function_calling": _MANAGED_FUNCTION_CALLING},
        }

    async def _sync_llm_workspace_models(self, http: httpx.AsyncClient, models: list[AvailableModel]) -> None:
        """Reconciles LLM model ids in the base-model registry (see ``_build_llm_model_data``).

        Reads ``list_base_models`` rather than ``list_models`` — see ``_sync_workspace_models``.

        A row is updated when its stored name drifted, or its stored function-calling mode drifted
        from ``_MANAGED_FUNCTION_CALLING`` — see ``_compute_model_diff``'s docstring for why the
        latter check exists (a changed default here would otherwise never reach an already-synced row).
        """
        existing_rows = await self._openwebui.list_base_models(http)
        existing_aihub = {
            m["id"]: m
            for m in existing_rows
            if not m.get("id", "").startswith(AGENT_PIPE_ID_PREFIX) and m.get("meta", {}).get(AIHUB_MANAGED_META_KEY)
        }

        desired = {model.litellm_name: model for model in models}

        for model_id, model in desired.items():
            existing = existing_aihub.get(model_id)
            if existing is None:
                await self._openwebui.create_model(http, self._build_llm_model_data(model))
                logger.info(f"OpenWebUI: Created LLM workspace model '{model_id}'")
            elif (
                existing.get("name") != model.display_name
                or existing.get("params", {}).get("function_calling") != _MANAGED_FUNCTION_CALLING
            ):
                await self._openwebui.update_model(http, self._build_llm_model_data(model))
                logger.info(f"OpenWebUI: Updated LLM workspace model '{model_id}'")

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
        """Extracts (agent_class, agent_id) from a managed base row's own id.

        Ids no longer carry a ``base_model_id`` hop to read this from — the row's ``id`` *is* the
        pipe id now (see ``_build_model_data``).
        """
        model_id = model.get("id", "")
        if not model_id.startswith(AGENT_PIPE_ID_PREFIX):
            return None
        parts = model_id[len(AGENT_PIPE_ID_PREFIX) :].split(".", 1)
        return (parts[0], parts[1]) if len(parts) == 2 else None

    @staticmethod
    def _parse_llm_from_model(model: dict[str, Any]) -> tuple[str, str] | None:
        """Extracts (capability, name) from a managed base row's own id — see ``_parse_agent_from_model``."""
        capability, _, name = model.get("id", "").partition("/")
        return (capability, name) if capability and name else None

    def _compute_grants_for_managed_model(
        self,
        model: dict[str, Any],
        groups: list[Group],
        tenant_rules: TenantAccessRules,
        role_rules: RoleAccessRules,
    ) -> list[AccessGrant] | None:
        """Dispatches grant computation by id shape; returns None for unparseable models."""
        model_id = model.get("id", "")
        if model_id.startswith(AGENT_PIPE_ID_PREFIX):
            parsed = self._parse_agent_from_model(model)
            return self._compute_access_for_model(*parsed, groups, tenant_rules, role_rules) if parsed else None
        parsed = self._parse_llm_from_model(model)
        return self._compute_access_for_llm_model(*parsed, groups, tenant_rules, role_rules) if parsed else None

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

    async def _delete_legacy_preset_models(self, http: httpx.AsyncClient) -> None:
        """One-time migration: removes pre-0.11.3 ``aihub-agent-*`` / ``aihub-model-*`` preset rows.

        Those pointed ``base_model_id`` at an unregistered raw id; provisioning now registers that
        raw id directly as a base row instead (see ``_build_model_data`` / ``_build_llm_model_data``),
        so a preset left behind by a prior version of this provisioner would otherwise sit alongside
        its replacement and double up the picker. Safe to remove once every deployment has synced
        past the change (see the comment on ``AIHUB_AGENT_PREFIX`` / ``AIHUB_LLM_MODEL_PREFIX``).
        """
        existing_models = await self._openwebui.list_models(http)
        legacy_ids = [
            m["id"] for m in existing_models if m.get("id", "").startswith((AIHUB_AGENT_PREFIX, AIHUB_LLM_MODEL_PREFIX))
        ]
        for model_id in legacy_ids:
            await self._openwebui.delete_model(http, model_id)
            logger.info(
                f"OpenWebUI: Deleted legacy preset model '{model_id}' (superseded by direct base-row registration)"
            )

    async def _sync_access_grants(self, http: httpx.AsyncClient) -> None:
        """Recomputes and pushes access grants for every managed base-registry row.

        Reads ``list_base_models`` rather than ``list_models`` — see ``_sync_workspace_models``.
        """
        await self._delete_legacy_preset_models(http)

        existing_rows = await self._openwebui.list_base_models(http)
        aihub_models = [m for m in existing_rows if m.get("meta", {}).get(AIHUB_MANAGED_META_KEY)]

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
