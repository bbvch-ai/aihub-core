"""Seed script for OpenWebUI agent visibility testing.

Creates two tenants, two users, and two agent configs with isolated access:
- tenant1/user1 can see agent1 only
- tenant2/user2 can see agent2 only

Usage:
    uv run python scripts/seed_visibility_test.py            # seed
    uv run python scripts/seed_visibility_test.py --cleanup   # remove seeded data
"""

import asyncio
import logging
import os
import sys

from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakPostError
from mongoengine import connect, disconnect

from aihub_lib.auth.dependencies.KeycloakAuthHandler.KeycloakSettings import KeycloakSettings
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig, LLMParameter
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.infrastructure.mongo.MongoSettings import MongoSettings
from aihub_lib.persistence.access.entities.TenantEntity import TenantEntity
from aihub_lib.persistence.access.entities.UserTenantRoleEntity import UserTenantRoleEntity
from aihub_lib.persistence.agents.AgentConfigEntityDocument import AgentConfigEntityDocument
from aihub_lib.persistence.user.UserEntity import UserEntity

from aihub_agent.agents.LLMWrappingAgent.LLMWrappingAgentConfig import LLMWrappingAgentConfig

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

AGENT_CLASS = "LLMWrappingAgent"

SEED_AGENTS = [
    LLMWrappingAgentConfig(
        agent_id="agent1",
        name=LocaleString(en="Visibility Test Agent 1", de="Sichtbarkeitstest Agent 1"),
        description=LocaleString(en="Agent visible only to tenant1", de="Agent nur für Tenant 1 sichtbar"),
        icon="mdi:robot-outline",
        number_of_input_tokens=100000,
        llm=LLMConfig(
            model_name="text-generation/gpt-oss-120b",
            default_parameter=LLMParameter(temperature=0.1),
        ),
    ),
    LLMWrappingAgentConfig(
        agent_id="agent2",
        name=LocaleString(en="Visibility Test Agent 2", de="Sichtbarkeitstest Agent 2"),
        description=LocaleString(en="Agent visible only to tenant2", de="Agent nur für Tenant 2 sichtbar"),
        icon="mdi:robot",
        number_of_input_tokens=100000,
        llm=LLMConfig(
            model_name="text-generation/gpt-oss-120b",
            default_parameter=LLMParameter(temperature=0.1),
        ),
    ),
]

SEED_USERS = [
    {"username": "visibility-user1", "email": "visibility-user1@test.local", "first_name": "Visibility", "last_name": "User1"},
    {"username": "visibility-user2", "email": "visibility-user2@test.local", "first_name": "Visibility", "last_name": "User2"},
]

SEED_TENANTS = [
    {"name": "visibility-test-tenant-1", "description": "Visibility test tenant 1 — sees agent1 only", "access_rules": [f"aihub.user.agent.{AGENT_CLASS}.agent1"]},
    {"name": "visibility-test-tenant-2", "description": "Visibility test tenant 2 — sees agent2 only", "access_rules": [f"aihub.user.agent.{AGENT_CLASS}.agent2"]},
]


def connect_mongo() -> None:
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
        uuidRepresentation="standard",
    )


def create_keycloak_admin() -> KeycloakAdmin:
    keycloak_settings = KeycloakSettings()
    return KeycloakAdmin(
        server_url=keycloak_settings.URL,
        realm_name=keycloak_settings.REALM,
        user_realm_name="master",
        username=os.environ.get("KEYCLOAK_ADMIN_USER", "admin"),
        password=os.environ.get("KEYCLOAK_ADMIN_PASSWORD", "admin"),
    )


async def find_keycloak_user_by_email(admin: KeycloakAdmin, email: str) -> str | None:
    """Finds a Keycloak user by email, returns user ID or None."""
    users = await admin.a_get_users({"email": email, "exact": True})
    if users:
        return users[0]["id"]
    return None


async def seed_keycloak_users(admin: KeycloakAdmin) -> list[str]:
    """Creates users in Keycloak. Returns list of Keycloak user IDs."""
    user_ids: list[str] = []

    for user_data in SEED_USERS:
        existing_id = await find_keycloak_user_by_email(admin, user_data["email"])
        if existing_id:
            user_ids.append(existing_id)
            logger.info(f"Keycloak user '{user_data['email']}' already exists (id={existing_id})")
            continue

        try:
            user_id = await admin.a_create_user({
                "username": user_data["username"],
                "email": user_data["email"],
                "firstName": user_data["first_name"],
                "lastName": user_data["last_name"],
                "enabled": True,
                "credentials": [{"type": "password", "value": "test1234", "temporary": False}],
            })
        except KeycloakPostError:
            user_id = await find_keycloak_user_by_email(admin, user_data["email"])

        logger.info(f"Keycloak user '{user_data['email']}' ready (id={user_id})")
        user_ids.append(user_id)

    return user_ids


async def seed_keycloak_tenant_groups(admin: KeycloakAdmin, user_ids: list[str]) -> None:
    """Creates /tenants/X groups and assigns users. Removes users from /tenants/default."""
    try:
        tenants_parent = await admin.a_get_group_by_path("/tenants")
        tenants_parent_id = tenants_parent["id"]
    except Exception:
        tenants_parent_id = await admin.a_create_group({"name": "tenants"}, skip_exists=True)

    for i, tenant_data in enumerate(SEED_TENANTS):
        tenant_name = tenant_data["name"]
        group_path = f"/tenants/{tenant_name}"

        try:
            group = await admin.a_get_group_by_path(group_path)
            group_id = group["id"]
        except Exception:
            group_id = await admin.a_create_group(
                {"name": tenant_name},
                parent=tenants_parent_id,
                skip_exists=True,
            )

        user_id = user_ids[i]
        await admin.a_group_user_add(user_id, group_id)
        logger.info(f"Keycloak: assigned user to group '{group_path}'")

    try:
        default_group = await admin.a_get_group_by_path("/tenants/default")
        default_group_id = default_group["id"]
        for user_id in user_ids:
            try:
                await admin.a_group_user_remove(user_id, default_group_id)
                logger.info(f"Keycloak: removed user {user_id} from /tenants/default")
            except Exception:
                pass
    except Exception:
        logger.info("Keycloak: /tenants/default group not found, skipping removal")


def seed_agent_configs() -> None:
    for config in SEED_AGENTS:
        existing = AgentConfigEntityDocument.find_for_class_and_id(AGENT_CLASS, config.agent_id)
        if existing:
            existing.update_from_agent_config(config, AGENT_CLASS)
            existing.save()
            logger.info(f"MongoDB: updated agent config '{AGENT_CLASS}/{config.agent_id}'")
        else:
            doc = AgentConfigEntityDocument.from_agent_config(config, AGENT_CLASS)
            doc.save()
            logger.info(f"MongoDB: created agent config '{AGENT_CLASS}/{config.agent_id}'")


def seed_mongo_users(keycloak_user_ids: list[str]) -> None:
    for i, user_data in enumerate(SEED_USERS):
        UserEntity.ensure_user_exists(
            oid=keycloak_user_ids[i],
            name=f"{user_data['first_name']} {user_data['last_name']}",
            email=user_data["email"],
        )
        logger.info(f"MongoDB: user '{user_data['email']}' ready (oid={keycloak_user_ids[i]})")


def seed_tenants() -> list[str]:
    """Creates tenants with agent-specific access rules. Returns tenant IDs."""
    tenant_ids: list[str] = []

    for tenant_data in SEED_TENANTS:
        existing = TenantEntity.get_tenant_by_name(tenant_data["name"])
        if existing:
            TenantEntity.update_tenant(
                tenant_id=str(existing.id),
                access_rules=tenant_data["access_rules"],
            )
            tenant_ids.append(str(existing.id))
            logger.info(f"MongoDB: updated tenant '{tenant_data['name']}'")
        else:
            tenant = TenantEntity.create_tenant(
                name=tenant_data["name"],
                description=tenant_data["description"],
                access_rules=tenant_data["access_rules"],
            )
            tenant_ids.append(str(tenant.id))
            logger.info(f"MongoDB: created tenant '{tenant_data['name']}'")

    return tenant_ids


def seed_user_tenant_roles(keycloak_user_ids: list[str], tenant_ids: list[str]) -> None:
    """Assigns users to their tenants with AIHubUser role and removes from default tenant."""
    default_tenant = TenantEntity.get_default_tenant()

    for i, user_id in enumerate(keycloak_user_ids):
        UserTenantRoleEntity.create_or_update(
            user_id=user_id,
            tenant_id=tenant_ids[i],
            roles=["AIHubUser"],
        )
        logger.info(f"MongoDB: assigned user {user_id} to tenant '{SEED_TENANTS[i]['name']}' with AIHubUser role")

        if default_tenant:
            removed = UserTenantRoleEntity.remove_user_from_tenant(user_id, str(default_tenant.id))
            if removed:
                logger.info(f"MongoDB: removed user {user_id} from default tenant")


async def seed() -> None:
    logger.info("=== Seeding visibility test data ===\n")

    connect_mongo()
    admin = create_keycloak_admin()

    logger.info("--- Keycloak users ---")
    keycloak_user_ids = await seed_keycloak_users(admin)

    logger.info("\n--- Keycloak tenant groups ---")
    await seed_keycloak_tenant_groups(admin, keycloak_user_ids)

    logger.info("\n--- Agent configs ---")
    seed_agent_configs()

    logger.info("\n--- MongoDB users ---")
    seed_mongo_users(keycloak_user_ids)

    logger.info("\n--- Tenants ---")
    tenant_ids = seed_tenants()

    logger.info("\n--- User-Tenant-Role assignments ---")
    seed_user_tenant_roles(keycloak_user_ids, tenant_ids)

    disconnect()

    logger.info("\n=== Seeding complete ===")
    logger.info(
        "\nNext steps:\n"
        "1. Have each user log in to OpenWebUI via Keycloak SSO (creates OpenWebUI user record)\n"
        f"   - user1: {SEED_USERS[0]['email']} / test1234\n"
        f"   - user2: {SEED_USERS[1]['email']} / test1234\n"
        "2. Restart the API or wait 60s for the OpenWebUI provisioner to sync\n"
        "3. Verify: user1 sees only agent1, user2 sees only agent2"
    )


async def cleanup() -> None:
    logger.info("=== Cleaning up visibility test data ===\n")

    connect_mongo()
    admin = create_keycloak_admin()

    for user_data in SEED_USERS:
        user_id = await find_keycloak_user_by_email(admin, user_data["email"])
        if user_id:
            await admin.a_delete_user(user_id)
            logger.info(f"Keycloak: deleted user '{user_data['email']}'")

    for tenant_data in SEED_TENANTS:
        try:
            group = await admin.a_get_group_by_path(f"/tenants/{tenant_data['name']}")
            await admin.a_delete_group(group["id"])
            logger.info(f"Keycloak: deleted group '/tenants/{tenant_data['name']}'")
        except Exception:
            pass

    for config in SEED_AGENTS:
        AgentConfigEntityDocument.delete_if_exists_for_class_and_id(AGENT_CLASS, config.agent_id)
        logger.info(f"MongoDB: deleted agent config '{AGENT_CLASS}/{config.agent_id}'")

    for tenant_data in SEED_TENANTS:
        tenant = TenantEntity.get_tenant_by_name(tenant_data["name"])
        if tenant:
            TenantEntity.delete_tenant(str(tenant.id))
            logger.info(f"MongoDB: deleted tenant '{tenant_data['name']}'")

    for user_data in SEED_USERS:
        try:
            user = UserEntity.by_email(user_data["email"])
            user.delete()
            logger.info(f"MongoDB: deleted user '{user_data['email']}'")
        except Exception:
            pass

    disconnect()
    logger.info("\n=== Cleanup complete ===")


if __name__ == "__main__":
    if "--cleanup" in sys.argv:
        asyncio.run(cleanup())
    else:
        asyncio.run(seed())
