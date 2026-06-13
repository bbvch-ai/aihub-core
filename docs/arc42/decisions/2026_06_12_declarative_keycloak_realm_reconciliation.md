# Declarative Keycloak Realm Reconciliation via keycloak-config-cli

## Context

The Keycloak realm is imported via `--import-realm` only on first start (fresh `keycloak` Postgres database) — Keycloak
skips existing realms by design to avoid destroying runtime state. Infrastructure changes to the realm config (new
clients, changed redirect URIs, new client scopes, new service-account roles) therefore never reached already-running
deployments. Two ad-hoc re-apply mechanisms had accumulated in `keycloak-entrypoint.sh` to work around this: identity
providers via `kcadm create partialImport -s ifResourceExists=OVERWRITE` and session lifespans via conditional `kcadm`
updates. Each new infrastructure change would have required another hand-rolled patch, and Keycloak's `partialImport`
API cannot carry client scopes, authentication flows, or components at all.

## Decision Drivers

- *Infrastructure config must reach running deployments*\
  Adding a client or changing a redirect URI must not require a fresh database or manual admin-console work.
- *Runtime data must never be touched*\
  Users, tenant groups (see `2026_04_15_keycloak_as_tenant_existence_authority`), and operator-tuned realm settings (see
  `2026_06_11_keycloak_sso_session_lifespans`) must survive every reconciliation.
- *File wins over drift*\
  The committed config is the source of truth for infrastructure objects; manual admin-console edits to managed objects
  are overwritten on the next start (config-as-code, auditable via git).
- *Full reconcile including deletions*\
  Infrastructure objects removed from config are deleted from running realms — no silent divergence between file and
  reality.
- *One mechanism instead of three*\
  Replace the growing pile of `partialImport`/`kcadm` patches with a single declarative tool.
- *Use Keycloak's sanctioned surface*\
  Keycloak offers no native config-as-code update mechanism; its official docs point to the Admin REST API for runtime
  changes. The two community-standard tools (Terraform provider, keycloak-config-cli) both use it. Terraform would add
  state-backend management and a toolchain this repo does not use.

## Decision

We run [adorsys/keycloak-config-cli](https://github.com/adorsys/keycloak-config-cli) (Apache-2.0, actively maintained,
image tag pinned to our exact Keycloak version) as a one-shot `keycloak-config` compose service in all stages. It starts
after Keycloak is healthy, reconciles the managed realm config through the Admin API, and exits.

**Config layout — single source, two render targets.** The realm config lives in standalone JSON templates under
`infra/deployment/templates/configs/keycloak/`, split by lifecycle and entity type:

| Folder       | Files                                                                                             | Lifecycle                                                    |
| ------------ | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| `bootstrap/` | realm-settings, components (user profile), groups (startup tenant seed), users-superuser          | First start only (`--import-realm`), never reconciled        |
| `managed/`   | 10-roles, 20-client-scopes, 30-clients, 40-auth-flows, 50-identity-providers, 60-service-accounts | Reconciled on every start by keycloak-config-cli (file wins) |

`generate_compose.py` renders the managed templates 1:1 as the keycloak-config-cli input files and additionally
JSON-merges all bootstrap + managed documents into the single `aihub-realm.{stage}.json` consumed by `--import-realm`.
Fresh boots therefore come up complete without waiting for the reconciler (no startup race for oauth2-proxies,
OpenWebUI, Langfuse, or the seeded service-account user), and keycloak-config-cli adopts the pre-created entities into
its remote state on its first run so deletion-reconcile works identically on fresh and existing deployments.

**Key keycloak-config-cli semantics the layout depends on:**

- Files are processed lexicographically as separate imports, each full-managed per entity type — so all entities of one
  type MUST live in a single file (a second file containing `clients` would delete the first file's clients). The
  numeric prefixes encode the dependency order: roles before flows (authenticator config references `AIHubAccess`),
  scopes before clients (`defaultClientScopes`), flows before identity providers (`postBrokerLoginFlowAlias`), clients
  before service accounts (`serviceAccountClientId`).
- Users are never a full-managed type: only users listed in a file are updated, absent users are never deleted. The
  `service-account-aihub-api-service` user lives in a managed file so realm-management role changes propagate, without
  endangering real users or the superuser.
- `IMPORT_CACHE_ENABLED=false` forces re-application even when file checksums are unchanged, so admin-console drift on
  managed objects is always reverted.
- `IMPORT_MANAGED_GROUP=no-delete` is set as defense in depth; no managed file may contain `groups`.

**Placeholder convention.** All realm config files use the keycloak-config-cli variable-substitution syntax `$(env:VAR)`
(its default `$(` prefix deliberately avoids colliding with Keycloak-internal `${role_...}` / `${CLAIM...}`
placeholders). The entrypoint's pure-bash envsubst substitutes the same syntax for the first-start import, plus a quoted
`"$(envjson:VAR)"` sentinel that injects raw JSON values (superuser roles array) while keeping the source files
parseable JSON.

**What stays in the entrypoint.** `--import-realm` for first-start bootstrap and the conditional kcadm session-lifespan
default-migration (`2026_06_11` — operator lifespan overrides survive because realm-level settings are bootstrap-only
and never appear in managed files). The identity-provider `partialImport` block is retired; identity providers are now a
managed file.

## Consequences

- Admin-console edits to managed objects (clients, scopes, realm roles, custom flows, identity providers) are
  overwritten on the next stack start. Intentional changes must go through the config templates.
- Objects removed from managed files are deleted from running realms. Keycloak built-in roles, flows, and default scopes
  are never touched.
- A failed `keycloak-config` run surfaces as a non-zero exit in `docker compose ps -a`; Keycloak keeps running with the
  previous config. Nothing depends on the service completing.
- New mirrored third-party image (`keycloak-config-cli`); its tag must be bumped together with the Keycloak image (tag
  scheme `{cli-version}-{keycloak-version}`).
- Realm-level settings (SMTP, brute force, themes, lifespans) remain first-start-only; changing them on existing
  deployments still requires the admin console or a dedicated mechanism.

## Related Decisions

- `2026_06_11_keycloak_sso_session_lifespans.md` — lifespan default-migration mechanism, unchanged by this decision
- `2026_04_15_keycloak_as_tenant_existence_authority.md` — tenant groups are runtime data, never reconciled
- `2026_04_14_superuser_via_keycloak_realm_role.md` — superuser is a bootstrap seed, never reconciled
- `2025_12_28_keycloak_as_identity_broker.md`
