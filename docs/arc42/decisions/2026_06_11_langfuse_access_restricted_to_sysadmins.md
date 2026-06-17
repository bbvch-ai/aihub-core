# Restrict Langfuse Access to AIHubSysAdmin via a Keycloak Authentication-Flow Gate

> **Partially superseded** by
> [`2026_06_12_declarative_keycloak_realm_reconciliation`](./2026_06_12_declarative_keycloak_realm_reconciliation.md):
> the gate is no longer reconciled imperatively via `kcadm` in `keycloak-entrypoint.sh` (see Decision → "Reconciliation
> on running instances" below). Its flows, marker scope, client attachment, and the realm `browserFlow` binding are now
> declarative **managed** config reconciled by keycloak-config-cli on every start. The decision to restrict Langfuse to
> `AIHubSysAdmin` and the authentication-flow design below are unchanged — only the reconciliation mechanism moved.

## Context

Langfuse is exposed at `langfuse.<domain>` and uses its native Keycloak SSO integration for login (see
[Replace Arize Phoenix with Langfuse](2026_02_10_replace_phoenix_with_langfuse.md)). Keycloak, by default, allows any
authenticated realm user to complete a login against any OIDC client. On top of that, Langfuse's auto-provisioning
(`LANGFUSE_DEFAULT_ORG_ID` / `LANGFUSE_DEFAULT_ORG_ROLE: MEMBER`) added every SSO user as a member of the `aihub-org`
organization and `aihub-project` project. As a result, **every AI-Hub user could log into Langfuse and read all
traces**, which may contain sensitive prompts and documents.

All other infrastructure UIs (Dagster, SeaweedFS, Attu, Backup) are gated behind oauth2-proxy sidecars with
`OAUTH2_PROXY_ALLOWED_GROUPS=AIHubSysAdmin`. Langfuse must be equally restricted to users holding the `AIHubSysAdmin`
realm role, but it differs from those services: it has first-class OIDC support and its own session handling, so
wrapping it in an additional proxy layer adds a container, a second cookie domain, and a second login hop without adding
value.

## Decision Drivers

- **Least privilege**\
  Traces contain user prompts, retrieved documents, and model outputs. Only system administrators may see them.
- **No additional runtime component**\
  Langfuse already authenticates against Keycloak; enforcing the restriction at the identity provider avoids an extra
  oauth2-proxy container and keeps the native SSO user experience (single login, clean Keycloak error page on denial).
- **Must reach already-running instances**\
  The realm JSON is only imported on the first Keycloak start, and Keycloak's `partialImport` API does not support
  authentication flows. The mechanism must therefore reconcile existing deployments without manual admin-console work.
- **Per-client scoping without per-client flow maintenance**\
  The deny rule must only affect the `langfuse` client; all other clients (frontend, OpenWebUI, account console,
  oauth2-proxy clients) must be untouched.
- **Established pattern**\
  The realm already denies IdP users without the `AIHubAccess` role via a conditional deny sub-flow
  (`Post Broker Login - AIHubAccess Check`). The same building blocks extend naturally to a per-client role gate.

## Decision

We gate Langfuse logins inside Keycloak with a conditional deny in the authentication flows:

**Marker client scope**: A mapper-less client scope `langfuse-sysadmin-gate` is attached as a *default* client scope to
the `langfuse` client only. Keycloak's `Condition - client scope` authenticator matches a client's default scopes
regardless of the requested `scope` parameter, so the scope acts as a reliable per-client marker.

**Gate sub-flows**: A conditional sub-flow — `Condition - client scope` (= `langfuse-sysadmin-gate`) AND
`Condition - user role` (`AIHubSysAdmin`, negated) → `Deny access` — is added in two places, covering all login paths:

- `langfuse-gate-browser` in a custom top-level browser flow `browser-aihub` (bound as the realm browser flow), which
  replicates the built-in browser flow (cookie, IdP redirector, forms, conditional OTP). The authentication alternatives
  are nested in a REQUIRED sub-flow (`browser-aihub-authenticate`) because Keycloak ignores ALTERNATIVE executions that
  share a level with a CONDITIONAL sub-flow — placing the gate next to the alternatives would break login for everyone.
  This flow covers users with an existing Keycloak SSO session and direct Keycloak logins.
- `langfuse-gate-post-broker` appended to the existing `Post Broker Login - AIHubAccess Check` flow. This covers fresh
  Azure AD brokered logins, which bypass the remainder of the browser flow after the IdP redirect.

**Reconciliation on running instances**: `keycloak-entrypoint.sh` applies the same configuration idempotently via
`kcadm` on every container start (create marker scope, attach to client, build the `browser-aihub` flow if absent, add
the gate sub-flows, bind the realm browser flow). Fresh installations get the identical state declaratively from the
realm import; every kcadm step checks for existence first and no-ops.

Langfuse-side settings (`LANGFUSE_DEFAULT_*` auto-provisioning, `AUTH_DISABLE_SIGNUP=false`) are intentionally kept:
with the Keycloak gate in place, only sysadmins can complete SSO, and auto-provisioning conveniently grants them
org/project membership on first login.

## Consequences

### Positive

- Only users with the `AIHubSysAdmin` realm role can log into Langfuse; everyone else is denied at Keycloak with a clear
  error message, on both fresh logins and existing SSO sessions.
- No new runtime component; single login flow preserved.
- Running environments converge automatically on the next deployment (Keycloak container restart) — no manual realm
  surgery, no re-import, no downtime beyond the restart.
- The deny pattern is consistent with the existing `AIHubAccess` gate and reusable for future per-client restrictions
  (add the marker scope to another client, or clone the pattern with a different scope/role).

### Trade-offs

- The custom `browser-aihub` flow no longer receives Keycloak's built-in browser-flow migrations on version upgrades
  (e.g. new passkey executions) and must be reviewed on major Keycloak upgrades. SPNEGO, organization, and passkey
  executions are intentionally omitted (unused in this deployment).
- Langfuse's email/password login bypasses Keycloak entirely. It is disabled on `nightly`/`latest`
  (`AUTH_DISABLE_USERNAME_PASSWORD=true`) but remains available on `dev`/`local`/`build` for development.
- The gate blocks future logins only. Users already provisioned into `aihub-org` must be removed manually in the
  Langfuse UI (Organization → Members), and active Langfuse sessions persist until expiry (rotate
  `LANGFUSE_NEXTAUTH_SECRET` for immediate revocation).
- Operators must hold the `AIHubSysAdmin` role (Azure AD app role, mapped by the `role-mapper-sysadmin` IdP mapper)
  before the rollout, otherwise they lock themselves out of Langfuse.

Related decisions: [Replace Arize Phoenix with Langfuse](2026_02_10_replace_phoenix_with_langfuse.md),
[Keycloak as Identity Broker](2026_02_28_keycloak_as_identity_broker.md),
[Superuser via Keycloak Realm Role](2026_04_14_superuser_via_keycloak_realm_role.md).
