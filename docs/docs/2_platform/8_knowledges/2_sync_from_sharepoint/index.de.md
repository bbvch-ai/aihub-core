---
title: Eine SharePoint-Bibliothek synchronisieren
description: Step by step, from an Entra ID app registration to a knowledge database that keeps itself in sync with a SharePoint document library.
source_sha: 6f6ceb5f8bf7fb74aa33ef4a07c8ae5d6b53c15727d7449cb75553da965755fd
---

# Eine SharePoint-Bibliothek synchronisieren

Eine Wissensdatenbank kann sich selbst mit einem Ordner in einer SharePoint-Dokumentbibliothek synchron halten. AI Hub
liest den Ordner einmal täglich: Neue und geänderte Dateien kommen hinzu, gelöschte Dateien werden entfernt, und jeder
Unterordner wird zu einer Sammlung. AI Hub liest nur aus SharePoint und ändert dort nie etwas.

<!-- Video walkthrough: docs/media/platform/sharepoint_sync/sharepoint_sync.webm, embedded here once recorded:
<video controls="controls" src="../../../../media/platform/sharepoint_sync/sharepoint_sync.webm" type="video/webm" />
-->

## Bevor Sie beginnen

Sie benötigen:

- ein Konto, das in Entra ID Apps registrieren darf (ein SharePoint-Administrator darf das),
- einen **globalen Administrator** oder Administrator für privilegierte Rollen für einen Klick in Schritt 3,
- ein AI Hub-Konto, das Wissensdatenbanken anlegen darf.

Unterwegs sammeln Sie vier Werte für Schritt 5: die **Tenant-ID**, die **Client-ID**, das **Client Secret** und die
**Laufwerks-ID**.

Die Bezeichnungen im Microsoft Entra Admin Center sind hier so angegeben, wie sie in der englischen Oberfläche
erscheinen.

## 1. Eine App in Entra ID registrieren

1. Öffnen Sie das [Microsoft Entra Admin Center](https://entra.microsoft.com) und gehen Sie zu **Entra ID → App
   registrations → New registration**.
2. Geben Sie einen Namen ein, zum Beispiel `AI Hub SharePoint sync`.
3. Wählen Sie unter **Supported account types** die Option **Single tenant only - …** (gefolgt vom Namen Ihrer
   Organisation).
4. Lassen Sie **Redirect URI** leer und klicken Sie auf **Register**.
5. Kopieren Sie auf der Seite **Overview** der App die **Application (client) ID** und die **Directory (tenant) ID**.

## 2. Ein Client Secret erstellen

1. Öffnen Sie in der App **Certificates & secrets** und klicken Sie auf **New client secret**.
2. Geben Sie eine Beschreibung ein, wählen Sie eine Gültigkeitsdauer und klicken Sie auf **Add**.
3. Kopieren Sie sofort den **Value**; Entra zeigt ihn nur einmal an. Kopieren Sie nicht die **Secret ID**, sie
   funktioniert nicht als Passwort.

Notieren Sie das Ablaufdatum: Wenn das Secret abläuft, stoppt die Synchronisation, bis Sie ein neues eintragen (siehe
[Das Secret erneuern](#das-secret-erneuern)).

## 3. Der App Lesezugriff auf SharePoint geben

1. Öffnen Sie in der App **API permissions** und klicken Sie auf **Add a permission**.
2. Wählen Sie **Microsoft Graph**.
3. Klicken Sie oben auf das Feld **Application permissions** neben „Delegated permissions“. Es ist eine Auswahl zum
   Anklicken, kein Suchbegriff.
4. Geben Sie im Suchfeld **Select permissions** `Sites` ein, klappen Sie **Sites** auf und aktivieren Sie
   **Sites.Read.All** („Read items in all site collections“).
5. Klicken Sie auf **Add permissions**. Die neue Zeile zeigt „Not granted for …“.
6. Ein globaler Administrator klickt auf derselben Seite auf **Grant admin consent for …** und bestätigt. Die Zeile
   zeigt nun ein grünes Häkchen. Es kann ein bis zwei Minuten dauern, bis die Berechtigung wirkt.

## 4. Die Laufwerks-ID der Bibliothek finden

AI Hub spricht die Dokumentbibliothek über ihre Laufwerks-ID an. Ihr Browser kann sie anzeigen:

1. Melden Sie sich wie gewohnt bei SharePoint an.
2. Öffnen Sie diese Adresse, mit Ihrem Tenant und Site-Namen anstelle von YOUR-TENANT und YOUR-SITE:
   ```
   https://YOUR-TENANT.sharepoint.com/sites/YOUR-SITE/_api/v2.0/drives
   ```
3. Die Seite listet die Bibliotheken der Site auf. Suchen Sie den Eintrag, dessen `"name"` Ihre Bibliothek ist (meist
   `"Documents"`), und kopieren Sie seine `"id"`. Sie beginnt mit `b!`. Aktivieren Sie in Microsoft Edge
   **Pretty-print**, um die Liste lesbar zu machen.

::: details Wenn die Seite statt der Liste einen Fehler zeigt
Verwenden Sie den [Microsoft Graph Explorer](https://developer.microsoft.com/graph/graph-explorer), angemeldet mit Ihrem
Microsoft 365-Konto. Führen Sie einen GET-Request auf
`https://graph.microsoft.com/v1.0/sites/YOUR-TENANT.sharepoint.com:/sites/YOUR-SITE` aus und kopieren Sie die `id`, dann
einen GET-Request auf `https://graph.microsoft.com/v1.0/sites/SITE-ID/drives` und kopieren Sie die `id` der Bibliothek.
Wenn der Graph Explorer fehlende Berechtigungen meldet, öffnen Sie **Modify permissions** und stimmen Sie
`Sites.Read.All` zu.
:::

## 5. Die Wissensdatenbank anlegen

1. Öffnen Sie in AI Hub die **Wissensdatenbanken** und klicken Sie auf **Wissensdatenbank hinzufügen**.

2. Geben Sie einen **Datenbankname** ein (Kleinbuchstaben und Ziffern, zum Beispiel `hrdocs`) und wählen Sie die
   Ingestion-Pipeline.

3. Wählen Sie unter **Quelle** die Option **Cloud-Speicher-Synchronisation (rclone)**.

4. Behalten Sie im Schritt **Grundinformationen** die Standardmodelle oder wählen Sie andere.

5. Wählen Sie im Schritt **Quelle** als **Speicher-Backend** die Option **OneDrive / SharePoint** und füllen Sie aus:

   | Feld             | Eingabe                                                                                                                                                              |
   | ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
   | Stammordner      | Der zu synchronisierende Ordner in der Bibliothek, z. B. `aihub-sync`. Jeder Unterordner wird zu einer Sammlung; Dateien direkt in diesem Ordner werden übersprungen |
   | Client-ID        | Aus Schritt 1                                                                                                                                                        |
   | Client-Geheimnis | Aus Schritt 2                                                                                                                                                        |
   | Mandanten-ID     | Die Tenant-ID aus Schritt 1                                                                                                                                          |
   | Laufwerks-ID     | Aus Schritt 4                                                                                                                                                        |
   | Laufwerkstyp     | `documentLibrary`                                                                                                                                                    |
   | Region           | `global`                                                                                                                                                             |

   Lassen Sie die übrigen Felder leer.

6. Klicken Sie auf **Erstellen**.

Wenn Sie die Quelle später wieder öffnen, zeigt das Secret `••••••••:` gefolgt von einer kurzen Referenz. Das ist so
gewollt: Das Secret wird verschlüsselt gespeichert und nie wieder angezeigt.

## 6. Erste Synchronisation

Die Datenbank zeigt **Noch nichts synchronisiert**, bis ihre erste Synchronisation gelaufen ist. Diese läuft um 22:00
Uhr mitteleuropäischer Zeit. Danach:

- hat die Datenbank eine Sammlung pro Unterordner des Stammordners,
- wird jede Datei innerhalb von ein bis zwei Minuten verarbeitet und ist danach durchsuchbar.

Um Fragen zu den Dokumenten zu stellen, fügen Sie die Datenbank einem Agent hinzu: Wählen Sie in den
Wissenseinstellungen des Agents die Datenbank und wählen Sie Sammlungen aus oder aktivieren Sie **Alle Namensräume
durchsuchen**.

::: tip Sie möchten nicht bis 22:00 Uhr warten?
Ein Operator kann eine Synchronisation in Dagster starten: Starten Sie den Job `rclone_source_observation` mit dem
Run-Tag `aihub/bucket`, gesetzt auf den Datenbanknamen.
:::

## Im Betrieb

**Änderungen in SharePoint** werden bei der nächsten Synchronisation übernommen. Solange eine Datenbank eine Quelle hat,
lassen sich ihre Dokumente nur in SharePoint ändern; manuelle Uploads und Löschungen sind deaktiviert.

### Das Secret erneuern

1. Erstellen Sie in Entra ID ein neues Client Secret (Schritt 2).
2. Öffnen Sie in AI Hub bei der Datenbank **Quelle bearbeiten**, tragen Sie den neuen Wert unter **Client-Geheimnis**
   ein und speichern Sie. Felder, die Sie nicht ändern, behalten ihre gespeicherten Werte.
3. Löschen Sie das alte Secret in Entra ID.

### SharePoint trennen

Öffnen Sie **Quelle bearbeiten** und wählen Sie **Auf manuellen Upload umstellen**. Die Synchronisation stoppt; die
Dokumente in der Datenbank bleiben erhalten.

## Fehlerbehebung

Eine fehlgeschlagene Synchronisation entfernt nie Dokumente. Operatoren finden den Fehler im Sync-Run in Dagster.

| Fehler im Sync-Run                                 | Lösung                                                                                      |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `failed to get token` mit `invalid_client`         | Falsches oder abgelaufenes Secret, oder die Secret ID wurde kopiert. Neues Secret eintragen |
| `failed to get token` mit `unauthorized_client`    | Falsche Client-ID oder Tenant-ID                                                            |
| `Failed to query root for drive` mit 401 oder 403  | Die Administratorzustimmung aus Schritt 3 fehlt oder wirkt noch nicht                       |
| `Failed to query root for drive` mit „not found“   | Falsche Laufwerks-ID                                                                        |
| Synchronisation erfolgreich, aber eine Datei fehlt | Die Datei liegt direkt im Stammordner; verschieben Sie sie in einen Unterordner             |

Der `rclone`-Container muss `login.microsoftonline.com`, `graph.microsoft.com` und `YOUR-TENANT.sharepoint.com` über
Port 443 erreichen. Wie die Synchronisation funktioniert, beschreibt die rclone Source Pipeline in
[Data Ingestion Pipeline](../../../3_sdk/3_building_pipelines/3_data_ingestion_pipeline/).
