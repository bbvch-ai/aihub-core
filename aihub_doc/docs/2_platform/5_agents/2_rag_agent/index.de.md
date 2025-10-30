---
title: Der RAG Agent
source_sha: 4eb9a05c40f9b6d6e1c91234da27d9eeb42f21c29701c6ce08c41ec1b01e9965
---

# Der RAG Agent: Ihr Wissensspezialist

Einer der Standard-Agenten, die im Swiss AI Hub enthalten sind, ist der **RAG Agent**. Dieser Agent ist der
Wissensspezialist Ihrer Organisation, der darauf ausgelegt ist, Fragen durch die Konsultation Ihrer internen Dokumente
und Datenquellen zu beantworten. Er nutzt eine leistungsstarke Technik namens **Retrieval-Augmented Generation (RAG)**,
um Antworten zu liefern, die präzise, aktuell und in Ihrem spezifischen Geschäftskontext verankert sind.

Dieser Abschnitt erklärt, was der RAG Agent ist, wie er funktioniert und warum er ein Eckpfeiler vertrauenswürdiger
Unternehmens-KI ist.

## Das Problem mit Standard-KI: Die Wissenslücke

Large Language Models (LLMs) werden mit riesigen Mengen öffentlicher Internetdaten trainiert. Obwohl dies sie
unglaublich sachkundig in Bezug auf allgemeine Themen macht, schafft es auch kritische Einschränkungen für den
Unternehmenseinsatz:

- **Ihr Wissen ist veraltet**: Ihre Informationen sind zum Zeitpunkt ihres letzten Trainings eingefroren, was Monate
  oder Jahre zurückliegen kann.
- **Sie kennen Ihr Geschäft nicht**: Sie haben keinen Zugriff auf Ihre internen Berichte, Richtlinien, Projektdokumente
  oder proprietären Daten.
- **Sie können „halluzinieren“**: Wenn sie eine Antwort nicht wissen, könnten sie eine plausibel klingende, aber
  faktisch falsche Antwort generieren.
- **Sie können ihre Quellen nicht zitieren**: Sie können nicht einfach überprüfen, woher ihre Informationen stammen.

Der RAG Agent wurde speziell entwickelt, um diese Einschränkungen zu überwinden.

## Wie der RAG Agent funktioniert

Anstatt sich ausschließlich auf sein vorab trainiertes Wissen zu verlassen, folgt der RAG Agent einem systematischen
Prozess, um seine Antworten auf die verifizierten Informationen Ihrer Organisation zu stützen.

Wenn Sie dem RAG Agenten eine Frage stellen, führt er einen ausgeklügelten Workflow aus:

1. **Fragenverständnis**: Zuerst nutzt der Agent ein LLM, um Ihre Frage zu verstehen und in eine optimale Abfrage für
   die Suche in seiner Knowledge Base umzuformululieren. Wenn Sie sich in einer langen Konversation befinden, verdichtet
   er den Chat-Verlauf, um sicherzustellen, dass die Abfrage eigenständig ist.
2. **Wissensabruf**: Der Agent führt dann eine semantische Suche über eine oder mehrere festgelegte **Knowledge Bases**
   durch. Dies sind vektorindizierte Sammlungen Ihrer Dokumente, die über den Knowledge Management Service der Plattform
   verwaltet und durch Datenpipelines befüllt werden (beide Themen werden später detailliert behandelt). Die Suche
   liefert die relevantesten Textausschnitte oder „Chunks“ aus Ihren Dokumenten.
3. **Kontextrekonstruktion**: Ein isolierter Text-Chunk ist oft bedeutungslos. Ein Ausschnitt, der besagt „gemäß der
   neuen Richtlinie“, ist ohne den Kontext der Richtlinie nutzlos. Der Agent rekonstruiert den umgebenden Kontext
   intelligent, indem er angrenzende Chunks aus dem Originaldokument oder sogar übergeordnete Zusammenfassungen abruft,
   um sicherzustellen, dass er das Gesamtbild versteht.
4. **Neuanordnung nach Relevanz**: Der Agent kann Dutzende potenziell relevanter Chunks erhalten. Um die Genauigkeit zu
   verbessern, setzt er einen **Re-Ranking**-Schritt ein. Ein spezialisiertes Modell bewertet die anfänglichen
   Suchergebnisse anhand Ihrer spezifischen Frage und ordnet sie neu an, wodurch die relevantesten Informationen an die
   Spitze gelangen.
5. **Antwortsynthese**: Schließlich nimmt der Agent Ihre ursprüngliche Frage, die am höchsten bewerteten, kontextreichen
   Informationen, die er abgerufen hat, und speist alles in ein LLM ein. Er weist das Modell an, eine umfassende Antwort
   zu formulieren, die *nur* auf den bereitgestellten Informationen basiert, und seine Quellen anzugeben.

Dieser rigorose Prozess stellt sicher, dass die Antwort, die Sie erhalten, nicht nur eine Vermutung einer generischen KI
ist, sondern eine synthetisierte Antwort, die auf Ihren tatsächlichen Daten basiert.

### Die Rolle von Knowledge Bases und Pipelines

Die Effektivität des RAG Agenten hängt von der Qualität und Aktualität seines Wissens ab. Hier kommen zwei weitere
Kernkomponenten des Swiss AI Hub ins Spiel:

- **Knowledge Bases**: Dies sind die strukturierten, durchsuchbaren Bibliotheken der Informationen Ihrer Organisation.
  In der Benutzeroberfläche können Sie verschiedene Knowledge Bases für unterschiedliche Themen erstellen und verwalten
  (z. B. „HR-Richtlinien“, „Technische Dokumentation“, „Projekt Alpha Dateien“). Ein RAG Agent ist immer so
  konfiguriert, dass er innerhalb einer oder mehrerer spezifischer Knowledge Bases sucht.
- **Data Ingestion Pipelines**: Dies sind die automatisierten Prozesse, die Ihre Knowledge Bases auf dem neuesten Stand
  halten. Eine Standard-Pipeline kann Dokumente, die Sie über die Benutzeroberfläche hochladen, automatisch verarbeiten.
  Fortgeschrittenere, benutzerdefinierte Pipelines können so konfiguriert werden, dass sie kontinuierlich mit externen
  Quellen wie **SharePoint** synchronisieren, um sicherzustellen, dass Änderungen an Ihren Dokumenten automatisch in der
  Knowledge Base widergespiegelt werden.

Während diese Komponenten später detailliert dokumentiert werden, ist es wichtig zu verstehen, dass der RAG Agent im
Zusammenspiel mit ihnen funktioniert, um ein lebendiges, atmendes Wissenssystem bereitzustellen.

## Erweiterte Funktionen

Der RAG Agent umfasst mehrere erweiterte Funktionen, um komplexe Abfragen zu verarbeiten und die Qualität seiner
Antworten sicherzustellen.

### Multi-Hop Retrieval

Manchmal reicht eine einzige Suche nicht aus, um eine komplexe Frage zu beantworten. Wenn der anfängliche Abruf des
Agenten nicht genügend Informationen liefert, kann er ein **Multi-Hop Retrieval** durchführen. Der Agent analysiert die
Informationslücke, formuliert eine neue, spezifischere Abfrage und führt eine weitere Suche durch, um die fehlenden
Teile zu sammeln. Dieser iterative Prozess ermöglicht es ihm, Fragen zu beantworten, die die Synthese von Informationen
aus mehreren verschiedenen Dokumenten oder Abschnitten erfordern.

### Guardrails und Sicherheitsüberprüfungen

Bevor der Agent antwortet, kann er „Guardrails“ einsetzen, um die Abfrage und den abgerufenen Kontext zu validieren:

- **Few-Shot Guard**: Dieser überprüft, ob Ihre Frage angemessen und innerhalb des vorgesehenen Bereichs des Agenten
  liegt, indem er sie mit vordefinierten Beispielen für gute und schlechte Fragen vergleicht. Wenn Ihre Abfrage
  außerhalb des Bereichs liegt, wird der Agent höflich ablehnen, zu antworten.
- **Context Sufficiency Guard**: Dieser überprüft, ob die abgerufenen Informationen tatsächlich ausreichen, um Ihre
  Frage zu beantworten. Falls nicht, kann er den Multi-Hop Retrieval-Prozess auslösen, um weitere Informationen zu
  finden, oder Sie darüber informieren, dass eine vollständige Antwort in seiner Knowledge Base nicht gefunden werden
  kann.

Diese Überprüfungen verhindern, dass der Agent minderwertige oder irrelevante Antworten liefert, was seine
Zuverlässigkeit weiter erhöht.

## Warum der RAG Agent für Ihr Unternehmen wichtig ist

Durch den Einsatz eines RAG Agenten erhalten Sie ein leistungsstarkes Tool, das:

- **Wissen demokratisiert**: Mitarbeiter können sofort genaue Antworten aus riesigen Beständen interner Dokumentationen
  erhalten, ohne wissen zu müssen, welches Dokument sie suchen oder wen sie fragen sollen.
- **Produktivität steigert**: Es reduziert drastisch die Zeit, die für die Informationssuche aufgewendet wird, sodass
  Ihr Team sich auf höherwertige Aufgaben konzentrieren kann.
- **Vertrauen in KI schafft**: Durch die Bereitstellung von überprüfbaren, quellenbasierten Antworten und das Agieren
  innerhalb definierter Guardrails zeigt der RAG Agent, dass KI ein zuverlässiger und transparenter Partner am
  Arbeitsplatz sein kann.
- **Stellt Informationsaktualität sicher**: Dank automatisierter Datenpipelines ist das Wissen des Agenten immer so
  aktuell wie Ihre Quelldokumente, wodurch das Risiko von Entscheidungen auf der Grundlage veralteter Informationen
  eliminiert wird.
