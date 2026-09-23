# Tenant chat disclaimer

Tenant admins edit the disclaimer under **Tenant Settings**. It accepts plain text in German, English,
French and Italian: at least one translation, at most 100 characters per language. Tenants without a
custom disclaimer use translated defaults. The text follows AI Hub's language, falling back to German,
then the first available translation.

Tenant Settings can load saved text above the current limit. Admins must shorten it before saving;
the chat footer accepts only text within the limit.

## API and storage

- Admin-only GET/PUT `/{tenant_id}/tenant-settings` uses `aihub.admin.service.tenantsettings`.
  The service catalog supplies the menu. Service-admin wildcards cover the permission;
  explicit allowlists need to include it.
- `TenantSettingsEntity` stores one document per tenant in `tenant_settings`. Authentication selects
  the tenant. Tenant deletion removes the settings; cleanup is not transactional with concurrent saves.
- Keeping these settings separate from `TenantMetadataEntity` avoids its permission-sync hooks and
  the tenant-deletion rollback snapshot.
- Chat users read the localized text through `/{tenant_id}/openai/chat-disclaimer` using the chat-service
  permission.
- Users can reload chat to see admin edits. The query also refreshes on navigation, language changes
  and window focus. Results are cached separately for each tenant and language; the default text appears
  until a result is available for that pair. There is no disclaimer polling.

## Deployment

Edit `infra/deployment/templates/openwebui-disclaimer/loader.js` and run `make generate-compose`.
The generator copies it to `infra/configs/openwebui/disclaimer/loader.js` and into release bundles.
Commit both the template and generated copy.

The parent cannot access `iframe.contentDocument` across origins. OpenWebUI loads `/static/loader.js`,
so Compose mounts the script at `/app/build/static/loader.js`. Compose creates
`/app/build/static/aihub-disclaimer.json` from the inline `configs.openwebui-disclaimer.content` value;
there is no separate JSON source file. OpenWebUI's normal startup copies both files into its served
static directory; mounting only the served copy would be overwritten.

The JSON uses `http://localhost:3333` in development and `https://${DOMAIN}` elsewhere. Custom deployments
must set their exact AI Hub origin, without a path or trailing slash. Inline configs require
[Docker Compose 2.23.1 or newer](https://docs.docker.com/reference/compose-file/configs/).
Deploy the API and frontend, then recreate OpenWebUI to apply the mounts.

The supplied deployment files and release bundles use Compose. Customer Compose overrides must also
include both mounts and the inline config; the hosting playbook can
[replace the core Compose file with a customer's file](https://github.com/bbvch-ai/aihub-playbook/blob/f2880c74649b8cd866f1daf46b9bbb3bb700219e/ansible/roles/aihub_application/tasks/compose.yml#L30).

Multiple tenants can share one AI Hub origin. Separate customer hostnames also work when each OpenWebUI
deployment trusts its customer's AI Hub origin. Sharing one OpenWebUI deployment across several AI Hub
origins would require an explicit origin allowlist and corresponding ingress changes.

For Kubernetes, mount the loader and JSON as individual ConfigMap files on every OpenWebUI replica,
preserving the other static files. Roll out pods when either file changes. Kubernetes manifests are
not included, and this setup has not been tested in Kubernetes.

The loader receives text through `postMessage`. Both ends check the exact origin and source window.
Messages contain only text and a protocol version. The loader uses `textContent` to display markup
literally. The script runs only inside an iframe. A tenant mismatch clears the custom footer while
AI Hub displays its tenant warning.

## Footer placement

Tested in Chromium with **OpenWebUI v0.11.3-slim**. The loader:

1. Finds `#chat-input-container #chat-input` and its form inside `#chat-pane`.
2. Searches that composer's ancestors for the upstream footer with
   `absolute bottom-1 text-xs text-center line-clamp-1` classes and leaves a populated footer intact.
3. Appends the text after the form controls in both chat layouts, leaving room for wrapping.
4. Uses a `MutationObserver` to reattach the element when Svelte replaces the composer.

The text wraps on narrow screens, including words longer than the available width. Rerun the browser
suite after OpenWebUI upgrades to check the selectors. Replace the script when OpenWebUI provides a
footer setting that accepts localized text from AI Hub.

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

The tests cover both chat layouts, navigation, wrapping, mobile and dark mode, text updates, removal,
literal markup, and rejection of messages with an invalid origin, source window, version or length.
The parent page is a test fixture. Test AI Hub's query cache and authentication in a full deployment.

In a full deployment, save translations as a tenant admin and reopen chat in each AI Hub language.
Switch tenants and verify the text follows the tenant. Confirm ordinary users cannot open Tenant Settings,
a failed save keeps the draft, and reloading an open chat displays an admin edit. Leave chat open for
over 30 seconds and check that only the existing active-tenant poll recurs, without disclaimer requests.
Also use a browser that accessed OpenWebUI before the upgrade and reload it after the service is recreated.
