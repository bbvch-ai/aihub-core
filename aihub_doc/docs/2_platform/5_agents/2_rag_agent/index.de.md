---
title: Der RAG-Agent
source_sha: 07eb9751c19e4fadedd1f2a3fe0edd35d5337cf9b1dea3a7edcf7c9947a220d7
---

# Der RAG-Agent: Ihr Wissensspezialist

Einer der Standard-Agenten, die im Swiss AI Hub enthalten sind, ist der **RAG-Agent**. Dieser Agent ist der
Wissensspezialist Ihrer Organisation, der entwickelt wurde, um Fragen durch Konsultation Ihrer internen Dokumente und
Datenquellen zu beantworten. Er nutzt eine leistungsstarke Technik namens **Retrieval-Augmented Generation (RAG)**, um
Antworten zu liefern, die präzise, aktuell und in Ihrem spezifischen Geschäftskontext verankert sind.

Dieser Abschnitt erklärt, was der RAG-Agent ist, wie er funktioniert und warum er ein Eckpfeiler vertrauenswürdiger
Unternehmens-KI ist.

## Das Problem mit Standard-KI: Die Wissenslücke

Große Sprachmodelle (LLMs) werden mit riesigen Mengen öffentlicher Internetdaten trainiert. Obwohl dies sie unglaublich
kenntnisreich in Bezug auf allgemeine Themen macht, schafft es auch entscheidende Einschränkungen für den
Unternehmenseinsatz:

- **Ihr Wissen ist veraltet**: Ihre Informationen sind zum Zeitpunkt ihres letzten Trainings eingefroren, was Monate
  oder Jahre zurückliegen kann.
- **Sie kennen Ihr Geschäft nicht**: Sie haben keinen Zugriff auf Ihre internen Berichte, Richtlinien, Projektdokumente
  oder proprietären Daten.
- **Sie können „halluzinieren“**: Wenn sie keine Antwort wissen, könnten sie eine plausibel klingende, aber sachlich
  falsche Antwort generieren.
- **Sie können ihre Quellen nicht zitieren**: Sie können nicht einfach überprüfen, woher ihre Informationen stammen.

Der RAG-Agent ist speziell dafür konzipiert, diese Einschränkungen zu überwinden.

## Wie der RAG-Agent funktioniert

Anstatt sich ausschließlich auf sein vortrainiertes Wissen zu verlassen, folgt der RAG-Agent einem systematischen
Prozess, um seine Antworten in den verifizierten Informationen Ihrer Organisation zu verankern.

Wenn Sie dem RAG-Agenten eine Frage stellen, führt er einen ausgeklügelten Workflow aus:

1. **Fragenverständnis**: Zuerst verwendet der Agent ein LLM, um Ihre Frage zu verstehen und in eine optimale Abfrage
   für die Suche in seiner Wissensbasis umzuformulieren. Wenn Sie sich in einem längeren Gespräch befinden, komprimiert
   er den Chatverlauf, um sicherzustellen, dass die Abfrage eigenständig ist.
2. **Wissensabruf**: Der Agent führt dann eine semantische Suche über eine oder mehrere designierte **Wissensbasen**
   durch. Dies sind vektorindizierte Sammlungen Ihrer Dokumente, die über den Wissensmanagement-Dienst der Plattform
   verwaltet und durch Datenpipelines befüllt werden (beide Themen werden später ausführlich behandelt). Die Suche
   liefert die relevantesten Textausschnitte oder „Chunks“ aus Ihren Dokumenten.
3. **Kontextrekonstruktion**: Ein isolierter Text-Chunk ist oft bedeutungslos. Ein Ausschnitt, der besagt „gemäß der
   neuen Richtlinie“, ist nutzlos ohne den Kontext der Richtlinie. Der Agent rekonstruiert intelligent den umgebenden
   Kontext, indem er angrenzende Chunks aus dem Originaldokument oder sogar Zusammenfassungen auf übergeordneter Ebene
   abruft, um sicherzustellen, dass er das Gesamtbild versteht.
4. **Re-Ranking zur Relevanzsteigerung**: Der Agent kann Dutzende potenziell relevanter Chunks erhalten. Um die
   Genauigkeit zu verbessern, wendet er einen **Re-Ranking**-Schritt an. Ein spezialisiertes Modell bewertet die
   anfänglichen Suchergebnisse im Vergleich zu Ihrer spezifischen Frage und ordnet sie neu an, wobei die relevantesten
   Informationen an die Spitze verschoben werden.
5. **Antwortsynthese**: Schließlich nimmt der Agent Ihre ursprüngliche Frage, die am höchsten bewerteten, kontextreichen
   Informationen, die er abgerufen hat, und speist all dies in ein LLM ein. Er weist das Modell an, eine umfassende
   Antwort zu formulieren, die *ausschließlich* auf den bereitgestellten Informationen basiert, und seine Quellen
   anzugeben.

Dieser rigorose Prozess stellt sicher, dass die Antwort, die Sie erhalten, nicht nur eine Vermutung einer generischen KI
ist, sondern eine synthetisierte Antwort, die in Ihren tatsächlichen Daten verankert ist.

### Die Rolle von Wissensbasen und Pipelines

Die Effektivität des RAG-Agenten hängt von der Qualität und Aktualität seines Wissens ab. Hier kommen zwei weitere
Kernkomponenten des Swiss AI Hub ins Spiel:

- **Wissensbasen**: Dies sind die strukturierten, durchsuchbaren Bibliotheken der Informationen Ihrer Organisation. In
  der Benutzeroberfläche können Sie verschiedene Wissensbasen für unterschiedliche Themen erstellen und verwalten (z.B.
  „HR-Richtlinien“, „Technische Dokumentation“, „Projekt Alpha-Dateien“). Ein RAG-Agent ist immer so konfiguriert, dass
  er innerhalb einer oder mehrerer spezifischer Wissensbasen sucht.
- **Datenaufnahme-Pipelines (Data Ingestion Pipelines)**: Dies sind die automatisierten Prozesse, die Ihre Wissensbasen
  aktuell halten. Eine Standard-Pipeline kann Dokumente, die Sie über die Benutzeroberfläche hochladen, automatisch
  verarbeiten. Fortschrittlichere, benutzerdefinierte Pipelines können konfiguriert werden, um kontinuierlich mit
  externen Quellen wie **SharePoint** zu synchronisieren und sicherzustellen, dass Änderungen an Ihren Dokumenten
  automatisch in der Wissensbasis widergespiegelt werden.

Obwohl diese Komponenten später ausführlich dokumentiert werden, ist es wichtig zu verstehen, dass der RAG-Agent mit
ihnen zusammenarbeitet, um ein lebendiges, atmendes Wissenssystem bereitzustellen.

## Erweiterte Funktionen

Der RAG-Agent umfasst mehrere erweiterte Funktionen, um komplexe Abfragen zu verarbeiten und die Qualität seiner
Antworten sicherzustellen.

### Multi-Hop Retrieval

Manchmal reicht eine einzelne Suche nicht aus, um eine komplexe Frage zu beantworten. Wenn der anfängliche Abruf des
Agenten nicht genügend Informationen liefert, kann er ein **Multi-Hop Retrieval** durchführen. Der Agent analysiert die
Informationslücke, formuliert eine neue, spezifischere Abfrage und führt eine weitere Suche durch, um die fehlenden
Teile zu sammeln. Dieser iterative Prozess ermöglicht es ihm, Fragen zu beantworten, die die Synthese von Informationen
aus mehreren verschiedenen Dokumenten oder Abschnitten erfordern.

### Schutzmechanismen und Sicherheitsprüfungen

Bevor der Agent antwortet, kann er „Schutzmechanismen“ einsetzen, um die Abfrage und den abgerufenen Kontext zu
validieren:

- **Few-Shot Schutzmechanismus**: Dieser prüft, ob Ihre Frage angemessen und im vorgesehenen Umfang des Agenten liegt,
  indem er sie mit vordefinierten Beispielen für gute und schlechte Fragen vergleicht. Wenn Ihre Abfrage außerhalb des
  Bereichs liegt, wird der Agent höflich ablehnen, zu antworten.
- **Kontext-Suffizienz Schutzmechanismus**: Dieser prüft, ob die abgerufenen Informationen tatsächlich ausreichen, um
  Ihre Frage zu beantworten. Falls nicht, kann er den Multi-Hop Retrieval-Prozess auslösen, um weitere Informationen zu
  finden, oder Sie darüber informieren, dass eine vollständige Antwort in seiner Wissensbasis nicht gefunden werden
  kann.

Diese Prüfungen verhindern, dass der Agent Antworten von geringer Qualität oder irrelevante Antworten liefert, was seine
Zuverlässigkeit weiter erhöht.

## Warum der RAG-Agent für Ihr Unternehmen wichtig ist

Durch den Einsatz eines RAG-Agenten erhalten Sie ein leistungsstarkes Werkzeug, das:

- **Demokratisiert Wissen**: Mitarbeiter erhalten sofortige, genaue Antworten aus riesigen Beständen interner
  Dokumentationen, ohne wissen zu müssen, welches Dokument sie suchen oder wen sie fragen müssen.
- **Steigert die Produktivität**: Es reduziert die Zeit, die für die Informationssuche aufgewendet wird, drastisch und
  ermöglicht Ihrem Team, sich auf höherwertige Aufgaben zu konzentrieren.
- **Schafft Vertrauen in KI**: Durch die Bereitstellung überprüfbarer, quellenzitierter Antworten und das Agieren
  innerhalb definierter Schutzmechanismen zeigt der RAG-Agent, dass KI ein zuverlässiger und transparenter Partner am
  Arbeitsplatz sein kann.
- **Gewährleistet Informationsaktualität**: Dank automatischer Datenpipelines ist das Wissen des Agenten immer so
  aktuell wie Ihre Quelldokumente, wodurch das Risiko von Entscheidungen, die auf veralteten Informationen basieren,
  eliminiert wird.
