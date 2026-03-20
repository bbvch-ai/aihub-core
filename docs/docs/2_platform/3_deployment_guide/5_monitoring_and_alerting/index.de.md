---
title: Überwachung und Alarmierung
source_sha: b98ed1c135f58cd35172468475e01986a1cb3f5b8efb92923b6bc518c4b0f801
---

# Überwachung und Alarmierung

Ein KI-Produktionssystem muss transparent, zuverlässig und vorhersagbar sein. Während es an Tag 1 um beeindruckende
Demos geht, geht es an Tag 2 darum, Vertrauen durch operationale Exzellenz aufrechtzuerhalten. Der Swiss AI Hub bietet
eine umfassende, integrierte Observability-Suite, um Ihnen ein vollständiges Bild der Gesundheit, Leistung und Kosten
Ihrer Plattform zu liefern.

Dieser Abschnitt erklärt die in die Plattform integrierten Schichten für Monitoring und Alarmierung. Sie erfahren, was
wir messen, wie Sie es visualisieren können und wie das System Sie proaktiv über Probleme informiert.

## Die Säulen der Observability

Die Monitoring-Philosophie der Plattform basiert auf den branchenüblichen Säulen der Observability und liefert Antworten
auf kritische operationale Fragen.

### 1. Health Checks: „Funktioniert es gerade?“

Health Checks sind der Herzschlag der Plattform und überprüfen kontinuierlich, ob jede Komponente aktiv und
funktionsfähig ist. Im Gegensatz zu Metriken oder Logs liefern sie eine einfache, unmittelbare Antwort auf die
grundlegendste Frage.

Die Plattform verwendet einen mehrschichtigen Ansatz:

- **Native Docker-Checks**: Überwachen automatisch, ob Service-Prozesse laufen und reagieren. Docker kann ungesunde
  Container neu starten und ermöglicht so eine Selbstheilung bei vorübergehenden Problemen.
- **Application Endpoint Checks**: Services legen dedizierte Health-Endpoints (`/health`) frei, die nicht nur die
  Liveness, sondern auch die Bereitschaft zur Ausführung ihrer spezifischen Funktion überprüfen (z.B. kann die Datenbank
  eine Abfrage akzeptieren?).
- **Synthetic Probes**: Für Services ohne native Health-Endpoints pollt die Plattform diese aktiv, um sicherzustellen,
  dass sie verfügbar und reaktionsfähig sind.

Jede Änderung des Health-Status – von gesund zu ungesund, Service-Starts und -Stopps – wird als strukturiertes Ereignis
erfasst und bietet eine vollständige historische Aufzeichnung der Service-Verfügbarkeit.

### 2. Metriken: „Wie ist die Performance?“

Metriken sind quantitative Messungen, die die Performance und Ressourcenauslastung über die Zeit verfolgen. Sie sind
unerlässlich für Trendanalysen, Kapazitätsplanung und die Identifizierung von Performance-Engpässen, bevor diese Nutzer
beeinträchtigen.

Die Plattform sammelt automatisch Schlüsselmetriken in zwei Hauptkategorien:

- **Infrastruktur-Metriken**: Daten auf Containerebene für jeden Service, einschliesslich CPU-Auslastung,
  Speicherverbrauch, Netzwerkverkehr und Disk I/O. Dies bietet einen klaren Überblick über die Ressourcennutzung und
  hilft beim Kostenmanagement und der Kapazitätsplanung.
- **Applikations-Metriken**: (In Arbeit) Wenn Services instrumentiert werden, werden sie detaillierte Performance-Daten
  wie API-Anfrage-Latenz, Fehlerraten, Ausführungszeiten von KI-Agents und den Durchsatz bei der Dokumentenverarbeitung
  emittieren.

Diese Metriken liefern die Daten, die zur Optimierung der Performance, zur Budgetprognose und zur fundierten
Entscheidungsfindung bezüglich der Skalierung Ihrer Infrastruktur erforderlich sind.

### 3. Logs: „Was ist passiert und warum?“

Logs liefern eine detaillierte, chronologische Aufzeichnung jedes Ereignisses, das innerhalb der Plattform auftritt.
Wenn ein Problem auftritt, sind Logs das primäre Werkzeug für die Ursachenanalyse und bieten den Kontext, der zum
genauen Verständnis des Geschehens erforderlich ist.

Die Plattform erfasst Logs aus mehreren Quellen:

- **Applikations-Logs**: Strukturierte Ausgabe aller Python-Services, einschliesslich informativer Nachrichten,
  Warnungen und kritischer Fehler.
- **Container-Logs**: Alle `stdout`- und `stderr`-Ausgaben jedes Containers, die alles von Startmeldungen bis zu
  unbehandelten Ausnahmen erfassen.
- **Request Logs**: Aufzeichnungen von HTTP-Anfragen und deren Ergebnissen.
- **Security Logs**: Audit-Trail von Authentifizierungsereignissen, Zugriffsversuchen und Berechtigungsprüfungen.

Alle Logs sind zentralisiert, strukturiert und durchsuchbar, sodass Sie Probleme schnell diagnostizieren, Aktivitäten
auditieren und Nutzungsmuster analysieren können.

## Dashboards: Die einheitliche Ansicht

Daten sind nur nützlich, wenn Sie sie verstehen können. Der Swiss AI Hub verwendet **SigNoz**, eine Open-Source-,
OpenTelemetry-native Plattform, als zentrales Observability-Backend. Sie bietet eine einzige, einheitliche Oberfläche
zur Visualisierung all Ihrer Health-, Metrik- und Log-Daten.

Out-of-the-box erhalten Sie Zugang zu mehreren Schlüssel-Dashboards:

- **Infrastruktur-Übersicht**: Eine übergeordnete Ansicht der CPU-, Speicher- und Netzwerkauslastung über alle Services
  hinweg, plus eine Echtzeitmatrix der Service-Health.
- **AI Operations Dashboard**: Spezialisierte Ansicht von KI-Aktivitäten, einschliesslich Modellnutzung,
  Token-Verbrauch, Abfragelatenz und Kosten pro Operation-Tracking.
- **Applikations-Performance**: Nutzerorientierte Service-Qualitätsmetriken wie API-Antwortzeiten, Anfragevolumen und
  Fehlerraten.
- **Log-Analyse**: Eine leistungsstarke Oberfläche zum Suchen, Filtern und Analysieren von Log-Daten jeder Komponente in
  der Plattform.

::: details Spezialisierte Service-Dashboards
Für tiefere Einblicke enthält die Plattform auch integrierte Dashboards für spezifische Infrastrukturkomponenten:

- **Traefik (Reverse Proxy)**: Visualisiert Request-Routing, Service-Health und den Status von TLS-Zertifikaten.
- **Langfuse (LLM Observability)**: Traced jeden LLM-Vorgang und zeigt Token-Nutzung, Latenz, Kostenattribution sowie
  den vollständigen Prompt/Response-Kontext. Bietet auch Dataset-Management und Experimentbewertung.
- **Dagster (Workflow Engine)**: Überwacht den Status, die Historie und die Performance aller Datenaufnahme- und
  Verarbeitungs-Pipelines.
:::

## Alarmierung: Proaktive Benachrichtigungen

Während Dashboards dazu dienen, Informationen abzurufen, stösst die Alarmierung proaktiv kritische Informationen an Sie.
Sie wandelt Ihre Observability-Daten in automatisierte Benachrichtigungen um und stellt sicher, dass Sie sich der
Probleme oft bewusst sind, bevor Ihre Nutzer es sind.

Das Alarmierungssystem ist hochflexibel und wird innerhalb Ihrer Observability-Plattform (z.B. SigNoz) konfiguriert,
nicht fest in den Swiss AI Hub eincodiert. Dies ermöglicht es Ihnen, Benachrichtigungen an die spezifischen Bedürfnisse
Ihrer Organisation anzupassen. Sie können Alarme konfigurieren für:

- **Kritische Service-Ausfälle**: Sofortige Benachrichtigung, wenn ein Kern-Service wie das API-Gateway oder die
  Datenbank ungesund wird.
- **Performance-Degradation**: Alarme, wenn API-Antwortzeiten Ziele überschreiten oder Fehlerraten zu steigen beginnen.
- **Ressourcenlimits**: Proaktive Warnungen, wenn die CPU-, Speicher- oder Speicherauslastung sich den Kapazitätsgrenzen
  nähert.
- **Kostenmanagement**: Benachrichtigungen, wenn der KI-Token-Verbrauch oder die Cloud-Ausgaben vordefinierte
  Budgetschwellenwerte erreichen.
- **Sicherheitsereignisse**: Alarme bei verdächtigen Aktivitäten, wie wiederholten fehlgeschlagenen Anmeldeversuchen.

Alarme können an verschiedene Kanäle weitergeleitet werden, einschliesslich E-Mail, Slack, Microsoft Teams und
Incident-Management-Plattformen wie PagerDuty.

## Die Observability-Grundlage: OpenTelemetry

Das gesamte Monitoring- und Alarmierungssystem basiert auf **OpenTelemetry (OTel)**, einem von der CNCF graduierten,
herstellerneutralen Standard für Observability.

Dies ist eine bewusste architektonische Entscheidung mit erheblichen Vorteilen:

- **Kein Vendor Lock-in**: Die Plattform emittiert Daten in einem Standardformat. Während SigNoz die Standardlösung ist,
  steht es Ihnen frei, Telemetriedaten an jedes OTel-kompatible Backend zu senden – sei es Grafana, Datadog, Splunk oder
  Ihr bestehendes Unternehmens-Monitoring-Tool. Das Hinzufügen eines neuen Ziels ist eine Konfigurationsänderung, kein
  Re-Instrumentation-Projekt.
- **Vereinheitlichte Daten**: OTel bietet eine konsistente Möglichkeit, Metriken, Logs und Traces zu sammeln. Dies
  bedeutet, dass all Ihre Daten automatisch korreliert werden, sodass Sie nahtlos von einem Performance-Metrik-Spike zu
  den exakten Logs und Traces wechseln können, die ihn erklären.
- **Zukunftssicher**: Durch die Nutzung eines Industriestandards profitiert die Plattform von der kontinuierlichen
  Innovation der gesamten Observability-Community.

Alle Telemetriedaten fliessen durch einen zentralen **OpenTelemetry Collector** innerhalb der Plattform. Diese
Komponente empfängt Daten von allen Services, reichert sie mit nützlichen Metadaten an und exportiert sie sicher an
Ihre(n) gewählte(n) Zielort(e). Diese Architektur stellt sicher, dass Sie die vollständige Kontrolle und
Eigentümerschaft über Ihre Observability-Daten haben, genau wie über den Rest der Plattform.
