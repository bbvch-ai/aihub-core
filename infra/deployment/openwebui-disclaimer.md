# Tenant chat disclaimer

Tenant admins edit the disclaimer under **Tenant Settings**. It accepts plain text in German, English,
French and Italian: at least one translation, at most 400 characters per language. Unconfigured tenants
use translated defaults without a migration. Missing translations follow AI Hub's fallback: German,
then the first populated supported language. The displayed language follows AI Hub.

## Placement and storage

This is shared tenant configuration, so it belongs in the tenant admin menu. **My Account** contains
personal preferences; the separate system-admin UI manages tenants across the platform.

- Admin-only GET/PUT `/{tenant_id}/tenant-settings` uses `aihub.admin.service.tenantsettings`.
  The existing service catalog supplies the menu. Service-admin wildcards cover the permission;
  explicit allowlists need to include it.
- `TenantSettingsEntity` stores one document per tenant in `tenant_settings`. Authentication selects
  the tenant; the request body cannot override it. Tenant deletion removes the settings, though cleanup
  is not transactional with in-flight saves.
- Keeping these settings separate from `TenantMetadataEntity` avoids its permission-sync hooks and
  the tenant-deletion rollback snapshot.
- Chat users read the localized text through `/{tenant_id}/openai/chat-disclaimer`, an AI Hub extension
  that uses the existing chat-service permission. The settings administration endpoints remain admin-only.
- Users can reload chat to see admin edits. The query also refreshes on navigation, language changes
  and window focus. Results are cached separately for each tenant and language; the default text appears
  until a result is available for that pair. There is no disclaimer polling.

## Deployment

Edit `infra/deployment/templates/openwebui-disclaimer/loader.js` and run `make generate-compose`.
The generator copies it to
`infra/configs/openwebui/disclaimer/loader.js` and into release bundles. The deployment copy is generated;
both files are committed, following the repository's existing convention.

The parent cannot access `iframe.contentDocument` across origins. OpenWebUI's stock page loads
`/static/loader.js`, so Compose mounts the adapter at `/app/build/static/loader.js`. Compose creates
`/app/build/static/aihub-disclaimer.json` from the inline `configs.openwebui-disclaimer.content` value;
there is no separate JSON source file. OpenWebUI's normal startup copies both files into its served
static directory; mounting only the served copy would be overwritten.

The JSON uses `http://localhost:3333` in development and `https://${DOMAIN}` elsewhere. Custom deployments
must set their exact AI Hub origin, without a path or trailing slash. Inline configs require
[Docker Compose 2.23.1 or newer](https://docs.docker.com/reference/compose-file/configs/).
Deploy the API/frontend and recreate OpenWebUI to apply the mounts. Its image and startup command
remain stock.

The supplied deployment files and release bundles use Compose. Customer Compose overrides must also
include both mounts and the inline config; the hosting playbook can
[replace the core Compose file with a customer's file](https://github.com/bbvch-ai/aihub-playbook/blob/f2880c74649b8cd866f1daf46b9bbb3bb700219e/ansible/roles/aihub_application/tasks/compose.yml#L30).

Multiple tenants can share one AI Hub origin. Separate customer hostnames also work when each OpenWebUI
deployment trusts its customer's AI Hub origin. Sharing one OpenWebUI deployment across several AI Hub
origins would require an explicit origin allowlist and corresponding ingress changes.

Kubernetes packaging is not provided here. An equivalent deployment would mount the loader and JSON
as individual ConfigMap files on every OpenWebUI replica, preserving the other static files, and roll
out pods when either file changes. This configuration has not been tested in a Kubernetes cluster.

The loader receives text through `postMessage`. Both ends check the exact origin and source window.
Messages contain only text and a protocol version. The loader uses `textContent` to display markup
literally. Standalone OpenWebUI does not initialize the bridge. A detected active-tenant mismatch
clears the custom footer while AI Hub displays its existing tenant warning.

## Temporary DOM contract

Verified in Chromium with stock **OpenWebUI v0.11.3-slim**; this branch pins OpenWebUI v0.11.3:

1. Find `#chat-input-container #chat-input` and its form inside `#chat-pane`.
2. Search that composer's ancestors for the empty footer with
   `absolute bottom-1 text-xs text-center line-clamp-1` classes. Insert the text there and reserve enough
   bottom spacing to avoid the controls.
3. In the centered new-chat layout, append the same styled text after the form controls.
4. A structural `MutationObserver` reattaches the element when Svelte replaces the composer.

The upstream one-line style truncates long text on narrow screens; the full text remains in its title
and DOM text. A populated outer footer is left intact. These selectors are version-dependent:
rerun the browser suite on OpenWebUI upgrades. Once an upstream footer setting accepts localized text
from AI Hub, replace the adapter and retain the settings page, storage and API.

## Verification

Backend tests cover defaults, validation, permissions (including chat-only users), menu visibility,
persistence, language fallback, tenant isolation and deletion:

```bash
uv run pytest packages/api/playground/testing/tests/tenant_settings/test_tenant_settings.py -q
```

The browser suite runs against a disposable stock OpenWebUI container using the same loader and
Compose config mount. It needs ports 18081, 3335 and 3336, but no LLM or full AI Hub deployment:

```bash
docker compose -f e2e/disclaimer/compose.yml up -d --wait
cd e2e
pnpm install --frozen-lockfile
pnpm exec playwright install chromium
pnpm exec playwright test --config=playwright.disclaimer.config.ts
cd ..
docker compose -f e2e/disclaimer/compose.yml down --volumes
```

It checks both chat layouts, navigation, geometry, mobile/dark mode, updates, cleanup, literal markup,
and rejection of messages from the wrong origin/window or with invalid versions/lengths. Its parent page
is a test fixture; it does not exercise AI Hub's query cache or authentication.

In a full deployment, save translations as a tenant admin and reopen chat in each AI Hub language.
Switch tenants and verify the text follows the tenant. Confirm ordinary users cannot open Tenant Settings,
a failed save keeps the draft, and reloading an open chat displays an admin edit. Leave chat open for
over 30 seconds and check that only the existing active-tenant poll recurs, without disclaimer requests.
For rollout verification, use a browser that accessed OpenWebUI before the upgrade and reload it after
the service is recreated.
