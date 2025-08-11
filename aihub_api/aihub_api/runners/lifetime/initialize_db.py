"""
Database initialization module for the AI-Hub.

This module provides functions to initialize the database with required initial state,
including roles, permissions, and other essential entities needed for the hub to operate.
"""

import logging

from aihub_lib.auth.dependencies.SuperuserAuthHandler.SuperuserSettings import SuperuserSettings
from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.persistence.access.entities.RoleEntity import RoleEntity

logger = logging.getLogger(__name__)


async def initialize_roles() -> None:
    """
    Initialize all required roles in the database.

    This function orchestrates the creation of all necessary roles
    for the AI-Hub to operate properly.
    """
    if SuperuserSettings().ENABLED:
        await initialize_role(
            name="AIHubSuperuser",
            description="Grants the AI-Hub Superuser global administrative access",
            access_rules=["aihub.admin.>"],
        )

    if AIHubSettings().CREATE_DEFAULT_ROLES:
        await initialize_role(
            name="AIHubUser",
            description="Grants global administrative access to AI-Hub",
            access_rules=["aihub.user.>"],
        )
        await initialize_role(
            name="AIHubAdmin",
            description="Grants global administrative access to AI-Hub",
            access_rules=["aihub.admin.>"],
        )
        await initialize_role(
            name="AIHubAgentUser",
            description="Grants access to all agents but to nothing else",
            access_rules=["aihub.user.agent.>"],
        )
        await initialize_role(
            name="AIHubAgentAdmin",
            description="Grants admin access to all agents but to nothing else",
            access_rules=["aihub.admin.agent.>"],
        )
        await initialize_role(
            name="AIHubKnowledgeAdmin",
            description="Grants admin access to knowledge and agents",
            access_rules=["aihub.admin.agent.>", "aihub.admin.knowledge.>"],
        )
        await initialize_role(
            name="AIHubProcessUser",
            description="Grants access to all processes but to nothing else",
            access_rules=["aihub.user.process.>"],
        )
        await initialize_role(
            name="AIHubProcessAdmin",
            description="Grants admin access to all processes but to nothing else",
            access_rules=["aihub.admin.process.>"],
        )

    logger.info("Role initialization completed successfully")


async def initialize_role(name: str, description: str, access_rules: list[str]) -> None:
    """
    Initialize a single role in the database if it doesn't already exist.

    This is a generic function that can be used to create any role with
    the specified permissions. It is idempotent and safe to call multiple times.

    Args:
        name: The unique name identifier for the role
        description: A human-readable description of the role's purpose
        access_rules: List of permission rules granted to this role
    """
    # Check if the role already exists
    existing_role = RoleEntity.get_role_by_name(name)

    if existing_role:
        logger.info(f"Role '{name}' already exists, skipping creation")
        return

    # Create the new role
    role = RoleEntity(name=name, description=description, access_rules=access_rules)

    try:
        role.save()
        logger.info(f"Successfully created role '{name}'")
    except Exception as e:
        logger.error(f"Failed to create role '{name}': {e}")
        raise
