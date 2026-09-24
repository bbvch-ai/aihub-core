# Tenant chat disclaimer

System administrators edit the disclaimer under **Tenants → Overview** in the SysAdmin UI. Enter at least
one translation in German, English, French or Italian, with up to 100 characters per language. The editor
loads the saved translations, or the defaults for an unconfigured tenant. The footer follows AI Hub's
language, falling back to German, then the first available translation.

The tenant editor can load saved text above the current limit. Admins must shorten it before saving;
the chat footer accepts only text within the limit.

## API and storage

- SysAdmin API GET/PATCH `/admin/tenants/{tenant_id}` reads and updates tenant metadata, including the
  disclaimer. It requires the `AIHubSysAdmin` realm role. Orphaned tenants remain read-only.
- `TenantMetadataEntity.chat_disclaimer` stores the translations in the existing `tenants` document.
  Missing values use translated defaults. No database migration is required for existing tenants.
- The Overview form saves the disclaimer, name, description and access rules together. Validation runs
  before any fields are written. Saving metadata also syncs OpenWebUI permissions.
- Tenant deletion removes the disclaimer with the metadata; deletion rollback restores it.
- Chat users read the localized text through `/{tenant_id}/openai/chat-disclaimer` using the chat-service
  permission.
- The text refreshes on reload, navigation, language changes and window focus. Results are cached by
  tenant and language, with default text shown while loading. There is no disclaimer polling.

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
Deploy both API and frontend pairs (main and SysAdmin), then recreate OpenWebUI to apply the mounts.

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

Tested in Chromium with OpenWebUI v0.11.3-slim. The loader:

1. Finds `#chat-input-container #chat-input` and its form inside `#chat-pane`.
2. Searches that composer's ancestors for the upstream footer with
   `absolute bottom-1 text-xs text-center line-clamp-1` classes and leaves a populated footer intact.
3. Appends the text after the form controls in both chat layouts, leaving room for wrapping.
4. Uses a `MutationObserver` to reattach the element when Svelte replaces the composer.

The text wraps on narrow screens, including words longer than the available width. Rerun the browser
suite after OpenWebUI upgrades to check the selectors. Replace the script when OpenWebUI provides a
footer setting that accepts localized text from AI Hub.

## Verification

Run the API tests:

```bash
uv run pytest packages/api/playground/testing/tests/openai/test_chat_disclaimer.py -q
uv run pytest packages/sysadmin-api/tests/tenant_admin/test_tenant_disclaimer.py -q
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

In a full deployment:

1. Save translations with the other fields on the SysAdmin tenant Overview page. Reopen chat in each
   AI Hub language and switch tenants. Check that the footer matches the selected tenant and language.
2. Confirm tenant admins without the SysAdmin role cannot edit the disclaimer.
3. Enter more than 100 characters in one language. Check that validation prevents saving any field.
   Simulate a failed save and check that the form keeps all edits.
4. Edit a disclaimer while chat is open, then reload chat and check that the new text appears.
5. Leave chat open for over 30 seconds. Check that only the existing active-tenant poll recurs, without
   disclaimer requests.
6. After recreating OpenWebUI, reload a browser that accessed it before the upgrade and check that the
   footer appears.
