---
title: Open WebUI-Modifikationen
source_sha: d0fa40d0b51bd16f055767c7e6e9cd050d5a2f0271c355c6365e10a815002e74
---

# Open WebUI-Modifikationen

**Open WebUI-Modifikationen**, kurz Mods, ermöglichen Systemadministratoren, die Chat-Oberfläche und ihr Backend-Verhalten
anzupassen. Ein Mod kann Bedienelemente hinzufügen, eine Komponente ersetzen oder die Verarbeitung einer Anfrage ändern.
Eigene Mods werden als Quellcode-ZIP hochgeladen und für die laufende Open WebUI-Instanz vorbereitet, ohne deren
Container neu zu bauen.

## Mods für einen Mandanten auswählen

Öffnen Sie in SysAdmin die Mandanten, wählen Sie einen Mandanten und öffnen Sie dessen Open-WebUI-Einstellungen.
Der Katalog steht allen Mandanten zur Verfügung; Aktivierung und Einstellungen werden pro Mandant gespeichert.

Für einen eigenen Mod:

1. Wählen Sie ZIP hochladen und das vom Autor bereitgestellte Paket.
2. Wählen Sie Installieren, oder bestätigen Sie Installierte Mod ersetzen, wenn die ID bereits installiert ist.
3. Aktivieren Sie den Mod, bearbeiten Sie die Felder unter Einstellungen und speichern Sie.

Die Installation prüft und kompiliert das Paket mit dem laufenden Open WebUI-Host. Ein fehlgeschlagener Upload bleibt
im Dialog; beim Schliessen wird der Versuch verworfen. Das installierte Paket bleibt unverändert. Eine fehlgeschlagene
Erstinstallation fügt keinen Eintrag hinzu.

Jeder Mod hat eine installierte Version für alle Mandanten. Ein erfolgreicher Austausch aktualisiert denselben Eintrag
und behält gespeicherte Einstellungen und Aktivierung bei. Erfüllen die Werte die Regeln des neuen Formulars nicht
mehr, unterstützt die normale Feldvalidierung die Korrektur. Deaktivieren und speichern Sie den Mod, wenn er inaktiv
bleiben soll. Schalteränderungen betreffen immer die installierte Version. Um früheren Code wiederherzustellen, laden
Sie dessen ZIP erneut hoch; es gibt weder Versionsverlauf noch Rollback-Schaltfläche. Bewahren Sie Ihre Quellcode-ZIPs auf.

Neue Mods sind zunächst deaktiviert. Fehlgeschlagene Speichervorgänge behalten ungespeicherte Änderungen bei. Hat ein
anderer Administrator Einstellungen geändert, laden Sie die Seite neu und prüfen Sie den gespeicherten Stand, bevor
Sie es erneut versuchen.

::: warning Vertrauenswürdiger Code und Einstellungen
Nur Systemadministratoren können Mods hochladen, installieren und konfigurieren. Mods laufen mit den Möglichkeiten
der Anwendung in den Browsern der Benutzer oder innerhalb von Open WebUI; sie sind nicht in einer Sandbox isoliert.
Aktivieren Sie nur Code, dem Sie vertrauen. Mandanteneinstellungen werden an den Browser übermittelt. Speichern Sie
darin deshalb keine Passwörter, Tokens oder sonstigen Geheimnisse.
:::

## Wann Benutzer Änderungen sehen

Offene Chats behalten ihre aktuelle Oberfläche bis zum Neuladen. Sie prüfen alle 30 Sekunden sowie bei der Rückkehr
zum Tab oder nach dem Wiederherstellen der Verbindung auf Änderungen und bieten dann einen Hinweis zum Neuladen an.
Das Speichern erzwingt kein Neuladen, während jemand schreibt. Neue Backend-Vorgänge verwenden die gespeicherte
Konfiguration; laufende Anfragen behalten ihren ausgewählten Code und ihre Einstellungen.

Ein Fehler beim Import, bei der Aktivierung oder beim Rendern einer Komponente deaktiviert den betroffenen Frontend-Mod
und bietet einen Hinweis zum Neuladen an. Die gespeicherte Aktivierung bleibt unverändert. Fehler beim Backend-Import
oder beim Erzeugen eines Filters werden protokolliert; diese Instanz wird übersprungen. Globale Ladefehler erscheinen
zusätzlich im Worker-Status. Andere Mods können weiterlaufen. Fehler während Backend-Vorgängen folgen der normalen
Fehlerbehandlung von Open WebUI.

## Den Chat-Hinweis konfigurieren

Der mitgelieferte Mod Chat disclaimer zeigt einen kurzen Hinweis unterhalb der Chat-Eingabe. Bearbeiten Sie in dessen
Einstellungen das Feld Hinweis und wählen Sie dazu DE, EN, FR oder IT. Jede Übersetzung erlaubt reinen Text mit bis
zu 100 Zeichen. Der Hinweis folgt der Sprache von AI Hub und fällt auf Deutsch, danach auf die erste nicht leere
Übersetzung zurück. Ungültige Texteinstellungen verhindern die Aktivierung dieses Mods. Deaktivieren Sie den Mod,
um den Hinweis auszublenden.

Die mitgelieferten Deployment-Vorgaben aktivieren Chat disclaimer, Account menu cleanup, Saved language recovery,
Voice reply recovery, Multi-model PDF export guard und Streaming indicator. Betreiber können festlegen, welche mitgelieferten
Mods anfänglich aktiviert sind. Sobald ein Mandant seine eigene Konfiguration speichert, hat diese Vorrang.
Mitgelieferte Mods sind mit Mit AI Hub aktualisiert gekennzeichnet und folgen dem installierten Release;
gespeicherte Einstellungen und Aktivierung bleiben erhalten.

Der Mod Account menu cleanup entfernt die doppelte Kontoanzeige von Open WebUI. Administratoren erhalten einen
direkten Link zum Admin Panel. Ihr Einstellungsdialog behält Admin-Tabs und About, ausgenommen Authentication, Connections und
Database. Andere Benutzer können den Einstellungsdialog nicht öffnen.

## Änderungen für alle Mandanten

Open WebUI global verwaltet Backend-Callable-Overrides und Startverhalten für alle Mandanten, einschliesslich Arbeit
ohne angemeldeten Benutzer. Frontend-Änderungen benötigen weiterhin eine Aktivierung pro Mandant. Jede Seite zeigt die
für ihren Geltungsbereich geeigneten Pakete. Wird ein ausschliesslich globales Paket auf einer Mandantenseite hochgeladen,
öffnet sich nach der Installation die globale Seite. Änderungen am Geltungsbereich eines Pakets behalten gespeicherte
Entscheidungen bei, aktivieren es aber niemals automatisch in einem anderen Geltungsbereich.

Gewöhnliche globale Änderungen werden ohne Container-Neustart wirksam. Sind Startänderungen ausstehend, warten alle
gespeicherten globalen Änderungen, bis Sie Gespeicherte Änderungen mit Neustart anwenden bestätigen. Eine Warnung zur
globalen Aktivierung nach der Installation bedeutet, dass das Paket installiert wurde, der Host es aber nicht
übernehmen konnte. Speichern Sie die globalen Open-WebUI-Einstellungen, um es erneut zu versuchen.
Die Seite zeigt gespeicherten und aktiven
Zustand sowie die Bereitschaft der Worker. Ein Neustart betrifft alle Mandanten und kann Chats oder Hintergrundjobs
unterbrechen. Planen Sie ein geeignetes Wartungsfenster. Werden die Worker nicht wieder bereit, muss der Betreiber die
Open WebUI-Logs prüfen.

[Open WebUI-Mods schreiben](../../../3_sdk/6_feature_overview/1_openwebui_mods/) beschreibt den Paketvertrag. Die
[Deployment-Anleitung](https://github.com/bbvch-ai/aihub-core/blob/main/infra/deployment/openwebui.md) im
Repository behandelt Initialisierung, Upgrades und Wiederherstellung.
