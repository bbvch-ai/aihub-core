---
title: Integrationsarchitektur
source_sha: "03bcd84fd2be561f8a251a79d23d0c9924453eccc50536beca6bf3ebc38ba663"
---

# Integrationsarchitektur

Der Swiss AI Hub bettet **Open WebUI** direkt in seine Oberfläche ein, anstatt auf ein separates Deployment zu verlinken. Dies gewährleistet eine einheitliche Benutzererfahrung, wobei die Open-Source-Komponente von der Plattform-Infrastruktur getrennt bleibt.

## Funktionsweise der Einbettung

Die Plattform verwendet einen Iframe, um die komplette Open WebUI-Oberfläche innerhalb des Servicebereichs der Suite zu rendern. Benutzer sehen eine einzige integrierte Anwendung. Die Architektur wahrt die Trennung zwischen der Open-Source-Komponente und der Plattform-Infrastruktur.

Wenn Benutzer zum Chat-Service navigieren, nimmt Open WebUI den gesamten Servicebereich ein. Die Navigationsleiste der Suite bleibt zugänglich, sodass Benutzer zu anderen Services wechseln können, ohne ihren Chat-Kontext zu verlieren.

Die Einbettung bewahrt Open WebUI's komplette Oberfläche und den vollen Funktionsumfang. Tastenkombinationen, Drag-and-Drop-Dateiverwaltung und Konversationsmanagement funktionieren wie in der eigenständigen Anwendung. Die eingebettete Oberfläche passt sich an verschiedene Bildschirmgrößen an – Desktop-Bildschirme bieten einen erweiterten Arbeitsbereich, während mobile Geräte den funktionalen Zugriff erhalten.

## Kommunikation zwischen Komponenten

Der Iframe und die Suite-Plattform kommunizieren über die Browser-Standard-PostMessage-API. Dies ermöglicht sicheres Cross-Origin-Messaging, wobei die Sicherheitsgrenzen zwischen den Komponenten gewahrt bleiben.

Die Chatschnittstelle und die Plattform tauschen strukturierte Nachrichten für Benutzerinteraktionen, Navigationsanfragen und Zustandsynchronisation aus. Wenn Benutzer innerhalb der Chatschnittstelle Plattformfunktionen anfordern – wie das Anzeigen von Wissensquellen oder Ausführungs-Traces –, sendet der Chat Nachrichten, die die Navigation und Datenanzeige auslösen.

Nachrichten folgen definierten Verträgen, die Absicht, Parameter und Verhalten festlegen. Typen umfassen Anforderungen zur Quellenanzeige, Anforderungen zur Trace-Sichtbarkeit und Kontextsynchronisation.

Wenn die Nachrichtenübermittlung fehlschlägt oder die Plattform Anfragen nicht erfüllen kann, erhalten Benutzer Feedback statt stiller Fehler.

## Authentifizierung und Sicherheit

Die Plattform und Open WebUI teilen sich die Authentifizierung über OAuth. Benutzer authentifizieren sich einmal bei der Swiss AI Hub Suite, und diese Authentifizierung wird an die eingebettete Instanz weitergegeben.

Die Plattform setzt Berechtigungsgrenzen für KI-Modelle, Wissensdatenbanken und Agent-Fähigkeiten durch. Benutzer können über die Chatschnittstelle nicht auf das zugreifen, worauf sie über andere Services nicht zugreifen können.

Sitzungen bleiben zwischen Plattform und Chat synchronisiert. Das Abmelden von der Suite beendet die Chatsitzung. Timeouts und Verlängerungen werden über beide Komponenten hinweg koordiniert.

Die Kommunikation erfolgt über sichere Kanäle mit Verschlüsselung und Validierung. Die Iframe-Integration umfasst Sicherheits-Header und Content Security Policies, um Cross-Site-Scripting zu verhindern.

## Konfiguration und Deployment

Open WebUI wird als unabhängiger Docker-Container innerhalb der Plattform deployt. Dies bietet Isolation, während der Lebenszyklus – Starten, Stoppen und Aktualisieren – zusammen mit anderen Services verwaltet wird.

Der Chat-Container greift über Standardmuster auf die Plattform-Infrastruktur wie Datenbanken, Objektspeicher und Nachrichtenwarteschlangen zu. Chat-Daten bleiben mit anderen Plattformdaten erhalten, was eine einheitliche Sicherung und Daten-Governance unterstützt.

Konfigurationsparameter werden über Umgebungsvariablen und Konfigurationsdateien weitergegeben. Authentifizierungsendpunkte, Modellzugriffs-URLs und Feature-Toggles bleiben über Entwicklungs-, Test- und Produktionsumgebungen hinweg konsistent.

Die Plattform testet neue Open WebUI Releases in isolierten Umgebungen vor dem Produktions-Deployment. Dies schützt vor Breaking Changes und ermöglicht gleichzeitig den Zugang zu Verbesserungen.

## Erweiterungspunkte

Die Integration bewahrt die Kernfunktionalität von Open WebUI, fügt aber plattformspezifische Erweiterungen hinzu.

Das PostMessage-Protokoll erweitert die Chat-Fähigkeiten über native Funktionen hinaus. Benutzerdefinierte Nachrichtentypen lösen Plattform-Workflows oder Datenanzeigen aus, ohne die Open-Source-Codebasis zu ändern.

Die Plattform kann UI-Elemente wie Benachrichtigungsabzeichen oder Schnellaktionsschaltflächen überlagern, ohne Open WebUI zu modifizieren. Diese verbessern die Funktionalität und halten Updates einfach.

API-Aufrufe zwischen der Chatschnittstelle und Backend-Services können abgefangen werden, um Kontext hinzuzufügen, Antworten anzureichern oder Governance durchzusetzen.

Plattform-Theme-Einstellungen werden durch CSS-Anpassung und nicht durch Quellcode-Modifikation angewendet. Dies gewährleistet visuelle Konsistenz mit dem Design der Suite.

## Monitoring

Die Plattform überwacht die Container-Gesundheit von Open WebUI über Standard-Endpunkte. Service-Fehler lösen automatische Wiederherstellung oder Administrator-Benachrichtigungen aus.

Nutzungsmetriken – Konversationsanzahlen, Antwortzeiten, Fehlerraten – fließen in die Plattform-Observability-Systeme. Administratoren überwachen die Performance des Chat-Services zusammen mit anderen Metriken.

Chat-Logs aggregieren mit Plattform-Logs in einer einheitlichen Infrastruktur. Dies unterstützt die Fehlerbehebung über mehrere Komponenten hinweg.

Die Überwachung des Ressourcenverbrauchs – CPU, Speicher, Netzwerk – unterstützt die Kapazitätsplanung, wenn die Benutzerzahlen und Konversationsvolumina wachsen.

## Vorteile dieses Ansatzes

Open WebUI und die Plattform entwickeln sich unabhängig voneinander. Neue Releases werden über Standardprozesse ohne Änderungen am Plattform-Code integriert. Plattform-Erweiterungen erfordern keine Änderungen an der Chat-Schnittstelle.

Verantwortlichkeiten bleiben klar. Open WebUI kümmert sich um Chat-Interaktionen. Die Plattform bietet Authentifizierung, Autorisierung, Wissensmanagement und Agent-Orchestrierung. Diese Trennung vereinfacht das Testen und die Wartung.

Die Einbettung statt eines Forking bewahrt die Vorteile von Open Source. Die Plattform erhält Community-Beiträge, Sicherheitspatches und Funktionen, ohne eine kundenspezifische Variante pflegen zu müssen.

Organisationen können Open WebUI durch alternative Chatschnittstellen ersetzen, indem sie dieselben Einbettungs- und Messaging-Muster verwenden. Dies vermeidet eine Abhängigkeit von einer bestimmten Chat-Technologie.
