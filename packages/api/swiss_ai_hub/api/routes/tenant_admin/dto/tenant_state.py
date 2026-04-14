from enum import StrEnum


class TenantState(StrEnum):
    """Visibility state of a tenant for the sysadmin view.

    - ACTIVE: exists both in Keycloak (as a group) and in MongoDB (as metadata).
    - ORPHANED: exists only in MongoDB; the Keycloak group is missing. Users cannot
      reach this tenant. Shown to sysadmins read-only with a delete action only.
    """

    ACTIVE = "active"
    ORPHANED = "orphaned"
