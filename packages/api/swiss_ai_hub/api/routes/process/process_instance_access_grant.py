import logging
import re
from collections.abc import Callable
from typing import Annotated, Any

from fastapi import HTTPException
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity

logger = logging.getLogger(__name__)


class ProcessInstanceAccessGrant:
    """Grants a new process instance to the tenant and user that create it, and takes the grant back on delete.

    Process instances live in one global collection with no tenant column, so the tenant ceiling carries only
    the bare ``aihub.admin.process`` root, which is what creating one is guarded on. This grant is the only
    thing that makes an instance reachable, and only for the tenant that created it. Mirrors
    ``AgentService._grant_instance_access``.
    """

    @staticmethod
    def role_name(process_id: str) -> str:
        """The process id PascalCased with a ``ProcessAdmin`` suffix, so it cannot collide with the
        ``<AgentId>Admin`` role of an agent profile sharing the id."""
        pascal_case = "".join(word[:1].upper() + word[1:] for word in re.split(r"[^0-9A-Za-z]+", process_id) if word)
        return f"{pascal_case}ProcessAdmin"

    @staticmethod
    def grant(
        process_class: str,
        process_id: str,
        user: UserIdentity,
        rollback: Annotated[Callable[[], Any], "Undoes the instance creation if the grant fails"],
    ) -> None:
        """Adds the instance admin rule to the creating tenant's ceiling, unless a broader rule already covers
        it, and binds the creator to a per-instance admin role. Any failure undoes what was granted and the
        creation itself."""
        tenant = user.acting_within_tenant
        admin_rule = AccessChecker.process_admin_rule(process_class, process_id)
        role_name = ProcessInstanceAccessGrant.role_name(process_id)
        granted_tenant_rule = False
        created_role = False
        try:
            if not AccessChecker.rules_grant_admin(tenant.access_rules, admin_rule):
                TenantMetadataEntity.grant_access_rule(tenant.id, admin_rule)
                granted_tenant_rule = True
            created_role = ProcessInstanceAccessGrant._ensure_admin_role(
                role_name, admin_rule, tenant.id, process_class, process_id
            )
            UserTenantRoleEntity.add_roles(user.id, tenant.id, [role_name])
        except Exception as error:
            if created_role:
                ProcessInstanceAccessGrant._best_effort(
                    lambda: RoleEntity.delete_role_from_all_tenants(role_name), f"delete role {role_name}"
                )
            if granted_tenant_rule:
                ProcessInstanceAccessGrant._best_effort(
                    lambda: TenantMetadataEntity.revoke_access_rule_from_all_tenants([admin_rule]),
                    f"revoke {admin_rule}",
                )
            ProcessInstanceAccessGrant._best_effort(rollback, f"roll back {process_class}/{process_id}")
            raise HTTPException(
                status_code=500,
                detail=(
                    f"Process instance '{process_class}/{process_id}' was created but access could not be granted; "
                    "the creation was rolled back."
                ),
            ) from error

    @staticmethod
    def revoke(process_class: str, process_id: str) -> None:
        """Removes the instance rules from every tenant and deletes its admin role, so a later instance with
        the same id does not reappear in tenants that held the old one. Best-effort: the instance is already
        gone when this runs."""
        rules = [
            AccessChecker.process_user_rule(process_class, process_id),
            AccessChecker.process_admin_rule(process_class, process_id),
        ]
        role_name = ProcessInstanceAccessGrant.role_name(process_id)
        ProcessInstanceAccessGrant._best_effort(
            lambda: TenantMetadataEntity.revoke_access_rule_from_all_tenants(rules), f"revoke {rules}"
        )
        ProcessInstanceAccessGrant._best_effort(
            lambda: RoleEntity.delete_role_from_all_tenants(role_name), f"delete role {role_name}"
        )

    @staticmethod
    def _ensure_admin_role(
        role_name: str, admin_rule: str, tenant_id: str, process_class: str, process_id: str
    ) -> bool:
        """Creates the per-instance admin role if absent. Returns whether it was created."""
        if RoleEntity.objects(name=role_name, tenant_id=tenant_id).first():
            return False
        RoleEntity.create_tenant_role(
            name=role_name,
            description=f"Admin access to process instance {process_class}/{process_id}",
            access_rules=[admin_rule],
            tenant_id=tenant_id,
        )
        return True

    @staticmethod
    def _best_effort(action: Callable[[], Any], description: str) -> None:
        """Runs a compensating action, swallowing and logging any failure so it cannot mask the outcome."""
        try:
            action()
        except Exception:
            logger.exception("Best-effort step failed: %s", description)
