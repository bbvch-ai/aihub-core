# OpenWebUI Accounts Are Provisioned Over SCIM Before The First Chat Login

## Context

A user created in Keycloak and given `AIHubAccess` could open the chat and find the model picker empty ("No results
found") until an administrator happened to change something access-related.

OpenWebUI only shows a user the models their groups are granted, and `OpenWebuiProvisioner` puts a user into the
`aihub:{tenant}:{role}` groups by matching their Keycloak email against the accounts OpenWebUI lists over SCIM. Before
this decision OpenWebUI created that account itself, on the user's first chat login. Two syncs could place a new user:

1. The sync that `AccessChangeHook` debounces two seconds after the user's first Admin UI request creates their
   `UserTenantRoleEntity`.
2. The sync that `WebhookController` ran when OpenWebUI posted its signup webhook.

When the chat login came after sync 1 had listed the accounts — the user lands on another Admin UI page first, or the
iframe's OAuth round-trip is simply slower than two seconds — only sync 2 could place them. OpenWebUI 0.11.3
silently removed that path, which was verified against the running image:

- `utils/webhook.py::post_webhook` now runs `validate_url`, which rejects every non-global address unless
  `ENABLE_LOCAL_WEB_FETCH` is set. `WEBHOOK_URL` points at `http://localhost:8000` (dev) or `http://api:8000` (every
  other stage), so each event is dropped with `Webhook skipped, URL invalid or not publicly resolvable`.
- The payload switched to an event schema (`event: user.created`, `actor`, `subject`) with no `action` field, which
  `OpenWebuiWebhookPayload` requires, so it would be rejected even if it arrived.

Reproduced on a fresh OpenWebUI 0.11.3 database: a user opening the chat ten seconds after their first Admin UI load
ended up in no group; one opening it after half a second ended up in theirs.

## Decision Drivers

- **No timing dependency.** Whether a user can use the chat must not depend on how fast their browser reaches it.
- **Keep OpenWebUI's SSRF protection.** Restoring the webhook needs `ENABLE_LOCAL_WEB_FETCH=true`, which also lets RAG
  web fetches and per-user webhooks (`ENABLE_USER_WEBHOOKS: True`) reach internal services.
- **No OpenWebUI fork**, and no change to how access is computed — only to when an account exists.

## Decision

**The provisioner creates the OpenWebUI account of every Keycloak user who holds a role but has none yet, over SCIM,
inside the group sync, and adds it to its groups in the same pass.**

- `_sync_groups_locked` calls `_provision_missing_accounts` after building the email mapping. It skips users without an
  email, disabled users, and users without any `UserTenantRoleEntity`.
- `OpenWebuiClient.create_user` sends the Keycloak `sub` as `externalId`. OpenWebUI's OAuth login links to that account
  instead of creating a second one (`OAUTH_MERGE_ACCOUNTS_BY_EMAIL` stays on). If the login created the account first,
  OpenWebUI answers 409; the client then reuses the account it finds by `externalId`, falling back to email. OpenWebUI
  matches the `externalId` filter against the OAuth sub too, so the lookup also finds an account whose email changed in
  Keycloak after its first chat login — OpenWebUI never updates it (`OAUTH_UPDATE_EMAIL_ON_LOGIN` is off), and an
  unresolved 409 aborts the group sync for every user.
- OpenWebUI runs with `SCIM_AUTH_PROVIDER: oidc`. Without it, 0.11.3 cannot record the external id: the create request
  fails with a 500, and the account never appears in the SCIM list, because `get_scim_users` only returns accounts
  linked to an OAuth or SCIM identity.
- `sync_access` now waits for a running access sync instead of skipping it, for the same reason: the running sync may
  have read its inputs before the change that triggered the waiting one.

## Consequences

### Positive

- A new user sees their models on their first chat visit, whenever it happens.
- Users already stuck are repaired by the startup `provision()` of the release that ships this.
- The ADR `2026_03_05` limitation "email-based user mapping requires users to have logged into both systems" is gone.

### Negative

- Every user with a role now has an OpenWebUI account, including users who only use the Admin UI.
- A provisioned account has role `user` until its owner's first chat login, where OAuth role management applies
  `AIHubSysAdmin` → `admin` as before.
- `sync_access` callers can queue behind one another; the debounce in `AccessChangeHook` keeps bulk changes to one run.
- The signup webhook (`WebhookController`, `WEBHOOK_URL`, `OPENWEBUI_WEBHOOK_SECRET`) no longer does anything and is left
  for a separate removal.

### Risks

- Like ADR `2026_09_04`, this rests on OpenWebUI internals verified by reading and running the 0.11.3 image
  (`routers/scim.py`, `models/users.py`), not on a published contract.
- An OpenWebUI account linked to neither an OAuth nor a SCIM identity (one added by hand in the admin panel) that shares
  a Keycloak user's email still fails the sync: the create conflicts on the email, but `get_scim_users` hides the
  account from both lookups. It resolves once its owner logs into the chat, which links it by email.
