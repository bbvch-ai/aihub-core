import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, ClassVar

import httpx
from redis.asyncio import Redis
from scim2_client.engines.httpx import AsyncSCIMClient
from scim2_models import Group, User

from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.infrastructure.openwebui.access_grant import AccessGrant
from swiss_ai_hub.core.infrastructure.openwebui.online_agent import OnlineAgent
from swiss_ai_hub.core.infrastructure.openwebui.openwebui_client import OpenWebuiClient
from swiss_ai_hub.core.infrastructure.openwebui.openwebui_settings import OpenWebuiSettings
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
from swiss_ai_hub.core.persistence.access.entities.tenant_entity import TenantEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity
from swiss_ai_hub.core.persistence.user.user_entity import UserEntity

logger = logging.getLogger(__name__)

AIHUB_GROUP_PREFIX = "aihub:"
AIHUB_MODEL_PREFIX = "aihub-agent-"

_LOCK_TIMEOUT = 60

type AiHubToOwuiUserIdMapping = dict[str, str]
"""Maps AI-Hub user IDs (keys) to OpenWebUI user IDs (values), matched by email."""

type TenantAccessRules = dict[str, list[str]]
"""Maps tenant name to its access rule strings."""

type RoleAccessRules = dict[str, list[str]]
"""Maps role name to its access rule strings."""


class OpenWebuiProvisioner:
    _redis: ClassVar[Redis | None] = None

    def __init__(self) -> None:
        self._settings = OpenWebuiSettings()
        self._openwebui = OpenWebuiClient(
            base_url=self._settings.BASE_URL,
            secret_key=self._settings.SECRET_KEY.get_secret_value(),
            scim_token=self._settings.SCIM_TOKEN.get_secret_value(),
            service_account_id=self._settings.SERVICE_ACCOUNT_ID,
        )

    @classmethod
    def initialize(cls, redis: Redis) -> None:
        cls._redis = redis

    @staticmethod
    @asynccontextmanager
    async def _sync_lock(redis: Redis | None, key: str) -> AsyncIterator[bool]:
        if redis is None:
            raise RuntimeError("OpenWebuiProvisioner not initialized")
        lock = redis.lock(key, timeout=_LOCK_TIMEOUT)
        if not await lock.acquire(blocking=False):
            logger.debug("OpenWebUI %s skipped: another instance is syncing", key.rsplit(":", 1)[-1])
            yield False
            return
        try:
            yield True
        finally:
            await lock.release()

    async def provision(self) -> None:
        async with self._sync_lock(self._redis, "openwebui:sync:provision") as acquired:
            if not acquired:
                return
            logger.info("Starting OpenWebUI provisioning...")

            async with httpx.AsyncClient(timeout=30.0) as http:
                await self._sync_groups()
                await self._sync_workspace_models(http, [])
                await self._sync_access_grants(http)

            logger.info("OpenWebUI provisioning completed")

    async def sync_agents(self, online_agents: list[OnlineAgent]) -> None:
        async with self._sync_lock(self._redis, "openwebui:sync:agents") as acquired:
            if not acquired:
                return
            async with httpx.AsyncClient(timeout=30.0) as http:
                await self._sync_workspace_models(http, online_agents)
                await self._sync_access_grants(http)

            logger.info(f"OpenWebUI sync: Updated {len(online_agents)} agent workspace models")

    async def sync_access(self) -> None:
        async with self._sync_lock(self._redis, "openwebui:sync:access") as acquired:
            if not acquired:
                return
            async with httpx.AsyncClient(timeout=30.0) as http:
                await self._sync_groups()
                await self._sync_access_grants(http)

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
    def _get_active_user_ids(tenant_id: str, default_tenant_id: str | None) -> set[str]:
        if tenant_id == default_tenant_id:
            active_users = UserEntity.objects(
                __raw__={"$or": [{"active_tenant_id": tenant_id}, {"active_tenant_id": None}]}
            ).only("id")
        else:
            active_users = UserEntity.objects(active_tenant_id=tenant_id).only("id")
        return {u.id for u in active_users}

    async def _sync_group_memberships(
        self,
        tenants: list[dict[str, Any]],
        roles_by_tenant: dict[str, list[dict[str, Any]]],
        aihub_groups: dict[str, Group],
        user_id_mapping: AiHubToOwuiUserIdMapping,
        scim: AsyncSCIMClient | None = None,
    ) -> None:
        default_tenant = TenantEntity.get_default_tenant()
        default_tenant_id = str(default_tenant.id) if default_tenant else None

        for tenant in tenants:
            tenant_id = tenant["id"]
            active_user_ids = self._get_active_user_ids(tenant_id, default_tenant_id)

            for role_data in roles_by_tenant.get(tenant["name"], []):
                group_name = f"{AIHUB_GROUP_PREFIX}{tenant['name']}:{role_data['name']}"
                if group_name not in aihub_groups:
                    continue

                all_utr = UserTenantRoleEntity.objects(tenant_id=tenant_id, roles=role_data["name"])
                aihub_user_ids = [utr.user_id for utr in all_utr if utr.user_id in active_user_ids]
                owui_member_ids = [user_id_mapping[uid] for uid in aihub_user_ids if uid in user_id_mapping]

                await self._openwebui.update_group_members(aihub_groups[group_name].id, owui_member_ids, scim=scim)

    async def _sync_groups(self) -> None:
        tenants = [{"name": t.name, "id": str(t.id), "access_rules": t.access_rules} for t in TenantEntity.objects()]

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
            aihub_users = [{"id": u.id, "email": u.email} for u in UserEntity.objects()]
            user_id_mapping = self._build_user_id_mapping(aihub_users, owui_users)

            await self._sync_group_memberships(tenants, roles_by_tenant, aihub_groups, user_id_mapping, scim=scim)

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
        desired_ids = {f"{AIHUB_MODEL_PREFIX}{agent.agent_class}-{agent.agent_id}" for agent in online_agents}
        to_create = [
            agent
            for agent in online_agents
            if f"{AIHUB_MODEL_PREFIX}{agent.agent_class}-{agent.agent_id}" not in existing_model_ids
        ]
        to_delete = existing_model_ids - desired_ids
        return to_create, to_delete

    async def _sync_workspace_models(self, http: httpx.AsyncClient, online_agents: list[OnlineAgent]) -> None:
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
            logger.info(f"OpenWebUI: Created workspace model '{model_data['id']}'")

        for model_id in to_delete:
            await self._openwebui.delete_model(http, model_id)
            logger.info(f"OpenWebUI: Deleted workspace model '{model_id}'")

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
            r_rules = role_rules.get(role_name, [])

            checker = AccessChecker(user_access_rules=r_rules, tenant_access_rules=t_rules)
            if checker.has_access_to_agent(agent_class, agent_id):
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
    def _build_role_rules() -> RoleAccessRules:
        return {role.name: list(role.access_rules) for role in RoleEntity.objects()}

    async def _sync_access_grants(self, http: httpx.AsyncClient) -> None:
        existing_models = await self._openwebui.list_models(http)
        aihub_models = [m for m in existing_models if m.get("id", "").startswith(AIHUB_MODEL_PREFIX)]

        if not aihub_models:
            return

        async with self._openwebui.scim_session() as scim:
            all_groups = await self._openwebui.list_groups(scim=scim)
        aihub_groups = [g for g in all_groups if (g.display_name or "").startswith(AIHUB_GROUP_PREFIX)]

        if not aihub_groups:
            return

        tenant_rules: TenantAccessRules = {t.name: t.access_rules for t in TenantEntity.objects()}
        role_rules = self._build_role_rules()

        # Limit concurrent HTTP requests to avoid overwhelming OpenWebUI
        semaphore = asyncio.Semaphore(5)

        async def update_single(model: dict[str, Any]) -> None:
            async with semaphore:
                parsed = self._parse_agent_from_model(model)
                if not parsed:
                    return
                agent_class, agent_id = parsed
                access_control = self._compute_access_for_model(
                    agent_class, agent_id, aihub_groups, tenant_rules, role_rules
                )
                await self._openwebui.update_model_access(http, model["id"], access_control)

        await asyncio.gather(*[update_single(m) for m in aihub_models])
