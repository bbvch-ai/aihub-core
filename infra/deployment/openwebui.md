# Open WebUI deployment and maintenance

AI Hub's derived Open WebUI image contains the mod compiler and runtime host. System administrators upload and
publish mods through SysAdmin; ordinary mod changes need no image build. See the
[administrator guide](../../docs/docs/2_platform/10_chat_ui/16_openwebui_mods/index.en.md) for activation and disclaimer
settings, and the [author guide](../../docs/docs/3_sdk/6_feature_overview/1_openwebui_mods/index.en.md) for the package contract.

## Deploy and initialize

Use the matching Open WebUI host, main API, SysAdmin API and frontends from the release. Compose starts the
`openwebui-mods-init` job after its dependencies. It reuses compatible bundled publications, compiles missing ones
through the SysAdmin publishing API, verifies them, and reconciles selected global built-ins. Check that the job
finishes successfully before opening chat to users; it can be rerun after a failure. Runtime requests do not compile
missing publications. Native Function registration remains in `openwebui-init` so API startup does not depend on mod
publication.

Compose mounts the generated loader at `/app/build/static/loader.js`, the stylesheet at
`/app/build/static/custom.css`, and parent-origin configuration at `/app/build/static/aihub-disclaimer.json`.
Custom deployments need those mounts and an exact AI Hub `parentOrigin`, without a path or trailing slash. Inline
Compose configs require Compose 2.23.1 or newer. Change files under `infra/deployment/templates/` and run
`make generate-compose`; generated files under `infra/configs/` are not source files.

The native host verifies its Open WebUI user and forwards the signed identity to AI Hub for tenant authorization.
The iframe bridge validates the parent origin and window; frontend mods load only in the AI Hub embed. The existing
SCIM credential protects publishing/global control, and service credentials stay on the backend. Tenant settings are
browser-visible and must not contain secrets.

## Deployment defaults

`OPENWEBUI_MODS_DEFAULTS` is a JSON array of bundled mod IDs, passed identically to the main API and SysAdmin API.
The shipped `.env.dev` and `.env.prod` set it to `["aihub-chat-disclaimer"]`. Unset or `[]` enables no defaults.
Unknown or duplicate IDs are rejected. After changing it, update/restart both API services; no Open WebUI rebuild is
needed.

Bundled packages are discovered from Core's `infrastructure/openwebui/mods/bundled/*/mod.json`. Initial settings come
from their manifests. Any saved tenant configuration, including an empty list, overrides deployment defaults.
Uploaded mods, their publication selections and settings are managed later through SysAdmin and stored in the database.

## Builds and upgrades

| Change | Required work |
| --- | --- |
| Add or edit a custom mod | Upload, publish for the running host, select the version and save. No image build. |
| Change tenant enablement/settings | Save. New backend operations use the change; open chats offer reload. |
| Ordinary AI Hub update | Run initialization for changed bundled sources. Saved settings/enablement and custom selections remain intact. Reuse the compatible host image. |
| Open WebUI or host adapter update | Build the derived image, check compatibility and behavior, then publish compatible custom mods and select them. |

`make -C infra/deployment build-openwebui-image` builds the tag from `compose-config.yml` locally.
`build-and-push-openwebui-image` also publishes it to the registry. Deployments using registry images need that tag
available before pulling it.

For a host upgrade, keep the upstream base image, pristine source commit and Svelte/Python versions aligned with
`docker/open-webui/mods/compatibility.json`. Bump `host_protocol` for incompatible host/publication contract changes.
The Dockerfile runs compiler/component, native backend and authenticated entrypoint checks. Recheck private component
contracts, callable signatures/decorators, request instrumentation and the startup entrypoint against the new source;
source fingerprints detect drift but do not prove unchanged behavior.

Run the host's [test instructions](docker/open-webui/mods/README.md#verification) and exercise the deployed combination:
login, tenant switching, both chat layouts, shared stores/context, native settings/admin access, mod failure/cleanup,
new and multi-model chats, regeneration and cancellation. For full-stack mods, also check an older open tab against a
new backend publication. Recheck the compatibility workarounds below. A mod rollback does not undo upstream database
migrations.

## Global changes and recovery

Ordinary global callable changes reach workers without restarting. Startup changes remain pending until SysAdmin
confirms Restart to apply saved changes. The control signals the standard Uvicorn PID 1 after responding; Docker's
`restart: always` policy restarts the container. This supports the supplied single-container deployment, including
multiple workers, not coordinated restarts across multiple Open WebUI replicas. Active chats/jobs may be interrupted.

A confirmed restart freezes the saved global version until the next boot. If delivery is interrupted, retry the same
confirmed version after checking status and logs. Do not interpret a timeout as successful recovery. If a startup mod
prevents Open WebUI from becoming usable, stop the container, restore known-good global data with its matching host
image, and restart through deployment tooling. Verify worker readiness and a chat before returning it to service.

## Persistence and backups

Back up these together:

- Tenant metadata, including saved mod selections/settings, and the MongoDB mod revision/publication collections.
- The private S3 `openwebui-mods` bucket, containing source and compiled archives.
- Open WebUI's `DATA_DIR/aihub-mods/`, containing global configuration and archives required during startup.

Include the bucket and directory explicitly; the database backup handlers do not cover them. Restore with Open WebUI
stopped and a compatible host image. Retain previous archives and known-good configuration for rollback. Boot markers
and worker heartbeat files are derived state, not proof that the restored workers are ready.

## Compatibility workarounds

These customizations live outside runtime mod packages and need checking when Open WebUI changes:

| Customization | Source and upgrade check |
| --- | --- |
| Locale correction | `templates/openwebui-disclaimer/loader.js` replaces unsupported saved locale codes with `en-US` before native startup, preserving French fallback. Check its locale list against upstream and run `e2e/disclaimer/locale.spec.ts`. |
| Speech failure fallback | The loader substitutes a silent clip for failed speech requests and shows a status message so voice calls can resume listening. Check `/api/v1/audio/speech` and the overlay status selector with a failing TTS service. |
| Multi-model PDF guard | The loader disables PDF download for chats with side-by-side model turns; text/JSON export remains available. Run `e2e/disclaimer/pdf-export.spec.ts`. Remove the guard once native PDF export retains all answers. |
| Streaming indicator | `templates/openwebui-style/custom.css` replaces the pulsing bar with typing dots and hides it during other progress. Check its selectors and reduced-motion behavior. |

The bundled disclaimer uses its own composer selectors in Core's `mods/bundled/chat-disclaimer/frontend.js`.
After an upgrade, check both native chat layouts, wrapping and populated native footers with
`e2e/disclaimer/openwebui.spec.ts`. Save translations through SysAdmin and verify locale changes, tenant isolation,
disable/re-enable and a fresh chat load.
