---
title: Open WebUI modifications
---

# Open WebUI modifications

**Open WebUI modifications**, or mods, let system administrators adapt the chat interface and its backend behavior.
A mod can add controls, replace a component or change how a request is handled. Custom mods are uploaded as source
ZIP files and prepared for the running Open WebUI instance without rebuilding its container.

## Choose mods for a tenant

In SysAdmin, open Tenants, choose a tenant, then open Open WebUI settings. The catalog is shared across tenants;
enablement and settings are saved separately for each tenant.

For a custom mod:

1. Choose Upload ZIP and upload the package supplied by its author.
2. Open Versions, select the source version, and choose Publish for this Open WebUI. Publishing checks and compiles
   the package; it does not activate it.
3. Choose Use this version, enable the mod, and edit the controls under Settings.
4. Save the tenant's settings.

Publishing requires a reachable, compatible Open WebUI mod host. Compilation errors appear in the version dialog.
If the package is already published for this host, select it without publishing again. Uploading a newer version
does not switch existing selections. To roll back, select an earlier compatible version and save.

Disabling a mod preserves its selected version and settings. Disable all followed by Save turns off the tenant's
mods. Failed saves retain your draft; if another administrator changed the configuration, review their saved settings
before retrying. Reload saved settings replaces your draft.

::: warning Trusted code and settings
Only system administrators can upload, publish and configure mods. Mods run with application capabilities in users'
browsers or inside Open WebUI; they are not sandboxed. Enable code you trust. Tenant settings are delivered to the
browser, so do not put passwords, tokens or other secrets in them.
:::

## When users see changes

Open chats keep their current interface until reloaded. They check for changes every 30 seconds and when users return
to the tab or reconnect, then offer a reload notice. Saving does not force a reload while someone is typing.
New backend operations use the saved configuration; requests already running retain their selected code and settings.

An import, activation or component-rendering failure disables the affected frontend mod and offers a reload notice.
Other mods can continue. Backend errors follow Open WebUI's normal error handling.

## Configure the chat disclaimer

The supplied Chat disclaimer mod displays a short note below the chat input. Open Settings, choose DE, EN, FR or IT
and edit the Disclaimer field. Each translation accepts plain text of up to 100 characters.
The note follows the AI Hub language, falling back to German and then the first nonempty translation. Invalid text
settings prevent this mod from activating. Disable the mod to hide the note.

The shipped deployment defaults enable Chat disclaimer. Operators can change which bundled mods start enabled;
once a tenant saves its own configuration, that saved configuration takes precedence. Bundled mods show Updated with
AI Hub and follow the installed release while keeping saved settings and enablement. Custom versions remain selected
until an administrator changes them.

## Changes across all tenants

Global Open WebUI manages backend callable overrides and startup behavior across tenants, including work without a
signed-in user. Frontend changes still require tenant activation. Versions shows which packages are eligible for
global use.

Ordinary global changes apply without a container restart. Changes to startup behavior remain pending until you
confirm Restart to apply saved changes. The page shows the saved and active state and worker readiness. Restarting
affects all tenants and can interrupt chats or background jobs; arrange a suitable maintenance window. If readiness
does not recover, the operator needs to inspect the Open WebUI logs.

See [Writing Open WebUI mods](../../../3_sdk/6_feature_overview/1_openwebui_mods/) for the package contract and
the repository's [deployment guide](https://github.com/bbvch-ai/aihub-core/blob/main/infra/deployment/openwebui.md)
for initialization, upgrades and recovery.
