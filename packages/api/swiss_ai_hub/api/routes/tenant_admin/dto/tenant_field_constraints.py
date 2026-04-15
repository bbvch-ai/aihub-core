"""Shared Pydantic field constraints for tenant request DTOs.

Kept in one place so ``ConfigureTenantRequest`` and ``UpdateTenantRequest`` cannot
drift — silently accepting a longer name in one but not the other would let an
update escape a constraint that create enforced.

Note on ``tenant_id``: the id is not user-chosen via this API. It must match an
existing Keycloak group name (verified in ``TenantAdminService.configure_tenant``
against ``KeycloakAdminService.get_tenant_group``). Keycloak is the real
authority on what constitutes a valid tenant id; imposing a regex here would
reject group names that Keycloak accepts (e.g. ``MyTenant``, ``customer.acme``)
and make configure fail even though the group was created legitimately via the
Keycloak admin console. The only checks that belong at this layer are a
minimum length (reject empty payloads) and a maximum length (Keycloak's own
group-name cap, as a DoS guard against unbounded strings reaching Mongo).
"""

from typing import Annotated

from pydantic import Field, StringConstraints

#: Keycloak's group-name length limit. Tenant ids are also the MongoDB primary
#: key on ``TenantMetadataEntity`` and URL path segments in ``/api/v1/{tenant_id}/...``;
#: 255 chars is well within those limits and matches the upstream source of truth.
TENANT_ID_MAX_LENGTH = 255

TenantId = Annotated[
    str,
    Field(
        description="Keycloak tenant group name (must already exist under /tenants/).",
        min_length=1,
        max_length=TENANT_ID_MAX_LENGTH,
    ),
]

TenantName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=120),
    Field(description="The unique display name of the tenant."),
]

TenantDescription = Annotated[
    str,
    StringConstraints(max_length=500),
    Field(description="A short description of the tenant."),
]
