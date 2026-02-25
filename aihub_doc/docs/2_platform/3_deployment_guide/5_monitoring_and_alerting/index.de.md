```markdown
---
title: Monitoring & Alarmierung
source_sha: "69330bf1595a2c3b8157fd70491a3699a298aecf3f3a0ceedc46b56959bbc078"
---

# Monitoring & Alarmierung

Ein produktives KI-System muss transparent, zuverlässig und vorhersehbar sein. Während es bei Tag 1 um beeindruckende Demos geht, dreht sich Tag 2 darum, Vertrauen durch operative Exzellenz aufrechtzuerhalten. Der Swiss AI Hub bietet eine umfassende, integrierte Observability-Suite, um Ihnen ein vollständiges Bild der Gesundheit, Performance und Kosten Ihrer Plattform zu geben.

Dieser Abschnitt erläutert die in die Plattform integrierten Ebenen des Monitorings und der Alarmierung. Sie erfahren, was wir messen, wie Sie es visualisieren können und wie das System Sie proaktiv über Probleme benachrichtigt.

## Die Säulen der Observability

Die Monitoring-Philosophie der Plattform basiert auf den branchenüblichen Säulen der Observability und liefert Antworten auf kritische operative Fragen.

### 1. Health Checks: „Funktioniert es gerade?“

Health Checks sind der Herzschlag der Plattform und überprüfen kontinuierlich, ob jede Komponente aktiv und funktionsfähig ist. Im Gegensatz zu Metriken oder Logs liefern sie eine einfache, sofortige Antwort auf die grundlegendste Frage.

Die Plattform verwendet einen mehrschichtigen Ansatz:

-   **Native Docker Checks**: Überwachen automatisch, ob Service-Prozesse laufen und responsiv sind. Docker kann ungesunde Container neu starten, was eine Selbstheilung bei vorübergehenden Problemen ermöglicht.
-   **Application Endpoint Checks**: Services exponieren dedizierte Health Endpoints (`/health`), die nicht nur die Liveness, sondern auch die Readiness zur Ausführung ihrer spezifischen Funktion überprüfen (z. B. kann die Datenbank eine Abfrage akzeptieren?).
-   **Synthetic Probes**: Für Services ohne native Health Endpoints fragt die Plattform diese aktiv ab, um sicherzustellen, dass sie verfügbar und responsiv sind.

Jede Änderung des Health-Status – von gesund zu ungesund, Service-Starts und -Stopps – wird als strukturiertes Ereignis erfasst und bietet eine vollständige historische Aufzeichnung der Service-Verfügbarkeit.

### 2. Metriken: „Wie ist die Performance?“

Metriken sind quantitative Messungen, die die Performance und Ressourcennutzung über die Zeit verfolgen. Sie sind unerlässlich für Trendanalysen, Kapazitätsplanung und die Identifizierung von Performance-Engpässen, bevor diese Benutzer beeinträchtigen.

Die Plattform sammelt automatisch Schlüsselmetriken in zwei Hauptkategorien:

-   **Infrastruktur-Metriken**: Container-spezifische Daten für jeden Service, einschließlich CPU-Auslastung, Speicherverbrauch, Netzwerk-Traffic und Disk-I/O. Dies bietet eine klare Übersicht über die Ressourcennutzung und hilft beim Kostenmanagement und der Kapazitätsplanung.
-   **Applikations-Metriken**: (In Arbeit) Sobald Services instrumentiert sind, werden sie detaillierte Performance-Daten emittieren, wie z. B. API-Request-Latenz, Fehlerraten, Ausführungszeiten von KI-Agents und Durchsatz bei der Dokumentenverarbeitung.

Diese Metriken liefern die Daten, die zur Optimierung der Performance, zur Budgetprognose und zur fundierten Entscheidungsfindung bei der Skalierung Ihrer Infrastruktur erforderlich sind.

### 3. Logs: „Was ist passiert und warum?“

Logs bieten eine detaillierte, chronologische Aufzeichnung jedes Ereignisses, das innerhalb der Plattform auftritt. Wenn ein Problem auftritt, sind Logs das primäre Tool für die Ursachenanalyse und bieten den Kontext, der benötigt wird, um genau zu verstehen, was passiert ist.

Die Plattform erfasst Logs aus mehreren Quellen:

-   **Applikations-Logs**: Strukturierte Ausgabe aller Python-Services, einschließlich informativer Meldungen, Warnungen und kritischer Fehler.
-   **Container-Logs**: Alle `stdout`- und `stderr`-Ausgaben jedes Containers, die alles von Startmeldungen bis zu unbehandelten Ausnahmen erfassen.
-   **Request-Logs**: Aufzeichnungen von HTTP-Anfragen und deren Ergebnissen.
-   **Security-Logs**: Audit-Trail von Authentifizierungsereignissen, Zugriffsversuchen und Berechtigungsprüfungen.

Alle Logs sind zentralisiert, strukturiert und durchsuchbar, sodass Sie Probleme schnell diagnostizieren, Aktivitäten auditieren und Nutzungsmuster analysieren können.

## Dashboards: Die einheitliche Ansicht

Daten sind nur dann nützlich, wenn man sie verstehen kann. Der Swiss AI Hub verwendet **SigNoz**, eine Open-Source, OpenTelemetry-native Plattform, als sein zentrales Observability-Backend. Es bietet eine einzige, einheitliche Oberfläche zur Visualisierung all Ihrer Health-, Metrik- und Log-Daten.

Standardmäßig haben Sie Zugriff auf mehrere wichtige Dashboards:

-   **Infrastruktur-Übersicht**: Eine übergeordnete Ansicht der CPU-, Speicher- und Netzwerkauslastung über alle Services hinweg, plus eine Echtzeit-Matrix des Service-Health-Status.
-   **AI Operations Dashboard**: Spezialisierte Ansicht von KI-Aktivitäten, einschließlich Modellnutzung, Token-Verbrauch, Abfragelatenz und Kosten-pro-Operation-Tracking.
-   **Applikations-Performance**: Benutzerorientierte Service-Qualitätsmetriken, wie z. B. API-Antwortzeiten, Anfragevolumen und Fehlerraten.
-   **Log-Analyse**: Eine leistungsstarke Oberfläche zum Suchen, Filtern und Analysieren von Log-Daten aus jeder Komponente der Plattform.

::: details Spezialisierte Service-Dashboards
Für tiefere Einblicke enthält die Plattform auch integrierte Dashboards für spezifische Infrastrukturkomponenten:

-   **Traefik (Reverse Proxy)**: Visualisiert Request-Routing, Service-Health und den Status von TLS-Zertifikaten.
-   **Langfuse (LLM Observability)**: Traced jede LLM-Operation, zeigt Token-Nutzung, Latenz, Kostenattribution und den vollständigen Prompt-/Response-Kontext. Bietet außerdem Dataset-Management und Experimentbewertung.
-   **Dagster (Workflow Engine)**: Überwacht den Status, die Historie und die Performance aller Daten-Ingestion- und Verarbeitungs-Pipelines.
:::

## Alarmierung: Proaktive Benachrichtigungen

Während Dashboards zum Abrufen von Informationen dienen, drängt die Alarmierung proaktiv kritische Informationen an Sie. Sie wandelt Ihre Observability-Daten in automatisierte Benachrichtigungen um und stellt sicher, dass Sie oft schon vor Ihren Benutzern über Probleme informiert sind.

Das Alarmierungssystem ist hochflexibel und wird innerhalb Ihrer Observability-Plattform (z. B. SigNoz) konfiguriert, nicht fest in den Swiss AI Hub eincodiert. Dies ermöglicht es Ihnen, Benachrichtigungen an die spezifischen Bedürfnisse Ihrer Organisation anzupassen. Sie können Alarme konfigurieren für:

-   **Kritische Service-Ausfälle**: Sofortige Benachrichtigung, wenn ein Kern-Service wie das API-Gateway oder die Datenbank ungesund wird.
-   **Performance-Degradation**: Alarme, wenn API-Antwortzeiten Ziele überschreiten oder Fehlerraten ansteigen.
-   **Ressourcenlimits**: Proaktive Warnungen, wenn die CPU-, Speicher- oder Speicherauslastung sich den Kapazitätsgrenzen nähert.
-   **Kostenmanagement**: Benachrichtigungen, wenn der KI-Token-Verbrauch oder die Cloud-Ausgaben vordefinierte Budgetschwellenwerte erreichen.
-   **Security-Events**: Alarme für verdächtige Aktivitäten, wie z. B. wiederholte fehlgeschlagene Anmeldeversuche.

Alarme können an verschiedene Kanäle weitergeleitet werden, darunter E-Mail, Slack, Microsoft Teams und Incident-Management-Plattformen wie PagerDuty.

## Die Observability-Grundlage: OpenTelemetry

Das gesamte Monitoring- und Alarmierungssystem basiert auf **OpenTelemetry (OTel)**, einem von der CNCF graduierten, herstellerneutralen Standard für Observability.

Dies ist eine bewusste architektonische Entscheidung mit erheblichen Vorteilen:

-   **Kein Vendor Lock-in**: Die Plattform emittiert Daten in einem Standardformat. Während SigNoz die Standardlösung ist, steht es Ihnen frei, Telemetriedaten an jedes OTel-kompatible Backend zu senden – sei es Grafana, Datadog, Splunk oder Ihr vorhandenes Enterprise-Monitoring-Tool. Das Hinzufügen eines neuen Ziels ist eine Konfigurationsänderung, kein Re-Instrumentierungs-Projekt.
-   **Einheitliche Daten**: OTel bietet eine konsistente Möglichkeit, Metriken, Logs und Traces zu sammeln. Dies bedeutet, dass all Ihre Daten automatisch korreliert werden, sodass Sie nahtlos von einem Performance-Metrik-Spike zu den genauen Logs und Traces wechseln können, die ihn erklären.
-   **Zukunftssicher**: Durch die Nutzung eines Industriestandards profitiert die Plattform von der kontinuierlichen Innovation der gesamten Observability-Community.

Alle Telemetriedaten fließen durch einen zentralen **OpenTelemetry Collector** innerhalb der Plattform. Diese Komponente empfängt Daten von allen Services, reichert sie mit nützlichen Metadaten an und exportiert sie sicher an Ihr(e) ausgewähltes(n) Ziel(e). Diese Architektur stellt sicher, dass Sie die vollständige Kontrolle und Eigentümerschaft über Ihre Observability-Daten haben, genau wie über den Rest der Plattform.
```
