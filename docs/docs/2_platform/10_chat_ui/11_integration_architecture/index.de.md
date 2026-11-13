---
title: Integrationsarchitektur
source_sha: e522274ef157401211dac84c809a39fc0ea5cb42ef76fa50cfd12f0e208da4aa
---

# Integrationsarchitektur

Der Swiss AI Hub bettet **Open WebUI** direkt in seine Oberfläche ein, anstatt auf ein separates Deployment zu
verlinken. Dies gewährleistet eine einheitliche Benutzererfahrung, während die Open-Source-Komponente von der
Plattforminfrastruktur getrennt bleibt.

## Wie die Einbettung funktioniert

Die Plattform verwendet ein Iframe, um die vollständige Open WebUI-Oberfläche innerhalb des Servicebereichs der Suite
darzustellen. Benutzer sehen eine einzige integrierte Anwendung. Die Architektur wahrt die Trennung zwischen der
Open-Source-Komponente und der Plattforminfrastruktur.

Wenn Benutzer zum Chat-Service navigieren, nimmt Open WebUI den gesamten Servicebereich ein. Die Navigationsseitenleiste
der Suite bleibt zugänglich, sodass Benutzer zu anderen Services wechseln können, ohne ihren Chat-Kontext zu verlieren.

Die Einbettung bewahrt die vollständige Oberfläche und den Funktionsumfang von Open WebUI. Tastenkombinationen,
Drag-and-Drop-Dateiverwaltung und Konversationsmanagement funktionieren wie in der eigenständigen Anwendung. Die
eingebettete Oberfläche passt sich an verschiedene Bildschirmgrößen an – Desktop-Displays bieten einen erweiterten
Arbeitsbereich, während mobile Geräte den funktionalen Zugriff aufrechterhalten.

## Kommunikation zwischen Komponenten

Das Iframe und die Suite-Plattform kommunizieren über die browserstandardisierte PostMessage API. Dies ermöglicht
sicheres Cross-Origin-Messaging unter Einhaltung von Sicherheitsgrenzen zwischen den Komponenten.

Die Chat-Oberfläche und die Plattform tauschen strukturierte Nachrichten für Benutzerinteraktionen, Navigationsanfragen
und Zustandsynchronisation aus. Wenn Benutzer innerhalb der Chat-Oberfläche Plattformfunktionen anfordern – wie das
Anzeigen von Wissensquellen oder Ausführungs-Traces –, sendet der Chat Nachrichten, die Navigation und Datenanzeige
auslösen.

Nachrichten folgen definierten Verträgen, die Absicht, Parameter und Verhaltensweisen festlegen. Typen umfassen
Anforderungen zur Quellenanzeige, Anforderungen zur Trace-Sichtbarkeit und Kontextsynchronisation.

Wenn die Nachrichtenübertragung fehlschlägt oder die Plattform Anfragen nicht erfüllen kann, erhalten Benutzer Feedback
anstelle von stillen Fehlern.

## Authentifizierung und Sicherheit

Die Plattform und Open WebUI teilen die Authentifizierung über OAuth. Benutzer authentifizieren sich einmal bei der
Swiss AI Hub Suite, und diese Authentifizierung wird an die eingebettete Instanz weitergegeben.

Die Plattform erzwingt Berechtigungsgrenzen für KI-Modelle, Wissensdatenbanken und Agent-Funktionen. Benutzer können
über die Chat-Oberfläche nicht auf das zugreifen, worauf sie über andere Services nicht zugreifen können.

Sitzungen bleiben zwischen Plattform und Chat synchronisiert. Das Abmelden von der Suite beendet die Chat-Sitzung.
Timeouts und Erneuerungen werden über beide Komponenten hinweg koordiniert.

Die Kommunikation nutzt sichere Kanäle mit Verschlüsselung und Validierung. Die Iframe-Integration umfasst
Sicherheitseinstellungen und Content Security Policies, um Cross-Site Scripting zu verhindern.

## Modellsichtbarkeit und Zugriffssteuerung

Die Plattform verwaltet, welche Agents jeder Benutzer in Open WebUI sehen kann. Da die Pipe Discovery von Open WebUI
ohne Benutzerkontext läuft, pusht der AI-Hub den Berechtigungsstatus in Open WebUI, anstatt auf Pipe-Ebene zu filtern.

**Funktionsweise:**

1. **Gruppen**: AI-Hub erstellt Open-WebUI-Gruppen für jede Mandant-Rollen-Kombination mit dem Namen
   `aihub:{tenant}:{role}`. Mitgliedschaften werden über die E-Mail-Adressen beider Systeme abgeglichen. Für Benutzer,
   die in ihrem aktiven Mandanten eine Rolle haben, aber den Chat noch nicht geöffnet haben, erstellt derselbe Sync
   ein Open-WebUI-Konto über SCIM. Ihre Modelle sind damit beim ersten Chat-Besuch verfügbar; die Chat-Anmeldung
   verknüpft sich mit diesem Konto. Jeder Mandant hat ausserdem eine Gruppe `aihub:{tenant}:AIHubSysAdmin` mit den
   Systemadministratoren, deren aktiver Mandant er ist. Ein Sysadmin sieht und nutzt somit alle Agents und Modelle
   dieses Mandanten, ohne eine Mandantenrolle zu benötigen. Im Chat hat er die Rechte eines regulären Benutzers dieses
   Mandanten: Anfragen über Open WebUI tragen keine Systemadministrationsrechte, etwa zum Löschen eines Mandanten.
   Der Rollenname `AIHubSysAdmin` ist reserviert und darf nicht als Mandantenrolle verwendet werden. Die Realm-Rolle
   `AIHubSysAdmin` wird in Keycloak vergeben oder entzogen, ohne AI-Hub zu benachrichtigen. Die Änderung erreicht den
   Chat daher beim nächsten Zugriffssync; ein Mandantenwechsel löst einen solchen Sync aus
2. **Workspace-Modelle**: Für jeden Online-Agent erstellt AI-Hub ein Workspace-Modell, das an die entsprechende
   Pipe-Funktion delegiert
3. **Zugriffsberechtigungen**: Für jedes Workspace-Modell berechnet AI-Hub mit dem Berechtigungssystem der Plattform,
   welche Gruppen Zugriff haben, berücksichtigt dabei die Berechtigungsobergrenze des Mandanten und setzt
   `access_control` für das Modell

Der Provisioner läuft beim API-Start, beim Erstellen, Umbenennen oder Löschen einer Agent-Instanz (sofort in der
Modellauswahl sichtbar), bei Änderungen der Online-Agents (periodischer Abgleich alle 60 Sekunden), beim
Mandantenwechsel und bei Änderungen an Rollen, Mandanten oder Benutzer-Rollen-Zuordnungen. Alle Änderungen werden
sofort weitergegeben.

**Zuverlässigkeit bei Multi-Replica-Deployments:**

- **Debouncing**: Schnelle Mutationen von Zugriffs-Entitäten (z. B. Massenzuweisungen von Benutzern) werden durch ein
  2-Sekunden-Ruhefenster zu einem einzigen Synchronisationsaufruf zusammengefasst.
- **Verteiltes Locking**: Jede Synchronisationsoperation erwirbt ein Redis-Lock, damit gleichzeitige API-Replicas nicht
  konkurrieren. Modellsyncs werden übersprungen, solange ein anderer Sync das Lock hält; Zugriffssyncs warten darauf,
  damit eine Rollenänderung während eines laufenden Syncs trotzdem angewendet wird.
- **Änderungserkennung**: Der Discovery Service speichert einen SHA-256-Hash des Online-Agent-Sets in Redis, der
  Neustarts übersteht und über Replicas hinweg korrekt funktioniert.

`BYPASS_MODEL_ACCESS_CONTROL=False` muss in Open WebUI gesetzt werden, um diese Zugriffssteuerungen durchzusetzen.

## Chat-Schalter für Agents

Bei Agents sind die Open-WebUI-Schalter Web Search, Code Interpreter und Image Generation eine Anfrage an den Agent.
Open WebUI führt diese Funktionen nicht selbst aus. Der Agent entscheidet über die Ausführung und erfasst sie als
Schritt mit Trace und Kostenzuordnung.

- **Welche Schalter erscheinen**: Ein Agent zeigt einen Schalter nur, wenn sein Blueprint die Funktion unterstützt.
  Diese Unterstützung ergibt sich aus den installierten Capabilities; der Provisioner hinterlegt sie im
  Open-WebUI-Modell des Agents. Reine LLM-Modelle behalten alle eigenen Schalter von Open WebUI.
- **Was ein aktivierter Schalter bewirkt**: Ein AI-Hub-Filter an Agent-Modellen entfernt die Schalter aus der Anfrage,
  bevor Open WebUI darauf reagiert, und übergibt die unterstützten Funktionen an den Agent. Open WebUI führt für
  Agents weder seine eigene Suche noch Bildgenerierung oder Code Interpreter aus und verändert den Prompt nicht.
- **Veraltete Schalterzustände**: Open WebUI sendet den Zustand auch nach einem Wechsel zu einem Modell, das den
  Schalter ausblendet. Der Filter leitet nur vom gewählten Agent unterstützte Funktionen weiter; andere von einem
  API-Aufrufer gesendete Funktionen ignoriert der Agent.
- **Memory**: Die eigene Memory-Injektion von Open WebUI ist für Agents deaktiviert. Sie rufen Benutzer- und
  Organisations-Memory selbst ab.

## Angehängte Dateien in Agent-Chats

Wenn ein Benutzer eine Datei in einem Agent-Chat anhängt, liest der Agent sie; Open WebUI speichert nur den Upload.

- **Open WebUI verarbeitet sie nicht für Agents**: Datei-Retrieval und -Injektion (die Capability File Context) sind
  bei Agent-Modellen deaktiviert. Open WebUI erstellt zudem keine Embeddings für Uploads mehr, da es im
  Vollkontextmodus läuft und diese Embeddings nie gelesen hat. Reine LLM-Modelle behalten die Dateiverarbeitung von
  Open WebUI.
- **Der Agent liest das ganze Dokument**: Die Pipe kopiert jede Datei einmal pro Agent in dessen Upload-Bucket. Der
  Agent verarbeitet sie mit der Dokumentextraktion der Plattform (MinerU für PDFs und Bilder, openpyxl für XLSX,
  MarkItDown für andere Office-Dateien). Ein inhaltsbasierter Cache sorgt dafür, dass jede Datei nur einmal konvertiert
  wird. Der vollständige Text kommt in den Modellkontext und wird bei Bedarf gekürzt. Der Benutzer erfährt, wenn nur
  ein Teil der Datei Platz hatte.
- **Spätere Antworten und bearbeitete Nachrichten**: Alle Dateien des aktuellen Nachrichtenzweigs werden bei jeder
  Anfrage mitgesendet. Eine früher angehängte Datei bleibt somit für spätere Fragen verfügbar; bearbeitete oder neu
  generierte Nachrichten sehen nur die Dateien ihres eigenen Zweigs.
- **Quellen**: Jede vom Modell gelesene Datei erscheint als Quelle, die den ursprünglichen Upload öffnet und den an
  das Modell übergebenen Text zeigt. Nicht lesbare Dateien werden gemeldet und nicht stillschweigend übersprungen.
- **Temporäre Chats**: Open WebUI speichert nichts und sendet den im Browser extrahierten Text. Der Agent liest
  diesen Text wie jeden anderen Anhang.

## Quellenverweise im Text

Agent-Antworten verknüpfen jede Aussage mit ihrer Quelle, wie Open WebUI es für sein eigenes Retrieval tut.

- **Was das Modell zitiert**: Jedes Wissensdokument und jede angehängte Datei im Prompt trägt eine kurze ID, die das
  Modell als `[s3f9a1c]` zitiert. Die IDs bleiben über Anfragen und Retrievals hinweg stabil, da sie aus dem Dokument
  selbst und nicht aus seiner Listenposition abgeleitet werden.
- **Was Open WebUI anzeigt**: Open WebUI verlinkt nur Zahlen, die über die Quellen einer Nachricht gezählt werden.
  Die Pipe listet jedes Dokument einmal in der vom Agent gelieferten Reihenfolge auf und ersetzt jede zitierte ID
  während des Streamings durch die entsprechende Dokumentnummer. Eine ID ohne vom Agent gelieferte Quelle wird
  entfernt, statt als ungültiger Verweis zu erscheinen.
- **Welche Dokumente erscheinen**: Aufgeführt werden die tatsächlich vom Modell gelesenen Dokumente nach dem
  Reranking, einschliesslich aus früheren Anfragen übernommener Dokumente, nicht jeder Suchtreffer. Jede Quelle zeigt
  ihren Titel oder Dateinamen und verlinkt das Dokument, sofern eine Referenz-URL vorhanden ist.

## Unser Wissen mit `#` referenzieren

In einem Agent-Chat listet `#` die lesbaren Wissenssammlungen als „Datenbank / Sammlung“ neben den Wissensdatenbanken
von Open WebUI auf. Open WebUI dient nur zur Auswahl: Die Einträge enthalten keinen Inhalt, und Open WebUI führt kein
Retrieval darauf aus. Der Agent durchsucht die referenzierten Sammlungen selbst mit dem jeweiligen Embedding-Modell
der Datenbank und zitiert Ergebnisse wie andere Quellen.

- **Wer was sieht**: Ein Eintrag ist für die Rollengruppen lesbar, die die Sammlung durchsuchen dürfen. Die Liste
  entspricht damit dem Wissensbereich. Der Agent prüft den Zugriff des fragenden Benutzers vor der Suche erneut,
  sodass eine Referenz nie eine unzulässige Sammlung erreicht. Eine nicht lesbare oder gelöschte Sammlung wird dem
  Modell genannt; es teilt dem Benutzer mit, dass es sie nicht verwenden konnte.
- **Automatisch synchronisiert**: Einträge entstehen beim Anlegen einer Sammlung, wenige Sekunden nach Änderungen
  an Sammlung oder Datenbank und bei jedem Discovery-Zyklus für von Pipelines erstellte Sammlungen. Verschwindet eine
  Sammlung, wird ihr Eintrag entfernt.
- **Zusätzlich zum Retrieval des Agents**: Ein Document Intelligence Assistant durchsucht seine konfigurierten
  Quellen und die referenzierten Sammlungen. Ein Instructed Assistant antwortet ausschliesslich aus den referenzierten
  Sammlungen.

## Tool-Aufrufe in Agent-Chats

Wenn ein Agent das Modell seine Tools auswählen lässt (siehe [Agents-Übersicht](../../5_agents/#tools-the-model-chooses)),
erscheint jeder Aufruf in Open WebUI als eigener aufklappbarer Tool-Block mit einer verständlichen Beschriftung wie
„Unser Wissen durchsuchen“. Darin steht das Ergebnis, wie das Modell es erhalten hat. Text, den das Modell vor einem
Aufruf gestreamt hat, wird in einen eingeklappten Denkabschnitt verschoben, sodass die Antwort nach der Arbeit beginnt.
Während der Agent Informationen sammelt, zeigt der Chat seine Tätigkeit, auch wenn eine lange Konversation für das
Modell verdichtet wird.

- **Freigaben**: Ein vom Administrator als freigabepflichtig markiertes Tool fragt im Chat nach Ja/Nein-Bestätigung
  und nennt seinen Namen und Zweck. Ein abgelehntes Tool wird für diese Antwort nicht erneut angefragt; das Modell
  antwortet ohne dieses Tool.
- **Schalter bestimmen das Angebot**: Ein Tool, das Code Interpreter oder My Files benötigt, wird nur bei aktivem
  Schalter angeboten. Siehe [Chat-Schalter für Agents](#chat-schalter-für-agents).
- **Grenzen**: Ein Profil begrenzt, wie oft das Modell entscheiden und wie viele Aufrufe es ausführen darf. Erreicht es
  die Grenze, antwortet es mit den vorhandenen Informationen und nennt den vorzeitigen Abbruch.
- **Quellen**: Eine vom Modell gewählte Wissenssuche erzeugt dieselben Quellen-Chips wie eine `#`-Referenz.

## Chat-Modifikationen

Systemadministratoren verwalten mandantenspezifische Frontend- und Backend-Mods über die Open-WebUI-Einstellungen.
Der mitgelieferte Mod Chat disclaimer zeigt lokalisierten Text unter der Eingabe. Unter
[Open WebUI-Modifikationen](../16_openwebui_mods/) finden Sie Installation, Konfiguration und den Zeitpunkt,
zu dem gespeicherte Änderungen für Benutzer sichtbar werden.

## Streaming-Anzeige

Während eine Antwort gestreamt wird, erscheinen drei pulsierende Punkte dahinter. Zeigt ein Denkprozess oder ein
Tool-Aufruf seinen eigenen Fortschritt, werden die Punkte ausgeblendet. Die native Anzeige von Open WebUI ist ein
schmaler pulsierender Balken, der unter der Denk-Anzeige wie ein einzelnes `|` wirkt. Der mitgelieferte Mod
`aihub-streaming-indicator` lädt das Stylesheet und entfernt es beim Dispose.

Bearbeiten Sie `infrastructure/openwebui/mods/bundled/streaming-indicator/style.css` in Core. Die Initialisierung
installiert geänderte mitgelieferte Quellen. Administratoren können den Mod pro Mandant aktivieren oder deaktivieren.
Die Regeln beziehen sich auf das Markup von Open WebUI v0.11.4. Ändert ein Upgrade dieses Markup, erscheint wieder der
native Balken. Prüfen Sie daher nach jedem Open-WebUI-Upgrade die Anzeige und das Verhalten bei reduzierter Bewegung.

## Konfiguration und Deployment

Open WebUI wird als unabhängiger Docker-Container innerhalb der Plattform deployed. Dies bietet Isolation und verwaltet
den Lebenszyklus – Starten, Stoppen und Aktualisieren – neben anderen Services.

Der Chat-Container greift über Standardmuster auf die Plattforminfrastruktur wie Datenbanken, Objektspeicher und Message
Queues zu. Chat-Daten bleiben zusammen mit anderen Plattformdaten erhalten, was eine einheitliche Sicherung und
Daten-Governance unterstützt.

Konfigurationsparameter werden über Umgebungsvariablen und Konfigurationsdateien weitergegeben.
Authentifizierungs-Endpoints, Modellzugriffs-URLs und Feature-Toggles bleiben über Entwicklungs-, Test- und
Produktionsumgebungen hinweg konsistent.

Die Plattform testet neue Open WebUI-Releases in isolierten Umgebungen vor dem Produktions-Deployment. Dies schützt vor
Breaking Changes und ermöglicht gleichzeitig den Zugang zu Verbesserungen.

## Erweiterungspunkte

Native Open WebUI Functions verbinden Agents, Funktionsschalter und Chat-Aktionen mit AI Hub. Runtime-Mods erweitern
die Oberfläche und das Backend über Komponenten- und Callable-Adapter des abgeleiteten Hosts. Die
[Anleitung für Autoren](../../../3_sdk/6_feature_overview/1_openwebui_mods/) beschreibt die unterstützten Grenzen.

## Monitoring

Die Plattform überwacht die Container-Health von Open WebUI über Standard-Endpoints. Service-Ausfälle lösen automatische
Wiederherstellung oder Administrator-Benachrichtigungen aus.

Nutzungsmetriken – Konversationsanzahlen, Antwortzeiten, Fehlerraten – fließen in die Observability-Systeme der
Plattform. Administratoren überwachen die Performance des Chat-Services zusammen mit anderen Metriken.

Chat-Logs aggregieren mit Plattform-Logs in einer vereinheitlichten Infrastruktur. Dies unterstützt die Fehlerbehebung
über mehrere Komponenten hinweg.

Die Überwachung des Ressourcenverbrauchs – CPU, Speicher, Netzwerk – unterstützt die Kapazitätsplanung, wenn
Benutzerpopulationen und Konversationsvolumen wachsen.

## Vorteile dieses Ansatzes

Open WebUI-Updates verwenden unveränderten Upstream-Quellcode mit den versionierten Host-Adaptern von AI Hub.
Upgrades erfordern Kompatibilitäts- und Verhaltenstests; private Upstream-Schnittstellen können Adapteränderungen
nötig machen. Gewöhnliche Mod-Installationen verwenden den installierten Host weiter.

Verantwortlichkeiten bleiben klar. Open WebUI verwaltet Chat-Interaktionen. Die Plattform bietet Authentifizierung,
Autorisierung, Wissensmanagement und Agenten-Orchestrierung. Diese Trennung vereinfacht Tests und Wartung.

Organisationen können Open WebUI durch alternative Chat-Oberflächen ersetzen, indem sie dieselben Einbettungs- und
Nachrichtenmuster verwenden. Dies vermeidet eine Bindung an eine spezifische Chat-Technologie.
