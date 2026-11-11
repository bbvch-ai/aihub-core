# Open WebUI mod host

This directory supplies the compiler, Svelte component adapter and native Python runtime used by AI Hub's derived
Open WebUI image. Mod authors use the [package guide](../../../../../docs/docs/3_sdk/6_feature_overview/1_openwebui_mods/index.en.md);
operators use the [deployment guide](../../../openwebui.md).

## Where to make changes

| Area | Entry points |
| --- | --- |
| Archive format, publication validation and built-in discovery | [Core mods](../../../../../packages/core/swiss_ai_hub/core/infrastructure/openwebui/mods/) |
| Upload, publish and tenant configuration | [SysAdmin routes](../../../../../packages/sysadmin-api/swiss_ai_hub/sysadmin_api/routes/openwebui_mods/) |
| Compilation and supported imports | [compiler.mjs](compiler.mjs) |
| Native component replacements and shared state | [host_plugin.mjs](host_plugin.mjs), [component_plugin.mjs](component_plugin.mjs), [component_boundary.mjs](component_boundary.mjs) |
| Browser startup, activation and execution events | [host.mjs](host.mjs), [script_entries.mjs](script_entries.mjs), [lifecycle.mjs](lifecycle.mjs), [executions.mjs](executions.mjs) |
| Tenant backend loading and chat hooks | [mod_runtime.py](backend/mod_runtime.py), [mod_run.py](backend/mod_run.py), [backend_package.py](backend/backend_package.py) |
| Native callable overrides and lazy imports | [callable_registry.py](backend/callable_registry.py), [callable_imports.py](backend/callable_imports.py), [callable_transform.py](backend/callable_transform.py) |
| Global activation, persistence and restart | [global_mod_runtime.py](backend/global_mod_runtime.py), [global_mod_store.py](backend/global_mod_store.py), [global_mod_control.py](backend/global_mod_control.py) |

## Integration boundaries

`host_plugin.mjs` instruments native component usages and emits the catalog/shared runtime. `request_plugin.mjs`
adds request context and completion readiness to the pinned frontend. `component_boundary.mjs` uses Svelte internals
to restore originals after rendering failures. These adapters require checks against each upstream/Svelte upgrade.

`install_client_hook.mjs` installs the supported SvelteKit client `init` hook. It stops the build if an upstream hook
already exists or moves, so an upgrade cannot silently discard upstream startup behavior. The hook authenticates
tenant selection with the native cookie, runs `runScripts('bootstrap')`, then loads the shared runtime. Normal
activation runs `runScripts('frontend')` after the native user store is populated. `script_entries.mjs` defines each
entry's compiler capabilities, prerequisites and deadline. Adding an entry requires a manifest field, publication
validation and an actual host invocation; choosing a new name alone does not establish an injection point.

`context.onRequest(handler)` registers middleware on the existing native API bridge. Each handler receives a
standard `Request` and `next`, and returns a `Response`. Registration order follows the tenant's mod list; disposal
removes registrations. `@aihub/mods` exports `fetch` for components that need the same chain. Configuration, assets,
private mod APIs and ordinary global `fetch` stay outside this bridge. No second fetch patch is installed.

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
is not executed during compilation. TypeScript is transpiled with syntax diagnostics; semantic type checking is not
included. `backend/initialize.py` prepares bundled publications through SysAdmin without
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

The [bundled customization suite](../../../../../e2e/openwebui-mods/customizations/README.md) checks startup locale repair,
native voice recovery, PDF menus, streaming styles and disclaimer rendering against a disposable authenticated host.
