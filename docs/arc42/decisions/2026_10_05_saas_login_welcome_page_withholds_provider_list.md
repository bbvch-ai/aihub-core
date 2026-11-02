# SaaS Login Welcome Page Withholds the Provider List

## Context

The shared SaaS instance serves many organisations, each signing in through its own Keycloak identity provider. The
generic login page renders one button per enabled provider from the anonymous `GET /api/v1/auth-providers/`, so anyone
who opens the instance sees every tenant's provider name — the client list — and the wall of buttons grows with every
customer. Per-tenant login links (`/{locale}/auth/login/<idp-alias>`, #1515) already give each tenant a single-button
page, but that page found its provider by filtering the same full list. Issue #1977 asks for a welcome page with no
tenant names on the shared instance, while dedicated single-customer instances keep today's page.

## Decision Drivers

- **No client list for anonymous callers** Hiding buttons is not enough while the endpoint behind them still lists every
  provider.
- **Per-instance and off by default** Dedicated instances must behave exactly as before.
- **Per-tenant links keep working** They are the only way in for tenant users once the list is gone.
- **Administrators keep a way in** Platform administrators sign in with Keycloak username/password accounts, not through
  a tenant's provider.

## Decision

The switch lives in the API, as `KeycloakSettings.LOGIN_WELCOME_PAGE` (`KEYCLOAK_LOGIN_WELCOME_PAGE` on `api` and
`sysadmin-api`, default `false`), next to `SHOW_KEYCLOAK_LOGIN` which already shapes the same page. A flag in the web
container's runtime config was rejected: it would hide the buttons while the anonymous endpoint still served every name.

- `GET /api/v1/auth-providers/` returns `{welcome_page, providers}`. With the switch on it returns `welcome_page: true`
  and at most the synthetic direct-Keycloak entry (when `SHOW_KEYCLOAK_LOGIN` is on), without querying Keycloak. The
  page then shows the welcome message and, if that entry is present, a small administrator login link.
- Per-tenant links resolve their one provider through `GET /api/v1/auth-providers/{alias}`, which returns the provider
  while it is enabled and not link-only, or `null`. It accepts providers hidden on Keycloak's login page, because
  `kc_idp_hint` still works for them.

## Consequences

- The `/auth-providers/` response changed from a list to an object; every consumer is in the web layer, which ships the
  page and composable together.
- The per-alias lookup confirms whether an alias exists and returns its display name. Keycloak answers the same question
  through `kc_idp_hint`, so nothing new is exposed.
- Keycloak's own login page still lists every provider not hidden on it, and the administrator link, OpenWebUI's sign-in
  and hand-built authorization URLs all reach it. A shared instance must enable "Hide on login page" for every tenant
  provider; because the per-alias lookup ignores that flag, per-tenant links are unaffected.
- The list filter still reads Keycloak's pre-26 `config.hideOnLoginPage` key. Fixing it would change the button list on
  instances with the switch off, so it is left to its own change; it can no longer break per-tenant links.
- Tenants without a link have no way in once the switch is on, so links must be handed out first.
