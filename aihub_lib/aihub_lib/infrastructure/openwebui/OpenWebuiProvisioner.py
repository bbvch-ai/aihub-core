import logging
from typing import Any

import httpx

from aihub_lib.auth.access.AccessChecker import AccessChecker
from aihub_lib.infrastructure.openwebui.OpenWebuiClient import OpenWebuiClient
from aihub_lib.infrastructure.openwebui.OpenWebuiSettings import OpenWebuiSettings
from aihub_lib.persistence.access.entities.RoleEntity import RoleEntity
from aihub_lib.persistence.access.entities.TenantEntity import TenantEntity
from aihub_lib.persistence.access.entities.UserTenantRoleEntity import UserTenantRoleEntity
from aihub_lib.persistence.user.UserEntity import UserEntity

logger = logging.getLogger(__name__)

AIHUB_GROUP_PREFIX = "aihub:"
AIHUB_MODEL_PREFIX = "aihub-agent-"


class OpenWebuiProvisioner:
    def __init__(self, settings: OpenWebuiSettings | None = None) -> None:
        self._settings = settings or OpenWebuiSettings()
        self._client = OpenWebuiClient(
            base_url=self._settings.BASE_URL,
            secret_key=self._settings.SECRET_KEY.get_secret_value(),
            scim_token=self._settings.SCIM_TOKEN.get_secret_value(),
        )

    async def provision(self) -> None:
        logger.info("Starting OpenWebUI provisioning...")

        async with httpx.AsyncClient(timeout=30.0) as client:
            await self._sync_groups(client)
            await self._sync_workspace_models(client, [])
            await self._sync_access_grants(client)

        logger.info("OpenWebUI provisioning completed")

    async def sync_agents(self, online_agents: list[tuple[str, str, str]]) -> None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            await self._sync_workspace_models(client, online_agents)
            await self._sync_access_grants(client)

        logger.info(f"OpenWebUI sync: Updated {len(online_agents)} agent workspace models")

    async def sync_access(self) -> None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            await self._sync_groups(client)
            await self._sync_access_grants(client)

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
    def _build_user_id_mapping(aihub_users: list[dict[str, str]], owui_users: list[dict[str, Any]]) -> dict[str, str]:
        """Maps AI-Hub user IDs to OpenWebUI user IDs via email."""
        owui_by_email = {u["userName"]: u["id"] for u in owui_users if "userName" in u and "id" in u}
        mapping: dict[str, str] = {}
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
        client: httpx.AsyncClient,
        tenants: list[dict[str, Any]],
        roles_by_tenant: dict[str, list[dict[str, Any]]],
        aihub_groups: dict[str, dict[str, Any]],
        user_id_mapping: dict[str, str],
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

                await self._client.update_group_members(client, aihub_groups[group_name]["id"], owui_member_ids)

    async def _sync_groups(self, client: httpx.AsyncClient) -> None:
        tenants = [{"name": t.name, "id": str(t.id), "access_rules": t.access_rules} for t in TenantEntity.objects()]

        roles_by_tenant: dict[str, list[dict[str, Any]]] = {}
        for tenant in tenants:
            roles = RoleEntity.get_roles_for_tenant(tenant["id"])
            roles_by_tenant[tenant["name"]] = [{"name": r.name, "access_rules": r.access_rules} for r in roles]

        desired = self._build_desired_groups(tenants, roles_by_tenant)

        existing_groups = await self._client.list_groups(client)
        aihub_groups = {
            g["displayName"]: g for g in existing_groups if g.get("displayName", "").startswith(AIHUB_GROUP_PREFIX)
        }

        for name in desired - set(aihub_groups.keys()):
            created = await self._client.create_group(client, name, f"AI-Hub managed group: {name}")
            aihub_groups[name] = created
            logger.info(f"OpenWebUI: Created group '{name}'")

        for name in set(aihub_groups.keys()) - desired:
            await self._client.delete_group(client, aihub_groups.pop(name)["id"])
            logger.info(f"OpenWebUI: Deleted orphaned group '{name}'")

        owui_users = await self._client.list_users(client)
        aihub_users = [{"id": u.id, "email": u.email} for u in UserEntity.objects()]
        user_id_mapping = self._build_user_id_mapping(aihub_users, owui_users)

        await self._sync_group_memberships(client, tenants, roles_by_tenant, aihub_groups, user_id_mapping)

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
        online_agents: list[tuple[str, str, str]], existing_model_ids: set[str]
    ) -> tuple[list[tuple[str, str, str]], set[str]]:
        """Returns (models_to_create, model_ids_to_delete)."""
        desired_ids = {f"{AIHUB_MODEL_PREFIX}{ac}-{ai}" for ac, ai, _ in online_agents}
        to_create = [
            (ac, ai, name)
            for ac, ai, name in online_agents
            if f"{AIHUB_MODEL_PREFIX}{ac}-{ai}" not in existing_model_ids
        ]
        to_delete = existing_model_ids - desired_ids
        return to_create, to_delete

    async def _sync_workspace_models(
        self, client: httpx.AsyncClient, online_agents: list[tuple[str, str, str]]
    ) -> None:
        existing_models = await self._client.list_models(client)
        existing_aihub = {m["id"] for m in existing_models if m.get("id", "").startswith(AIHUB_MODEL_PREFIX)}

        to_create, to_delete = self._compute_model_diff(online_agents, existing_aihub)

        for agent_class, agent_id, display_name in to_create:
            model_data = {
                "id": self._workspace_model_id(agent_class, agent_id),
                "name": display_name,
                "base_model_id": self._base_model_id(agent_class, agent_id),
                "meta": {"description": f"AI-Hub agent: {agent_class}/{agent_id}"},
            }
            await self._client.create_model(client, model_data)
            logger.info(f"OpenWebUI: Created workspace model '{model_data['id']}'")

        for model_id in to_delete:
            await self._client.delete_model(client, model_id)
            logger.info(f"OpenWebUI: Deleted workspace model '{model_id}'")

    # ------------------------------------------------------------------
    # Access grant computation
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_access_for_model(
        agent_class: str,
        agent_id: str,
        groups: list[dict[str, Any]],
        tenant_rules: dict[str, list[str]],
        role_rules: dict[str, list[str]],
    ) -> list[dict[str, str]]:
        """Computes which groups should have read access to a given agent workspace model."""
        grants: list[dict[str, str]] = []

        for group in groups:
            group_name = group["displayName"]
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
                grants.append({"principal_type": "group", "principal_id": group["id"], "permission": "read"})

        return grants

    @staticmethod
    def _parse_agent_from_model(model: dict[str, Any]) -> tuple[str, str] | None:
        """Extracts (agent_class, agent_id) from a workspace model, preferring base_model_id."""
        base_model_id = model.get("base_model_id", "")
        if base_model_id.startswith("aihub-pipeline."):
            parts = base_model_id[len("aihub-pipeline.") :].split(".", 1)
            return (parts[0], parts[1]) if len(parts) == 2 else None

        suffix = model["id"][len(AIHUB_MODEL_PREFIX) :]
        dash_idx = suffix.rfind("-")
        return (suffix[:dash_idx], suffix[dash_idx + 1 :]) if dash_idx > 0 else None

    @staticmethod
    def _build_role_rules() -> dict[str, list[str]]:
        role_rules: dict[str, list[str]] = {}
        for role in RoleEntity.objects():
            if role.name not in role_rules:
                role_rules[role.name] = list(role.access_rules)
            else:
                role_rules[role.name] = list(set(role_rules[role.name]) | set(role.access_rules))
        return role_rules

    async def _sync_access_grants(self, client: httpx.AsyncClient) -> None:
        existing_models = await self._client.list_models(client)
        aihub_models = [m for m in existing_models if m.get("id", "").startswith(AIHUB_MODEL_PREFIX)]

        if not aihub_models:
            return

        all_groups = await self._client.list_groups(client)
        aihub_groups = [g for g in all_groups if g.get("displayName", "").startswith(AIHUB_GROUP_PREFIX)]

        if not aihub_groups:
            return

        tenant_rules = {t.name: t.access_rules for t in TenantEntity.objects()}
        role_rules = self._build_role_rules()

        for model in aihub_models:
            parsed = self._parse_agent_from_model(model)
            if not parsed:
                continue

            agent_class, agent_id = parsed
            access_control = self._compute_access_for_model(
                agent_class, agent_id, aihub_groups, tenant_rules, role_rules
            )
            await self._client.update_model_access(client, model["id"], access_control)
