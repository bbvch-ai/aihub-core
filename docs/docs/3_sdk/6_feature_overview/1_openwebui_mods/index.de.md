---
title: Open WebUI-Mods schreiben
source_sha: fda728f0d60d572578aba69fdef77e5c30efff43eeb20c6b29e5427a50178ba3
---

# Open WebUI-Mods schreiben

Ein **Open WebUI-Mod** ist ein Quellcode-ZIP, das ein Systemadministrator über die
[Open WebUI-Einstellungen](../../../2_platform/10_chat_ui/16_openwebui_mods/) hochlädt und veröffentlicht. Es kann
Svelte-Komponenten, JavaScript oder TypeScript, Python und lokale Assets enthalten. Nutzen Sie die nativen
Einstellungen oder Functions von Open WebUI, wenn diese das gewünschte Verhalten bereits bieten.

Mods verwenden die Svelte-Laufzeit und Python-Umgebung des laufenden Hosts. Die Veröffentlichung kompiliert für diesen
Host, ohne Abhängigkeiten zu installieren oder hochgeladenen Code auszuführen. Sie prüft Syntax, Frontend-Imports und deklarierte
Ziele, belegt aber weder korrektes Laufzeitverhalten noch führt sie eine semantische TypeScript-Prüfung durch. Prüfen
Sie Typen in Ihrem Entwicklungsprojekt und testen Sie den veröffentlichten Mod auf einem passenden temporären Host.

## Den Quellcode paketieren

Legen Sie `mod.json` zusammen mit den referenzierten Dateien im Wurzelverzeichnis des ZIPs ab. Das
[Manifest-Modell](https://github.com/bbvch-ai/aihub-core/blob/main/packages/core/swiss_ai_hub/core/infrastructure/openwebui/mods/openwebui_mod_manifest.py)
definiert die akzeptierten Felder und ihre Validierung. Das mitgelieferte
[Chat-disclaimer-Paket](https://github.com/bbvch-ai/aihub-core/tree/main/packages/core/swiss_ai_hub/core/infrastructure/openwebui/mods/bundled/chat-disclaimer)
ist ein kleines Frontend-Beispiel mit Einstellungen, Sprachwechseln und Aufräumen beim Beenden.

| Manifest-Feld | Zweck |
| --- | --- |
| `format`, `id`, `name`, `version` | Erforderliche Metadaten. Das Format ist `1`; die stabile ID verwendet Kleinbuchstaben, Ziffern und Bindestriche. Version ist eine Bezeichnung des Autors, nicht die Identität des Archivs. |
| `description` | Optionale Erläuterung im Katalog. |
| `frontend` | Optionaler Einstiegspunkt mit `.js`, `.mjs` oder `.ts`, der `activate(context)` exportiert. |
| `replacements` | Ordnet nativen Komponenten-IDs `src/.../*.svelte` die `.svelte`-Dateien des Pakets zu. |
| `backend` | Optionaler `.py`-Einstiegspunkt, der Chat-Hooks, Override-Handler oder einen privaten HTTP-Handler exportiert. |
| `backend_overrides` | Ordnet nativen Zielen `open_webui.module:Class.method` oder `open_webui.module:function` die vom Backend-Einstiegspunkt exportierten Handler-Namen zu. |
| `backend_restart_required` | Kennzeichnet Import-/Starteffekte, die globale Aktivierung und einen Neustart erfordern. Benötigt einen Backend-Einstiegspunkt. |
| `default_settings` | Anfängliche JSON-Einstellungen beim Hinzufügen eines Mods. Gespeicherte Einstellungen ersetzen dieses Objekt; Upgrades führen neue Vorgaben nicht mit gespeicherten Einstellungen zusammen. |

Mindestens ein Frontend-Einstiegspunkt, eine Ersetzung oder ein Backend-Einstiegspunkt ist erforderlich. Pfade sind
relativ zum Archivwurzelverzeichnis. Absolute Pfade, Traversierung, Symlinks und doppelte Einträge werden abgelehnt.
Ein Quellcode-ZIP ist auf 16 MiB komprimiert, 32 MiB entpackt, 512 Einträge und ein 64-KiB-Manifest begrenzt.
Einstellungen erlauben 16 KiB pro Mod; eine Mandantenauswahl erlaubt insgesamt 64 Mods und 64 KiB.

Quell- und Veröffentlichungsrevisionen identifizieren die exakten Archivbytes über SHA-256. Erneutes Paketieren
identischen Quellcodes kann eine neue Revision erzeugen. Bei der Veröffentlichung werden Quellrevision,
Host-Kompatibilität und Fingerabdrücke nativer Ziele erfasst. Hochladen und Veröffentlichen aktiviert keinen Code;
ein Administrator wählt und speichert die Veröffentlichung separat. Es gibt keine Oberfläche zum Löschen von
Archiven. Bewahren Sie frühere Revisionen für Rollbacks auf.

## Komponenten hinzufügen oder ersetzen

Lesen Sie den Komponentenkatalog des laufenden Hosts über SysAdmins `GET /api/v1/admin/openwebui-mods/host`.
Verwenden Sie dessen Quell-IDs als Schlüssel für Ersetzungen. Eine Ersetzung erhält Props, Bindings und Slots der
nativen Komponente und muss den von ihren Aufrufern benötigten Vertrag erhalten. Zwei aktivierte Mods können nicht
dieselbe Komponente ersetzen.

Neue Kindkomponenten sind gewöhnliche Svelte-Imports innerhalb des Pakets. Um eine native Komponente zu erweitern,
importieren Sie `getOriginalComponent` aus `@aihub/mods`, holen das Original über seine Katalog-ID und kombinieren es
mit Ihren neuen Kindkomponenten. So wird die eigene Referenz nicht rekursiv ersetzt. Ein im bestehenden Baum
gerendertes Kind nimmt an Sveltes Reaktivität und Kontext teil. Eine separat gemountete Komponente erbt diesen
Kontext nicht automatisch.

Importieren Sie Open WebUI-Stores aus `@openwebui/stores` (`$lib/stores` wird ebenfalls akzeptiert). Gemeinsame Module
sind `svelte`, `svelte/store`, `svelte/transition`, `svelte/motion`, `svelte/easing`, `svelte/reactivity`, `svelte/events`
und `svelte/animate`. Verwenden Sie die Versionen des Hosts statt einer zusätzlich gebündelten Svelte-Laufzeit.
Native Store-Namen und Komponentenverträge können sich mit Open WebUI-Upgrades ändern.

Ersetzungen erfassen instrumentierte Verwendungen von Quellkomponenten. Sie legen keine privaten lexikalischen
Zustände offen, verwandeln Inline-Markup nicht in Komponenten und fangen imperative Mounts oder Interna von
Drittanbieterkomponenten nicht automatisch ab. Diese Fälle benötigen einen Adapter für die festgelegte Open
WebUI-Version. Das Ersetzen einer Instanz setzt ihren privaten Zustand zurück.

### Imports und Assets

Verwenden Sie explizite relative Dateinamen für Paket-Imports, Re-Exports und literale dynamische Imports. Der Compiler
unterstützt Svelte-Dateien, TypeScript, JavaScript und Runen-Module mit `.svelte.ts`/`.svelte.js`. JSON-Imports liefern
einen Standardwert, andere Asset-Imports eine Standard-URL. Literale Verweise mit
`new URL('./asset', import.meta.url)` werden ebenfalls aufgenommen.

Nur erreichbare Frontend-Dateien werden für Browser veröffentlicht. Andere Bare Imports, Query-Imports wie `?raw`,
berechnete dynamische Imports, Import-Attribute/-Optionen und Asset-Side-Effect-Imports werden abgelehnt. Relative
CSS-Verweise mit `url(...)` werden nicht unterstützt; verwenden Sie eine importierte Asset-URL in einem Style-Attribut.
Backend-Abhängigkeiten müssen bereits auf dem Host installiert sein. Für einen Mod läuft keine npm- oder pip-Installation.

## Den Frontend-Lebenszyklus verwalten

Der optionale Frontend-Einstiegspunkt exportiert `activate(context)` und darf eine Aufräumfunktion oder ein Promise
darauf zurückgeben. Ersetzungen werden nach erfolgreicher Aktivierung installiert. Der Kontext enthält `id`
(View-Nonce), `tenantId`, `modId`, `publication`, tief eingefrorene `settings` und ein Abbruch-`signal`.

| Kontext-Member | Verwendung |
| --- | --- |
| `onDispose(cleanup)` | Registrieren Sie die Bereinigung vor asynchroner Arbeit. Entfernen Sie eigene Listener, Observer und Mounts. |
| `locale`, `onLocale(callback)` | AI Hub-Sprache lesen und abonnieren. Das Abonnement ruft sofort zurück und liefert eine Funktion zum Abmelden. |
| `onEvent(callback)` | Die zugeordneten Backend-Ereignisse dieses Mods empfangen; liefert eine Funktion zum Abmelden. |
| `api(path, options)` | Den privaten Backend-Endpunkt dieses Mods aufrufen. Liefert eine `Response` und bricht beim Beenden des Mods ab. |

Exportieren Sie einen paketlokalen Store aus dem Frontend-Einstiegspunkt, wenn Ersatzkomponenten seine Einstellungen
benötigen. Platzieren Sie Seiteneffekte in der Aktivierung oder in Svelte-Lebenszyklus-Hooks und beachten Sie das
Abbruchsignal nach asynchroner Arbeit. Mandantenwechsel, Abmelden und Verlassen des eingebetteten Chats beenden die
View. Navigation innerhalb von Open WebUI behält sie bei. Frontend-Mods werden nur im vertrauenswürdigen AI Hub-Embed
aktiviert.

Fehler beim Import, bei der Aktivierung und beim Rendern beenden den betroffenen Mod; native Komponenten werden
wiederhergestellt. Die Rendering-Grenze fängt nicht jede Event-Handler- oder asynchrone Ausnahme ab. Die Auswertung
von JavaScript-Modulen und beliebige globale Patches lassen sich nicht automatisch entladen.

## Backend-Arbeit verarbeiten

Der Backend-Einstiegspunkt kann `class Filter` mit optionalen asynchronen Methoden `inlet`, `request`, `stream` und
`outlet` exportieren. Jede akzeptiert `(value, context)` und gibt das geänderte Dictionary zurück; `stream` darf
`None` zurückgeben, um einen Chunk auszulassen. Dies sind native Chat-Lebenszyklus-Hooks, keine Hooks für den Start
oder beliebige HTTP-Anfragen. Jede Ausführung erhält eine neue Filter-Instanz und kopierte Einstellungen. Native
Anfrage, Benutzer, Metadaten, Modell und Ausführungskennungen stehen im Kontext bereit; siehe `ModRunContext` in
`backend/mod_run_context.py` des Hosts.

`await context.emit(type, data)` sendet JSON an den `onEvent`-Callback des zugehörigen Frontends. Ereignisnamen erlauben
128 Zeichen; die vollständige Nachricht ist auf 64 KiB begrenzt. Die Zustellung prüft View, Mandant, Mod, Chat,
Assistentennachricht, Ausführung und nativen Task. Abschluss oder Abbruch des Tasks beendet das Senden. Eigenständige
Backend-Ausführung hat keinen Frontend-Empfänger. Hook-Fehler folgen Open WebUIs Fehlerbehandlung; Stream-/Outlet-Hooks
sind keine universelle Durchsetzungsgrenze.

Relative Python-Imports und über `__file__` lokalisierte Assets funktionieren. Module werden pro Worker bis zu dessen
Beendigung gecacht. Speichern Sie keine Mandantendaten in Modulglobalen und erwarten Sie nicht, dass beliebige
Import-Seiteneffekte beim Deaktivieren rückgängig gemacht werden.

### Native Callables überschreiben

Wählen Sie Ziele für `backend_overrides` aus dem Callable-Katalog des Hosts. Exportieren Sie Handler mit der
positional-only Signatur `(next, context, /, *args, **kwargs)` und passen Sie sie an das native synchrone, asynchrone
oder Generator-Verhalten an. Ein Handler kann Argumente oder Ergebnisse ändern, einen Aufruf ablehnen oder die Kette
mit `next` fortsetzen. Mandanten-Handler umschliessen globale Handler, die wiederum das native Callable umschliessen.
Fehler werden weitergegeben, ohne die ursprüngliche Operation erneut auszuführen.

Mandantenkontexte liefern verifizierten Benutzer, Mandant, Anfrage, kopierte Einstellungen und veränderlichen
anfragebezogenen `state`. Der Import-Adapter bindet verzögert geladene Ziele beim Import ihrer nativen Module; Mods
benötigen weder Polling noch einen Warte-Lebenszyklus. Quellfingerabdrücke erkennen Zieländerungen, können aber nicht
prüfen, ob eine Upstream-Signatur oder ein Verhalten weiterhin dieselbe Bedeutung hat. Testen Sie jeden
überschriebenen Pfad einschliesslich seiner Decorators und Caches.

Verschachtelte Closures, Descriptors, nativer Erweiterungscode, eigene Loader und gemeinsam genutzter veränderlicher
Zustand können explizite Host-Adapter benötigen. Erkannte äussere `cache`-, `lru_cache`- und `aiocache.cached`-Decorators
werden während überschriebener Arbeit umgangen; manuelle Caches und andere Decorators werden nicht mandantenlokal.
Nicht zugeordnete Anfragen ausserhalb des Chats, WebSockets und unabhängige Jobs erhalten nicht automatisch einen
Mandantenkontext.

### Eine private API bereitstellen

Exportieren Sie `async handle(request, context)` aus dem Backend-Einstiegspunkt. Im Frontend ruft
`context.api(path, options)` den Pfad `/_aihub/mods/tenants/{tenant_id}/mods/{mod_id}/api/{path}` auf. `context.path`
ist das Pfadsuffix; der Kontext liefert ausserdem Anfragezustand, Identität und Einstellungen. Geben Sie
JSON-kompatible Daten oder eine native Response zurück, einschliesslich Streams. Native HTTP-Fehler behalten Status
und Details.

Der Server wählt das aktuell aktivierte Backend über die Mod-ID. Ein Browser kann keine alte Backend-Revision
anfordern. Halten Sie private APIs und Ereignis-Payloads mit älteren offenen Frontend-Views kompatibel: Speichern
ändert neue Backend-Vorgänge, während ein gemountetes Frontend bis zum Neuladen bestehen bleibt. Laufende Anfragen,
Streams und geerbte native Tasks behalten ihre vorbereiteten Handler und Einstellungen. Verzögerte Imports einer
ersetzten oder deaktivierten Frontend-Veröffentlichung können ein Neuladen erfordern.

## Globales Verhalten und Startverhalten

Globale Aktivierung unterstützt Backend-Callable-Overrides und Pakete mit `backend_restart_required`.
Frontend-Ersetzungen und Chat-Filter-Hooks benötigen weiterhin Mandantenaktivierung. Globale Kontexte stellen
`scope='global'`, `app`, Einstellungen und Anfragezustand sowie gegebenenfalls eine HTTP-Anfrage bereit; sie bestätigen
keinen Mandanten oder Benutzer.

Ein Override von `open_webui.main:lifespan` erfordert immer globale Aktivierung und einen Neustart. Geben Sie einen
asynchronen Context Manager zurück, treten Sie in `next(...)` ein, um den nativen Start zu erhalten, geben Sie dessen
Zustand mit Yield weiter und räumen Sie eigene Arbeit beim Verlassen auf. Lifespan läuft in jedem Worker; Jobs, die
nur einmal laufen dürfen, benötigen eigene Koordination. Upstream-Imports sind bereits gelaufen, wenn globale Pakete
geladen werden. Verhalten zu ändern, das während dieser Imports bereits ausgeführt wurde, benötigt daher einen
expliziten Host-Adapter.

## Einen Mod prüfen und pflegen

Testen Sie Veröffentlichung, Aktivierung, Einstellungen, Deaktivierung und Rollback auf dem festgelegten Host.
Prüfen Sie bei Frontend-Mods beide Chat-Layouts, Navigation, gemeinsamen Zustand und Bereinigung. Prüfen Sie bei
Backend-Mods parallele Mandanten, Abbruch, Streams und die genutzten eigenständigen/globalen Pfade. Berücksichtigen Sie
Fehlerfälle und verifizieren Sie, dass natives Verhalten nutzbar bleibt.

Veröffentlichen Sie nach einem Host-Upgrade eine kompatible Version und prüfen Sie geänderte Ziele vor deren Auswahl.
Kompilierungswarnungen bleiben der Veröffentlichung zugeordnet. Die Quelldefinitionen liegen im
[Host-Verzeichnis](https://github.com/bbvch-ai/aihub-core/tree/main/infra/deployment/docker/open-webui/mods).
Die [Deployment-Anleitung](https://github.com/bbvch-ai/aihub-core/blob/main/infra/deployment/openwebui.md)
beschreibt Host-Builds, Initialisierung, Backups und Wiederherstellung.
