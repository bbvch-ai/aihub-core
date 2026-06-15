# Keycloak SSO Session Lifespans

## Context

The Keycloak realm import never set any session or token lifetime values, so every deployment ran on Keycloak's
defaults: 30 minutes SSO session idle timeout and 10 hours SSO session max lifespan. The admin UI is a pure SPA OIDC
client (`oidc-client-ts`) whose refresh token is an *online* token bound to the SSO session — `offline_access` is not
requested. Any overnight pause therefore exceeded the 30-minute idle window, invalidated the refresh token stored in
localStorage, and forced users through a full credential login every morning.

Two timers govern an SSO session, whichever fires first ends it:

- **`ssoSessionIdleTimeout`** — sliding window; resets on every session activity (most importantly each refresh-token
  grant). Expires sessions that go unused.
- **`ssoSessionMaxLifespan`** — hard ceiling counted from login, regardless of activity. Bounds the total lifetime of
  any session.

A complicating operational constraint: the realm JSON is imported on **first container start only**
(`keycloak-entrypoint.sh` deliberately avoids `OVERWRITE_EXISTING`, see import strategy comments there). Realm-level
settings added to the template never reach already-provisioned deployments.

## Decision Drivers

- **Daily forced re-login is unacceptable UX**:\
  An enterprise platform used as a daily co-worker must survive an overnight pause and a normal weekend (Friday evening
  → Monday morning, ~2.5 days idle) without re-authentication.
- **Sessions must still expire**:\
  Unbounded sessions extend the window in which a stolen refresh token or an offboarded user's live session remains
  usable. Periodic re-authentication re-verifies credentials against the identity provider (e.g. picks up disabled Entra
  ID accounts).
- **Existing deployments must converge without manual intervention**:\
  Automatically updated customer environments cannot rely on a first-start-only realm import to pick up lifespan
  changes, and operators should not have to run `kcadm` by hand.
- **Single source of truth**:\
  The values must not drift between the realm template (fresh installs) and any runtime enforcement mechanism.

## Decision

**SSO session lifespans are set explicitly to 5 days idle (`ssoSessionIdleTimeout: 432000`) and 30 days max
(`ssoSessionMaxLifespan: 2592000`), defined once in `infra/deployment/compose-config.yml` under the `keycloak:`
section.**

The chosen values balance the drivers: 5 days idle comfortably covers overnight pauses and weekends while expiring
sessions abandoned for a full vacation week; 30 days max caps the total lifetime of even continuously used sessions,
forcing a credential re-verification at least monthly.

### Implementation

- **`compose-config.yml`** holds the values; both Jinja2 templates below render from it, so there is exactly one place
  to change them.
- **`bootstrap/realm-settings.json.j2`** (merged into `aihub-realm.{stage}.json`) includes the lifespans in the realm
  import — fresh installs are correct from first start. As bootstrap config they are first-start-only, which is why the
  entrypoint migration below is needed to reach existing deployments.
- **`keycloak-entrypoint.sh.j2`** applies the lifespans via `kcadm.sh update realms/aihub` in the post-startup block on
  container start, but **only for fields still holding the Keycloak default** (30 min idle / 10 h max). Existing
  deployments converge on their next Keycloak container recreation, without realm re-import and without touching users,
  clients, or sessions — while values an operator customized in the admin console are left untouched. Each of the two
  fields is checked independently.

## Consequences

### Positive

- Users stay logged in across nights and weekends; silent token renewal succeeds instead of redirecting to the login
  page.
- The persisted active-tenant restore (see related decision) is reached through silent renew rather than a fresh login,
  so users land directly in their last tenant.
- Lifespan changes are a one-line config edit followed by `make generate-compose`; rollout to all deployments is
  automatic on the next Keycloak container start.

### Trade-offs

- A leaked refresh token remains usable for up to 5 days of inactivity (previously 30 minutes). Mitigations: tokens are
  bound to the Keycloak session and revoked server-side on logout (`useAuth.logout()` calls the backchannel logout), and
  the 30-day ceiling bounds the worst case.
- The entrypoint only migrates away from Keycloak defaults; it does not enforce the configured values. A deployment
  whose lifespans were already migrated (or customized) will not pick up future changes to the platform defaults in
  `compose-config.yml` — rolling out new values to such deployments requires a manual `kcadm`/admin-console change.
- An operator who deliberately sets a lifespan back to the exact Keycloak default (1800 or 36000 seconds) will see it
  migrated to the platform value on the next container start, since it is indistinguishable from a never-configured
  realm.
- Sessions already expired before the rollout cannot be revived; users see one final forced login after the change is
  deployed.

### Related Decisions

- `2026_04_07_active_tenant_as_keycloak_user_attribute.md` — active tenant persisted in Keycloak, restored after login
- `2025_12_28_keycloak_as_identity_broker.md` — Keycloak as sole OIDC provider
- `2026_06_12_declarative_keycloak_realm_reconciliation.md` — managed realm config reconciled via keycloak-config-cli;
  realm-level settings (incl. these lifespans) stay bootstrap-only, so the kcadm default-migration here is unchanged
