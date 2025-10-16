---
title: Der RAG-Agent
index: 2
source_sha: "d7ed6f1f11dc2003a76f9c4416888bbfd4201cbcdb5ddaa71bbeea1dce1c253d"
---

# Der RAG-Agent: Ihr Wissensspezialist

Einer der Standard-Agenten, die im Swiss AI Hub enthalten sind, ist der **RAG-Agent**. Dieser Agent ist der Wissensspezialist Ihrer Organisation, der darauf ausgelegt ist, Fragen durch Konsultation Ihrer internen Dokumente und Datenquellen zu beantworten. Er nutzt eine leistungsstarke Technik namens **Retrieval-Augmented Generation (RAG)**, um Antworten zu liefern, die präzise, aktuell und in Ihrem spezifischen Geschäftskontext verankert sind.

Dieser Abschnitt erklärt, was der RAG-Agent ist, wie er funktioniert und warum er ein Eckpfeiler vertrauenswürdiger Unternehmens-KI ist.

## Das Problem mit Standard-KI: Die Wissenslücke

Große Sprachmodelle (LLMs) werden mit riesigen Mengen öffentlicher Internetdaten trainiert. Obwohl sie dadurch über ein unglaubliches Wissen zu allgemeinen Themen verfügen, ergeben sich daraus auch kritische Einschränkungen für den Unternehmenseinsatz:
-   **Ihr Wissen ist veraltet**: Ihre Informationen sind zum Zeitpunkt ihres letzten Trainings eingefroren, was Monate oder Jahre zurückliegen kann.
-   **Sie kennen Ihr Geschäft nicht**: Sie haben keinen Zugang zu Ihren internen Berichten, Richtlinien, Projektdokumenten oder proprietären Daten.
-   **Sie können „halluzinieren“**: Wenn sie eine Antwort nicht wissen, könnten sie eine plausibel klingende, aber sachlich falsche Antwort generieren.
-   **Sie können ihre Quellen nicht zitieren**: Sie können nicht einfach überprüfen, woher ihre Informationen stammen.

Der RAG-Agent wurde speziell entwickelt, um diese Einschränkungen zu überwinden.

## Wie der RAG-Agent funktioniert

Anstatt sich ausschließlich auf sein vortrainiertes Wissen zu verlassen, folgt der RAG-Agent einem systematischen Prozess, um seine Antworten in den verifizierten Informationen Ihrer Organisation zu verankern.

Wenn Sie dem RAG-Agenten eine Frage stellen, führt er einen ausgeklügelten Workflow aus:

1.  **Fragenverständnis**: Zuerst nutzt der Agent ein LLM, um Ihre Frage zu verstehen und in eine optimale Abfrage für die Suche in seiner Wissensbasis umzuformulieren. Wenn Sie sich in einer langen Unterhaltung befinden, fasst er den Chatverlauf zusammen, um sicherzustellen, dass die Abfrage eigenständig ist.
2.  **Wissensabruf**: Der Agent führt dann eine semantische Suche über eine oder mehrere festgelegte **Wissensbasen** durch. Dies sind vektor-indizierte Sammlungen Ihrer Dokumente, die über den Wissensmanagement-Dienst der Plattform verwaltet und durch Datenpipelines befüllt werden (beide Themen werden später ausführlich behandelt). Die Suche liefert die relevantesten Textausschnitte, oder „Chunks“, aus Ihren Dokumenten zurück.
3.  **Kontextrekonstruktion**: Ein isolierter Text-Chunk ist oft bedeutungslos. Ein Ausschnitt, der besagt „gemäß der neuen Richtlinie“, ist ohne den Kontext der Richtlinie nutzlos. Der Agent rekonstruiert intelligent den umgebenden Kontext, indem er angrenzende Chunks aus dem Originaldokument oder sogar Zusammenfassungen auf übergeordneter Ebene abruft, um sicherzustellen, dass er das Gesamtbild versteht.
4.  **Neubewertung der Relevanz (Re-ranking)**: Der Agent kann Dutzende potenziell relevanter Chunks erhalten. Um die Genauigkeit zu verbessern, wendet er einen **Re-ranking**-Schritt an. Ein spezialisiertes Modell bewertet die anfänglichen Suchergebnisse anhand Ihrer spezifischen Frage und ordnet sie neu an, wobei die relevantesten Informationen an die Spitze gerückt werden.
5.  **Antwortsynthese**: Schließlich nimmt der Agent Ihre ursprüngliche Frage, die am höchsten bewerteten, kontextreichen Informationen, die er abgerufen hat, und speist all dies in ein LLM ein. Er weist das Modell an, eine umfassende Antwort *nur* auf der Grundlage der bereitgestellten Informationen zu formulieren und seine Quellen anzugeben.

Dieser rigorose Prozess stellt sicher, dass die Antwort, die Sie erhalten, nicht nur eine Vermutung einer generischen KI ist, sondern eine synthetisierte Antwort, die auf Ihren tatsächlichen Daten basiert.

### Die Rolle von Wissensbasen und Pipelines

Die Effektivität des RAG-Agenten hängt von der Qualität und Aktualität seines Wissens ab. Hier kommen zwei weitere Kernkomponenten des Swiss AI Hub ins Spiel:

-   **Wissensbasen**: Dies sind die strukturierten, durchsuchbaren Bibliotheken der Informationen Ihrer Organisation. In der Benutzeroberfläche (UI) können Sie verschiedene Wissensbasen für unterschiedliche Themen erstellen und verwalten (z. B. „HR-Richtlinien“, „Technische Dokumentation“, „Projekt Alpha-Dateien“). Ein RAG-Agent ist immer so konfiguriert, dass er in einer oder mehreren spezifischen Wissensbasen sucht.
-   **Datenaufnahme-Pipelines (Data Ingestion Pipelines)**: Dies sind die automatisierten Prozesse, die Ihre Wissensbasen auf dem neuesten Stand halten. Eine Standard-Pipeline kann Dokumente, die Sie über die Benutzeroberfläche hochladen, automatisch verarbeiten. Fortgeschrittenere, kundenspezifische Pipelines können so konfiguriert werden, dass sie sich kontinuierlich mit externen Quellen wie **SharePoint** synchronisieren, um sicherzustellen, dass Änderungen an Ihren Dokumenten automatisch in der Wissensbasis widergespiegelt werden.

Obwohl diese Komponenten später ausführlich dokumentiert werden, ist es wichtig zu verstehen, dass der RAG-Agent mit ihnen zusammenarbeitet, um ein lebendiges, atmendes Wissenssystem bereitzustellen.

## Erweiterte Funktionen

Der RAG-Agent umfasst mehrere erweiterte Funktionen, um komplexe Abfragen zu verarbeiten und die Qualität seiner Antworten zu gewährleisten.

### Multi-Hop-Abruf

Manchmal reicht eine einzelne Suche nicht aus, um eine komplexe Frage zu beantworten. Wenn der anfängliche Abruf des Agenten nicht genügend Informationen liefert, kann er einen **Multi-Hop-Abruf** durchführen. Der Agent analysiert die Informationslücke, formuliert eine neue, spezifischere Abfrage und führt eine weitere Suche durch, um die fehlenden Teile zu sammeln. Dieser iterative Prozess ermöglicht es ihm, Fragen zu beantworten, die die Synthese von Informationen aus mehreren verschiedenen Dokumenten oder Abschnitten erfordern.

### Schutzmechanismen und Sicherheitsprüfungen

Bevor der Agent antwortet, kann er Schutzmechanismen einsetzen, um die Abfrage und den abgerufenen Kontext zu validieren:

-   **Few-Shot-Schutzmechanismus (Few-Shot Guard)**: Dieser prüft, ob Ihre Frage angemessen und innerhalb des vorgesehenen Umfangs des Agenten liegt, indem er sie mit vordefinierten Beispielen für gute und schlechte Fragen vergleicht. Wenn Ihre Abfrage außerhalb des Umfangs liegt, lehnt der Agent die Beantwortung höflich ab.
-   **Kontext-Hinreichendkeits-Schutzmechanismus (Context Sufficiency Guard)**: Dieser prüft, ob die abgerufenen Informationen tatsächlich ausreichen, um Ihre Frage zu beantworten. Falls nicht, kann er den Multi-Hop-Abrufprozess auslösen, um weitere Informationen zu finden, oder Sie darüber informieren, dass eine vollständige Antwort in seiner Wissensbasis nicht gefunden werden kann.

Diese Prüfungen verhindern, dass der Agent minderwertige oder irrelevante Antworten liefert, was seine Zuverlässigkeit weiter erhöht.

## Warum der RAG-Agent für Ihr Unternehmen wichtig ist

Durch den Einsatz eines RAG-Agenten erhalten Sie ein leistungsstarkes Tool, das:
-   **Demokratisiert Wissen**: Mitarbeiter erhalten sofortige, präzise Antworten aus riesigen internen Dokumentationsbeständen, ohne wissen zu müssen, welches Dokument zu suchen ist oder wen sie fragen sollen.
-   **Erhöht die Produktivität**: Es reduziert die Zeit, die für die Informationssuche aufgewendet wird, drastisch, sodass sich Ihr Team auf höherwertige Aufgaben konzentrieren kann.
-   **Baut Vertrauen in KI auf**: Indem er überprüfbare, quellenzitierte Antworten liefert und innerhalb definierter Schutzmechanismen operiert, zeigt der RAG-Agent, dass KI ein zuverlässiger und transparenter Partner am Arbeitsplatz sein kann.
-   **Gewährleistet Informationsaktualität**: Dank automatisierter Datenpipelines ist das Wissen des Agenten immer so aktuell wie Ihre Quelldokumente, wodurch das Risiko von Entscheidungen auf der Grundlage veralteter Informationen eliminiert wird.
