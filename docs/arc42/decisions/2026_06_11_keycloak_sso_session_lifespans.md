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
  Auto-deployed customer environments (ansible-pull every 15 minutes) cannot rely on a first-start-only realm import to
  pick up lifespan changes, and operators should not have to run `kcadm` by hand.
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
- **`keycloak-realm.json.j2`** includes the lifespans in the realm import — fresh installs are correct from first start.
- **`keycloak-entrypoint.sh.j2`** applies the lifespans via `kcadm.sh update realms/aihub` in the post-startup block on
  **every container start** — existing deployments converge on their next Keycloak container recreation, without realm
  re-import and without touching users, clients, or sessions.

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
- The lifespans are enforced on every start, so ad-hoc changes made through the Keycloak admin console are overwritten
  on the next container restart — intended, since config-as-code is the source of truth, but admins must know the
  console is not authoritative for these two settings.
- Sessions already expired before the rollout cannot be revived; users see one final forced login after the change is
  deployed.

### Related Decisions

- `2026_04_07_active_tenant_as_keycloak_user_attribute.md` — active tenant persisted in Keycloak, restored after login
- `2025_12_28_keycloak_as_identity_broker.md` — Keycloak as sole OIDC provider
