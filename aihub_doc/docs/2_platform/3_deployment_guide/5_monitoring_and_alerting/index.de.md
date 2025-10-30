---
title: Monitoring & Alerting
source_sha: 4bd30a24c6895c3f17dd700af55d4968c6b5c4f1d191c0bd8a38c3a4f1bf2765
---

# Monitoring & Alerting

Ein produktives KI-System muss transparent, zuverlässig und vorhersehbar sein. Während es an Tag 1 um beeindruckende
Demos geht, steht an Tag 2 die Aufrechterhaltung des Vertrauens durch operative Exzellenz im Vordergrund. Der Swiss AI
Hub bietet eine umfassende, integrierte Observability Suite, um Ihnen ein vollständiges Bild der Gesundheit, Leistung
und Kosten Ihrer Plattform zu liefern.

Dieser Abschnitt erläutert die Ebenen der Überwachung und Alarmierung, die in die Plattform integriert sind. Sie
erfahren, was wir messen, wie Sie es visualisieren können und wie das System Sie proaktiv über Probleme benachrichtigt.

## Die Säulen der Observability

Die Überwachungsphilosophie der Plattform basiert auf den branchenüblichen Säulen der Observability und liefert
Antworten auf kritische operative Fragen.

### 1. Health Checks: „Funktioniert es gerade?“

Health Checks sind der Herzschlag der Plattform und überprüfen kontinuierlich, ob jede Komponente aktiv und
funktionsfähig ist. Im Gegensatz zu Metriken oder Logs liefern sie eine einfache, unmittelbare Antwort auf die
grundlegendste Frage.

Die Plattform verwendet einen mehrschichtigen Ansatz:

- **Native Docker Checks**: Überwachen automatisch, ob Dienstprozesse laufen und reagieren. Docker kann fehlerhafte
  Container neu starten und ermöglicht so eine Selbstheilung bei vorübergehenden Problemen.
- **Application Endpoint Checks**: Dienste stellen dedizierte Health-Endpunkte (`/health`) bereit, die nicht nur die
  Liveness, sondern auch die Readiness zur Ausführung ihrer spezifischen Funktion überprüfen (z. B. kann die Datenbank
  eine Abfrage akzeptieren?).
- **Synthetic Probes**: Für Dienste ohne native Health-Endpunkte befragt die Plattform diese aktiv, um sicherzustellen,
  dass sie verfügbar und reaktionsfähig sind.

Jede Änderung des Gesundheitsstatus – von fehlerfrei zu fehlerhaft, Dienststarts und -stopps – wird als strukturiertes
Ereignis erfasst und bietet eine vollständige historische Aufzeichnung der Dienstverfügbarkeit.

### 2. Metriken: „Wie ist die Leistung?“

Metriken sind quantitative Messungen, die die Leistung und Ressourcennutzung über die Zeit verfolgen. Sie sind
unerlässlich für Trendanalysen, Kapazitätsplanung und die Identifizierung von Leistungsengpässen, bevor diese Benutzer
beeinträchtigen.

Die Plattform sammelt automatisch wichtige Metriken in zwei Hauptkategorien:

- **Infrastrukturmetriken**: Container-spezifische Daten für jeden Dienst, einschließlich CPU-Auslastung,
  Speicherverbrauch, Netzwerkverkehr und Disk I/O. Dies bietet eine klare Übersicht über die Ressourcennutzung und hilft
  bei Kostenmanagement und Kapazitätsplanung.
- **Anwendungsmetriken**: (In Bearbeitung) Wenn Dienste instrumentiert werden, geben sie detaillierte Leistungsdaten
  aus, wie z. B. API-Anforderungslatenz, Fehlerraten, Ausführungszeiten von KI-Agenten und
  Dokumentenverarbeitungsdurchsatz.

Diese Metriken liefern die Daten, die zur Leistungsoptimierung, Budgetprognose und fundierten Entscheidungen bezüglich
der Skalierung Ihrer Infrastruktur erforderlich sind.

### 3. Logs: „Was ist passiert und warum?“

Logs liefern eine detaillierte, chronologische Aufzeichnung jedes Ereignisses, das innerhalb der Plattform auftritt.
Wenn ein Problem auftritt, sind Logs das primäre Werkzeug für die Ursachenanalyse und bieten den Kontext, der zum
genauen Verständnis des Geschehenen erforderlich ist.

Die Plattform erfasst Logs aus mehreren Quellen:

- **Application Logs**: Strukturierte Ausgabe aller Python-Dienste, einschließlich Informationsmeldungen, Warnungen und
  kritischer Fehler.
- **Container Logs**: Alle `stdout`- und `stderr`-Ausgaben von jedem Container, die alles von Startmeldungen bis zu
  unbehandelten Ausnahmen erfassen.
- **Request Logs**: Aufzeichnungen von HTTP-Anforderungen und deren Ergebnissen.
- **Security Logs**: Audit-Trail von Authentifizierungsereignissen, Zugriffsversuchen und Berechtigungsprüfungen.

Alle Logs sind zentralisiert, strukturiert und durchsuchbar, sodass Sie Probleme schnell diagnostizieren, Aktivitäten
überprüfen und Nutzungsmuster analysieren können.

## Dashboards: Die einheitliche Ansicht

Daten sind nur nützlich, wenn Sie sie verstehen können. Der Swiss AI Hub verwendet **SigNoz**, eine Open-Source-,
OpenTelemetry-native Plattform, als zentrales Observability-Backend. Sie bietet eine einzige, einheitliche Oberfläche
zur Visualisierung all Ihrer Gesundheits-, Metrik- und Logdaten.

Out-of-the-box erhalten Sie Zugriff auf mehrere wichtige Dashboards:

- **Infrastruktur-Übersicht**: Eine übergeordnete Ansicht der CPU-, Speicher- und Netzwerkauslastung über alle Dienste
  hinweg, plus eine Echtzeit-Matrix des Dienstzustands.
- **KI-Operations-Dashboard**: Spezialisierte Ansicht von KI-Aktivitäten, einschließlich Modellnutzung, Token-Verbrauch,
  Abfragelatenz und Nachverfolgung der Kosten pro Operation.
- **Anwendungsleistung**: Benutzerorientierte Dienstqualitätsmetriken, wie z. B. API-Antwortzeiten, Anforderungsvolumen
  und Fehlerraten.
- **Log-Analyse**: Eine leistungsstarke Oberfläche zum Suchen, Filtern und Analysieren von Logdaten aus jeder Komponente
  der Plattform.

::: details Spezialisierte Dienst-Dashboards
Für tiefere Einblicke enthält die Plattform auch integrierte Dashboards für spezifische Infrastrukturkomponenten:

- **Traefik (Reverse Proxy)**: Visualisiert Anforderungs-Routing, Dienstzustand und TLS-Zertifikatstatus.
- **Phoenix (LLM Observability)**: Verfolgt jede LLM-Operation und zeigt Token-Nutzung, Latenz und den vollständigen
  Prompt/Response-Kontext zur Fehlerbehebung an.
- **Dagster (Workflow Engine)**: Überwacht den Status, die Historie und die Leistung aller Datenaufnahme- und
  Verarbeitungspipelines.
:::

## Alarmierung: Proaktive Benachrichtigungen

Während Dashboards zum Abrufen von Informationen dienen, drängt die Alarmierung proaktiv kritische Informationen an Sie.
Sie wandelt Ihre Observability-Daten in automatisierte Benachrichtigungen um und stellt sicher, dass Sie oft vor Ihren
Benutzern über Probleme informiert sind.

Das Alarmierungssystem ist hochflexibel und wird innerhalb Ihrer Observability-Plattform (z. B. SigNoz) konfiguriert,
nicht fest in den Swiss AI Hub integriert. Dies ermöglicht es Ihnen, Benachrichtigungen an die spezifischen Bedürfnisse
Ihrer Organisation anzupassen. Sie können Alarme konfigurieren für:

- **Kritische Dienstausfälle**: Sofortige Benachrichtigung, wenn ein Kerndienst wie das API-Gateway oder die Datenbank
  fehlerhaft wird.
- **Leistungsverschlechterung**: Alarme, wenn API-Antwortzeiten Ziele überschreiten oder Fehlerraten zu steigen
  beginnen.
- **Ressourcenlimits**: Proaktive Warnungen, wenn die CPU-, Speicher- oder Speicherauslastung Kapazitätsgrenzen
  erreicht.
- **Kostenmanagement**: Benachrichtigungen, wenn der KI-Token-Verbrauch oder die Cloud-Ausgaben vordefinierte
  Budgetschwellenwerte erreichen.
- **Sicherheitsereignisse**: Alarme bei verdächtigen Aktivitäten, wie z. B. wiederholten fehlgeschlagenen
  Anmeldeversuchen.

Alarme können an verschiedene Kanäle weitergeleitet werden, darunter E-Mail, Slack, Microsoft Teams und
Incident-Management-Plattformen wie PagerDuty.

## Die Observability-Grundlage: OpenTelemetry

Das gesamte Überwachungs- und Alarmierungssystem basiert auf **OpenTelemetry (OTel)**, einem von der CNCF graduierten,
herstellerneutralen Standard für Observability.

Dies ist eine bewusste architektonische Entscheidung mit erheblichen Vorteilen:

- **Keine Herstellerbindung (Vendor Lock-in)**: Die Plattform gibt Daten in einem Standardformat aus. Während SigNoz der
  Standard ist, steht es Ihnen frei, Telemetriedaten an jedes OTel-kompatible Backend zu senden – sei es Grafana,
  Datadog, Splunk oder Ihr bestehendes Enterprise-Monitoring-Tool. Das Hinzufügen eines neuen Ziels ist eine
  Konfigurationsänderung, kein Re-Instrumentierungsprojekt.
- **Vereinheitlichte Daten**: OTel bietet eine konsistente Möglichkeit, Metriken, Logs und Traces zu sammeln. Das
  bedeutet, dass alle Ihre Daten automatisch korreliert werden, sodass Sie nahtlos von einem Performance-Metrik-Spike zu
  den exakten Logs und Traces übergehen können, die ihn erklären.
- **Zukunftssicher**: Durch die Aufbau auf einem Industriestandard profitiert die Plattform von der kontinuierlichen
  Innovation der gesamten Observability-Community.

Alle Telemetriedaten fließen durch einen zentralen **OpenTelemetry Collector** innerhalb der Plattform. Diese Komponente
empfängt Daten von allen Diensten, reichert sie mit nützlichen Metadaten an und exportiert sie sicher an Ihr(e)
gewähltes(n) Ziel(e). Diese Architektur stellt sicher, dass Sie die vollständige Kontrolle und Hoheit über Ihre
Observability-Daten haben, genau wie über den Rest der Plattform.
