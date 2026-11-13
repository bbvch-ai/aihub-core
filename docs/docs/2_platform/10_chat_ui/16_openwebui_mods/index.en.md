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

1. Choose Upload ZIP and select the package supplied by its author.
2. Choose Install, or confirm Replace installed mod if its ID is already installed.
3. Enable the mod, edit the controls under Settings, and Save.

Installation checks and compiles the package using the running Open WebUI host. A failed upload stays in the dialog;
closing it discards the attempt. The installed package remains unchanged, and a failed first installation adds no row.

Each mod has one installed version shared by all tenants. A successful replacement updates that same row and keeps
saved settings and enablement. If those values no longer meet the new form's rules, ordinary field validation guides
the edit. Disable the mod and Save if it should stay inactive. Toggle changes always apply to the installed version.
To restore earlier code, upload its ZIP again; there is no version history or rollback button. Keep your source ZIPs.

New mods start disabled. Failed settings saves retain unsaved edits; if another administrator changed the settings,
reload the page and review the saved configuration before retrying.

::: warning Trusted code and settings
Only system administrators can upload, install and configure mods. Mods run with application capabilities in users'
browsers or inside Open WebUI; they are not sandboxed. Enable code you trust. Tenant settings are delivered to the
browser, so do not put passwords, tokens or other secrets in them.
:::

## When users see changes

Open chats keep their current interface until reloaded. They check for changes every 30 seconds and when users return
to the tab or reconnect, then offer a reload notice. Saving does not force a reload while someone is typing.
New backend operations use the saved configuration; requests already running retain their selected code and settings.

An import, activation or component-rendering failure disables the affected frontend mod and offers a reload notice.
Saved enablement remains unchanged. Backend import/filter-construction failures are logged and skip that instance;
global load errors also appear in worker status. Other mods can continue. Exceptions during backend operations follow
Open WebUI's normal error handling.

## Configure the chat disclaimer

The supplied Chat disclaimer mod displays a short note below the chat input. Open Settings, choose DE, EN, FR or IT
and edit the Disclaimer field. Each translation accepts plain text of up to 100 characters.
The note follows the AI Hub language, falling back to German and then the first nonempty translation. Invalid text
settings prevent this mod from activating. Disable the mod to hide the note.

The shipped deployment defaults enable Chat disclaimer, Saved language recovery, Voice reply recovery,
Multi-model PDF export guard and Streaming indicator. Operators can change which bundled mods start enabled;
once a tenant saves its own configuration, that saved configuration takes precedence. Bundled mods show Updated with
AI Hub and follow the installed release while keeping saved settings and enablement.

The optional Admin Panel shortcut mod replaces the duplicate account display with a direct Admin Panel link for
admins. Their Settings dialog keeps admin tabs and About, excluding Authentication, Connections and Database.
Other users cannot open the Settings dialog. This mod is installed with AI Hub but is not enabled by default.

## Changes across all tenants

Global Open WebUI manages backend callable overrides and startup behavior across tenants, including work without a
signed-in user. Frontend changes still require tenant activation. Each page lists packages eligible for its scope.
Uploading a global-only package from a tenant page opens the global page after installation. Updating a package's
scope preserves saved choices but never automatically enables it in a different scope.

Ordinary global changes apply without a container restart. If startup changes are pending, all saved global changes
wait until you confirm Restart to apply saved changes. An installation warning about global activation means the
package was installed, but the host could not adopt it; save Global Open WebUI settings to retry.
The page shows the saved and active state and worker readiness. Restarting
affects all tenants and can interrupt chats or background jobs; arrange a suitable maintenance window. If readiness
does not recover, the operator needs to inspect the Open WebUI logs.

See [Writing Open WebUI mods](../../../3_sdk/6_feature_overview/1_openwebui_mods/) for the package contract and
the repository's [deployment guide](https://github.com/bbvch-ai/aihub-core/blob/main/infra/deployment/openwebui.md)
for initialization, upgrades and recovery.
