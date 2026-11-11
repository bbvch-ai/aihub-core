# Open WebUI runtime mod packages

## Context

AI Hub needs tenant-specific chat controls and backend changes while retaining Open WebUI's native Svelte state,
authentication and administration. SysAdmins need to install custom packages without rebuilding the image for every
change. Private upstream interfaces can change between releases.

## Decision Drivers

- Keep upstream source pristine and isolate version-dependent integration in a checked host adapter.
- Allow runtime installation of frontend and backend packages by trusted SysAdmins.
- Reuse tenant metadata, authorization, MongoDB, private S3 storage and the existing deployment.
- Preserve native behavior, isolate failures where possible and keep rollback explicit.

## Decision

Build a generic host into AI Hub's derived Open WebUI image from a pinned upstream source commit. It instruments
native Svelte component usages, exposes the shared runtime/stores, dispatches native chat hooks, and installs stable
Python callable dispatchers before upstream imports. Mods declare targets through generated catalogs; they do not
require an individual image build or a maintained Python registry.

Use the supported SvelteKit client initialization hook for authenticated embedded startup. Optional bootstrap and
frontend entries share lifecycle context but compile separately; a named script runner defines their capabilities,
ordering and deadlines. Bootstrap runs before native layout/i18n without importing the native runtime. Normal frontend
activation follows native user initialization. A bootstrap that missed startup requires a reload.

Route native API calls through the existing request bridge. Mods register lifecycle-owned Request/Response middleware
to handle, rewrite or wrap requests; components can import the same fetch function. Keep host control and asset traffic
outside the chain. Request middleware does not replace backend authorization, replay failures or patch global fetch.

Use immutable source ZIPs and host-compatible publications. SysAdmin sends stored source to the running host's
compiler, which validates and compiles without executing uploaded code. Source/publication archives stay in private
S3 storage, with catalog metadata in MongoDB. Tenant metadata holds versioned selections and settings. Bundled mods
follow the installed AI Hub source; custom selections retain their publication. Operator defaults name bundled IDs
and apply only until a tenant saves its configuration.

Authorize native users and current tenant selections independently of browser view identifiers. Frontend assets
require current publication access; backend source is not exposed to browsers. New backend operations resolve
current selections, while admitted work retains its handlers/settings. Mounted frontend components remain until
reload, with a notice when configuration changes. Authors must support older open frontends when changing APIs/events.

Keep global backend activation separate from tenant selections. Ordinary callable changes apply to new work without
restarting; startup effects require an explicit Open WebUI restart. Persist global inputs on the Open WebUI data
volume so startup does not depend on AI Hub APIs. Initialize bundled publications through a separate job, preserving
saved selections and avoiding a cycle with native Function registration and API startup.

## Consequences

SysAdmins can publish and configure mods at runtime. Ordinary AI Hub releases reuse a compatible host image;
Open WebUI/host upgrades require a new image and compatible publications. Private component/callable contracts,
Svelte internals and unknown caches may need adapter changes despite successful syntax/fingerprint checks.

Mods are trusted application code, not sandboxed tenant code. Request/run contexts separate settings and state;
module globals and arbitrary side effects do not become tenant-local or automatically reversible. Startup failures
can require operator recovery. Backups must include tenant/catalog data, private archives and global startup files.
Native settings and Functions remain appropriate when they already provide the required behavior.

See [Writing Open WebUI mods](../../docs/3_sdk/6_feature_overview/1_openwebui_mods/index.en.md) for the contract and
[deployment and maintenance](../../../infra/deployment/openwebui.md) for upgrade and recovery duties.
