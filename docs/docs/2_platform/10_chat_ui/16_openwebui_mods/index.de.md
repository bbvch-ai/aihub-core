---
title: Open WebUI-Modifikationen
source_sha: 1f89ba0a7948c098731264ef5c145f1e0624f664682a7526a592f5a23ddf738b
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

1. Wählen Sie ZIP hochladen und laden Sie das Paket des Autors hoch.
2. Öffnen Sie Versionen, wählen Sie die Quellversion und dann Für dieses Open WebUI veröffentlichen. Dabei wird das
   Paket geprüft und kompiliert, aber noch nicht aktiviert.
3. Wählen Sie Diese Version verwenden, aktivieren Sie den Mod und bearbeiten Sie Einstellungen (JSON) gemäss den
   Anweisungen des Autors.
4. Speichern Sie die Einstellungen des Mandanten.

Die Veröffentlichung erfordert einen erreichbaren, kompatiblen Open WebUI-Mod-Host. Kompilierungsfehler erscheinen im
Versionsdialog. Ist das Paket bereits für diesen Host veröffentlicht, können Sie es ohne erneute Veröffentlichung
auswählen. Das Hochladen einer neueren Version ändert bestehende Auswahlen nicht. Für ein Rollback wählen Sie eine
frühere kompatible Version und speichern.

Beim Deaktivieren bleiben die ausgewählte Version und die Einstellungen erhalten. Alle deaktivieren und anschliessendes
Speichern schaltet die Mods des Mandanten aus. Fehlgeschlagene Speichervorgänge erhalten Ihren Entwurf. Falls ein anderer
Administrator die Konfiguration geändert hat, prüfen Sie dessen gespeicherte Einstellungen vor einem erneuten Versuch.
Gespeicherte Einstellungen neu laden ersetzt Ihren Entwurf.

::: warning Vertrauenswürdiger Code und Einstellungen
Nur Systemadministratoren können Mods hochladen, veröffentlichen und konfigurieren. Mods laufen mit den Möglichkeiten
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
und bietet einen Hinweis zum Neuladen an. Andere Mods können weiterlaufen. Backend-Fehler folgen der normalen
Fehlerbehandlung von Open WebUI.

## Den Chat-Hinweis konfigurieren

Der mitgelieferte Mod Chat disclaimer zeigt einen kurzen Hinweis unterhalb der Chat-Eingabe. Bearbeiten Sie in dessen
Einstellungen (JSON) die Werte `de`, `en`, `fr` und `it` im Objekt `text`. Jede Übersetzung erlaubt reinen Text mit bis
zu 100 Zeichen. Der Hinweis folgt der Sprache von AI Hub und fällt auf Deutsch, danach auf die erste nicht leere
Übersetzung zurück. Ungültige Texteinstellungen verhindern die Aktivierung dieses Mods. Deaktivieren Sie den Mod,
um den Hinweis auszublenden.

Die mitgelieferten Deployment-Vorgaben aktivieren Chat disclaimer. Betreiber können festlegen, welche mitgelieferten
Mods anfänglich aktiviert sind. Sobald ein Mandant seine eigene Konfiguration speichert, hat diese Vorrang.
Mitgelieferte Mods sind mit Mit AI Hub aktualisiert gekennzeichnet und folgen dem installierten Release;
gespeicherte Einstellungen und Aktivierung bleiben erhalten. Eigene Versionen bleiben ausgewählt, bis ein
Administrator die Auswahl ändert.

## Änderungen für alle Mandanten

Open WebUI global verwaltet Backend-Callable-Overrides und Startverhalten für alle Mandanten, einschliesslich Arbeit
ohne angemeldeten Benutzer. Frontend-Änderungen benötigen weiterhin eine Aktivierung pro Mandant. Versionen zeigt,
welche Pakete global verwendet werden können.

Gewöhnliche globale Änderungen werden ohne Container-Neustart wirksam. Änderungen am Startverhalten bleiben ausstehend,
bis Sie Gespeicherte Änderungen mit Neustart anwenden bestätigen. Die Seite zeigt gespeicherten und aktiven
Zustand sowie die Bereitschaft der Worker. Ein Neustart betrifft alle Mandanten und kann Chats oder Hintergrundjobs
unterbrechen. Planen Sie ein geeignetes Wartungsfenster. Werden die Worker nicht wieder bereit, muss der Betreiber die
Open WebUI-Logs prüfen.

[Open WebUI-Mods schreiben](../../../3_sdk/6_feature_overview/1_openwebui_mods/) beschreibt den Paketvertrag. Die
[Deployment-Anleitung](https://github.com/bbvch-ai/aihub-core/blob/main/infra/deployment/openwebui.md) im
Repository behandelt Initialisierung, Upgrades und Wiederherstellung.
