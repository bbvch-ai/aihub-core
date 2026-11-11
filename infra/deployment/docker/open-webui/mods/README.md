# Open WebUI mod host

This directory supplies the compiler, Svelte component adapter and native Python runtime used by AI Hub's derived
Open WebUI image. Mod authors use the [package guide](../../../../../docs/docs/3_sdk/6_feature_overview/1_openwebui_mods/index.en.md);
operators use the [deployment guide](../../../openwebui.md).

## Integration boundaries

`host_plugin.mjs` instruments native component usages and emits the catalog/shared runtime. `request_plugin.mjs`
adds request context and completion readiness to the pinned frontend. `component_boundary.mjs` uses Svelte internals
to restore originals after rendering failures. These adapters require checks against each upstream/Svelte upgrade.

`backend/main.py` installs callable dispatch before upstream imports and retains native routes, dependencies,
exception handlers and lifespan. `patch_startup.py` changes the checked ASGI entrypoint in upstream `start.sh`.
The native Function in `infra/deployment/templates/openwebui_functions/aihub_mods.py` dispatches chat hooks. Lazy callable targets bind
when their modules import; publication records their source fingerprints.

Native verified-user authentication and AI Hub authorization determine tenant selections. Each asset request
reauthorizes the currently selected publication, including cache hits. Browser view nonces correlate modules/events;
they do not grant access or select backend code. Backend source has no browser delivery route. Keep the main API's
service-token/signed-identity checks distinct from ordinary browser authentication.

`compiler_cli.mjs` is bundled into the image and runs through Playwright's Node runtime. Compilation has a shared
worker lock, a 256 MiB JavaScript heap limit and a 60-second timeout; cancellation reaps the subprocess. Uploaded code
is not executed during compilation. `backend/initialize.py` prepares bundled publications through SysAdmin without
rewriting tenant settings, and reconciles global built-ins.

## Verification

The parent Dockerfile runs JavaScript and Python checks in the pinned upstream environment. In a prepared upstream
checkout with this directory copied to `aihub-mods/`, run:

```sh
node --conditions=browser --test aihub-mods/tests/*.test.mjs
```

Native tests require the pinned Open WebUI installation and `aihub_mods` on `PYTHONPATH`. The Dockerfile also runs
`tests/native_backend_acceptance.py` in a fresh authenticated interpreter with an in-memory Hub transport.

On a disposable derived host, set `OPENWEBUI_MODS_CONTROL_TOKEN` to its SCIM credential before running the
component browser check:

```sh
OPENWEBUI_MODS_URL=http://localhost:18081 pnpm -C e2e exec playwright test component-boundary.spec.ts --config openwebui-mods/playwright.config.ts
```

The component tests cover shared state, bindings, slots, events, cleanup and restoration. Also validate the actual
package with the complete AI Hub login/publishing flow; fixture tests alone do not establish deployment acceptance.
