---
title: Observability
source_sha: 226ffbdba46c1cce64ff9adb4bccf3aeddf7ab626d3eaa603f6e548fbccedac4
---

# Observability

Der Swiss AI Hub bietet Transparenz bei den Ausführungsprozessen von Agents. Nutzer können die Schritte sehen, die ein
Agent ausgeführt hat, die Entscheidungen, die er getroffen hat, und die Daten, die er verarbeitet hat.

## Warum Observability wichtig ist

Traditionelle KI-Systeme zeigen Ergebnisse, ohne die zugrunde liegende Argumentation darzulegen. Nutzer sehen Antworten,
können aber keine Zwischenschritte, die Entscheidungslogik oder Fehlerquellen erkennen.

Entscheidungsträger zögern, sich auf Systeme zu verlassen, die sie nicht verstehen oder validieren können. Wenn KI
unerwartete Ergebnisse liefert, benötigen Nutzer Informationen, um festzustellen, ob das System fehlerhaft war oder
fehlerhafte Eingaben korrekt verarbeitet hat.

Entwicklungsteams, die unerwartetes Agent-Verhalten debuggen, benötigen mehr als nur Logdateien.
Qualitätssicherungsteams benötigen systematische Wege, um das Verhalten von Agents zu validieren.

Regulierte Industrien müssen KI-gestützte Entscheidungen erklären und begründen. Compliance-Frameworks erfordern
Nachweise, die zeigen, wie Systeme zu Schlussfolgerungen gelangt sind und wo menschliche Aufsicht stattfand.

## Wie Execution Tracing funktioniert

Die Plattform erfasst detaillierte Aufzeichnungen der Workflow-Ausführung von Agents.

Execution Traces zeigen die vollständige Abfolge der vom Agent ausgeführten Schritte – Entscheidungspunkte,
Tool-Aufrufe, Wissensabrufe, Zwischenberechnungen. Nutzer sehen strukturierte Prozesse statt undurchsichtiger
Berechnungen.

Jeder Workflow-Schritt konsumiert Eingabe-Events und produziert Ausgabe-Events. Die Trace-Anzeige zeigt, wie sich Daten
im Workflow transformieren. Eingabenachrichten werden zu Klassifikations-Events, dann zu Retrieval-Anfragen und
schließlich zu synthetisierten Antworten.

Traces enthalten Zeitinformationen für jeden Schritt. Nutzer können Performance-Engpässe identifizieren und beurteilen,
ob langsame Antworten auf komplexe Logik oder Infrastrukturverzögerungen zurückzuführen sind.

Wenn Workflows bedingte Logik enthalten, zeigen Traces, welche Zweige ausgeführt wurden und warum. Dies hilft Nutzern zu
validieren, dass Agents die entsprechende Logik auf spezifische Szenarien anwenden.

## Interaktive Exploration

Die Trace-Anzeige öffnet ein angrenzendes Panel innerhalb der Chat-Oberfläche. Nutzer können Chat-Antworten mit
Workflow-Schritten korrelieren, ohne Anwendungen wechseln zu müssen.

Traces präsentieren Informationen hierarchisch – Workflow-Übersicht, Schrittausführung, Event-Daten. Nutzer können in
Interessensbereiche eintauchen, ohne bei einfachen Operationen übermäßige Details zu erhalten.

Auf der granularsten Ebene können Nutzer vollständige Event-Daten – die JSON-Strukturen, die zwischen Workflow-Schritten
fließen – untersuchen. Dies unterstützt komplexes Debugging und die Validierung.

Von Trace-Ansichten aus navigieren Nutzer zu verwandten Funktionen – Wissensdokumenten, die während des Retrievals
abgerufen wurden, Agent-Konfigurationen, System-Logs.

## Langfuse Tracing-Integration

Die Plattform nutzt Langfuse, eine Open-Source-KI-Observability-Plattform.

Die Implementierung folgt den semantischen Konventionen von OpenInference. Trace-Daten verwenden standardisierte
Formate, die mit branchenüblichen Observability-Tools kompatibel sind.

Das System erfasst semantische Events – LLM-Aufrufe, Retrieval-Operationen, Embedding-Generierungen – als strukturierte
Trace-Spans. Diese erfassen KI-spezifische Konzepte wie Token-Nutzung, Retrieval-Relevanzwerte und Modellauswahl.

Wenn Workflows mehrere Agents involvieren, halten Traces die Korrelation über Interaktionen hinweg aufrecht. Nutzer
können Ausführungsflüsse verfolgen, die sich über mehrere Agents erstrecken.

Execution Traces bleiben über Konversationssitzungen hinaus bestehen. Nutzer können historische Ausführungen für die
Qualitätssicherung, Compliance-Dokumentation oder Vorfalluntersuchungen überprüfen.

## Was dies bietet

Wenn Agents sich unerwartet verhalten, ermöglichen Execution Traces eine schnelle Fehlerbehebung. Support-Teams können
Ausführungssequenzen untersuchen, Fehlerquellen identifizieren und Probleme ohne umfangreiche Reproduktion lösen.

Qualitätssicherungsteams validieren das Agent-Verhalten systematisch. Durch die Untersuchung, wie Agents Eingaben
verarbeiten und Edge Cases handhaben, verifiziert die QS die Korrektheit vor dem Produktions-Deployment.

Entwickler identifizieren Optimierungsmöglichkeiten aus Trace-Daten. Traces, die ineffiziente Muster oder unnötige
Schritte aufzeigen, leiten Verfeinerungsbemühungen.

Für die Einhaltung gesetzlicher Vorschriften dokumentieren Execution Traces, wie Systeme zu Schlussfolgerungen
gelangten. Audits können Traces überprüfen, die eine angemessene Datennutzung und menschliche Aufsicht an erforderlichen
Stellen belegen.

Wenn Nutzer Ausführungsdetails untersuchen können, steigt das Vertrauen. Die Möglichkeit, Prozesse zu inspizieren, macht
KI verständlicher.

## Entwickler-Nutzung

Entwickler, die Agents erstellen, nutzen die Trace-Visualisierung während der Entwicklung. Anstatt Logdateien oder
Print-Statements zu verwenden, beobachten Entwickler die Workflow-Ausführung über Trace-Interfaces.

Automatisierte Tests erfassen Execution Traces. Tests können überprüfen, ob Agents die geeigneten Tools aufgerufen, die
korrekten Wissensquellen abgerufen und die erwarteten Pfade verfolgt haben.

Trace-Timing-Daten ermöglichen Performance-Profiling. Entwickler identifizieren langsame Schritte, quantifizieren
Konfigurationseinflüsse und validieren Optimierungsergebnisse.

Execution Traces dienen als lebendige Dokumentation. Entwickler können sich auf tatsächliche Traces beziehen, die
zeigen, wie sich Agents in der Praxis verhalten.

## Datenschutz und Sicherheit

Die Trace-Sichtbarkeit respektiert das Berechtigungssystem. Nutzer können Traces nur für Konversationen einsehen, an
denen sie teilgenommen haben oder für die sie zur Prüfung autorisiert sind. Administratorzugriff erfordert explizite
Berechtigungen.

Die Plattform kann sensible Informationen aus Traces – personenbezogene Daten, vertrauliche Daten – redigieren, während
die Workflow-Struktur erhalten bleibt.

Das System protokolliert den Trace-Zugriff und dokumentiert, wer welche Traces wann überprüft hat. Dies unterstützt
Compliance-Anforderungen und erkennt unangemessene Zugriffe.

Organisationen konfigurieren Trace-Aufbewahrungsrichtlinien, die den Wert der Observability gegen Speicherkosten und
Vorschriften abwägen. Traces können nach bestimmten Zeiträumen ablaufen, oder eine selektive Aufbewahrung kann wichtige
Konversationen erhalten, während routinemäßige Interaktionen veralten.
