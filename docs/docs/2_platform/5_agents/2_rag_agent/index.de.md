---
title: RAG-Agent
source_sha: 1888c2987eea1d564747512aa5c25aa8f5a307003c28a0eaef705a62606f2763
---

# RAG-Agent

Der RAG-Agent beantwortet Fragen, indem er Informationen aus Ihren internen Dokumenten abruft. Er verwendet
Retrieval-Augmented Generation (RAG), um Antworten auf die Daten Ihrer Organisation zu stützen, anstatt sich nur auf das
vortrainierte Wissen des LLM zu verlassen.

## LLM-Einschränkungen

LLMs werden mit öffentlichen Internetdaten trainiert. Dies führt zu Einschränkungen für den Einsatz in Unternehmen:

- Wissensstichtag: Informationen sind auf das letzte Trainingsdatum (Monate oder Jahre zurückliegend) beschränkt.
- Kein Geschäftskontext: LLMs haben keinen Zugriff auf interne Berichte, Richtlinien und proprietäre Daten.
- Halluzinationen: LLMs generieren plausible, aber inkorrekte Antworten, wenn sie etwas nicht wissen.
- Keine Quellenangabe: Antworten enthalten keine Zitate zur Überprüfung.

RAG begegnet diesen Einschränkungen, indem es vor der Generierung von Antworten Informationen aus Ihren Dokumenten
abruft.

::: tip Über das "Trainieren" von Agents
Der Swiss AI Hub bietet kein Modelltraining oder Fine-Tuning an. Stattdessen greift der RAG-Agent zur Abfragezeit auf
aktuelle Informationen zu, indem er sie aus Ihrer Wissensdatenbank abruft. Das bedeutet, dass der Agent automatisch über
neue oder aktualisierte Dokumente "Bescheid weiss", ohne dass ein erneuter Trainingsprozess erforderlich ist.
:::

## Wie RAG funktioniert

Der RAG-Agent folgt diesem Workflow:

1. **Fragenverständnis**: Das LLM formuliert Ihre Frage in eine optimale Suchanfrage um. Bei laufenden Gesprächen fasst
   es den Chatverlauf zusammen, um die Anfrage eigenständig zu machen.

2. **Wissensabruf**: Eine semantische Suche wird über bestimmte Wissensdatenbanken (vektorindizierte Sammlungen Ihrer
   Dokumente) ausgeführt. Die Suche liefert relevante Textabschnitte.

3. **Kontextrekonstruktion**: Textabschnitte benötigen einen umgebenden Kontext, um aussagekräftig zu sein. Der Agent
   ruft benachbarte Abschnitte aus dem Originaldokument oder Zusammenfassungen auf übergeordneter Ebene ab, um das
   Gesamtbild zu verstehen.

4. **Neubewertung (Re-Ranking)**: Ein spezialisiertes Modell bewertet die abgerufenen Abschnitte im Hinblick auf Ihre
   Frage und ordnet sie nach Relevanz neu an.

5. **Antwortsynthese**: Das LLM generiert eine Antwort, indem es nur die am höchsten bewerteten Informationen verwendet
   und deren Quellen zitiert.

Dieser Prozess stützt die Antwort auf Ihre tatsächlichen Daten und nicht auf generisches KI-Wissen.

### Wissensdatenbanken und Pipelines

Der Agent ruft Informationen aus Wissensdatenbanken ab, bei denen es sich um vektorindizierte Sammlungen von Dokumenten
handelt. Sie konfigurieren, welche Wissensdatenbanken der Agent durchsucht. Es können mehrere Wissensdatenbanken für
verschiedene Themen (HR-Richtlinien, technische Dokumentation, Projektdateien) erstellt werden.

[Datenaufnahme-Pipelines](../../6_pipelines/) pflegen den Inhalt der Wissensdatenbank. Die Standard-Pipeline verarbeitet
Dokumente, die über die Benutzeroberfläche hochgeladen werden. Benutzerdefinierte Pipelines können mit externen Quellen
wie SharePoint synchronisiert werden und die Wissensdatenbank automatisch aktualisieren, wenn sich die Quelldokumente
ändern.

## Erweiterte Funktionen

### Multi-Hop-Retrieval

Wenn der anfängliche Abruf nicht genügend Informationen liefert, kann der Agent ein Multi-Hop-Retrieval durchführen. Er
analysiert die Informationslücke, formuliert eine neue Abfrage und führt eine weitere Suche durch. Dieser iterative
Prozess hilft bei der Beantwortung von Fragen, die Informationen aus mehreren Dokumenten oder Abschnitten erfordern.

### Guardrails

Der Agent kann [Eingabe- und Ausgabe-Guards](../../13_language_models/3_guards/) verwenden, um Abfragen und Antworten zu
validieren. Beispielsweise prüft der Guard für ausreichenden Kontext, ob die abgerufenen Informationen ausreichen, um
eine Frage zu beantworten. Wenn der Kontext unzureichend ist, teilt der Agent dies dem Benutzer mit, anstatt eine
halluzinierte Antwort zu generieren.
