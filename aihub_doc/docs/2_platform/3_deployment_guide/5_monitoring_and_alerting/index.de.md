---
title: 'Monitoring & Alarmierung'
source_sha: "b2e5216169884e086ca621a49384c36b2ce62d6f8b8f2cea3aa478824ca77df5"
---

# Monitoring & Alarmierung

Ein produktives KI-System muss transparent, zuverlässig und vorhersehbar sein. Während es bei Tag 1 um beeindruckende Demos geht, dreht sich Tag 2 um die Aufrechterhaltung des Vertrauens durch operative Exzellenz. Der Swiss AI Hub bietet eine umfassende, integrierte Observability-Suite, um Ihnen ein vollständiges Bild über den Zustand, die Leistung und die Kosten Ihrer Plattform zu liefern.

Dieser Abschnitt erläutert die in die Plattform integrierten Schichten für Monitoring und Alarmierung. Sie erfahren, was wir messen, wie Sie es visualisieren können und wie das System Sie proaktiv über Probleme informiert.

## Die Säulen der Observability

Die Monitoring-Philosophie der Plattform basiert auf den branchenüblichen Säulen der Observability, die Antworten auf kritische operative Fragen liefern.

### 1. Statusprüfungen: „Funktioniert es gerade?"

Statusprüfungen sind der Herzschlag der Plattform, die kontinuierlich überprüfen, ob jede Komponente aktiv und funktionsfähig ist. Im Gegensatz zu Metriken oder Logs liefern sie eine einfache, sofortige Antwort auf die grundlegendste Frage.

Die Plattform verwendet einen mehrschichtigen Ansatz:
- **Native Docker-Checks**: Überwachen automatisch, ob Serviceprozesse ausgeführt werden und reagieren. Docker kann fehlerhafte Container neu starten, was eine Selbstheilung bei transienten Problemen ermöglicht.
- **Anwendungs-Endpunkt-Checks**: Services stellen dedizierte Health-Endpunkte (`/health`) bereit, die nicht nur die Aktivität, sondern auch die Bereitschaft zur Ausführung ihrer spezifischen Funktion überprüfen (z. B. kann die Datenbank eine Abfrage akzeptieren?).
- **Synthetische Probes**: Für Services ohne native Health-Endpunkte fragt die Plattform diese aktiv ab, um sicherzustellen, dass sie verfügbar und reaktionsschnell sind.

Jede Änderung des Gesundheitsstatus – von gesund zu ungesund, Service-Starts und -Stops – wird als strukturiertes Ereignis erfasst und bietet eine vollständige historische Aufzeichnung der Serviceverfügbarkeit.

### 2. Metriken: „Wie ist die Leistung?"

Metriken sind quantitative Messungen, die die Leistung und Ressourcennutzung im Zeitverlauf verfolgen. Sie sind unerlässlich für Trendanalysen, Kapazitätsplanung und die Identifizierung von Leistungsengpässen, bevor diese die Benutzer beeinträchtigen.

Die Plattform sammelt automatisch wichtige Metriken in zwei Hauptkategorien:
- **Infrastruktur-Metriken**: Daten auf Containerebene für jeden Dienst, einschließlich CPU-Auslastung, Speicherverbrauch, Netzwerkverkehr und Festplatten-I/O. Dies bietet eine klare Übersicht über die Ressourcennutzung und hilft bei der Kostenverwaltung und Kapazitätsplanung.
- **Anwendungsmetriken**: (In Bearbeitung) Sobald Services instrumentiert sind, werden sie detaillierte Leistungsdaten liefern, wie z. B. Latenzzeiten von API-Anfragen, Fehlerraten, Ausführungszeiten von KI-Agenten und den Durchsatz bei der Dokumentenverarbeitung.

Diese Metriken liefern die Daten, die zur Leistungsoptimierung, Budgetprognose und fundierten Entscheidungen über die Skalierung Ihrer Infrastruktur erforderlich sind.

### 3. Logs: „Was ist passiert und warum?"

Logs bieten eine detaillierte, chronologische Aufzeichnung jedes Ereignisses, das innerhalb der Plattform auftritt. Wenn ein Problem auftritt, sind Logs das primäre Werkzeug für die Ursachenanalyse und liefern den Kontext, der erforderlich ist, um genau zu verstehen, was passiert ist.

Die Plattform erfasst Logs aus mehreren Quellen:
- **Anwendungs-Logs**: Strukturierte Ausgabe aller Python-Services, einschließlich Informationsmeldungen, Warnungen und kritischer Fehler.
- **Container-Logs**: Alle `stdout`- und `stderr`-Ausgaben jedes Containers, die alles von Startmeldungen bis hin zu unbehandelten Ausnahmen erfassen.
- **Anfrage-Logs**: Aufzeichnungen von HTTP-Anfragen und deren Ergebnissen.
- **Sicherheits-Logs**: Audit-Trail von Authentifizierungsereignissen, Zugriffsversuchen und Berechtigungsprüfungen.

Alle Logs sind zentralisiert, strukturiert und durchsuchbar, sodass Sie Probleme schnell diagnostizieren, Aktivitäten prüfen und Nutzungsmuster analysieren können.

## Dashboards: Die vereinheitlichte Ansicht

Daten sind nur nützlich, wenn Sie sie verstehen können. Der Swiss AI Hub verwendet **SigNoz**, eine Open-Source-, OpenTelemetry-native Plattform, als zentrales Observability-Backend. Es bietet eine einzige, vereinheitlichte Schnittstelle zur Visualisierung all Ihrer Status-, Metrik- und Logdaten.

Out-of-the-box erhalten Sie Zugriff auf mehrere wichtige Dashboards:

- **Infrastrukturübersicht**: Eine übergeordnete Ansicht der CPU-, Speicher- und Netzwerkauslastung über alle Services hinweg, plus eine Echtzeitmatrix des Service-Zustands.
- **KI-Betriebs-Dashboard**: Spezialisierte Ansicht von KI-Aktivitäten, einschließlich Modellnutzung, Token-Verbrauch, Abfragelatenz und Kosten-pro-Operation-Verfolgung.
- **Anwendungsleistung**: Benutzerorientierte Service-Qualitätsmetriken, wie z. B. API-Antwortzeiten, Anfragemengen und Fehlerraten.
- **Log-Analyse**: Eine leistungsstarke Schnittstelle zum Suchen, Filtern und Analysieren von Logdaten aus jeder Komponente der Plattform.

::: details Spezialisierte Service-Dashboards
Für tiefere Einblicke enthält die Plattform auch integrierte Dashboards für spezifische Infrastrukturkomponenten:

- **Traefik (Reverse Proxy)**: Visualisiert Anfrage-Routing, Service-Zustand und TLS-Zertifikatsstatus.
- **Phoenix (LLM Observability)**: Verfolgt jede LLM-Operation und zeigt Token-Nutzung, Latenz und den vollständigen Prompt-/Response-Kontext zur Fehlerbehebung.
- **Dagster (Workflow Engine)**: Überwacht den Status, die Historie und die Leistung aller Datenaufnahme- und Verarbeitungspipelines.
:::

## Alarmierung: Proaktive Benachrichtigungen

Während Dashboards zum Abrufen von Informationen dienen, drängt die Alarmierung proaktiv kritische Informationen an Sie. Sie wandelt Ihre Observability-Daten in automatisierte Benachrichtigungen um und stellt sicher, dass Sie über Probleme informiert sind, oft bevor Ihre Benutzer es sind.

Das Alarmsystem ist hochflexibel und wird innerhalb Ihrer Observability-Plattform (z. B. SigNoz) konfiguriert, nicht fest in den Swiss AI Hub eincodiert. Dies ermöglicht es Ihnen, Benachrichtigungen an die spezifischen Bedürfnisse Ihrer Organisation anzupassen. Sie können Alarme konfigurieren für:

- **Kritische Serviceausfälle**: Sofortige Benachrichtigung, wenn ein Kernservice wie das API-Gateway oder die Datenbank ungesund wird.
- **Leistungsabbau**: Alarme, wenn API-Antwortzeiten Ziele überschreiten oder Fehlerraten zu steigen beginnen.
- **Ressourcenlimits**: Proaktive Warnungen, wenn die CPU-, Speicher- oder Speichernutzung Kapazitätsgrenzen erreicht.
- **Kostenmanagement**: Benachrichtigungen, wenn der Verbrauch von KI-Tokens oder die Cloud-Ausgaben vordefinierte Budgetschwellenwerte erreichen.
- **Sicherheitsereignisse**: Alarme bei verdächtigen Aktivitäten, wie z. B. wiederholten fehlgeschlagenen Anmeldeversuchen.

Alarme können an verschiedene Kanäle weitergeleitet werden, darunter E-Mail, Slack, Microsoft Teams und Incident-Management-Plattformen wie PagerDuty.

## Die Observability-Grundlage: OpenTelemetry

Das gesamte Monitoring- und Alarmierungssystem basiert auf **OpenTelemetry (OTel)**, einem von der CNCF graduierten, herstellerneutralen Standard für Observability.

Dies ist eine bewusste architektonische Entscheidung mit erheblichen Vorteilen:

- **Keine Herstellerbindung**: Die Plattform gibt Daten in einem Standardformat aus. Während SigNoz der Standard ist, steht es Ihnen frei, Telemetriedaten an jedes OTel-kompatible Backend zu senden – sei es Grafana, Datadog, Splunk oder Ihr vorhandenes unternehmensweites Monitoring-Tool. Das Hinzufügen eines neuen Ziels ist eine Konfigurationsänderung, kein Re-Instrumentierungsprojekt.
- **Vereinheitlichte Daten**: OTel bietet eine konsistente Möglichkeit zum Sammeln von Metriken, Logs und Traces. Dies bedeutet, dass alle Ihre Daten automatisch korreliert werden, sodass Sie nahtlos von einem Leistungsspitzenwert zu den genauen Logs und Traces wechseln können, die ihn erklären.
- **Zukunftssicher**: Durch die Nutzung eines Industriestandards profitiert die Plattform von der kontinuierlichen Innovation der gesamten Observability-Community.

Alle Telemetriedaten fließen durch einen zentralen **OpenTelemetry Collector** innerhalb der Plattform. Diese Komponente empfängt Daten von allen Services, reichert sie mit nützlichen Metadaten an und exportiert sie sicher an Ihr(e) gewähltes/n Ziel(e). Diese Architektur stellt sicher, dass Sie die vollständige Kontrolle und Eigentümerschaft über Ihre Observability-Daten haben, genau wie bei dem Rest der Plattform.
