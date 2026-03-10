---
title: Integrationsarchitektur
source_sha: 4ccd11d5655ea3ae14efd9bcb67a04bc1583c7fe5bb9d744861e9bb99ef21081
---

# Integrationsarchitektur

Der Swiss AI Hub bettet **Open WebUI** direkt in seine Oberfläche ein, anstatt auf eine separate Bereitstellung zu
verweisen. Dies sorgt für eine einheitliche Benutzererfahrung, während die Open-Source-Komponente von der
Plattforminfrastruktur getrennt bleibt.

## Wie die Einbettung funktioniert

Die Plattform verwendet ein iframe, um die vollständige Open WebUI-Oberfläche innerhalb des Dienstbereichs der Suite
darzustellen. Benutzer sehen eine einzige integrierte Anwendung. Die Architektur wahrt die Trennung zwischen der
Open-Source-Komponente und der Plattforminfrastruktur.

Wenn Benutzer zum Chat-Dienst navigieren, nimmt Open WebUI den gesamten Dienstbereich ein. Die Navigationsleiste der
Suite bleibt zugänglich, sodass Benutzer zu anderen Diensten wechseln können, ohne ihren Chat-Kontext zu verlieren.

Die Einbettung bewahrt die vollständige Oberfläche und den Funktionsumfang von Open WebUI. Tastenkombinationen,
Drag-and-Drop-Dateiverwaltung und Konversationsmanagement funktionieren wie in der Standalone-Anwendung. Die
eingebettete Oberfläche passt sich an verschiedene Bildschirmgrößen an – Desktop-Displays bieten einen erweiterten
Arbeitsbereich, während mobile Geräte den funktionalen Zugriff beibehalten.

## Kommunikation zwischen Komponenten

Das iframe und die Suite-Plattform kommunizieren über die browserübergreifende PostMessage API. Dies ermöglicht sichere
Cross-Origin-Nachrichtenübermittlung unter Wahrung der Sicherheitsgrenzen zwischen den Komponenten.

Die Chat-Oberfläche und die Plattform tauschen strukturierte Nachrichten für Benutzerinteraktionen, Navigationsanfragen
und Zustandsynchronisation aus. Wenn Benutzer Plattformfunktionen innerhalb der Chat-Oberfläche anfordern – wie das
Anzeigen von Wissensquellen oder Ausführungs-Traces – sendet der Chat Nachrichten, die die Navigation und Datenanzeige
auslösen.

Nachrichten folgen definierten Verträgen, die Absicht, Parameter und Verhaltensweisen festlegen. Zu den Typen gehören
Anfragen zur Quellenanzeige, Anfragen zur Sichtbarkeit von Traces und Kontextsynchronisation.

Falls die Nachrichtenübermittlung fehlschlägt oder die Plattform Anfragen nicht erfüllen kann, erhalten Benutzer
Feedback anstelle stillschweigender Fehler.

## Authentifizierung und Sicherheit

Die Plattform und Open WebUI teilen die Authentifizierung über OAuth. Benutzer authentifizieren sich einmal an der Swiss
Swiss AI Hub Suite, und diese Authentifizierung wird an die eingebettete Instanz weitergegeben.

Die Plattform setzt Berechtigungsgrenzen für KI-Modelle, Wissensdatenbanken und Agentenfähigkeiten durch. Benutzer
können über die Chat-Oberfläche nicht auf Inhalte zugreifen, auf die sie über andere Dienste ebenfalls keinen Zugriff
haben.

Sitzungen bleiben zwischen Plattform und Chat synchronisiert. Das Abmelden von der Suite beendet die Chat-Sitzung.
Timeouts und Erneuerungen werden über beide Komponenten hinweg koordiniert.

Die Kommunikation verwendet sichere Kanäle mit Verschlüsselung und Validierung. Die iframe-Integration umfasst
Sicherheits-Header und Content-Security-Policies, um Cross-Site Scripting zu verhindern.

## Konfiguration und Bereitstellung

Open WebUI wird als unabhängiger Docker-Container innerhalb der Plattform bereitgestellt. Dies bietet Isolation, während
der Lebenszyklus – Starten, Stoppen und Aktualisieren – zusammen mit anderen Diensten verwaltet wird.

Der Chat-Container greift über Standardmuster auf die Plattforminfrastruktur wie Datenbanken, Objektspeicher und
Nachrichtenwarteschlangen zu. Chat-Daten bleiben zusammen mit anderen Plattformdaten bestehen und unterstützen eine
einheitliche Sicherung und Datenverwaltung.

Konfigurationsparameter werden über Umgebungsvariablen und Konfigurationsdateien weitergegeben.
Authentifizierungsendpunkte, Modellzugriffs-URLs und Funktionsschalter bleiben in Entwicklungs-, Test- und
Produktionsumgebungen konsistent.

Die Plattform testet neue Open WebUI-Releases in isolierten Umgebungen vor der Produktionseinführung. Dies schützt vor
abwärtsinkompatiblen Änderungen und ermöglicht gleichzeitig den Zugriff auf Verbesserungen.

## Erweiterungspunkte

Die Integration bewahrt die Kernfunktionalität von Open WebUI, fügt aber plattformspezifische Erweiterungen hinzu.

Das PostMessage-Protokoll erweitert die Chat-Fähigkeiten über native Funktionen hinaus. Benutzerdefinierte
Nachrichtentypen lösen Plattform-Workflows oder Datenanzeigen aus, ohne die Open-Source-Codebasis zu ändern.

Die Plattform kann UI-Elemente wie Benachrichtigungsabzeichen oder Schnellaktionsschaltflächen überlagern, ohne Open
WebUI zu modifizieren. Dies verbessert die Funktionalität und vereinfacht gleichzeitig Aktualisierungen.

API-Aufrufe zwischen der Chat-Oberfläche und Backend-Diensten können abgefangen werden, um Kontext hinzuzufügen,
Antworten anzureichern oder die Governance durchzusetzen.

Plattform-Theme-Einstellungen werden durch CSS-Anpassung und nicht durch Quellcodeänderung angewendet. Dies
gewährleistet visuelle Konsistenz mit dem Design der Suite.

## Überwachung

Die Plattform überwacht die Container-Gesundheit von Open WebUI über Standard-Endpunkte. Dienstausfälle lösen
automatische Wiederherstellungen oder Administratoralarme aus.

Nutzungsmetriken – Konversationszähler, Antwortzeiten, Fehlerraten – fließen in die Observability-Systeme der Plattform.
Administratoren überwachen die Leistung des Chat-Dienstes zusammen mit anderen Metriken.

Chat-Protokolle werden mit Plattform-Protokollen in einer einheitlichen Infrastruktur zusammengeführt. Dies unterstützt
die Fehlerbehebung über mehrere Komponenten hinweg.

Die Überwachung des Ressourcenverbrauchs – CPU, Arbeitsspeicher, Netzwerk – unterstützt die Kapazitätsplanung, wenn die
Benutzerpopulationen und Konversationsvolumen wachsen.

## Was dieser Ansatz bietet

Open WebUI und die Plattform entwickeln sich unabhängig voneinander. Neue Releases werden durch Standardprozesse
integriert, ohne Änderungen am Plattformcode. Plattformverbesserungen erfordern keine Änderungen an der Chat-Oberfläche.

Verantwortlichkeiten bleiben klar. Open WebUI verwaltet Chat-Interaktionen. Die Plattform bietet Authentifizierung,
Autorisierung, Wissensmanagement und Agenten-Orchestrierung. Diese Trennung vereinfacht Tests und Wartung.

Einbetten statt Forken bewahrt die Vorteile von Open Source. Die Plattform erhält Beiträge der Community,
Sicherheitspatches und Funktionen, ohne eine benutzerdefinierte Variante pflegen zu müssen.

Organisationen können Open WebUI durch alternative Chat-Oberflächen ersetzen, indem sie die gleichen Einbettungs- und
Nachrichtenmuster verwenden. Dies vermeidet eine Bindung an eine bestimmte Chat-Technologie.
