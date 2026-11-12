---
title: Open WebUI-Mods schreiben
source_sha: 2c39d7ffed06bda0a16b05e680b394f96c1221926690ae3f495a5a12d73dfe7a
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
| `bootstrap` | Optionaler Einstiegspunkt mit `.js`, `.mjs` oder `.ts`, der `activate(context)` exportiert und vor der nativen Layout-Initialisierung abgewartet wird. |
| `frontend` | Optionaler Einstiegspunkt mit `.js`, `.mjs` oder `.ts`, der `activate(context)` exportiert. |
| `replacements` | Ordnet nativen Komponenten-IDs `src/.../*.svelte` die `.svelte`-Dateien des Pakets zu. |
| `backend` | Optionaler `.py`-Einstiegspunkt, der Chat-Hooks, Override-Handler oder einen privaten HTTP-Handler exportiert. |
| `backend_overrides` | Ordnet nativen Zielen `open_webui.module:Class.method` oder `open_webui.module:function` die vom Backend-Einstiegspunkt exportierten Handler-Namen zu. |
| `backend_restart_required` | Kennzeichnet Import-/Starteffekte, die globale Aktivierung und einen Neustart erfordern. Benötigt einen Backend-Einstiegspunkt. |
| `default_settings` | Anfängliche JSON-Einstellungen beim Hinzufügen eines Mods. Gespeicherte Einstellungen ersetzen dieses Objekt; Upgrades führen neue Vorgaben nicht mit gespeicherten Einstellungen zusammen. |
| `settings_fields` | Optionale Felddefinitionen: Eingabefelder, übersetzte Beschriftungen/Hilfe, Auswahlwerte und Validierungseigenschaften. |

Mindestens ein Bootstrap-Einstiegspunkt, Frontend-Einstiegspunkt, eine Ersetzung oder ein Backend-Einstiegspunkt ist erforderlich. Pfade sind
relativ zum Archivwurzelverzeichnis. Absolute Pfade, Traversierung, Symlinks und doppelte Einträge werden abgelehnt.
Ein Quellcode-ZIP ist auf 16 MiB komprimiert, 32 MiB entpackt, 512 Einträge und ein 64-KiB-Manifest begrenzt.
Einstellungen erlauben 16 KiB pro Mod; eine Mandantenauswahl erlaubt insgesamt 64 Mods und 64 KiB.

Quell- und Veröffentlichungsrevisionen identifizieren die exakten Archivbytes über SHA-256. Erneutes Paketieren
identischen Quellcodes kann eine neue Revision erzeugen. Bei der Veröffentlichung werden Quellrevision,
Host-Kompatibilität und Fingerabdrücke nativer Ziele erfasst. Hochladen und Veröffentlichen aktiviert keinen Code;
ein Administrator wählt und speichert die Veröffentlichung separat. Es gibt keine Oberfläche zum Löschen von
Archiven. Bewahren Sie frühere Revisionen für Rollbacks auf.

## Eingabefelder für Einstellungen

Legen Sie Anfangswerte in `default_settings` fest. SysAdmin leitet daraus folgende Felder ab:

| Vorgabewert | FormKit-Feld |
| --- | --- |
| Zeichenfolge | `primeInputText` |
| Zahl | `primeInputNumber` |
| Boolescher Wert | `primeToggleSwitch` |
| Sprachobjekt wie `{"en": "Hello", "de": "Hallo"}` | `localeInput` |
| Liste von Zeichenfolgen, einschliesslich `[]` | `chipsInput` |
| Objekt | `group` |
| Nicht leere Objektliste | `repeater`, mit den Feldern der ersten Zeile |
| `null` | `primeInputText` mit einem Aktivierungsschalter |

Ergänzen Sie `settings_fields`, wenn Sie ein anderes Feld oder zusätzliche Eigenschaften benötigen. Diese Einträge
in `mod.json` ergänzen eine Auswahlliste und ein mehrzeiliges Textfeld. Die Übersetzungen von `notice` verwenden das
automatisch gewählte Sprachfeld:

```json
{
  "default_settings": {
    "style": "concise",
    "message": "",
    "notice": { "en": "Check the answer.", "de": "Prüfen Sie die Antwort." }
  },
  "settings_fields": {
    "style": { "options": ["concise", "detailed"] },
    "message": {
      "control": "primeTextarea",
      "label": { "en": "Message", "de": "Nachricht" },
      "rows": 4
    }
  }
}
```

`options` ergibt eine Auswahlliste; `control` wählt ein anderes bestehendes Eingabefeld. Beschriftungen und Hilfetexte
folgen der Oberflächensprache des Administrators. Eine mehrsprachige Einstellung wie `notice` speichert die
Übersetzungen, die der Mod verwendet.

Verwenden Sie die Eigenschaften der bestehenden [Formularfelder](https://github.com/bbvch-ai/aihub-core/tree/main/packages/core/swiss_ai_hub/core/form/elements),
etwa `required`, Grenzwerte und `help`. Für übersetzte Auswahlmöglichkeiten verwenden Sie Objekte mit einem übersetzten
`label` und einem stabilen `value`. Setzen Sie dazu `optionLabel` auf `label` und `optionValue` auf `value`.

`children` von Gruppen und Repeatern enthält Felddefinitionen mit einem `name`. Für eine leere Objektliste geben Sie
`control: "repeater"` und dessen `children` an. Repeater können keine weiteren Repeater enthalten. Vorgaben bleiben in
`default_settings`. Feldnamen entsprechen `[A-Za-z][A-Za-z0-9_]*`; `slots`, `constructor` und `prototype` sind reserviert.
Felddefinitionen sind auf 16 KiB begrenzt. Ungültige Definitionen führen beim Hochladen zu einem Feldfehler; bei dieser
Prüfung wird kein Mod-Code ausgeführt.

Wählen Sie bei hochgeladenen Mods vor dem Bearbeiten der Einstellungen eine veröffentlichte Version; deren
Quellrevision liefert das Formular. Mandanten- und globale Einstellungen unterstützen dieselben Felder. Geheimnisfelder,
Mandanten-/Modell-/Agenten-/Wissensauswahl und automatische Übersetzung sind hier nicht verfügbar. Auswahlwerte müssen
im Paket enthalten sein. Mods müssen verwendete Einstellungen selbst prüfen; Formularvalidierung unterstützt lediglich
die Eingabe.

Gespeicherte Werte ohne passendes Eingabefeld bleiben erhalten. Neu hinzugekommene Vorgaben erscheinen im Formular
und werden beim Speichern wirksam. Öffnen der Einstellungen oder ein Upgrade allein ändert die Laufzeitkonfiguration nicht.

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
und `svelte/animate`. `@openwebui/shortcuts` stellt die native Erkennung von Tastenkürzeln und den Keybinding-Store
einschließlich benutzerdefinierter Belegungen bereit. Verwenden Sie die Versionen des Hosts statt einer zusätzlich
gebündelten Svelte-Laufzeit.
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

Beide Skript-Einstiegspunkte sind optional und exportieren `activate(context)`. Jeder darf eine Aufräumfunktion oder
ein Promise darauf zurückgeben. `bootstrap` läuft vor der nativen Root-Layout-Initialisierung einschliesslich i18n;
`frontend` läuft, sobald der native Benutzer-Store gesetzt ist. Ersetzungen werden nach erfolgreicher
Frontend-Aktivierung installiert. Beide Einstiegspunkte erhalten denselben Kontext. Er enthält `id`
(View-Nonce), `tenantId`, `modId`, `publication`, tief eingefrorene `settings` und ein Abbruch-`signal`.

Verwenden Sie Bootstrap für kleine Änderungen, die vor der nativen Initialisierung erfolgen müssen. Seine Imports
müssen innerhalb des Pakets bleiben: JavaScript, TypeScript, JSON und Assets werden unterstützt; Svelte-Komponenten,
Runen-Module und Imports aus der nativen Laufzeit nicht. Warten Sie nicht auf nativen Anwendungszustand oder die UI,
da der Start Bootstrap abwartet. Für alle Bootstrap-Skripte zusammen gilt eine Frist von 15 Sekunden; ein Fehler
deaktiviert den betroffenen Mod. Der Host kann beliebigen JavaScript-Code nicht unterbrechen oder nicht registrierte
Seiteneffekte rückgängig machen. Bootstrap läuft vor dem nativen Layout, aber nicht vor Inline-Theme-Skripten oder
sämtlichem Framework-Code.

Bootstrap und Frontend haben getrennte kompilierte Abhängigkeitsgraphen. Modullokale Variablen werden deshalb nicht
zwischen ihnen geteilt. Verwenden Sie den gemeinsamen Kontext für Identität und Einstellungen. Ein Paket nur mit
Bootstrap benötigt keinen Frontend-Einstiegspunkt. Hat Bootstrap den Startzeitpunkt verpasst, ist ein Neuladen nötig;
es wird niemals nachträglich gegen die bereits initialisierte Anwendung ausgeführt.

| Kontext-Member | Verwendung |
| --- | --- |
| `onDispose(cleanup)` | Registrieren Sie die Bereinigung vor asynchroner Arbeit. Entfernen Sie eigene Listener, Observer und Mounts. |
| `locale`, `onLocale(callback)` | AI-Hub-Sprache lesen und abonnieren. Das Abonnement ruft sofort zurück, gibt eine Abmeldefunktion zurück und wird beim Dispose der Mod entfernt. |
| `onEvent(callback)` | Die zugeordneten Backend-Ereignisse dieses Mods empfangen; liefert eine Funktion zum Abmelden. |
| `onRequest(handler)` | Native API-Anfragen über eine geordnete Request/Response-Kette verarbeiten; gibt eine Abmeldefunktion zurück. |
| `api(path, options)` | Den privaten Backend-Endpunkt dieses Mods aufrufen. Liefert eine `Response` und bricht beim Beenden des Mods ab. |

Exportieren Sie einen paketlokalen Store aus dem Frontend-Einstiegspunkt, wenn Ersatzkomponenten seine Einstellungen
benötigen. Platzieren Sie Seiteneffekte in der Aktivierung oder in Svelte-Lebenszyklus-Hooks und beachten Sie das
Abbruchsignal nach asynchroner Arbeit. Mandantenwechsel, Abmelden und Verlassen des eingebetteten Chats beenden die
View. Navigation innerhalb von Open WebUI behält sie bei. Frontend-Mods werden nur im vertrauenswürdigen AI Hub-Embed
aktiviert.

Fehler beim Import, bei der Aktivierung und beim Rendern beenden den betroffenen Mod; native Komponenten werden
wiederhergestellt. Die Rendering-Grenze fängt nicht jede Event-Handler- oder asynchrone Ausnahme ab. Die Auswertung
von JavaScript-Modulen und beliebige globale Patches lassen sich nicht automatisch entladen.

## Native Frontend-Anfragen verarbeiten

Registrieren Sie bei der Aktivierung `context.onRequest(async (request, next) => response)`. Geben Sie eine `Response`
zurück, um die Anfrage selbst zu beantworten, rufen Sie `next()` zur Weitergabe auf oder ändern Sie die Anfrage mit
`next(new Request(...))`. Auch die zurückgegebene Antwort lässt sich prüfen oder ersetzen. Die erste konfigurierte Mod
ist der äußerste Handler; innerhalb einer Mod gilt die Registrierungsreihenfolge. Die Registrierung gibt eine
Abmeldefunktion zurück und wird beim Dispose der Mod automatisch entfernt.

```js
export function activate(context) {
  context.onRequest((request, next) => {
    const url = new URL(request.url);
    if (url.origin === location.origin && url.pathname === '/api/example') {
      return Response.json({ message: 'Handled by the mod' });
    }
    return next();
  });
}
```

Die Kette erfasst native Aufrufe über `src/lib/apis/` sowie aus `@aihub/mods` importiertes `fetch`. Globales `fetch`,
Host-Konfiguration und Assets sowie `context.api` bleiben außerhalb. Verwenden Sie im Handler `next`, damit die Kette
nicht rekursiv erneut beginnt. Native Completion-Aufrufe warten auf die Frontend-Aktivierung; andere Aufrufe verwenden
die zum jeweiligen Zeitpunkt registrierten Handler. Bootstrap kann Handler vor der nativen Initialisierung
registrieren, ohne die gemeinsame Runtime zu importieren.

Anfragen behalten die Abbruchsignale des Aufrufers und der Ansicht, auch nach einer Änderung der Anfrage. Beachten Sie
`request.signal` bei eigenen Aufgaben; der Host kann ein beliebig wartendes Promise nicht unterbrechen. Ein geworfener
Fehler lässt diese Anfrage fehlschlagen; der Host wiederholt sie niemals stillschweigend. Handler-Fehler deaktivieren
die Mod nicht automatisch. Die Auswahl der Anfragen, das Klonen von Bodies und bewusste Wiederholungen gehören in den
Handler. Dies steuert Browserverhalten und ist keine Autorisierungsgrenze: Backend-Authentifizierung und
-Autorisierung gelten weiterhin.

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
