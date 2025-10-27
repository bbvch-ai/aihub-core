---
title: Integrationsarchitektur
index: 1
source_sha: a05be570ab6241f0514ee07ba68b066aa0f17d74f7b58dc1906314ceba51692c
---

# Integrationsarchitektur

Die Integration von Open WebUI in den Swiss AI Hub demonstriert ausgeklügelte Architekturmuster, die eine nahtlose
Einbettung von Open-Source-Komponenten Dritter ermöglichen und dabei das einheitliche Benutzererlebnis sowie das
Sicherheitsmodell der Plattform aufrechterhalten.

## Muster der eingebetteten Integration

Anstatt Benutzer über Links oder Weiterleitungen zu einer separaten Open WebUI-Bereitstellung zu leiten, bettet der
Swiss AI Hub die Chat-Oberfläche direkt in den einheitlichen Arbeitsbereich der Suite ein, wodurch ein kohärentes
Benutzererlebnis entsteht, das von nativen Plattformkomponenten nicht zu unterscheiden ist.

**Iframe-Einbettung**: Die Integration nutzt die Iframe-Einbettungstechnologie, um die vollständige Open
WebUI-Oberfläche innerhalb des Servicebereichs der Suite darzustellen. Dieser Ansatz bietet eine vollständige visuelle
Integration und bewahrt gleichzeitig klare Grenzen zwischen der Open-Source-Komponente und der Plattforminfrastruktur.
Benutzer nehmen eine einzige, integrierte Anwendung wahr, während die zugrundeliegende Architektur die Trennung der
Belange aufrechterhält.

**Vollbild-Service-Integration**: Wenn Benutzer innerhalb der Suite zum Chat-Dienst navigieren, nimmt die Open
WebUI-Oberfläche den gesamten Servicebereich ein und bietet die vollständige Funktionalität und Benutzererfahrung der
eigenständigen Anwendung. Die dauerhafte Navigationsleiste der Suite bleibt zugänglich, was Benutzern ermöglicht, zu
anderen Plattformdiensten zu navigieren, ohne ihren Chat-Kontext zu unterbrechen.

**Bewahrtes Benutzererlebnis**: Der Einbettungsansatz bewahrt die vollständige Benutzeroberfläche, Interaktionsmuster
und den Funktionsumfang von Open WebUI. Benutzer profitieren von der vollen Bandbreite des Open-Source-Projekts –
Tastenkürzel, Drag-and-Drop-Dateiverwaltung, Konversationsmanagement – ohne Kompromisse, die durch benutzerdefinierte
Integrations-Wrapper entstehen würden.

**Integration des responsiven Layouts**: Die eingebettete Oberfläche passt sich dem responsiven Layoutsystem der Suite
an. Auf großen Desktop-Bildschirmen bietet die Chat-Oberfläche einen großzügigen Arbeitsbereich für komplexe
Konversationen. Auf Tablets und Mobilgeräten passt sich die Integration entsprechend an, wobei der funktionale Zugriff
auf Chat-Funktionen erhalten bleibt.

## Architektur für bidirektionale Kommunikation

Ein kennzeichnendes Merkmal der Integration ist die ausgeklügelte bidirektionale Kommunikation zwischen der
eingebetteten Open WebUI-Oberfläche und der umgebenden Suite-Plattform, die Funktionen über die einfache
Iframe-Einbettung hinaus ermöglicht.

**PostMessage-Protokoll**: Die Integration implementiert die browserübliche PostMessage-Kommunikation für eine sichere,
ursprungsübergreifende Nachrichtenübermittlung zwischen dem Iframe und der übergeordneten Anwendung. Dieser
standardbasierte Ansatz ermöglicht eine zuverlässige Kommunikation und wahrt dabei die Sicherheitsgrenzen zwischen der
eingebetteten Komponente und der Plattforminfrastruktur.

**Ereignisgesteuerte Koordination**: Die Chat-Oberfläche und die Suite-Plattform tauschen strukturierte Nachrichten aus,
die Benutzerinteraktionen, Navigationsanfragen und Zustandsynchronisation darstellen. Wenn Benutzer Aktionen innerhalb
der Chat-Oberfläche initiieren, die Plattformfunktionen erfordern – das Anzeigen von Wissensquellen, das Untersuchen von
Ausführungsspuren – sendet die Chat-Oberfläche Nachrichten an die Plattform, die eine entsprechende Navigation und
Datenanzeige auslösen.

**Typisierte Nachrichtenverträge**: Die Kommunikation folgt gut definierten Nachrichten-Typ-Verträgen, die Absicht,
erforderliche Parameter und erwartetes Verhalten festlegen. Nachrichtentypen umfassen Anfragen zur Quellenanzeige,
Anfragen zur Rückverfolgbarkeitsanzeige und Kontextsynchronisation, was eine zuverlässige Koordination zwischen den
Komponenten gewährleistet.

**Fehlertolerantes Verhalten**: Die Integrationsarchitektur handhabt Kommunikationsfehler fehlertolerant. Wenn die
Nachrichtenübermittlung Fehler aufweist oder die Plattform Anfragen nicht erfüllen kann, erhalten Benutzer eine
entsprechende Rückmeldung, anstatt auf stille Fehler oder unterbrochene Interaktionen zu stoßen.

## Authentifizierungs- und Sicherheitsintegration

Die Integration einer Drittanbieter-Oberfläche unter Beibehaltung der Plattformsicherheit und Zugriffssteuerung
erfordert eine ausgeklügelte Authentifizierungskoordination.

**Single Sign-On-Integration**: Die Plattform und Open WebUI teilen den Authentifizierungskontext über die
OAuth-Integration. Benutzer authentifizieren sich einmal bei der Swiss AI Hub Suite, und diese Authentifizierung wird an
die eingebettete Open WebUI-Instanz weitergegeben, wodurch doppelte Anmeldeaufforderungen entfallen und ein nahtloses
Benutzererlebnis erhalten bleibt.

**Durchsetzung von Berechtigungsgrenzen**: Während Open WebUI Chat-Interaktionen handhabt, setzt die Plattform
Berechtigungsgrenzen für den Zugriff auf zugrunde liegende KI-Modelle, Wissensdatenbanken und Agentenfunktionen durch.
Benutzer können über die Chat-Oberfläche keine Ressourcen aufrufen, für die ihnen über andere Plattformdienste die
Berechtigung fehlt.

**Sitzungssynchronisation**: Authentifizierungssitzungen bleiben zwischen der Plattform und der eingebetteten
Chat-Oberfläche synchronisiert. Wenn Benutzer sich von der Suite abmelden, wird die Chat-Oberflächensitzung gleichzeitig
beendet. Sitzungs-Timeouts und -Verlängerungen werden über beide Komponenten hinweg koordiniert.

**Sichere Kommunikationskanäle**: Die gesamte Kommunikation zwischen der Plattform und Open WebUI erfolgt über sichere
Kanäle mit entsprechender Verschlüsselung und Validierung. Die Iframe-Integration umfasst entsprechende
Sicherheits-Header und Content Security Policies, um Cross-Site-Scripting und andere Web-Sicherheitslücken zu
verhindern.

## Konfigurations- und Bereitstellungskoordination

Die Integrationsarchitektur ermöglicht ein koordiniertes Deployment und Konfigurationsmanagement zwischen Plattform- und
Chat-Komponenten.

**Containerisierte Bereitstellung**: Open WebUI wird als unabhängiger Docker-Container innerhalb der
Bereitstellungsarchitektur der Plattform bereitgestellt. Diese Containerisierung bietet Isolation und ermöglicht
gleichzeitig ein koordiniertes Lifecycle-Management – Starten, Stoppen, Aktualisieren der Chat-Oberfläche zusammen mit
anderen Plattformdiensten.

**Zugriff auf gemeinsame Infrastruktur**: Der Chat-Container greift über Standard-Integrationsmuster auf die
Plattforminfrastruktur – Datenbanken, Objektspeicher, Nachrichtenwarteschlangen – zu. Dieser Ansatz der gemeinsamen
Infrastruktur stellt sicher, dass Chat-Daten zusammen mit anderen Plattformdaten persistent gespeichert werden, was eine
einheitliche Sicherung, Notfallwiederherstellung und Daten-Governance unterstützt.

**Umgebungsbasierte Konfiguration**: Konfigurationsparameter – Authentifizierungsendpunkte, Modellzugriffs-URLs,
Feature-Toggles – werden über Umgebungsvariablen und Konfigurationsdateien an die Chat-Oberfläche weitergegeben, die vom
Plattform-Deployment-System verwaltet werden. Dieser Ansatz ermöglicht eine konsistente Konfiguration über
Entwicklungs-, Test- und Produktionsumgebungen hinweg ohne manuelle Koordination.

**Versionskompatibilitätsmanagement**: Die Plattform verwaltet die Versionskompatibilität von Open WebUI, indem sie neue
Releases in isolierten Umgebungen testet, bevor diese in die Produktion überführt werden. Dieser kontrollierte
Update-Prozess schützt Organisationen vor grundlegenden Änderungen und ermöglicht es ihnen gleichzeitig, von den
Verbesserungen des Open-Source-Projekts zu profitieren.

## Erweiterungspunkte und Anpassung

Während die Integration die Kernfunktionalität von Open WebUI unverändert bewahrt, bietet die Architektur
Erweiterungspunkte für plattformspezifische Verbesserungen.

**Integration von benutzerdefinierter Nachrichtenübermittlung**: Das PostMessage-Protokoll ermöglicht es der Plattform,
die Fähigkeiten der Chat-Oberfläche über die nativen Open WebUI-Funktionen hinaus zu erweitern. Benutzerdefinierte
Nachrichtentypen können plattformspezifische Workflows, Datenanzeigen oder Integrationspunkte auslösen, ohne den
Open-Source-Code ändern zu müssen.

**UI-Erweiterungs-Overlays**: Die Plattform kann zusätzliche UI-Elemente über die eingebettete Chat-Oberfläche legen –
Benachrichtigungs-Badges, Kontextindikatoren oder Schnellaktionsschaltflächen – ohne Open WebUI selbst zu ändern. Diese
Overlays erweitern die Funktionalität und bewahren gleichzeitig die Möglichkeit, die zugrundeliegende
Open-Source-Komponente zu aktualisieren.

**API-Abfangen und -Erweiterung**: Die Plattform kann API-Aufrufe zwischen der Chat-Oberfläche und den Backend-Diensten
abfangen und erweitern, indem sie plattformspezifischen Kontext hinzufügt, Antworten anreichert oder zusätzliche
Governance durchsetzt, ohne Open WebUI-Modifikationen zu erfordern.

**Theme- und Branding-Integration**: Unter Beibehaltung der Designsprache von Open WebUI wendet die Integration
Plattform-Theme-Einstellungen an – Farbschemata, Typografie, Ikonografie – um visuelle Konsistenz mit dem gesamten
Designsystem der Suite zu gewährleisten. Dieses Branding erfolgt durch CSS-Anpassung und nicht durch
Quellcode-Modifikation.

## Betriebliches Monitoring

Die Integrationsarchitektur ermöglicht ein umfassendes Monitoring der Gesundheit und Leistung der Chat-Oberfläche.

**Health-Check-Integration**: Die Plattform überwacht die Gesundheit des Open WebUI-Containers über
Standard-Health-Check-Endpunkte, erkennt Dienstausfälle und ermöglicht die automatische Wiederherstellung oder
Administratorbenachrichtigung, wenn die Chat-Funktionalität Probleme aufweist.

**Erfassung von Leistungsmetriken**: Nutzungsmetriken – Konversationszahlen, Antwortzeiten, Fehlerraten – fließen von
der Chat-Oberfläche zu den Beobachtbarkeitssystemen der Plattform, was Administratoren ermöglicht, die Leistung des
Chat-Dienstes zusammen mit anderen Plattformmetriken zu überwachen.

**Log-Aggregation**: Chat-Oberflächen-Logs werden mit Plattform-Logs in einer einheitlichen Logging-Infrastruktur
aggregiert, was eine umfassende Fehlerbehebung und die Erstellung von Audit-Trails ermöglicht, die Interaktionen über
mehrere Plattformkomponenten hinweg abdecken.

**Ressourcennutzungsverfolgung**: Die Plattform überwacht den Ressourcenverbrauch des Chat-Containers – CPU, Speicher,
Netzwerk – was die Kapazitätsplanung und die Sicherstellung der Skalierbarkeit des Chat-Dienstes ermöglicht, wenn
Benutzerzahlen und Konversationsvolumen zunehmen.

## Vorteile der Architektur

Diese Integrationsarchitektur bietet mehrere spezifische technische und betriebliche Vorteile.

**Unabhängige Entwicklung**: Open WebUI und die Plattform können sich unabhängig voneinander entwickeln. Neue Open
WebUI-Releases werden über Standard-Update-Prozesse integriert, ohne dass Änderungen am Plattformcode erforderlich sind.
Ebenso erfordern Plattformverbesserungen keine Änderungen an der Chat-Oberfläche.

**Klare Verantwortlichkeitsbereiche**: Die Architektur bewahrt klare Verantwortlichkeitsbereiche. Open WebUI kümmert
sich um exzellente Chat-Interaktionen. Die Plattform bietet Authentifizierung, Autorisierung, Wissensmanagement und
Agenten-Orchestrierung. Diese Trennung der Belange vereinfacht Tests, Debugging und Wartung.

**Bewahrung der Open-Source-Vorteile**: Durch das Einbetten statt des Forkings bewahrt die Plattform die
Open-Source-Vorteile von Open WebUI – Community-Beiträge, Sicherheitspatches, Funktionserweiterungen – ohne eine
benutzerdefinierte Variante pflegen zu müssen, die laufende Merge- und Konfliktlösungsbemühungen erfordert.

**Bereitstellungsflexibilität**: Organisationen können die vollständige Integration bereitstellen oder, falls die
Anforderungen es vorschreiben, Open WebUI durch alternative Chat-Oberflächen ersetzen, indem sie die gleichen
Einbettungs- und Nachrichtenmuster implementieren. Die Architektur erzeugt keine unwiderruflichen technischen Schulden
oder eine Anbieterbindung an eine bestimmte Chat-Technologie.

Diese Integrationsarchitektur zeigt, dass die Einführung von Open-Source-Komponenten keine Kompromisse bei der Qualität
der Plattformintegration oder des Benutzererlebnisses erfordert. Durchdachte Architekturmuster ermöglichen es dem Swiss
AI Hub, sowohl den Funktionsreichtum von Community-entwickelten Chat-Oberflächen als auch die Kohäsion einer
integrierten Unternehmens-KI-Plattform zu liefern.
