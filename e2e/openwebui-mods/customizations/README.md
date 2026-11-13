# Bundled customization browser checks

Use a locally built AI Hub Open WebUI image. This fixture retains native authentication, routes, Svelte and the mod
host. It compiles the actual bundled packages; only the AI Hub service transport and model/audio responses are fixtures.
It creates a disposable native user and chat data. No production identity provider, model or tenant service is used.

```sh
export OPENWEBUI_MODS_TEST_IMAGE='your-local-derived-image:tag'
docker compose -f e2e/openwebui-mods/customizations/compose.yml up -d --wait
pnpm -C e2e exec playwright test --config openwebui-mods/customizations/playwright.config.ts
docker compose -f e2e/openwebui-mods/customizations/compose.yml down
```

The fixture binds Open WebUI to `127.0.0.1:18081`; Playwright serves its trusted parent at `127.0.0.1:18082`.
No persistent volume is used. The test-only credentials endpoint requires the disposable SCIM token and is never
part of the deployment image. Set `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` if using an existing Chromium installation.

The suite checks locale correction before native settings, real toolbar/sidebar PDF entries and a single-model
PDF download, failed voice playback returning to listening, streaming styles and lifecycle cleanup. Admin shortcut checks
use separate native admin and regular-user sessions: only admins see the direct Admin Panel link, and account details
are absent. They verify native search and saving with the allowed admin tabs and About. Authentication, Connections
and Database are excluded; empty section headings disappear while populated headings remain. Regular users cannot
open Settings through shortcuts, commands or direct links. Tests retain
unrelated shortcuts, slash commands and terminal selection while hiding personal-terminal configuration. They also
cover native sidebar styling, role changes, mobile navigation and restoring native behavior on disposal or in standalone
Open WebUI. Renderer checks
also exercise disclaimer wrapping, navigation, translations, invalid settings and disposal against native markup.
The renderer checks deliberately bypass the host to isolate that DOM contract; the other tests use actual publications.

For an already running equivalent fixture, override `OPENWEBUI_MODS_URL`, `OPENWEBUI_MODS_TEST_PARENT` and
`OPENWEBUI_MODS_CONTROL_TOKEN` and set the server's `TEST_PARENT_ORIGIN` to the same parent origin. This suite must never
point at a production host. Full AI Hub login, installation and deployment acceptance remain separate checks.
