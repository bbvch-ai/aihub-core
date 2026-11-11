---
title: Writing Open WebUI mods
---

# Writing Open WebUI mods

An **Open WebUI mod** is a source ZIP that a system administrator uploads and publishes through
[Open WebUI settings](../../../2_platform/10_chat_ui/16_openwebui_mods/). It can contain Svelte components,
JavaScript or TypeScript, Python and local assets. Use Open WebUI's native settings or Functions when they already
provide the behavior you need.

Mods use the running host's Svelte runtime and Python environment. Publication compiles against that host without
installing dependencies or executing uploaded code. It checks syntax, frontend imports and declared targets, but does not prove
runtime correctness or perform semantic TypeScript checking. Check types in your authoring project and test the
published mod on a matching disposable host.

## Package the source

Place `mod.json` at the ZIP root, alongside the files it references. The
[manifest model](https://github.com/bbvch-ai/aihub-core/blob/main/packages/core/swiss_ai_hub/core/infrastructure/openwebui/mods/openwebui_mod_manifest.py)
defines the accepted fields and validation. The supplied
[chat disclaimer package](https://github.com/bbvch-ai/aihub-core/tree/main/packages/core/swiss_ai_hub/core/infrastructure/openwebui/mods/bundled/chat-disclaimer)
is a small frontend example with settings, locale changes and cleanup.

| Manifest field | Purpose |
| --- | --- |
| `format`, `id`, `name`, `version` | Required metadata. Format is `1`; the stable ID uses lowercase letters, digits and hyphens. Version is an author label, not the archive identity. |
| `description` | Optional explanation shown in the catalog. |
| `bootstrap` | Optional `.js`, `.mjs` or `.ts` entry exporting `activate(context)`, awaited before native layout initialization. |
| `frontend` | Optional `.js`, `.mjs` or `.ts` entry exporting `activate(context)`. |
| `replacements` | Maps native `src/.../*.svelte` component IDs to package `.svelte` files. |
| `backend` | Optional `.py` entry exporting chat hooks, override handlers or a private HTTP handler. |
| `backend_overrides` | Maps native `open_webui.module:Class.method` or `open_webui.module:function` targets to handler names exported by the backend entry. |
| `backend_restart_required` | Marks import/startup effects that require global activation and a restart. Requires a backend entry. |
| `default_settings` | Initial JSON settings offered when a mod is added. Saving settings replaces this object; upgrades do not merge new defaults into saved settings. |
| `settings_fields` | Optional field definitions: controls, translated labels/help, choices and validation properties. |

At least one bootstrap entry, frontend entry, replacement or backend entry is required. Paths are relative to the archive root;
absolute paths, traversal, symlinks and duplicate entries are rejected. A source ZIP is limited to 16 MiB compressed,
32 MiB expanded, 512 entries and a 64 KiB manifest. Settings allow 16 KiB per mod; a tenant selection allows 64 mods
and 64 KiB in total.

Source and publication revisions identify exact archive bytes by SHA-256. Repacking identical source can create a new
revision. Publishing records the source revision, host compatibility and native target fingerprints. Uploading and
publishing do not activate code; an administrator selects and saves the publication separately. There is no archive
deletion interface; keep prior revisions for rollback.

## Settings controls

Put initial values in `default_settings`. SysAdmin infers these controls:

| Default value | FormKit control |
| --- | --- |
| String | `primeInputText` |
| Number | `primeInputNumber` |
| Boolean | `primeToggleSwitch` |
| Language object such as `{"en": "Hello", "de": "Hallo"}` | `localeInput` |
| List of strings, including `[]` | `chipsInput` |
| Object | `group` |
| Nonempty list of objects | `repeater`, using the first row's fields |
| `null` | `primeInputText` with an enable toggle |

Add `settings_fields` where you need a different control or extra properties. For example, these entries in `mod.json`
add a dropdown and a multiline text field. The `notice` translations use the inferred language editor:

```json
{
  "default_settings": {
    "style": "concise",
    "message": "",
    "notice": { "en": "Check the answer.", "de": "Prüfen Sie die Antwort." }
  },
  "settings_fields": {
    "style": { "options": ["concise", "detailed"] },
    "message": {
      "control": "primeTextarea",
      "label": { "en": "Message", "de": "Nachricht" },
      "rows": 4
    }
  }
}
```

`options` implies a dropdown; `control` selects another existing input. Labels and help text follow the administrator's
UI language. A multilingual setting such as `notice` stores the translations that the mod uses.

Use the properties of the existing [form elements](https://github.com/bbvch-ai/aihub-core/tree/main/packages/core/swiss_ai_hub/core/form/elements),
including `required`, bounds and `help`. For translated dropdown choices, supply objects with a translated `label` and
a stable `value`, and set `optionLabel` to `label` and `optionValue` to `value`.

Group/repeater `children` are field definitions with a `name`. For an empty object list, specify `control: "repeater"`
and its `children`; repeaters cannot contain other repeaters. Keep defaults in `default_settings`. Field names match
`[A-Za-z][A-Za-z0-9_]*`; `slots`, `constructor` and `prototype` are reserved. Field definitions are limited to 16 KiB.
Invalid definitions fail upload with a field error; mod code does not run during this check.

For uploaded mods, select a published version before editing settings; its source revision supplies the form.
Tenant and global settings support the same controls. Secret inputs, tenant/model/agent/knowledge pickers and automatic
translation are unavailable here. Supply choices in the package. Mods must validate the settings they consume;
form validation only assists editing.

Saved values without a matching editor are retained. Newly introduced defaults appear in the form and take effect
when the administrator saves. Opening settings or upgrading alone does not change the runtime configuration.

## Add or replace components

Read the running host's component catalog through SysAdmin's `GET /api/v1/admin/openwebui-mods/host`. Use its source
IDs as replacement keys. The replacement receives the native component's props, bindings and slots; it must preserve
the contract needed by its callers. Two enabled mods cannot replace the same component.

New child components are ordinary Svelte imports inside the package. To extend a native component, import
`getOriginalComponent` from `@aihub/mods`, obtain the original by its catalog ID, and compose it with your new children.
This avoids replacing your own reference recursively. A child rendered in the existing tree participates in Svelte's
reactivity and context. A separately mounted component does not automatically inherit that context.

Import Open WebUI stores from `@openwebui/stores` (`$lib/stores` is also accepted). Shared modules include `svelte`,
`svelte/store`, `svelte/transition`, `svelte/motion`, `svelte/easing`, `svelte/reactivity`, `svelte/events` and
`svelte/animate`. Use the host's versions, not another bundled Svelte runtime. Native store names and component
contracts can change with Open WebUI upgrades.

Replacement covers instrumented source component usages. It does not expose private lexical state, turn inline markup
into a component, or automatically intercept imperative mounts and third-party component internals. Those cases need
an adapter for the pinned Open WebUI version. Replacing an instance resets its private state.

### Imports and assets

Use explicit relative filenames for package imports, re-exports and literal dynamic imports. The compiler supports
Svelte files, TypeScript, JavaScript and `.svelte.ts`/`.svelte.js` runes modules. JSON imports provide a default value;
other asset imports provide a default URL. Literal `new URL('./asset', import.meta.url)` references are included.

Only reachable frontend files are published to browsers. Other bare imports, query imports such as `?raw`, computed
dynamic imports, import attributes/options and asset side-effect imports are rejected. Relative CSS `url(...)`
references are unsupported; use an imported asset URL in a style attribute. Backend dependencies must already be
installed in the host. No npm or pip installation runs for a mod.

## Own the frontend lifecycle

Both script entries are optional and export `activate(context)`. Each may return a cleanup function or a promise of one.
`bootstrap` runs before native root-layout initialization, including i18n; `frontend` runs after the native user store
is populated. Replacements are installed after frontend activation succeeds. Both entries receive the same context,
which supplies `id` (view nonce), `tenantId`, `modId`,
`publication`, deeply frozen `settings` and an abort `signal`.

Use bootstrap for small changes that must precede native initialization. Its imports must remain within the package:
JavaScript, TypeScript, JSON and assets are supported; Svelte components, rune modules and native-runtime imports are
not. Do not wait for native application state or UI, since startup awaits bootstrap. The bootstrap script batch has
a 15-second deadline; a failure disables the affected mod. The host cannot interrupt arbitrary JavaScript or undo
unregistered side effects. Bootstrap precedes the native layout, but not inline theme scripts or all framework code.

Bootstrap and frontend have separate compiled dependency graphs, so module-local variables are not shared between
them. Use the common context for identity and settings. A bootstrap-only package needs no frontend entry. A bootstrap
that missed startup requires a reload; it is never run late against the initialized application.

| Context member | Use |
| --- | --- |
| `onDispose(cleanup)` | Register cleanup before awaiting work; remove listeners, observers and mounts you own. |
| `locale`, `onLocale(callback)` | Read the AI Hub locale and subscribe to it. Subscription calls back immediately, returns an unsubscribe function and is removed on mod disposal. |
| `onEvent(callback)` | Receive this mod's scoped backend events; returns an unsubscribe function. |
| `onRequest(handler)` | Handle native API requests through an ordered Request/Response chain; returns an unsubscribe function. |
| `api(path, options)` | Fetch this mod's private backend endpoint. Returns a `Response` and aborts on disposal. |

Export a package-local store from the frontend entry when replacement components need its settings. Keep side effects
inside activation or Svelte lifecycle hooks, and respect the abort signal after asynchronous work. Tenant changes,
sign-out and leaving the embedded chat dispose the view. Navigation within Open WebUI keeps it. Frontend mods activate
only inside the trusted AI Hub embed.

Import, activation and component-rendering failures dispose the affected mod; native components are restored.
The rendering boundary does not catch every event-handler or asynchronous exception. JavaScript module evaluation and
arbitrary global patches cannot be unloaded automatically.

## Handle native frontend requests

Register `context.onRequest(async (request, next) => response)` during activation. Return a `Response` to handle a
request yourself, call `next()` to pass it on, or call `next(new Request(...))` to rewrite it. You can also inspect or
replace the returned response. The first configured mod is the outermost handler; registrations within a mod run in
registration order. Registration returns an unsubscribe function and is removed automatically on mod disposal.

```js
export function activate(context) {
  context.onRequest((request, next) => {
    const url = new URL(request.url);
    if (url.origin === location.origin && url.pathname === '/api/example') {
      return Response.json({ message: 'Handled by the mod' });
    }
    return next();
  });
}
```

The chain covers native calls through `src/lib/apis/` and `fetch` imported from `@aihub/mods`. It does not intercept
ordinary global `fetch`, host configuration/assets, or `context.api`. Use `next` inside a handler to avoid recursively
entering the chain. Native completion calls wait for frontend activation; other calls use handlers registered at that
moment. Bootstrap can register handlers before native initialization without importing the shared runtime.

Requests retain caller/view cancellation, including rewritten requests. Respect `request.signal` in your own work;
the host cannot interrupt an arbitrary pending promise. A thrown error fails that request; the host never silently
retries or replays it. Handler failures do not automatically disable the mod. Matching, body cloning and any deliberate
retry policy belong to the handler. This is browser behavior, not an authorization boundary: backend authentication
and authorization still apply.

## Handle backend work

The backend entry may export `class Filter` with optional async `inlet`, `request`, `stream` and `outlet` methods.
Each accepts `(value, context)` and returns the modified dictionary; `stream` may return `None` to omit a chunk.
These are native chat lifecycle hooks, not startup or arbitrary HTTP hooks. Each execution receives a fresh Filter
instance and copied settings. The native request, user, metadata, model and execution identifiers are available on
the context; see `ModRunContext` in the host's `backend/mod_run_context.py`.

`await context.emit(type, data)` sends JSON to the paired frontend's `onEvent` callback. Event names allow 128
characters; the complete envelope is limited to 64 KiB. Delivery checks the view, tenant, mod, chat, assistant message,
execution and native task. Task completion/cancellation closes emission. Standalone backend execution has no frontend
recipient. Hook errors follow Open WebUI's handling; stream/outlet hooks are not a universal enforcement boundary.

Relative Python imports and assets located through `__file__` work. Modules are cached per worker until shutdown.
Do not keep tenant data in module globals or assume arbitrary import-time effects will be undone on disablement.

### Override native callables

Use the host's callable catalog to choose `backend_overrides` targets. Export handlers with the positional-only
signature `(next, context, /, *args, **kwargs)` and match the native sync, async or generator behavior. A handler can
change arguments or results, reject a call, or call `next` to continue the chain. Tenant handlers wrap global handlers,
which wrap the native callable. Errors propagate without retrying the original operation.

Tenant contexts provide the verified user, tenant, request, copied settings and mutable per-request `state`.
The import adapter binds lazy targets when their native modules load; mods need no polling or waiting lifecycle.
Source fingerprints detect target changes, but cannot verify that an upstream signature or behavior still means the
same thing. Test each overridden path, including its decorators and caches.

Nested closures, descriptors, native extension code, custom loaders and shared mutable state may need explicit host
adapters. Recognized outer `cache`, `lru_cache` and `aiocache.cached` decorators are bypassed during overridden work;
manual caches and other decorators are not made tenant-local. Unscoped non-chat requests, WebSockets and unrelated
jobs do not automatically acquire tenant context.

### Provide a private API

Export `async handle(request, context)` from the backend entry. Frontend `context.api(path, options)` calls
`/_aihub/mods/tenants/{tenant_id}/mods/{mod_id}/api/{path}`. `context.path` is the path suffix; the context also provides
request state, identity and settings. Return JSON-compatible data or a native response, including a stream.
Native HTTP errors retain their status and details.

The server selects the currently enabled backend by mod ID. A browser cannot request an old backend revision.
Keep private APIs and event payloads compatible with older open frontend views: saves change new backend operations,
while a mounted frontend remains until reload. In-flight requests, streams and inherited native tasks keep their
prepared handlers and settings. Delayed imports from a replaced or disabled frontend publication may require reload.

## Global and startup behavior

Global activation supports backend callable overrides and packages declaring `backend_restart_required`.
Frontend replacements and chat Filter hooks still require tenant activation. Global contexts expose `scope='global'`,
`app`, settings and request state, with an HTTP request when available; they do not assert a tenant or user.

An `open_webui.main:lifespan` override always requires global activation and a restart. Return an async context
manager, enter `next(...)` to preserve native startup, yield its state and clean up owned work on exit. Lifespan runs
in every worker; jobs that must run once need their own coordination. Upstream imports have already run when global
packages load, so changing behavior consumed during those imports needs an explicit host adapter.

## Validate and maintain a mod

Test publication, enablement, settings, disablement and rollback on the pinned host. For frontend mods, check both
chat layouts, navigation, shared state and cleanup. For backend mods, check concurrent tenants, cancellation, streams
and any standalone/global paths used by the mod. Include failure cases and verify that native behavior remains usable.

After a host upgrade, publish a compatible version and inspect changed targets before selecting it. Compilation
warnings remain attached to the publication. Source definitions are in the
[host directory](https://github.com/bbvch-ai/aihub-core/tree/main/infra/deployment/docker/open-webui/mods);
the [deployment guide](https://github.com/bbvch-ai/aihub-core/blob/main/infra/deployment/openwebui.md)
describes host builds, initialization, backups and recovery.
