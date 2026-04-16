---
title: Integrationsarchitektur
source_sha: "9441d72cf5e8e26d30b2b0f541247f06b8ffd52287381f4ec1c7d147586864fc"
---

# Integrationsarchitektur

Der Swiss AI Hub bettet **Open WebUI** direkt in seine Oberfläche ein, anstatt auf ein separates Deployment zu verlinken. Dies gewährleistet eine einheitliche Benutzererfahrung, während die Open-Source-Komponente von der Plattforminfrastruktur getrennt bleibt.

## Wie die Einbettung funktioniert

Die Plattform verwendet ein Iframe, um die vollständige Open WebUI-Oberfläche innerhalb des Servicebereichs der Suite darzustellen. Benutzer sehen eine einzige integrierte Anwendung. Die Architektur wahrt die Trennung zwischen der Open-Source-Komponente und der Plattforminfrastruktur.

Wenn Benutzer zum Chat-Service navigieren, nimmt Open WebUI den gesamten Servicebereich ein. Die Navigationsseitenleiste der Suite bleibt zugänglich, sodass Benutzer zu anderen Services wechseln können, ohne ihren Chat-Kontext zu verlieren.

Die Einbettung bewahrt die vollständige Oberfläche und den Funktionsumfang von Open WebUI. Tastenkombinationen, Drag-and-Drop-Dateiverwaltung und Konversationsmanagement funktionieren wie in der eigenständigen Anwendung. Die eingebettete Oberfläche passt sich an verschiedene Bildschirmgrößen an – Desktop-Displays bieten einen erweiterten Arbeitsbereich, während mobile Geräte den funktionalen Zugriff aufrechterhalten.

## Kommunikation zwischen Komponenten

Das Iframe und die Suite-Plattform kommunizieren über die browserstandardisierte PostMessage API. Dies ermöglicht sicheres Cross-Origin-Messaging unter Einhaltung von Sicherheitsgrenzen zwischen den Komponenten.

Die Chat-Oberfläche und die Plattform tauschen strukturierte Nachrichten für Benutzerinteraktionen, Navigationsanfragen und Zustandsynchronisation aus. Wenn Benutzer innerhalb der Chat-Oberfläche Plattformfunktionen anfordern – wie das Anzeigen von Wissensquellen oder Ausführungs-Traces –, sendet der Chat Nachrichten, die Navigation und Datenanzeige auslösen.

Nachrichten folgen definierten Verträgen, die Absicht, Parameter und Verhaltensweisen festlegen. Typen umfassen Anforderungen zur Quellenanzeige, Anforderungen zur Trace-Sichtbarkeit und Kontextsynchronisation.

Wenn die Nachrichtenübertragung fehlschlägt oder die Plattform Anfragen nicht erfüllen kann, erhalten Benutzer Feedback anstelle von stillen Fehlern.

## Authentifizierung und Sicherheit

Die Plattform und Open WebUI teilen die Authentifizierung über OAuth. Benutzer authentifizieren sich einmal bei der Swiss AI Hub Suite, und diese Authentifizierung wird an die eingebettete Instanz weitergegeben.

Die Plattform erzwingt Berechtigungsgrenzen für KI-Modelle, Wissensdatenbanken und Agent-Funktionen. Benutzer können über die Chat-Oberfläche nicht auf das zugreifen, worauf sie über andere Services nicht zugreifen können.

Sitzungen bleiben zwischen Plattform und Chat synchronisiert. Das Abmelden von der Suite beendet die Chat-Sitzung. Timeouts und Erneuerungen werden über beide Komponenten hinweg koordiniert.

Die Kommunikation nutzt sichere Kanäle mit Verschlüsselung und Validierung. Die Iframe-Integration umfasst Sicherheitseinstellungen und Content Security Policies, um Cross-Site Scripting zu verhindern.

## Modellsichtbarkeit und Zugriffssteuerung

Die Plattform verwaltet, welche Agents jeder Benutzer in Open WebUI sehen kann. Da die Pipe Discovery von Open WebUI ohne Benutzerkontext läuft, pusht der AI-Hub den Berechtigungsstatus in Open WebUI, anstatt auf Pipe-Ebene zu filtern.

### Funktionsweise:

- **Gruppen**: Der AI-Hub erstellt Open WebUI-Gruppen für jede Mandant-Rollen-Kombination (benannt `aihub:{tenant}:{role}`), wobei die Mitgliedschaften basierend auf dem E-Mail-Abgleich zwischen beiden Systemen synchronisiert werden.
- **Workspace-Modelle**: Für jeden Online-Agent erstellt der AI-Hub ein Workspace-Modell, das an die entsprechende Pipe-Funktion delegiert.
- **Zugriffsberechtigungen**: Für jedes Workspace-Modell berechnet der AI-Hub, welche Gruppen Zugriff haben, unter Verwendung des Berechtigungssystems der Plattform (mit Erzwingung der Mandantenobergrenze), und setzt dann `access_control` für das Modell.

Der Provisioner läuft beim API-Start, wenn sich der Satz der Online-Agents ändert (alle 60 Sekunden überprüft), wenn Benutzer Mandanten wechseln, wenn sich neue Benutzer über einen Open WebUI Webhook anmelden und wenn Rollen, Mandanten oder Benutzer-Rollen-Zuordnungen geändert werden. Alle Zugriffsänderungen werden sofort weitergegeben.

### Zuverlässigkeit bei Multi-Replica-Deployments:

- **Debouncing**: Schnelle Mutationen von Zugriffs-Entitäten (z. B. Massenzuweisungen von Benutzern) werden durch ein 2-Sekunden-Ruhefenster zu einem einzigen Synchronisationsaufruf zusammengefasst.
- **Verteiltes Locking**: Jede Synchronisationsoperation erwirbt ein nicht-blockierendes Redis-Lock, sodass gleichzeitige API-Replicas überspringen, anstatt um die Ressourcen zu konkurrieren.
- **Änderungserkennung**: Der Discovery Service speichert einen SHA-256-Hash des Online-Agent-Sets in Redis, der Neustarts übersteht und über Replicas hinweg korrekt funktioniert.

`BYPASS_MODEL_ACCESS_CONTROL=False` muss in Open WebUI gesetzt werden, um diese Zugriffssteuerungen durchzusetzen.

## Konfiguration und Deployment

Open WebUI wird als unabhängiger Docker-Container innerhalb der Plattform deployed. Dies bietet Isolation und verwaltet den Lebenszyklus – Starten, Stoppen und Aktualisieren – neben anderen Services.

Der Chat-Container greift über Standardmuster auf die Plattforminfrastruktur wie Datenbanken, Objektspeicher und Message Queues zu. Chat-Daten bleiben zusammen mit anderen Plattformdaten erhalten, was eine einheitliche Sicherung und Daten-Governance unterstützt.

Konfigurationsparameter werden über Umgebungsvariablen und Konfigurationsdateien weitergegeben. Authentifizierungs-Endpoints, Modellzugriffs-URLs und Feature-Toggles bleiben über Entwicklungs-, Test- und Produktionsumgebungen hinweg konsistent.

Die Plattform testet neue Open WebUI-Releases in isolierten Umgebungen vor dem Produktions-Deployment. Dies schützt vor Breaking Changes und ermöglicht gleichzeitig den Zugang zu Verbesserungen.

## Erweiterungspunkte

Die Integration bewahrt die Kernfunktionalität von Open WebUI, fügt aber plattformspezifische Erweiterungen hinzu.

Das PostMessage-Protokoll erweitert die Chat-Funktionen über native Features hinaus. Benutzerdefinierte Nachrichtentypen lösen Plattform-Workflows oder Datenanzeigen aus, ohne die Open-Source-Codebasis zu modifizieren.

Die Plattform kann UI-Elemente wie Benachrichtigungsabzeichen oder Schnellaktions-Buttons überlagern, ohne Open WebUI zu modifizieren. Dies verbessert die Funktionalität und vereinfacht gleichzeitig Updates.

API-Aufrufe zwischen der Chat-Oberfläche und Backend-Services können abgefangen werden, um Kontext hinzuzufügen, Antworten anzureichern oder Governance durchzusetzen.

Plattform-Theme-Einstellungen werden durch CSS-Anpassung und nicht durch Quellcode-Modifikation angewendet. Dies gewährleistet die visuelle Konsistenz mit dem Design der Suite.

## Monitoring

Die Plattform überwacht die Container-Health von Open WebUI über Standard-Endpoints. Service-Ausfälle lösen automatische Wiederherstellung oder Administrator-Benachrichtigungen aus.

Nutzungsmetriken – Konversationsanzahlen, Antwortzeiten, Fehlerraten – fließen in die Observability-Systeme der Plattform. Administratoren überwachen die Performance des Chat-Services zusammen mit anderen Metriken.

Chat-Logs aggregieren mit Plattform-Logs in einer vereinheitlichten Infrastruktur. Dies unterstützt die Fehlerbehebung über mehrere Komponenten hinweg.

Die Überwachung des Ressourcenverbrauchs – CPU, Speicher, Netzwerk – unterstützt die Kapazitätsplanung, wenn Benutzerpopulationen und Konversationsvolumen wachsen.

## Vorteile dieses Ansatzes

Open WebUI und die Plattform entwickeln sich unabhängig voneinander. Neue Releases werden durch Standardprozesse ohne Änderungen am Plattformcode integriert. Plattformverbesserungen erfordern keine Modifikationen an der Chat-Oberfläche.

Verantwortlichkeiten bleiben klar. Open WebUI verwaltet Chat-Interaktionen. Die Plattform bietet Authentifizierung, Autorisierung, Wissensmanagement und Agenten-Orchestrierung. Diese Trennung vereinfacht Tests und Wartung.

Die Einbettung statt eines Forkings bewahrt die Vorteile von Open Source. Die Plattform erhält Community-Beiträge, Sicherheitspatches und Features, ohne eine benutzerdefinierte Variante pflegen zu müssen.

Organisationen können Open WebUI durch alternative Chat-Oberflächen ersetzen, indem sie dieselben Einbettungs- und Nachrichtenmuster verwenden. Dies vermeidet eine Bindung an eine spezifische Chat-Technologie.
