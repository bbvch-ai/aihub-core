# Parent Application Owns Authentication State for Iframe Services

## Context

Swiss AI Hub embeds third-party services (e.g., OpenWebUI) in iframes within the Admin UI (`packages/web`). Both the
parent application and embedded services authenticate against the same Keycloak realm (`aihub`), sharing a single SSO
session.

When a user logs out of an embedded service (e.g., OpenWebUI's logout button), the service calls Keycloak's
`end_session_endpoint`, which destroys the **shared SSO session**. This has two visible consequences:

1. The iframe navigates away from the service (to a Keycloak redirect or blank page), leaving a white screen visible to
   the user.
2. The parent application's Keycloak SSO session is silently invalidated. The parent app continues to work because its
   local JWT (stored in localStorage) remains valid. However, once the JWT expires and `automaticSilentRenew` fails
   (because the SSO session no longer exists), the user is unexpectedly logged out — potentially minutes later or on the
   next page refresh.

OpenWebUI does not provide an environment variable to disable the OIDC RP-initiated logout (the `end_session_endpoint`
call is triggered automatically when `ENABLE_OAUTH_SIGNUP=True`). We cannot prevent embedded services from destroying
the SSO session without forking their source code.

The question is: should the parent application react to an iframe service logout by logging itself out, or should it
preserve its own session and redirect the user to a safe landing page?

## Decision Drivers

- **User intent**: Logging out of a chat interface (OpenWebUI) does not imply intent to leave the entire platform. Users
  expect the parent application to remain functional.
- **Session independence**: The parent application holds its own JWT in localStorage with a finite lifetime
  (`accessTokenLifespan` configured in Keycloak). This JWT remains valid regardless of the SSO session state at
  Keycloak.
- **Seamless re-entry**: When the user navigates back to the embedded service, the iframe loads the OIDC login endpoint
  (`/oauth/oidc/login`). If the parent application is still authenticated, Keycloak will prompt for credentials (or
  silently re-authenticate via an upstream IdP like Azure AD), creating a new SSO session. The embedded service
  auto-authenticates without additional user interaction.
- **No source modification**: The solution must work with unmodified third-party service images.

## Decision

**The parent application (`packages/web`) is solely responsible for the user's authentication state.** Logout actions
within iframe-embedded services do not propagate to the parent application. Instead:

1. **No session monitoring**: `oidc-client-ts` session monitoring (`monitorSession`) is explicitly disabled. The parent
   application does not poll Keycloak's `check_session_iframe` endpoint and does not react to SSO session invalidation
   caused by embedded services.

2. **Iframe navigation detection**: The iframe's `@load` event detects when an embedded service navigates away (e.g.,
   Keycloak logout redirect). After the initial load, any subsequent `load` event triggers a redirect to the parent
   application's home page.

3. **Parent session preserved**: The redirect to home does **not** call `removeUser()` or clear the local JWT. The
   parent application remains fully functional with its existing access token.

4. **Natural token expiry**: When the access token approaches expiry, `automaticSilentRenew` attempts a silent renewal
   against Keycloak. If the SSO session no longer exists (destroyed by the iframe logout), renewal fails. The
   `accessTokenExpired` event handler then redirects to the login page. This is the only path that logs the user out of
   the parent application.

5. **Auto-login on re-entry**: When the user navigates back to the embedded service page, the iframe reloads the OIDC
   login endpoint. Keycloak either silently authenticates (if an upstream IdP session exists) or prompts for
   credentials. A new SSO session is established, and the embedded service loads without additional interaction.

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
  (determined by `accessTokenLifespan`) is acceptable because the user is still within a valid, locally-verified
  session.
- The `@load` event detection assumes embedded services are SPAs that do not trigger full page navigations during normal
  use. If an embedded service performs server-side redirects during regular operation, false positives could occur.
  OpenWebUI is a SPA and does not exhibit this behavior.

### Related Decisions

- `2025_12_28_keycloak_as_identity_broker.md` — Establishes Keycloak as the sole identity provider for all services
- `2026_02_18_seamless_openwebui_sso_via_iframe.md` — Describes the iframe SSO login flow that this decision complements

## Addendum (2026-10-13): parent logs out when the SSO session is gone

**Context.** The stored OIDC user lives in localStorage and survives a browser restart; Keycloak's SSO cookie is a
session cookie and does not. Refresh-token renewal still succeeds afterwards, because the Keycloak session is
server-side, so the parent app looks fully logged in — but the OpenWebUI iframe signs in through the cookie and shows
Keycloak's login screen instead of the chat.

**Change.** On the first protected navigation of each browser session, `middleware/auth.global.ts` probes the SSO
session with a `prompt=none` round trip (`UserManager.querySessionStatus`). If Keycloak answers that there is no session
(`login_required`, `interaction_required`, `consent_required`), or that it belongs to another user, the parent removes
its stored user and redirects to login. Any other outcome keeps the stored session: no answer (timeout after 5 s,
network error), a server-side OAuth error (`server_error`, `temporarily_unavailable`, a failed code exchange), or a
status without `session_state`. None of these says anything about the cookie, and an unhealthy Keycloak must not log
users out.

The probe is costly: the hidden iframe boots the whole app a second time on `/auth/renew`, and a code exchange runs
whose tokens are discarded, all before the first page renders. It therefore runs once per browser session, not per page
load: a passed probe records the user's `sub` in sessionStorage (`utils/ssoSessionCheck.ts`), and later loads in that
tab skip it. sessionStorage ends together with the session cookie, so the skip cannot hide a lost cookie. The login
callback records the `sub` too, since Keycloak has just set the cookie; this also keeps a deployment where the iframe
cannot see the cookie (Keycloak on another site, third-party cookies blocked) from looping between login and the probe.
Keycloak must still be on the same site as the app, or the OpenWebUI iframe cannot sign in at all.

**Effect on this decision.** The probe cannot tell a lost cookie from an SSO session ended by an embedded service's
logout — both answer `login_required`. A new tab after an OpenWebUI logout therefore logs the parent out. In a tab that
already passed the probe, the parent logs out at its next token renewal instead: ending the Keycloak session also
invalidates the refresh token. This narrows Decision 3: the parent session is still preserved for a while (no
`monitorSession`, the `@load` handler still redirects home), but no longer indefinitely. It is accepted because the
preserved state was only half-working: every later visit to the chat sent the iframe to Keycloak's login page while the
parent looked logged in, and the Context above already expected a logout on the next refresh. Live mirroring via
`monitorSession` remains rejected.

**Correction to Decision 4.** There is no `accessTokenExpired` handler; one would race the middleware's own renewal on
load (see `plugins/oidc-client.ts`). A renewal that Keycloak rejects logs out through the `silentRenewError` handler or
through the renewal in `middleware/auth.global.ts` and `useAuth().getToken()`; a renewal that gets no answer keeps the
session and only fails the request. `useAuth().getToken()` re-runs the route guard on the current page, as the
`silentRenewError` handler does, so a tenant page goes to its identity provider and is restored after login. Together
with the probe above, these are the paths that log the user out of the parent application.

## Addendum (2026-10-30): renew on entering a page with an SSO iframe

**Context.** The probe runs once per tab, so a Keycloak session that ends on the server while the tab stays open (idle
timeout, revocation, a logout through OpenWebUI or another client) went unnoticed until the next token renewal, up to
the access token lifespan later. Entering the chat in that window sent the OpenWebUI iframe to Keycloak's login form.
An Entra sign-in inside that frame then fails OpenWebUI's OAuth callback with `mismatching_state`, which OpenWebUI shows
as "The email or password provided is incorrect" (bbvch-ai/aihub-core-private#307).

**Change.** Pages whose iframe signs in through the SSO cookie declare `definePageMeta({ embedsSsoIframe: true })`.
When a protected navigation enters such a page from one without it, `middleware/auth.global.ts` renews the session with
the refresh token, through the same branch as an expired token: Keycloak rejects the refresh token of an ended session,
so the parent removes its stored user and redirects to login before the iframe is created. A renewal that gets no
answer keeps the session, as before. It costs one token request per entry; moving within the page (opening a chat side
panel) does not renew again. The probe is still needed: after a browser restart the server-side session is alive and
the renewal succeeds, while the cookie the iframe needs is gone.

**Effect on this decision.** After an OpenWebUI logout, the parent now logs out the next time the user enters the chat
rather than at its next token renewal. That is the moment the preserved session would otherwise put Keycloak's login
form inside the iframe.
