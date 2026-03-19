---
title: Observability
source_sha: "63a135b18d4d8d74632546a60f1332c15b8ce170e80f632948bff234a1ef04fe"
---

# Observability

Der Swiss AI Hub bietet Einblick in die Ausführungsprozesse von Agents. Benutzer können die Schritte sehen, die ein Agent ausgeführt hat, die Entscheidungen, die er getroffen hat, und die Daten, die er verarbeitet hat.

## Warum Observability wichtig ist

Traditionelle KI-Systeme zeigen Ergebnisse, ohne die zugrunde liegende Argumentation aufzuzeigen. Benutzer sehen Antworten, können aber keine Zwischenschritte, Entscheidungslogik oder Fehlerursachen erkennen.

Entscheidungsträger zögern, sich auf Systeme zu verlassen, die sie nicht verstehen oder validieren können. Wenn KI unerwartete Ergebnisse liefert, benötigen Benutzer Informationen, um festzustellen, ob das System fehlerhaft war oder fehlerhafte Eingaben korrekt verarbeitet hat.

Entwicklungsteams, die unerwartetes Agent-Verhalten debuggen, benötigen mehr als nur Log-Dateien. Qualitätssicherungsteams benötigen systematische Wege, um das Verhalten von Agents zu validieren.

Regulierende Industrien müssen KI-gestützte Entscheidungen erklären und rechtfertigen. Compliance-Frameworks erfordern Nachweise, die zeigen, wie Systeme zu Schlussfolgerungen gelangt sind und wo menschliche Aufsicht stattgefunden hat.

## Wie die Ausführungsverfolgung funktioniert

Die Plattform erfasst detaillierte Aufzeichnungen der Ausführung von Agent-Workflows.

Ausführungs-Traces zeigen die vollständige Abfolge der vom Agenten ausgeführten Schritte – Entscheidungspunkte, Tool-Aufrufe, Wissensabfragen, Zwischenberechnungen. Benutzer sehen strukturierte Prozesse anstelle mysteriöser Berechnungen.

Jeder Workflow-Schritt konsumiert Eingabeereignisse und erzeugt Ausgabeereignisse. Die Trace-Anzeige zeigt, wie sich Daten im Workflow transformieren. Eingabenachrichten werden zu Klassifizierungsereignissen, dann zu Abrufanfragen und schließlich zu synthetisierten Antworten.

Traces enthalten Zeitinformationen für jeden Schritt. Benutzer können Leistungsengpässe identifizieren und beurteilen, ob langsame Antworten auf komplexe Logik oder Infrastrukturverzögerungen zurückzuführen sind.

Wenn Workflows bedingte Logik enthalten, zeigen Traces, welche Zweige ausgeführt wurden und warum. Dies hilft Benutzern zu validieren, dass Agents die geeignete Logik auf bestimmte Szenarien anwenden.

## Interaktive Exploration

Die Trace-Anzeige öffnet ein angrenzendes Panel innerhalb der Chat-Benutzeroberfläche. Benutzer können Chat-Antworten mit Workflow-Schritten korrelieren, ohne die Anwendungen wechseln zu müssen.

Traces präsentieren Informationen hierarchisch – Workflow-Übersicht, Schrittausführung, Ereignisdaten. Benutzer können bei Bedarf in Interessensbereiche eintauchen, ohne bei einfachen Operationen mit übermäßigen Details konfrontiert zu werden.

Auf der granularsten Ebene untersuchen Benutzer vollständige Ereignisdaten – die JSON-Strukturen, die zwischen den Workflow-Schritten fließen. Dies unterstützt komplexe Fehlersuche und Validierung.

Von den Trace-Ansichten aus können Benutzer zu verwandten Funktionen navigieren – Wissensdokumente, die während des Abrufs aufgerufen wurden, Agent-Konfigurationen, Systemprotokolle.

## Langfuse Tracing-Integration

Die Plattform nutzt Langfuse, eine Open-Source-Plattform für AI-Observability.

Die Implementierung folgt den semantischen Konventionen von OpenInference. Trace-Daten verwenden standardisierte Formate, die mit branchenüblichen Observability-Tools kompatibel sind.

Das System erfasst semantische Ereignisse – LLM-Aufrufe, Abrufoperationen, Embedding-Generierungen – als strukturierte Trace-Spans. Diese erfassen KI-spezifische Konzepte wie Token-Nutzung, Abruf-Relevanzwerte und Modellauswahl.

Wenn Workflows mehrere Agents umfassen, behalten Traces die Korrelation über Interaktionen hinweg bei. Benutzer können Ausführungsabläufe verfolgen, die sich über mehrere Agents erstrecken.

Ausführungs-Traces bleiben über Gesprächssitzungen hinaus bestehen. Benutzer können historische Ausführungen zur Qualitätssicherung, Compliance-Dokumentation oder Vorfalluntersuchung überprüfen.

## Was dies bietet

Wenn Agents unerwartet handeln, ermöglichen Ausführungs-Traces eine schnelle Fehlerbehebung. Support-Teams untersuchen Ausführungssequenzen, identifizieren Fehlerpunkte und lösen Probleme ohne aufwändige Reproduktion.

Qualitätssicherungsteams validieren das Agent-Verhalten systematisch. Durch die Untersuchung, wie Agents Eingaben verarbeiten und Grenzfälle behandeln, überprüft die Qualitätssicherung die Korrektheit vor dem Production-Deployment.

Entwickler identifizieren Optimierungsmöglichkeiten aus Trace-Daten. Traces, die ineffiziente Muster oder unnötige Schritte aufzeigen, leiten die Verfeinerungsbemühungen.

Für die Einhaltung regulatorischer Vorschriften dokumentieren Ausführungs-Traces, wie Systeme zu Schlussfolgerungen gelangt sind. Audits können Traces überprüfen, die eine angemessene Datennutzung und menschliche Aufsicht an den erforderlichen Stellen belegen.

Wenn Benutzer Ausführungsdetails untersuchen können, steigt das Vertrauen. Die Möglichkeit, Prozesse zu inspizieren, macht KI verständlicher.

## Entwickler-Nutzung

Entwickler, die Agents erstellen, nutzen die Trace-Visualisierung während der Entwicklung. Anstatt Log-Dateien oder Print-Anweisungen zu verwenden, beobachten Entwickler die Workflow-Ausführung über Trace-Schnittstellen.

Automatisierte Tests erfassen Ausführungs-Traces. Tests können überprüfen, ob Agents die entsprechenden Tools aufgerufen, die richtigen Wissensquellen genutzt und die erwarteten Pfade verfolgt haben.

Trace-Timing-Daten ermöglichen die Performance-Profilierung. Entwickler identifizieren langsame Schritte, quantifizieren Konfigurationseinflüsse und validieren Optimierungsergebnisse.

Ausführungs-Traces dienen als lebendige Dokumentation. Entwickler können sich auf tatsächliche Traces beziehen, die zeigen, wie sich Agents in der Praxis verhalten.

## Datenschutz und Sicherheit

Die Trace-Sichtbarkeit respektiert das Berechtigungssystem. Benutzer können nur Traces für Konversationen einsehen, an denen sie teilgenommen haben oder für deren Audit sie autorisiert sind. Administratorzugriff erfordert explizite Berechtigungen.

Die Plattform kann sensible Informationen aus Traces redigieren – persönlich identifizierbare Informationen, vertrauliche Daten – während die Workflow-Struktur erhalten bleibt.

Das System protokolliert den Trace-Zugriff und dokumentiert, wer wann welche Traces überprüft hat. Dies unterstützt Compliance-Anforderungen und erkennt unangemessenen Zugriff.

Organisationen konfigurieren Trace-Aufbewahrungsrichtlinien, die den Observability-Wert gegen Speicherkosten und Vorschriften abwägen. Traces können nach bestimmten Zeiträumen ablaufen, oder eine selektive Aufbewahrung kann wichtige Konversationen erhalten, während Routineinteraktionen nach einer gewissen Zeit gelöscht werden.
