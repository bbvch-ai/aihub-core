# Seamless OpenWebUI SSO via Direct OAuth Login in Iframe

## Context

Swiss AI Hub embeds OpenWebUI (the chat interface) in an iframe within the Admin UI at `/service/openai`. Users
authenticate against Keycloak in the Admin UI first. When the iframe loads OpenWebUI, the user is already authenticated
at Keycloak but has no OpenWebUI session yet. OpenWebUI's default behavior is to show a login page with a "Login with
Keycloak" button, requiring a manual click before the OAuth flow begins. This creates a poor user experience: the user
is already authenticated but must click through an additional login screen.

OpenWebUI does not provide a built-in environment variable or configuration option to auto-redirect unauthenticated
users to the OAuth provider (see
[open-webui/open-webui#7337](https://github.com/open-webui/open-webui/discussions/7337)). The redirect to `/auth` (the
login page) happens client-side within OpenWebUI's SPA, making it invisible to the reverse proxy (Traefik) and
impossible to intercept at the infrastructure level.

## Decision Drivers

- **Seamless User Experience**: Users should not encounter a second login screen for a service they are already
  authenticated to use. The iframe should feel like a native part of the Admin UI.
- **No OpenWebUI Source Modification**: The solution must work with the unmodified OpenWebUI image to avoid maintaining
  a fork solely for login behavior.
- **Shared Keycloak Session**: Since both the Admin UI and OpenWebUI authenticate against the same Keycloak realm
  (`aihub`), the user's Keycloak session is already established when the iframe loads. The OAuth flow completes silently
  (no Keycloak login form) because the session exists.
- **Simplicity**: Prefer the simplest solution that achieves the goal without introducing fragile infrastructure
  workarounds.

## Decision

**The Admin UI iframe loads OpenWebUI's OAuth login endpoint directly** (`/oauth/oidc/login`) instead of the root URL
(`/`).

In `aihub_web/aihub_web/pages/service/openai.vue`, the iframe `src` is set to:

```vue
<iframe :src="`${runtimeConfig.public.webui.url}/oauth/oidc/login`" ... />
```

This bypasses OpenWebUI's SPA login page entirely. The resulting flow is:

1. Iframe loads `https://openwebui.${DOMAIN}/oauth/oidc/login`
2. OpenWebUI initiates the OAuth authorization flow, redirecting to Keycloak
3. Keycloak detects the existing session and silently redirects back with an authorization code
4. OpenWebUI exchanges the code for a token, creates a session, and redirects to `/`
5. The user sees OpenWebUI's chat interface without any login interaction

### Supporting Infrastructure Changes

To make the server-to-server OAuth flow work correctly in Docker environments, two additional changes were made to
Keycloak's configuration in the Docker Compose template:

- **`OPENID_PROVIDER_URL` uses the internal Docker hostname** (`http://keycloak:8080`) for all stages, not just dev.
  This URL is used for server-to-server OIDC discovery and must be reachable from within the Docker network.
- **`--hostname-backchannel-dynamic=true`** is added to Keycloak's startup command. This ensures that when OpenWebUI
  fetches the OIDC discovery document via the internal URL, the returned endpoint URLs (token, userinfo, etc.) also use
  the internal hostname rather than the external `auth.${DOMAIN}`.

### Alternatives Considered

- **Traefik redirect middleware**: Intercept requests to `/auth` and redirect to `/oauth/oidc/login`. Rejected because
  OpenWebUI's redirect to `/auth` is a client-side SPA navigation, invisible to Traefik.
- **`ENABLE_OAUTH_AUTO_REDIRECT` environment variable**: Does not exist in OpenWebUI. No built-in auto-redirect feature
  is available.
- **OpenWebUI source modification**: Modifying the SPA to redirect from `/auth` to `/oauth/oidc/login` would work but
  requires maintaining a fork for a single-line change.

## Consequences

### Positive

- Users experience seamless SSO: no additional login click when opening the chat interface
- No OpenWebUI source modifications required; works with the stock image
- The OAuth flow completes in under a second with an existing Keycloak session
- The approach is straightforward and easy to understand

### Negative

- Every iframe load triggers a full OAuth round-trip (OpenWebUI -> Keycloak -> OpenWebUI), even if the user already has
  a valid OpenWebUI session cookie. This adds a small latency (~300-500ms) on each navigation to the chat page. In
  practice, this is imperceptible since Keycloak's silent redirect is fast.
- If the Keycloak session has expired, the user will see Keycloak's login form rendered inside the iframe. This is
  acceptable since it means the user's overall session has expired and re-authentication is required.

### Related Decisions

- `2025_12_28_keycloak_as_identity_broker.md` -- Establishes Keycloak as the sole identity provider, which this decision
  builds upon for shared SSO sessions
- `2025_08_27_adopt_sse_for_openwebui_integration.md` -- Describes the overall OpenWebUI integration architecture
