# Superuser is a Keycloak-Seeded User, Not a Synthetic Identity

## Context

ADR `2025_08_11_global_superuser_authentication` introduced a synthetic superuser: `SuperuserAuthHandler` validated a
static `SUPERUSER_TOKEN` bearer against environment variables and returned a `UserIdentity` backed by a hardcoded
"virtual tenant" (`__superuser_tenant__`). The handler was chained in front of every other bearer check in
`TokenAndOauth2Handler`. A Keycloak-seeded admin user (`KEYCLOAK_DEV_USER_*`) existed in parallel as the interactive
login identity.

Two follow-up decisions made this dual design untenable:

- `2026_02_20_keycloak_tenant_assignment_via_groups` and the later `TenantMetadataEntity` refactor made Keycloak groups
  the sole source of truth for tenant existence. The superuser's virtual tenant has no Keycloak group; under the new
  model it is an orphan.
- `2026_04_14_tenant_scoped_roles` (companion ADR) removes the "system role" escape hatch. Every role now belongs to a
  concrete tenant. A user acting on no real tenant has no access rules to combine; the superuser auth handler relied on
  `is_sys_admin=True` short-circuiting the `AccessChecker` to paper over this.

The `AIHubSysAdmin` realm role already existed (ADR `2025_12_28_keycloak_as_identity_broker`) and `KeycloakAuthHandler`
already flipped `is_sys_admin=True` when it appeared in the JWT. The mechanism for "this Keycloak user is platform
admin" was therefore already in place — the superuser was a parallel channel that added complexity without adding
capability.

## Decision Drivers

- **One source of truth for admin rights**: `AIHubSysAdmin` in Keycloak (realm role) is the authoritative signal. A
  separate static token that bypasses it splits the audit surface and invites drift.
- **No synthetic identities**: Every authenticated request should resolve to a real Keycloak user with a real Keycloak
  ID. Tooling like Langfuse tracing, audit logs, OpenWebUI provisioning, and tenant membership queries all assume this.
- **Merge the dev admin and the machine superuser**: `KEYCLOAK_DEV_USER_*` and `SUPERUSER_*` described the same platform
  concept — the "first admin". One set of variables, one identity.
- **Internal services still need a static bearer**: OpenWebUI, RAG, images, audio, the external document loader, and the
  Langfuse provisioner call the API as a machine. They need a long-lived, configurable bearer token; OIDC flows with
  refresh cycles are not workable for them.

## Decision

**Delete `SuperuserAuthHandler`. The superuser is an ordinary Keycloak user seeded into the realm import as
`SUPERUSER_USERNAME`/`SUPERUSER_EMAIL`/`SUPERUSER_PASSWORD`/`SUPERUSER_FIRSTNAME`/`SUPERUSER_LASTNAME`, with realm roles
declared in `SUPERUSER_ROLES_JSON` (which must include `AIHubSysAdmin`). The seed is emitted in every stage's realm
JSON, not only `dev`. A static bearer token (`SUPERUSER_TOKEN`) is materialized into the `bearer_tokens` collection at
API startup, bound to that Keycloak user; internal services authenticate with it via `TokenAuthHandler`, which now
derives `is_sys_admin` from the token owner's current Keycloak realm roles.**

## Consequences

### Positive

- Single identity model: every authenticated principal is a Keycloak user with a real ID, resolvable via the Admin API,
  visible in tenant membership queries, traceable through Langfuse.
- `AccessChecker` no longer needs the virtual-tenant special case; the superuser's access derives from the same
  mechanism as any other sysadmin user.
- Token holders transparently inherit their owner's current Keycloak realm role membership — revoking `AIHubSysAdmin` in
  Keycloak immediately strips token-based sysadmin access on the next request.
- `.env.dev` and `.env.prod` lose the duplicated `SUPERUSER_ENABLED/NAME/OID/ROLE` block; one coherent block remains.
- Production deployments now ship with a seeded admin by default, matching operator expectations.

### Trade-offs

- Every `TokenAuthHandler` authentication incurs one Keycloak Admin API call to fetch realm roles (previously zero for
  `SUPERUSER_TOKEN`, still one `get_user_by_id` call for regular API tokens). Acceptable for the current load; cacheable
  later with short-TTL invalidation if it becomes a hot-path issue.
- Platform availability now depends more heavily on Keycloak Admin API reachability — a Keycloak outage previously only
  affected OAuth2 flows, now also affects machine-token flows. JWKS-based validation is still independent.
- `SUPERUSER_TOKEN` rotation requires both an env update and an API restart (or equivalent re-run of
  `initialize_superuser_token`). A follow-up ADR may add an endpoint to rotate the token at runtime.

### Supersedes

- `2025_08_11_global_superuser_authentication.md` — The synthetic superuser identity, `SuperuserAuthHandler`, and the
  virtual tenant are all removed. `SUPERUSER_TOKEN` remains, but its meaning changes: it is now a regular bearer token
  that happens to be provisioned from an environment variable.

### Related Decisions

- `2025_12_28_keycloak_as_identity_broker.md` — Keycloak as sole OIDC provider (premise)
- `2026_02_20_keycloak_tenant_assignment_via_groups.md` — Tenant membership via Keycloak groups (premise)
- `2026_04_14_tenant_scoped_roles.md` — Companion ADR; `AIHubSuperuser` role retired along with the handler
- `2026_04_14_opaque_api_token_format.md` — New token format used by the superuser bearer
