---
title: Beobachtbarkeit
source_sha: d072f5ae87f253cf6a2e466f3b4a36c0fa2d6a25c8782e1c9e3cac9cdbd99c5f
---

# Beobachtbarkeit

Der Swiss AI Hub bietet Einblick in die Ausführungsprozesse von Agenten. Benutzer können die Schritte sehen, die ein
Agent ausgeführt hat, die Entscheidungen, die er getroffen hat, und die Daten, die er verarbeitet hat.

## Warum Beobachtbarkeit wichtig ist

Traditionelle KI-Systeme zeigen Ergebnisse, ohne die zugrunde liegende Argumentation darzulegen. Benutzer sehen
Antworten, können aber keine Zwischenschritte, Entscheidungslogik oder Fehlerquellen erkennen.

Entscheidungsträger zögern, sich auf Systeme zu verlassen, die sie nicht verstehen oder validieren können. Wenn KI
unerwartete Ergebnisse liefert, benötigen Benutzer Informationen, um festzustellen, ob das System fehlerhaft war oder
fehlerhafte Eingaben korrekt verarbeitet hat.

Entwicklungsteams, die unerwartetes Agentenverhalten debuggen, benötigen mehr als Protokolldateien.
Qualitätssicherungsteams benötigen systematische Wege zur Validierung des Agentenverhaltens.

Regulierte Branchen müssen KI-gestützte Entscheidungen erklären und begründen können. Compliance-Frameworks erfordern
Nachweise, die zeigen, wie Systeme zu Schlussfolgerungen gelangt sind und wo menschliche Aufsicht stattgefunden hat.

## Wie die Ausführungsverfolgung funktioniert

Die Plattform erfasst detaillierte Aufzeichnungen der Agenten-Workflow-Ausführung.

Ausführungsverfolgungen zeigen die vollständige Abfolge der vom Agenten ausgeführten Schritte – Entscheidungspunkte,
Tool-Aufrufe, Wissensabfragen, Zwischenberechnungen. Benutzer sehen strukturierte Prozesse anstelle von mysteriösen
Berechnungen.

Jeder Workflow-Schritt verbraucht Eingabeereignisse und erzeugt Ausgabeereignisse. Die Trace-Anzeige zeigt, wie sich
Daten im Workflow transformieren. Eingabe-Nachrichten werden zu Klassifizierungsereignissen, dann zu Abfrageanfragen und
schließlich zu synthetisierten Antworten.

Traces enthalten Zeitinformationen für jeden Schritt. Benutzer können Leistungsengpässe identifizieren und beurteilen,
ob langsame Antworten auf komplexe Argumentation oder Infrastrukturverzögerungen zurückzuführen sind.

Wenn Workflows bedingte Logik enthalten, zeigen Traces, welche Zweige ausgeführt wurden und warum. Dies hilft Benutzern
zu validieren, dass Agenten die geeignete Logik auf spezifische Szenarien anwenden.

## Interaktive Erkundung

Die Trace-Anzeige öffnet ein angrenzendes Panel innerhalb der Chat-Benutzeroberfläche. Benutzer können Chat-Antworten
mit Workflow-Schritten korrelieren, ohne die Anwendung wechseln zu müssen.

Traces präsentieren Informationen hierarchisch – Workflow-Übersicht, Schrittausführung, Ereignisdaten. Benutzer können
in interessante Bereiche eintauchen, ohne bei einfachen Operationen übermäßige Details zu erhalten.

Auf der granularsten Ebene untersuchen Benutzer vollständige Ereignisdaten – die JSON-Strukturen, die zwischen
Workflow-Schritten fließen. Dies unterstützt ausgeklügeltes Debugging und Validierung.

Von den Trace-Ansichten aus navigieren Benutzer zu verwandten Funktionen – Wissensdokumente, auf die während der Abfrage
zugegriffen wurde, Agentenkonfigurationen, Systemprotokolle.

## Phoenix Trace-Integration

Die Plattform verwendet Arize Phoenix, eine Open-Source-Plattform für KI-Beobachtbarkeit.

Die Implementierung folgt den semantischen Konventionen von OpenInference. Trace-Daten verwenden standardisierte
Formate, die mit branchenüblichen Beobachtbarkeits-Tools kompatibel sind.

Das System erfasst semantische Ereignisse – LLM-Aufrufe, Abrufoperationen, Embedding-Generierungen – als strukturierte
Trace-Spans. Diese erfassen KI-spezifische Konzepte wie Token-Nutzung, Relevanzbewertungen für Abrufe und Modellauswahl.

Wenn Workflows mehrere Agenten umfassen, pflegen Traces die Korrelation über Interaktionen hinweg. Benutzer können
Ausführungsabläufe verfolgen, die sich über mehrere Agenten erstrecken.

Ausführungsverfolgungen bleiben über Gesprächssitzungen hinaus bestehen. Benutzer können historische Ausführungen zur
Qualitätssicherung, Compliance-Dokumentation oder Vorfallsuntersuchung überprüfen.

## Was dies bietet

Wenn Agenten sich unerwartet verhalten, ermöglichen Ausführungsverfolgungen eine schnelle Fehlerbehebung. Support-Teams
untersuchen Ausführungssequenzen, identifizieren Fehlerpunkte und lösen Probleme ohne umfangreiche Reproduktion.

Qualitätssicherungsteams validieren das Agentenverhalten systematisch. Durch die Untersuchung, wie Agenten Eingaben
verarbeiten und Grenzfälle handhaben, verifiziert die QS die Korrektheit vor der Produktionsbereitstellung.

Entwickler identifizieren Optimierungsmöglichkeiten aus Trace-Daten. Traces, die ineffiziente Muster oder unnötige
Schritte aufzeigen, leiten Verfeinerungsbemühungen.

Für die Einhaltung gesetzlicher Vorschriften dokumentieren Ausführungsverfolgungen, wie Systeme zu Schlussfolgerungen
gelangt sind. Audits können Traces überprüfen, die eine angemessene Datennutzung und menschliche Aufsicht an den
erforderlichen Stellen belegen.

Wenn Benutzer Ausführungsdetails untersuchen können, steigt das Vertrauen. Die Möglichkeit, Prozesse zu inspizieren,
macht KI verständlicher.

## Nutzung durch Entwickler

Entwickler, die Agenten erstellen, nutzen die Trace-Visualisierung während der Entwicklung. Anstatt Protokolldateien
oder Print-Statements zu verwenden, beobachten Entwickler, wie Workflows über Trace-Interfaces ausgeführt werden.

Automatisierte Tests erfassen Ausführungsverfolgungen. Tests können überprüfen, ob Agenten die entsprechenden Tools
aufgerufen, die richtigen Wissensquellen genutzt und die erwarteten Pfade verfolgt haben.

Trace-Zeitdaten ermöglichen Leistungs-Profiling. Entwickler identifizieren langsame Schritte, quantifizieren
Konfigurationseinflüsse und validieren Optimierungsergebnisse.

Ausführungsverfolgungen dienen als lebendige Dokumentation. Entwickler referenzieren tatsächliche Traces, die zeigen,
wie Agenten in der Praxis agieren.

## Datenschutz und Sicherheit

Die Trace-Sichtbarkeit respektiert das Berechtigungssystem. Benutzer können nur Traces für Konversationen einsehen, an
denen sie teilgenommen haben oder zu deren Prüfung sie berechtigt sind. Administratorzugriff erfordert explizite
Berechtigungen.

Die Plattform kann sensible Informationen aus Traces – personenbezogene Daten, vertrauliche Daten – redigieren, während
die Workflow-Struktur erhalten bleibt.

Das System protokolliert den Trace-Zugriff und dokumentiert, wer welche Traces wann überprüft hat. Dies unterstützt
Compliance-Anforderungen und erkennt unangemessene Zugriffe.

Organisationen konfigurieren Trace-Aufbewahrungsrichtlinien, die den Wert der Beobachtbarkeit gegen Speicherkosten und
Vorschriften abwägen. Traces können nach bestimmten Zeiträumen ablaufen, oder eine selektive Aufbewahrung kann wichtige
Konversationen bewahren, während routinemäßige Interaktionen veralten.
