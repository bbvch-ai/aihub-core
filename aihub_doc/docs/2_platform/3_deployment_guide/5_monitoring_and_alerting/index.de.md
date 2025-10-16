---
title: 'Überwachung & Alarmierung'
index: 5
source_sha: "b43bd61b6a4770fd1986302c04c32eee9f5cc45c815236293a595474fae568ec"
---

# Überwachung & Alarmierung

Ein Produktions-KI-System muss transparent, zuverlässig und vorhersehbar sein. Während es an Tag 1 um beeindruckende Demos geht, geht es an Tag 2 darum, Vertrauen durch operative Exzellenz zu erhalten. Der Swiss AI Hub bietet eine umfassende, integrierte Observability-Suite, um Ihnen ein vollständiges Bild über den Zustand, die Leistung und die Kosten Ihrer Plattform zu geben.

Dieser Abschnitt erklärt die in die Plattform integrierten Schichten der Überwachung und Alarmierung. Sie erfahren, was wir messen, wie Sie es visualisieren können und wie das System Sie proaktiv über Probleme benachrichtigt.

## Die Säulen der Observability

Die Monitoring-Philosophie der Plattform basiert auf den branchenüblichen Säulen der Observability, die Antworten auf kritische operative Fragen liefern.

### 1. Health Checks: „Funktioniert es gerade?"

Health Checks sind der Herzschlag der Plattform, der kontinuierlich überprüft, ob jede Komponente aktiv und funktionsfähig ist. Im Gegensatz zu Metriken oder Logs liefern sie eine einfache, sofortige Antwort auf die grundlegendste Frage.

Die Plattform verwendet einen mehrschichtigen Ansatz:
- **Native Docker Checks**: Überwachen automatisch, ob Service-Prozesse laufen und reagieren. Docker kann fehlerhafte Container neu starten und ermöglicht so die Selbstheilung bei temporären Problemen.
- **Anwendungs-Endpunkt-Checks**: Services stellen dedizierte Health-Endpunkte (`/health`) zur Verfügung, die nicht nur die Liveness, sondern auch die Bereitschaft zur Ausführung ihrer spezifischen Funktion überprüfen (z. B. kann die Datenbank eine Abfrage akzeptieren?).
- **Synthetische Probes**: Für Services ohne native Health-Endpunkte befragt die Plattform diese aktiv, um sicherzustellen, dass sie verfügbar und reaktionsfähig sind.

Jede Änderung des Health-Status – von fehlerfrei zu fehlerhaft, Service-Starts und -Stopps – wird als strukturiertes Ereignis erfasst und liefert eine vollständige historische Aufzeichnung der Service-Verfügbarkeit.

### 2. Metriken: „Wie ist die Leistung?"

Metriken sind quantitative Messungen, die die Leistung und Ressourcennutzung über die Zeit verfolgen. Sie sind unerlässlich für Trendanalysen, Kapazitätsplanung und die Identifizierung von Leistungsengpässen, bevor diese die Benutzer beeinträchtigen.

Die Plattform sammelt automatisch Schlüsselmetriken in zwei Hauptkategorien:
- **Infrastruktur-Metriken**: Daten auf Containerebene für jeden Service, einschließlich CPU-Auslastung, Speicherverbrauch, Netzwerkverkehr und Festplatten-I/O. Dies bietet eine klare Übersicht über die Ressourcennutzung und hilft bei der Kostenverwaltung und Kapazitätsplanung.
- **Anwendungsmetriken**: (In Arbeit) Wenn Services instrumentiert werden, geben sie detaillierte Leistungsdaten aus, wie z. B. Latenz von API-Anfragen, Fehlerraten, Ausführungszeiten von KI-Agenten und den Durchsatz bei der Dokumentenverarbeitung.

Diese Metriken liefern die Daten, die zur Leistungsoptimierung, Budgetprognose und für fundierte Entscheidungen zur Skalierung Ihrer Infrastruktur erforderlich sind.

### 3. Logs: „Was ist passiert und warum?"

Logs bieten eine detaillierte, chronologische Aufzeichnung jedes Ereignisses, das innerhalb der Plattform auftritt. Wenn ein Problem auftritt, sind Logs das primäre Werkzeug für die Ursachenanalyse und bieten den Kontext, der zum Verständnis des genauen Hergangs erforderlich ist.

Die Plattform erfasst Logs aus mehreren Quellen:
- **Anwendungs-Logs**: Strukturierte Ausgabe aller Python-Services, einschließlich Informationsmeldungen, Warnungen und kritischer Fehler.
- **Container-Logs**: Alle `stdout`- und `stderr`-Ausgaben jedes Containers, die alles von Startmeldungen bis zu unbehandelten Ausnahmen erfassen.
- **Anfrage-Logs**: Aufzeichnungen von HTTP-Anfragen und deren Ergebnissen.
- **Sicherheits-Logs**: Audit-Trail von Authentifizierungsereignissen, Zugriffsversuchen und Berechtigungsprüfungen.

Alle Logs sind zentralisiert, strukturiert und durchsuchbar, sodass Sie Probleme schnell diagnostizieren, Aktivitäten überprüfen und Nutzungsmuster analysieren können.

## Dashboards: Die einheitliche Ansicht

Daten sind nur nützlich, wenn man sie verstehen kann. Der Swiss AI Hub verwendet **SigNoz**, eine Open-Source-, OpenTelemetry-native Plattform, als zentrales Observability-Backend. Es bietet eine einzige, einheitliche Oberfläche zur Visualisierung all Ihrer Health-, Metrik- und Log-Daten.

Standardmäßig erhalten Sie Zugriff auf mehrere Schlüssel-Dashboards:

- **Infrastruktur-Übersicht**: Eine übergeordnete Ansicht der CPU-, Speicher- und Netzwerkauslastung aller Services, plus eine Echtzeit-Matrix des Service-Zustands.
- **KI-Operations-Dashboard**: Spezialisierte Ansicht von KI-Aktivitäten, einschließlich Modellnutzung, Token-Verbrauch, Abfrage-Latenz und Kosten pro Operation-Tracking.
- **Anwendungsleistung**: Benutzerorientierte Service-Qualitätsmetriken, wie API-Antwortzeiten, Anfragevolumen und Fehlerraten.
- **Log-Analyse**: Eine leistungsstarke Oberfläche zum Suchen, Filtern und Analysieren von Log-Daten jeder Komponente der Plattform.

::: details Spezialisierte Service-Dashboards
Für tiefere Einblicke enthält die Plattform auch integrierte Dashboards für spezifische Infrastrukturkomponenten:

- **Traefik (Reverse Proxy)**: Visualisiert Anfragen-Routing, Service-Zustand und TLS-Zertifikatsstatus.
- **Phoenix (LLM Observability)**: Verfolgt jede LLM-Operation und zeigt Token-Nutzung, Latenz und den vollständigen Prompt-/Response-Kontext zum Debugging.
- **Dagster (Workflow Engine)**: Überwacht den Status, die Historie und die Leistung aller Datenaufnahme- und Verarbeitungspipelines.
:::

## Alarmierung: Proaktive Benachrichtigungen

Während Dashboards dem Abrufen von Informationen dienen, drängt die Alarmierung proaktiv kritische Informationen an Sie. Sie wandelt Ihre Observability-Daten in automatisierte Benachrichtigungen um und stellt sicher, dass Sie Probleme oft schon vor Ihren Benutzern bemerken.

Das Alarmierungssystem ist hochflexibel und wird innerhalb Ihrer Observability-Plattform (z. B. SigNoz) konfiguriert, nicht fest in den Swiss AI Hub einkodiert. Dies ermöglicht es Ihnen, Benachrichtigungen an die spezifischen Bedürfnisse Ihrer Organisation anzupassen. Sie können Alarme konfigurieren für:

- **Kritische Service-Ausfälle**: Sofortige Benachrichtigung, wenn ein Kernservice wie das API-Gateway oder die Datenbank fehlerhaft wird.
- **Leistungsverschlechterung**: Alarme, wenn API-Antwortzeiten Ziele überschreiten oder Fehlerraten ansteigen.
- **Ressourcenlimits**: Proaktive Warnungen, wenn CPU-, Speicher- oder Speicherauslastung sich den Kapazitätsgrenzen nähert.
- **Kostenmanagement**: Benachrichtigungen, wenn der Verbrauch von KI-Tokens oder Cloud-Ausgaben vordefinierte Budgetschwellenwerte erreicht.
- **Sicherheitsereignisse**: Alarme bei verdächtigen Aktivitäten, wie z. B. wiederholten fehlgeschlagenen Anmeldeversuchen.

Alarme können an verschiedene Kanäle geleitet werden, darunter E-Mail, Slack, Microsoft Teams und Incident-Management-Plattformen wie PagerDuty.

## Die Observability-Grundlage: OpenTelemetry

Das gesamte Überwachungs- und Alarmierungssystem basiert auf **OpenTelemetry (OTel)**, einem von der CNCF graduierten, herstellerneutralen Standard für Observability.

Dies ist eine bewusste architektonische Entscheidung mit erheblichen Vorteilen:

- **Kein Vendor Lock-in**: Die Plattform gibt Daten in einem Standardformat aus. Während SigNoz der Standard ist, steht es Ihnen frei, Telemetriedaten an jedes OTel-kompatible Backend zu senden – sei es Grafana, Datadog, Splunk oder Ihr bestehendes Enterprise-Monitoring-Tool. Das Hinzufügen eines neuen Ziels ist eine Konfigurationsänderung, kein Re-Instrumentierungsprojekt.
- **Vereinheitlichte Daten**: OTel bietet eine konsistente Möglichkeit, Metriken, Logs und Traces zu sammeln. Das bedeutet, dass all Ihre Daten automatisch korreliert werden, sodass Sie nahtlos von einem Leistungsmetrik-Spike zu den genauen Logs und Traces wechseln können, die ihn erklären.
- **Zukunftssicher**: Durch die Nutzung eines Industriestandards profitiert die Plattform von der kontinuierlichen Innovation der gesamten Observability-Community.

Alle Telemetriedaten fließen durch einen zentralen **OpenTelemetry Collector** innerhalb der Plattform. Diese Komponente empfängt Daten von allen Services, reichert sie mit nützlichen Metadaten an und exportiert sie sicher an Ihre gewählten Ziele. Diese Architektur stellt sicher, dass Sie die vollständige Kontrolle und Eigentümerschaft über Ihre Observability-Daten haben, genau wie bei dem Rest der Plattform.
