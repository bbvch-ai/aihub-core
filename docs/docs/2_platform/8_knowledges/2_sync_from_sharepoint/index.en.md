---
title: Syncing a SharePoint library
description: Step by step, from an Entra ID app registration to a knowledge database that keeps itself in sync with a SharePoint document library.
---

# Syncing a SharePoint library

A knowledge database can keep itself in sync with a folder in a SharePoint document library. AI Hub reads the folder
once a day: new and changed files are added, deleted files are removed, and every sub-folder becomes a collection. AI
Hub only reads from SharePoint; it never changes anything there.

<!-- Video walkthrough: docs/media/platform/sharepoint_sync/sharepoint_sync.webm, embedded here once recorded:
<video controls="controls" src="../../../../media/platform/sharepoint_sync/sharepoint_sync.webm" type="video/webm" />
-->

## Before you start

You need:

- an account that may register apps in Entra ID (a SharePoint Administrator can),
- a **Global Administrator** or Privileged Role Administrator for one click in step 3,
- an AI Hub account that may create knowledge databases.

On the way you collect four values for step 5: the **tenant ID**, the **client ID**, the **client secret** and the
**drive ID**.

## 1. Register an app in Entra ID

1. Open the [Microsoft Entra admin center](https://entra.microsoft.com) and go to **Entra ID → App registrations → New
   registration**.
2. Enter a name, for example `AI Hub SharePoint sync`.
3. Under **Supported account types**, choose **Single tenant only - …** (followed by your organisation's name).
4. Leave **Redirect URI** empty and click **Register**.
5. On the app's **Overview** page, copy the **Application (client) ID** and the **Directory (tenant) ID**.

## 2. Create a client secret

1. In the app, open **Certificates & secrets** and click **New client secret**.
2. Enter a description, choose an expiry and click **Add**.
3. Copy the **Value** right away; Entra shows it only once. Do not copy the **Secret ID**, which does not work as a
   password.

Note the expiry date: when the secret expires, syncing stops until you enter a new one (see
[Rotating the secret](#rotating-the-secret)).

## 3. Give the app read access to SharePoint

1. In the app, open **API permissions** and click **Add a permission**.
2. Choose **Microsoft Graph**.
3. Click the **Application permissions** box at the top, next to "Delegated permissions". It is a choice to click, not a
   search term.
4. In the **Select permissions** search field, type `Sites`, expand **Sites** and tick **Sites.Read.All** ("Read items
   in all site collections").
5. Click **Add permissions**. The new row shows "Not granted for …".
6. A Global Administrator clicks **Grant admin consent for …** on the same page and confirms. The row now shows a green
   check. Allow a minute or two before it takes effect.

## 4. Find the drive ID of the library

AI Hub addresses the document library by its drive ID. Your browser can show it:

1. Sign in to SharePoint as usual.
2. Open this address, with your tenant and site name in place of YOUR-TENANT and YOUR-SITE:
   ```
   https://YOUR-TENANT.sharepoint.com/sites/YOUR-SITE/_api/v2.0/drives
   ```
3. The page lists the site's libraries. Find the one whose `"name"` is your library (usually `"Documents"`) and copy its
   `"id"`. It starts with `b!`. In Microsoft Edge, tick **Pretty-print** to make the list readable.

::: details If the page shows an error instead of the list
Use [Microsoft Graph Explorer](https://developer.microsoft.com/graph/graph-explorer), signed in with your Microsoft 365
account. Run a GET request on `https://graph.microsoft.com/v1.0/sites/YOUR-TENANT.sharepoint.com:/sites/YOUR-SITE` and
copy the `id`, then a GET request on `https://graph.microsoft.com/v1.0/sites/SITE-ID/drives` and copy the library's
`id`. If Graph Explorer reports missing permissions, open **Modify permissions** and consent to `Sites.Read.All`.
:::

## 5. Create the knowledge database

1. In AI Hub, open **Knowledge** and click **Add Knowledge Database**.

2. Enter a **Database Name** (lowercase letters and digits, for example `hrdocs`) and choose the ingestion pipeline.

3. Under **Source**, choose **Cloud storage sync (rclone)**.

4. In the **Basic Info** step, keep the default models or choose others.

5. In the **Source** step, choose **OneDrive / SharePoint** as the **Storage backend** and fill in:

   | Field         | Enter                                                                                                                                 |
   | ------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
   | Root folder   | The folder in the library to sync, e.g. `aihub-sync`. Each sub-folder becomes a collection; files directly in this folder are skipped |
   | Client ID     | From step 1                                                                                                                           |
   | Client secret | From step 2                                                                                                                           |
   | Tenant ID     | From step 1                                                                                                                           |
   | Drive ID      | From step 4                                                                                                                           |
   | Drive type    | `documentLibrary`                                                                                                                     |
   | Region        | `global`                                                                                                                              |

   Leave the other fields empty.

6. Click **Create**.

When you open the source again later, the secret shows as `••••••••:` followed by a short reference. That is expected:
the secret is stored encrypted and never shown again.

## 6. First sync

The database shows **Nothing synced yet** until its first sync, which runs at 22:00 Central European time. After it:

- the database has one collection per sub-folder of the root folder,
- each file is processed within a minute or two and then becomes searchable.

To ask questions about the documents, add the database to an agent: in the agent's knowledge settings, select the
database and pick collections or turn on **Search all namespaces**.

::: tip Don't want to wait until 22:00?
An operator can start a sync from Dagster: launch the job `rclone_source_observation` with the run tag `aihub/bucket`
set to the database name.
:::

## Keeping it running

**Changes in SharePoint** are picked up on the next sync. While a database has a source, its documents can only be
changed in SharePoint; manual uploads and deletions are disabled.

### Rotating the secret

1. In Entra ID, create a new client secret (step 2).
2. In AI Hub, open the database's **Edit source**, enter the new value in **Client secret** and save. Fields you leave
   untouched keep their stored values.
3. Delete the old secret in Entra ID.

### Disconnecting SharePoint

Open **Edit source** and choose **Switch to manual upload**. Syncing stops; the documents already in the database stay.

## Troubleshooting

A failed sync never removes documents. Operators find the error in the sync run in Dagster.

| Error in the sync run                             | Fix                                                                      |
| ------------------------------------------------- | ------------------------------------------------------------------------ |
| `failed to get token` with `invalid_client`       | Wrong or expired secret, or the Secret ID was copied. Enter a new secret |
| `failed to get token` with `unauthorized_client`  | Wrong client ID or tenant ID                                             |
| `Failed to query root for drive` with 401 or 403  | Admin consent from step 3 is missing or not active yet                   |
| `Failed to query root for drive` with "not found" | Wrong drive ID                                                           |
| Sync succeeds but a file is missing               | The file lies directly in the root folder; move it into a sub-folder     |

The `rclone` container must reach `login.microsoftonline.com`, `graph.microsoft.com` and `YOUR-TENANT.sharepoint.com` on
port 443. For how the sync works, see the rclone source pipeline in
[Data Ingestion Pipeline](../../../3_sdk/3_building_pipelines/3_data_ingestion_pipeline/).
