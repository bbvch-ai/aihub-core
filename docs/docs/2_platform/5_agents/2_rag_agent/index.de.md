---
title: RAG-Agent
source_sha: 029048fe44cab81ec8feb555b623269ab6948dbdc4291ae9c4ea6b0aa4c070fb
---

# RAG-Agent

Der RAG-Agent beantwortet Fragen, indem er Informationen aus Ihren internen Dokumenten abruft. Er verwendet
Retrieval-Augmented Generation (RAG), um Antworten auf die Daten Ihrer Organisation zu stützen, anstatt sich nur auf das
vortrainierte Wissen des LLM zu verlassen.

## LLM-Einschränkungen

LLMs werden mit öffentlichen Internetdaten trainiert. Dies führt zu Einschränkungen für den Unternehmenseinsatz:

- Wissensstichtag: Informationen sind auf das letzte Trainingsdatum (Monate oder Jahre zurückliegend) eingefroren
- Kein Geschäftskontext: LLMs haben keinen Zugriff auf interne Berichte, Richtlinien und proprietäre Daten
- Halluzinationen: LLMs generieren plausible, aber falsche Antworten, wenn sie etwas nicht wissen
- Keine Quellenangabe: Antworten enthalten keine Zitate zur Überprüfung

RAG begegnet diesen Einschränkungen, indem es Informationen aus Ihren Dokumenten abruft, bevor Antworten generiert
werden.

::: tip Über das "Trainieren" von Agenten
Der Swiss AI Hub bietet kein Modelltraining oder Fine-Tuning an. Stattdessen greift der RAG-Agent auf aktuelle
Informationen zu, indem er diese zum Zeitpunkt der Abfrage aus Ihrer Wissensbasis abruft. Dies bedeutet, dass der Agent
automatisch über neue oder aktualisierte Dokumente "Bescheid weiß", ohne dass ein erneuter Trainingsprozess erforderlich
ist.
:::

## Wie RAG funktioniert

Der RAG-Agent folgt diesem Workflow:

1. **Fragenverständnis**: Das LLM formuliert Ihre Frage in eine optimale Suchanfrage um. Bei laufenden Konversationen
   fasst es den Chatverlauf zusammen, um die Anfrage eigenständig zu gestalten.

2. **Wissensabruf**: Eine semantische Suche wird über bestimmte Wissensbasen (vektorindizierte Sammlungen Ihrer
   Dokumente) ausgeführt. Die Suche liefert relevante Textabschnitte.

3. **Kontextrekonstruktion**: Textabschnitte benötigen einen umgebenden Kontext, um bedeutungsvoll zu sein. Der Agent
   ruft benachbarte Abschnitte aus dem Originaldokument oder Zusammenfassungen auf übergeordneter Ebene ab, um das
   Gesamtbild zu verstehen.

4. **Re-Ranking**: Ein spezialisiertes Modell bewertet die abgerufenen Abschnitte anhand Ihrer Frage und ordnet sie nach
   Relevanz neu.

5. **Antwortsynthese**: Das LLM generiert eine Antwort, indem es nur die höchstgereihten Informationen verwendet und
   seine Quellen zitiert.

Dieser Prozess verankert die Antwort in Ihren tatsächlichen Daten und nicht im generischen KI-Wissen.

### Wissensbasen und Pipelines

Der Agent ruft Informationen aus Wissensbasen ab, die vektorindizierte Sammlungen von Dokumenten sind. Sie
konfigurieren, welche Wissensbasen der Agent durchsucht. Es können mehrere Wissensbasen für verschiedene Themen erstellt
werden (HR-Richtlinien, technische Dokumentation, Projektdateien).

[Daten-Ingestions-Pipelines](../../6_pipelines/) pflegen den Inhalt der Wissensbasis. Die Standard-Pipeline verarbeitet
Dokumente, die über die Benutzeroberfläche hochgeladen werden. Benutzerdefinierte Pipelines können mit externen Quellen
wie SharePoint synchronisiert werden und die Wissensbasis automatisch aktualisieren, wenn sich Quelldokumente ändern.

## Erweiterte Funktionen

### Multi-Hop-Retrieval

Wenn der anfängliche Abruf nicht genügend Informationen liefert, kann der Agent ein Multi-Hop-Retrieval durchführen. Er
analysiert die Informationslücke, formuliert eine neue Abfrage und führt eine weitere Suche durch. Dieser iterative
Prozess hilft bei der Beantwortung von Fragen, die Informationen aus mehreren Dokumenten oder Abschnitten erfordern.

### Guardrails

Der Agent kann [Input- und Output-Guards](/de/docs/2_platform/13_language_models/3_guards/) verwenden, um Abfragen und
Antworten zu validieren. Zum Beispiel prüft der Context Sufficiency Guard, ob die abgerufenen Informationen ausreichen,
um eine Frage zu beantworten. Wenn der Kontext unzureichend ist, teilt der Agent dies dem Benutzer mit, anstatt eine
halluzinierte Antwort zu generieren.
