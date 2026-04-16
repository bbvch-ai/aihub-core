from enum import StrEnum


class TenantState(StrEnum):
    """Visibility state of a tenant for the sysadmin view.

    - ACTIVE: exists both in Keycloak (as a group) and in MongoDB (as metadata).
    - ORPHANED: exists only in MongoDB; the Keycloak group is missing. Users cannot
      reach this tenant. Shown to sysadmins read-only with a delete action only.

    Unconfigured tenants (Keycloak group only, no metadata) deliberately do not
    appear here: they carry no MongoDB fields (name/description/access_rules) to
    wrap in a ``TenantResponse``, so they are served separately as ``list[str]``
    by ``/admin/tenants/unconfigured``. Promoting one to Active via
    ``configure_tenant`` is what introduces the metadata row that makes a
    ``TenantState`` value meaningful.
    """

    ACTIVE = "active"
    ORPHANED = "orphaned"
