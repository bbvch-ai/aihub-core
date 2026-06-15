# No Bot-First Keycloak Provisioning; Require a One-Time Web Login

## Context

Keycloak is the platform's identity **broker** (ADR `2025_12_28_keycloak_as_identity_broker`). A federated Keycloak user
record is created **lazily** by Keycloak's *first-broker-login* flow, which only runs during an **OIDC browser login**
through the upstream IdP (Azure AD). Tenant membership and the active-tenant attribute are likewise held in Keycloak
(ADRs `2026_02_20_keycloak_tenant_assignment_via_groups`, `2026_04_07_active_tenant_as_keycloak_user_attribute`), so
*everything that authorizes a user to act* already routes through a Keycloak account.

The Teams/Slack bot, however, authenticates inbound activities with **Azure Bot Service credentials**, not an OIDC
browser flow. A bot message therefore never triggers first-broker-login. A user who interacts with the **bot first** —
without ever logging into the Hub web UI — has no Keycloak account, and the bot's `resolve_user_identity` cannot build a
`UserIdentity` for them. `KeycloakAdminService.create_user()` exists but was called nowhere in production code.

The result was that bot-first users were stuck, and the failure was **opaque**: `resolve_user_identity` raised a plain
`ValueError("...not found in Keycloak")` that surfaced to the user as the generic "something went wrong" error, with no
indication that a one-time web login was required (issue #1315).

## Decision Drivers

- **Single provisioning path / one source of truth**: First-broker-login is the only flow that correctly creates a
  federated user *with* the upstream identity link. A bot-side `create_user()` would produce a record that is not linked
  to the IdP and diverges from what a later browser login would create — two ways to mint a user, only one of them
  correct.
- **Avoid partial, unauthorized accounts**: A bot-provisioned user would still have no tenant membership, roles, or
  active tenant, so they could not actually be authorized to do anything until those were also synthesized — replicating
  significant parts of the login flow outside Keycloak.
- **Clarity over silent failure**: Whatever the policy, the end user must get an actionable message, not an opaque
  error.
- **Lowest responsible effort**: The use case (Teams-only onboarding with zero web touch) is not common enough to
  justify reimplementing identity provisioning; a one-time web login is an acceptable prerequisite.

## Decision

**The platform does not provision Keycloak users from bot interactions. A user must sign in to the Hub web portal once
(triggering Keycloak first-broker-login) before using the bot.** When a bot message arrives from a user with no Keycloak
account, the bot raises a typed `UserNotProvisionedError` (in `swiss_ai_hub.core.auth`) and replies with a clear,
actionable message (`bot.error.user_not_provisioned`, localized in de/en/fr/it) telling the user to log in to the Hub
web portal first. The unused `KeycloakAdminService.create_user()` bot-provisioning path is explicitly rejected, not
adopted.

The typed exception is what makes the message specific: the bot's `handle_exception` distinguishes the "not provisioned"
case from genuine errors (which keep the generic message) and surfaces the actionable text only for the former. The
developer-facing reason is still logged at info level.

## Consequences

### Positive

- One correct way to create a user (first-broker-login); no divergent, IdP-unlinked records to reconcile later.
- Bot-first users get an actionable instruction instead of an opaque error; the failure mode is self-explanatory.
- Minimal, well-contained change: a typed exception, one i18n key, and a branch in the bot's exception handler.

### Negative

- A genuinely Teams-only onboarding experience is not possible: every user must perform one web login before the bot
  works. This is a deliberate, documented constraint, not an oversight.
- If frictionless bot-first onboarding becomes a real requirement later, it will need a properly designed provisioning
  flow (IdP-linked account creation plus tenant/role assignment), which this ADR intentionally defers.
