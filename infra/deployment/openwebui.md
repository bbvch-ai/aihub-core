# Open WebUI deployment and maintenance

AI Hub's derived Open WebUI image contains the mod compiler and runtime host. System administrators upload and
install mods through SysAdmin; ordinary mod changes need no image build. See the
[administrator guide](../../docs/docs/2_platform/10_chat_ui/16_openwebui_mods/index.en.md) for activation and disclaimer
settings, and the [author guide](../../docs/docs/3_sdk/6_feature_overview/1_openwebui_mods/index.en.md) for the package contract.

## Deploy and initialize

Use the matching Open WebUI host, main API, SysAdmin API and frontends from the release. Compose starts the
`openwebui-mods-init` job after its dependencies. It reuses compatible bundled publications, compiles missing ones
through the SysAdmin installation API, and reconciles installed packages selected globally. Check that the job
finishes successfully before opening chat to users; it can be rerun after a failure. Runtime requests do not compile
missing publications. Native Function registration remains in `openwebui-init` so API startup does not depend on mod
publication.

Compose mounts parent-origin configuration at `/app/build/static/aihub-mods.json`. The image installs the client
startup hook; custom deployments need this configuration and an exact AI Hub `parentOrigin`, without a path or trailing slash. Inline
Compose configs require Compose 2.23.1 or newer. Change files under `infra/deployment/templates/` and run
`make generate-compose`; generated files under `infra/configs/` are not source files.

The native host verifies its Open WebUI user and forwards the signed identity to AI Hub for tenant authorization.
The iframe bridge validates the parent origin and window; frontend mods load only in the AI Hub embed. The existing
SCIM credential protects compilation/global control, and service credentials stay on the backend. Tenant settings are
browser-visible and must not contain secrets.

## Deployment defaults

`OPENWEBUI_MODS_DEFAULTS` is a JSON array of bundled mod IDs, passed identically to the main API and SysAdmin API.
The shipped `.env.dev` and `.env.prod` enable `aihub-chat-disclaimer`, `aihub-locale-recovery`,
`aihub-speech-recovery`, `aihub-pdf-export-guard` and `aihub-streaming-indicator`. Unset or `[]` enables no defaults.
Unknown or duplicate IDs are rejected. After changing it, update/restart both API services; no Open WebUI rebuild is
needed.

Bundled packages are discovered from Core's `infrastructure/openwebui/mods/bundled/*/mod.json`. Initial settings come
from their manifests. Any saved tenant configuration, including an empty list, overrides deployment defaults.
Uploaded packages and tenant settings are managed later through SysAdmin. One installed record per ID is stored in
MongoDB; saved selections contain only enablement and settings.

## Builds and upgrades

| Change | Required work |
| --- | --- |
| Add or edit a custom mod | Upload and confirm installation/replacement. Enable new mods and save settings. No image build. |
| Change tenant enablement/settings | Save. New backend operations use the change; open chats offer reload. |
| Ordinary AI Hub update | Run initialization for changed bundled sources. Saved settings/enablement and custom selections remain intact. Reuse the compatible host image. |
| Open WebUI or host adapter update | Build the derived image, check compatibility and behavior, then reinstall compatible custom mods. |

`make -C infra/deployment build-openwebui-image` builds the tag from `compose-config.yml` locally.
`build-and-push-openwebui-image` also publishes it to the registry. Deployments using registry images need that tag
available before pulling it.

For a host upgrade, keep the upstream base image, pristine source commit and Svelte/Python versions aligned with
`docker/open-webui/mods/compatibility.json`. Once the contract is released, bump `host_protocol` for incompatible host/publication contract changes.
The Dockerfile runs compiler/component, native backend and authenticated entrypoint checks. Recheck private component
contracts, callable signatures/decorators, request instrumentation and the startup entrypoint against the new source;
source fingerprints detect drift but do not prove unchanged behavior.

Run the host's [test instructions](docker/open-webui/mods/README.md#verification) and exercise the deployed combination:
login, tenant switching, both chat layouts, shared stores/context, native settings/admin access, mod failure/cleanup,
new and multi-model chats, regeneration and cancellation. For full-stack mods, also check an older open tab against a
new backend publication. Recheck the compatibility workarounds below. A mod rollback does not undo upstream database
migrations.

Package replacement changes the installed code for every scope using its ID, without rewriting settings. Failed
validation/compilation leaves the old record intact. Obsolete central archives are pruned after installation; save
source ZIPs outside the platform if rollback is needed. Global host archives keep boot, live and pending selections,
then prune unreferenced files on saves/startup. There is no session draining; schedule changes accordingly. Loaded
Python packages remain in worker memory until shutdown.

## Global changes and recovery

Ordinary global callable changes reach workers without restarting. While startup changes are pending, all saved
global changes wait until SysAdmin confirms Restart to apply saved changes. The control signals the standard Uvicorn PID 1 after responding; Docker's
`restart: always` policy restarts the container. This supports the supplied single-container deployment, including
multiple workers, not coordinated restarts across multiple Open WebUI replicas. Active chats/jobs may be interrupted.

A confirmed restart freezes the saved global version until the next boot. If delivery is interrupted, retry the same
confirmed version after checking status and logs. Do not interpret a timeout as successful recovery. If a startup mod
prevents Open WebUI from becoming usable, stop the container, restore known-good global data with its matching host
image, and restart through deployment tooling. Verify worker readiness and a chat before returning it to service.

## Persistence and backups

Back up these together:

- Tenant metadata, including saved mod selections/settings, and the MongoDB `openwebui_mods` collection.
- The private S3 `openwebui-mods` bucket, containing source and compiled archives.
- Open WebUI's `DATA_DIR/aihub-mods/`, containing global configuration and archives required during startup.

Include the bucket and directory explicitly; the database backup handlers do not cover them. Restore with Open WebUI
stopped and a compatible host image. Retain previous archives and known-good configuration for rollback. Boot markers
and worker heartbeat files are derived state, not proof that the restored workers are ready.

## Bundled customizations

These packages live in Core's `infrastructure/openwebui/mods/bundled/` and use the same installation and lifecycle as
uploaded mods. Check their upstream dependencies when upgrading Open WebUI:

| Package | Upgrade check |
| --- | --- |
| `locale-recovery` | Bootstrap repairs unsupported saved locales before native i18n. Compare `locales.json` with upstream `src/lib/i18n/locales/languages.json`; preserve shipped codes and French fallback. |
| `speech-recovery` | A request handler supplies a silent clip only for failed voice-mode speech requests. The native CallOverlay wrapper displays the localized status. Check its props/events and that a failing TTS service returns the call to listening. |
| `pdf-export-guard` | Native menu wrappers share the selected chat's export policy through Svelte context. Check toolbar and sidebar menus, including a sidebar chat different from the open one. Single-model PDF and text/JSON export must work. Remove the guard once upstream PDF retains all side-by-side answers. |
| `streaming-indicator` | A lifecycle-owned stylesheet replaces the pulsing bar with dots. Check response selectors, competing progress, reduced motion and disposal. |
| `chat-disclaimer` | A lifecycle-owned renderer adds text below the composer. Check both chat layouts, wrapping, populated native footers, locale changes and disposal. |
| `account-menu` | Optional Admin Panel shortcut and Settings restrictions. Check the native sidebar, allowed admin tabs and About, empty section headings, and blocked settings entry points for ordinary users. |

The [customization browser suite](../../e2e/openwebui-mods/customizations/README.md) uses an authenticated disposable
native host and the actual bundled archives. Also verify the real AI Hub login, installation, tenant switching and
settings flow before release.
