# Parent Application Owns Authentication State for Iframe Services

## Context

Swiss AI-Hub embeds third-party services (e.g., OpenWebUI) in iframes within the Admin UI (`aihub_web`). Both the parent
application and embedded services authenticate against the same Keycloak realm (`aihub`), sharing a single SSO session.

When a user logs out of an embedded service (e.g., OpenWebUI's logout button), the service calls Keycloak's
`end_session_endpoint`, which destroys the **shared SSO session**. This has two visible consequences:

1. The iframe navigates away from the service (to a Keycloak redirect or blank page), leaving a white screen visible to
   the user.
2. The parent application's Keycloak SSO session is silently invalidated. The parent app continues to work because its
   local JWT (stored in localStorage) remains valid. However, once the JWT expires and `automaticSilentRenew` fails
   (because the SSO session no longer exists), the user is unexpectedly logged out — potentially minutes later or on the
   next page refresh.

OpenWebUI does not provide an environment variable to disable the OIDC RP-initiated logout (the `end_session_endpoint`
call is triggered automatically when `ENABLE_OAUTH_SIGNUP=True`). We cannot prevent embedded services from destroying the
SSO session without forking their source code.

The question is: should the parent application react to an iframe service logout by logging itself out, or should it
preserve its own session and redirect the user to a safe landing page?

## Decision Drivers

- **User intent**: Logging out of a chat interface (OpenWebUI) does not imply intent to leave the entire platform. Users
  expect the parent application to remain functional.
- **Session independence**: The parent application holds its own JWT in localStorage with a finite lifetime
  (`accessTokenLifespan` configured in Keycloak). This JWT remains valid regardless of the SSO session state at Keycloak.
- **Seamless re-entry**: When the user navigates back to the embedded service, the iframe loads the OIDC login endpoint
  (`/oauth/oidc/login`). If the parent application is still authenticated, Keycloak will prompt for credentials (or
  silently re-authenticate via an upstream IdP like Azure AD), creating a new SSO session. The embedded service
  auto-authenticates without additional user interaction.
- **No source modification**: The solution must work with unmodified third-party service images.

## Decision

**The parent application (`aihub_web`) is solely responsible for the user's authentication state.** Logout actions within
iframe-embedded services do not propagate to the parent application. Instead:

1. **No session monitoring**: `oidc-client-ts` session monitoring (`monitorSession`) is explicitly disabled. The parent
   application does not poll Keycloak's `check_session_iframe` endpoint and does not react to SSO session invalidation
   caused by embedded services.

2. **Iframe navigation detection**: The iframe's `@load` event detects when an embedded service navigates away (e.g.,
   Keycloak logout redirect). After the initial load, any subsequent `load` event triggers a redirect to the parent
   application's home page.

3. **Parent session preserved**: The redirect to home does **not** call `removeUser()` or clear the local JWT. The parent
   application remains fully functional with its existing access token.

4. **Natural token expiry**: When the access token approaches expiry, `automaticSilentRenew` attempts a silent renewal
   against Keycloak. If the SSO session no longer exists (destroyed by the iframe logout), renewal fails. The
   `accessTokenExpired` event handler then redirects to the login page. This is the only path that logs the user out of
   the parent application.

5. **Auto-login on re-entry**: When the user navigates back to the embedded service page, the iframe reloads the OIDC
   login endpoint. Keycloak either silently authenticates (if an upstream IdP session exists) or prompts for credentials.
   A new SSO session is established, and the embedded service loads without additional interaction.

### Implementation

**`plugins/oidc-client.ts`**: `monitorSession: false` and no `userSignedOut` event handler.

**`pages/service/openai.vue`**: `@load` handler on the iframe skips the first load and redirects to `localePath('/')` on
subsequent loads.

### Alternatives Considered

- **Mirror the iframe logout in the parent**: Enable `monitorSession: true` and call `removeUser()` on `userSignedOut`.
  Rejected because it logs the user out of the entire platform when they only intended to leave a single service.
- **Prevent the embedded service from calling `end_session_endpoint`**: Not possible without forking OpenWebUI. The OIDC
  logout is hardcoded when `ENABLE_OAUTH_SIGNUP=True`, and disabling signup breaks OIDC login entirely.
- **Separate Keycloak clients with isolated sessions**: Each embedded service could use a different Keycloak session
  scope. Rejected as overengineered — Keycloak SSO sessions are realm-wide by design, and working around this requires
  significant Keycloak customization.

## Consequences

### Positive

- Users stay logged into the parent application after logging out of an embedded service — no unexpected session loss
- No white/blank iframe screen — users are immediately redirected to the home page
- Navigating back to the embedded service re-authenticates automatically via the existing OIDC flow
- No third-party source modifications required
- The approach generalizes to any iframe-embedded service sharing the same Keycloak realm

### Trade-offs

- After an iframe logout, the parent application's local JWT remains valid but the Keycloak SSO session is gone. The
  parent app works normally until the token expires, at which point the user must re-authenticate. This window
  (determined by `accessTokenLifespan`) is acceptable because the user is still within a valid, locally-verified session.
- The `@load` event detection assumes embedded services are SPAs that do not trigger full page navigations during normal
  use. If an embedded service performs server-side redirects during regular operation, false positives could occur.
  OpenWebUI is a SPA and does not exhibit this behavior.

### Related Decisions

- `2025_12_28_keycloak_as_identity_broker.md` — Establishes Keycloak as the sole identity provider for all services
- `2026_02_18_seamless_openwebui_sso_via_iframe.md` — Describes the iframe SSO login flow that this decision complements
