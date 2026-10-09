# Tenant Login Links Resolve Their Identity Provider from a Per-Instance API Setting

## Context

Per-provider login pages (#1515) give each Keycloak identity provider a bookmarkable link, `/auth/login/<idp-alias>`.
They are keyed by the IdP alias because tenants and identity providers are not linked anywhere in the data model; #1515
explicitly deferred a tenant-to-IdP mapping, and the anonymous resolver it would need, to the multi-tenant login epic
(#1064).

On the SaaS instance that deferral now blocks login. #1977 removes the provider list from the login page so the page no
longer advertises every customer, which leaves a visitor without their link no way in. The links themselves use
technical aliases that customers cannot guess or remember. #1986 therefore makes a tenant's own address its login link:
a logged-out visit to `/<tenant-id>` or any page below it goes straight to that tenant's identity provider.

That needs an answer to "which IdP does this tenant log in with?", and nothing in the platform gives one. Keycloak only
holds the opposite direction, and only optionally: a `Hardcoded Group` IdP mapper adds every user of an IdP to one
tenant group (ADR `2026_02_20_keycloak_tenant_assignment_via_groups`). That mapper cannot describe an IdP shared by
several tenants, because it would put all of its users into a single tenant.

## Decision Drivers

- **Do not publish the client list**\
  Runtime frontend configuration is served to anyone as `/config.js`. A mapping there would list every tenant ID on the
  instance, which is exactly what #1977 removes from the login page.
- **Reveal nothing about tenant existence**\
  An unknown tenant ID must get the same answer as an existing tenant without a login link. Keycloak is the authority on
  tenant existence (ADR `2026_04_15_keycloak_as_tenant_existence_authority`), so the lookup must not consult it.
- **Shared identity providers**\
  Several tenants can log in through one IdP, so the mapping must allow many tenants per alias.
- **Dedicated instances stay unchanged**\
  Single-customer instances must behave exactly as before unless an operator opts in.
- **Leave the data-model design to #1064**\
  A tenant attribute with a sysadmin UI is the long-term home, but it needs schema, API and UI work this story does not
  need to wait for.

## Decision

**The tenant-to-IdP mapping is a per-instance API setting, and the frontend reads it one tenant at a time through an
anonymous lookup endpoint.**

- **Setting**: `KeycloakSettings.TENANT_IDP_ALIASES`, set as
  `KEYCLOAK_TENANT_IDP_ALIASES='acme=acme-entra,beta=shared-idp,gamma=shared-idp'` on the `api` service. Empty is the
  default and turns tenant login links off. A malformed pair or a tenant listed twice fails API startup, since a typo
  would otherwise silently send a tenant's users to the login page.
- **Endpoint**: `GET /api/v1/auth-providers/tenants/{tenant_id}` returns `{"alias": "<alias>"}` or `{"alias": null}`,
  always with status 200. It reads only the mapping and never asks whether the tenant exists. A mapped alias is returned
  only while its IdP is enabled and not link-only. IdPs hidden on Keycloak's login page are accepted, because Keycloak
  still honours `kc_idp_hint` for them and hiding them is how an operator keeps Keycloak's own page from listing every
  customer. The usable aliases are cached in Redis for five minutes, like the public provider list.
- **Frontend**: `middleware/auth.global.ts` looks up the first path segment, after an optional locale, whenever a
  visitor has no valid session, and redirects with `kc_idp_hint`. The redirect replaces the tenant page in the browser
  history, so Back from the IdP does not land on it and redirect again. Anything else ends on `/auth/login` as before. A
  failed background token refresh re-runs the same guard. After login, `middleware/home-redirect.ts` makes the linked
  tenant the active one when the user is a member, because OpenWebUI follows the active tenant rather than the URL (ADR
  `2026_04_07_active_tenant_as_keycloak_user_attribute`).

**Alternatives considered:**

- **Mapping in `/config.js`**: no backend change, but it publishes the full tenant list. Rejected.
- **Tenant metadata attribute with a sysadmin UI**: the right long-term home, deferred to #1064. Moving there changes
  only where the service reads the mapping from; the endpoint and the frontend stay as they are.
- **Derive the mapping from Keycloak's `Hardcoded Group` IdP mappers**: those mappers are optional and cannot express a
  shared IdP. Rejected.

## Consequences

### Positive

- A tenant's address is its login link, and customers no longer need to know an IdP alias.
- The tenant list is never published. Unknown and unlisted tenants get identical responses.
- Instances without a mapping keep their login flow, and no schema change or migration is needed.
- The #1515 per-provider pages keep working unchanged alongside tenant links.

### Trade-offs

- Changing the mapping means editing the instance's `.env` and restarting the `api` service. There is no UI, and
  creating a tenant that needs a login link also means updating the setting.
- A listed tenant reveals itself by redirecting to its IdP, as any working login link must, so tenant IDs can still be
  probed one at a time.
- Every logged-out visit to a page outside `/auth/` makes one extra anonymous request, including on instances with an
  empty mapping.
- A user of a shared IdP can authenticate through another tenant's link without being a member of that tenant. The API
  still denies access, but the user lands on a tenant page they cannot use.
- `/api/v1/auth-providers/` still lists every enabled, visible IdP to anyone. Hiding that list is a separate concern of
  #1977.
