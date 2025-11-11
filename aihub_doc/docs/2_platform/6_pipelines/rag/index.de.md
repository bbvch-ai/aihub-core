---
title: Dokumentenrekonstruktion für Kontext
source_sha: 485b00c2e36d76a62ddd1579b7b79232a42d5227c48e0d10a544d132a4513970
---

# Deep Dive: Die RAG-Ingestion-Pipeline

Die Fähigkeit des RAG-Agenten, kontextsensitive, präzise Antworten zu liefern, ist keine Magie; sie ist das direkte
Ergebnis der sorgfältigen Arbeit, die von der **RAG Ingestion Pipeline** geleistet wird. Diese Pipeline ist der
automatisierte Prozess, der Ihre rohen, unstrukturierten Dokumente in eine hochstrukturierte und semantisch reichhaltige
Wissensbasis umwandelt.

Dieser Abschnitt befasst sich mit den einzelnen Phasen dieser Pipeline und erklärt, wie sie weit über die einfache
Textextraktion hinausgeht, um eine Grundlage für eine wahrhaft intelligente Retrieval-Funktion zu schaffen.

## Die Herausforderung: Rohdaten sind kein Wissen

Das bloße Extrahieren von Text aus einem Dokument und dessen Speicherung in einer Datenbank reicht nicht aus, um eine
nützliche Wissensbasis für eine KI zu schaffen. Rohem Text fehlt der entscheidende Kontext und die Beziehungen, die ein
menschlicher Leser intuitiv versteht. Für eine KI ist ein Absatz, der besagt „*siehe das Diagramm in Abschnitt 3.2*“,
bedeutungslos, ohne zu wissen, was Abschnitt 3.2 enthält.

Die grundlegende Herausforderung für jedes RAG-System ist ein Kompromiss:

- **Kleine Text-Chunks** eignen sich hervorragend für die präzise Suche, aber es fehlt ihnen an Kontext.
- **Große Text-Chunks** bieten viel Kontext, sind aber schlecht für die präzise Suche und können die Speichergrenze
  eines LLMs überschreiten.

Die RAG-Pipeline des Swiss AI Hub wurde entwickelt, um dieses Problem zu lösen, indem sie Dokumente nicht nur in Chunks
unterteilt, sondern ihre interne Struktur aktiv abbildet und bewahrt.

## Die Phasen der RAG-Pipeline

Die Pipeline verarbeitet jedes Dokument in einer Reihe von ausgeklügelten Phasen und erstellt dabei eine reichhaltige,
miteinander verknüpfte Darstellung der Informationen.

### 1. Ingestion und Parsing

Der Prozess beginnt, wenn die Pipeline ein Dokument aus einer verbundenen Quelle abruft. Anschließend nutzt sie
fortschrittliche Parsing-Technologie, um nicht nur den reinen Text zu extrahieren, sondern auch Strukturelemente wie
Überschriften, Tabellen, Listen und Abschnitte zu identifizieren. Dieses strukturelle Verständnis ist der erste Schritt
zur Bewahrung des Kontexts.

### 2. Intelligentes Chunking

Als Nächstes unterteilt die Pipeline das Dokument in optimal große Text-Chunks oder „Nodes“. Dies ist ein entscheidender
Schritt, der die Retrieval-Präzision mit dem Kontext in Einklang bringt. Das System verwendet semantische
Chunking-Techniken, um sicherzustellen, dass diese Trennungen an natürlichen Themen- oder Abschnittsgrenzen erfolgen und
zusammenhängende Gedanken beibehalten werden.

### 3. Anreicherung und Beziehungsabbildung

Dies ist die wichtigste Phase der Pipeline, in der sie eine einfache Liste von Chunks in einen „Knowledge Graph“
umwandelt. Anstatt jeden Chunk als isoliertes Datenelement zu behandeln, stellt die Pipeline explizite Beziehungen
zwischen ihnen her.

**Bewahrung des sequenziellen Kontexts** Die Pipeline analysiert die ursprüngliche Dokumentenreihenfolge und erstellt
eine bidirektionale Verknüpfung zwischen jedem aufeinanderfolgenden Chunk. Jeder Chunk kennt seinen Vorgänger und seinen
Nachfolger. Dies verwandelt den Inhalt des Dokuments effektiv in eine verknüpfte Liste, wodurch ein Agent später ganze
Passagen durch das Traversieren dieser Verknüpfungen rekonstruieren kann.

**Erfassung des hierarchischen Kontexts** Bei komplexen Dokumenten mit Abschnitten und Unterabschnitten leistet die
Pipeline noch mehr. Sie identifiziert die hierarchische Struktur und kann Zusammenfassungen auf jeder Ebene generieren
(z. B. eine Zusammenfassung für Abschnitt 3 und eine weitere für Abschnitt 3.2). Anschließend verknüpft sie die
einzelnen Text-Chunks wieder mit ihren übergeordneten Zusammenfassungen. Ein Chunk aus Unterabschnitt 3.2.4 hat nun eine
direkte Verknüpfung zur Zusammenfassung von 3.2, die wiederum mit der Zusammenfassung von Abschnitt 3 verknüpft ist.

### 4. Embedding und Indexierung

Schließlich wird jeder Chunk und jede Zusammenfassung in ein Vektor-Embedding umgewandelt und in der Vektordatenbank
gespeichert. Der entscheidende Unterschied besteht darin, dass diese Vektoren *zusammen mit allen Metadaten der
Beziehungen* gespeichert werden, die im vorherigen Schritt erstellt wurden.

::: tip Das Ergebnis: Eine strukturbewusste Wissensbasis
Das Endprodukt der RAG-Pipeline ist nicht nur ein durchsuchbarer Textindex. Es ist eine strukturbewusste Wissensbasis,
in der jedes Informationselement seinen Platz innerhalb des Originaldokuments und seine Beziehung zum umgebenden Inhalt
kennt. Diese reichhaltige Struktur ist der Schlüssel, der die erweiterten Fähigkeiten des RAG-Agenten freischaltet.
:::

## Wie die Pipeline den RAG-Agenten befähigt

Diese sorgfältige Vorbereitung durch die Pipeline ermöglicht die ausgeklügelten Retrieval- und Reasoning-Funktionen des
RAG-Agenten. Wenn ein Agent die Wissensbasis abfragt, erhält er nicht nur eine Liste unzusammenhängender Textausschnitte
zurück; er erhält eine Reihe von Einstiegspunkten in einen reichhaltigen Knowledge Graph.

::: details Freischaltung erweiterter Agentenfunktionen
- **Dokumentenrekonstruktion**: Wenn der Agent einen relevanten Chunk abruft, kann er die von der Pipeline erstellten
  „Vorher-Nächster“-Verknüpfungen nutzen, um die umgebenden Chunks abzurufen und so den vollständigen Absatz oder die
  Passage für einen vollständigen Kontext effektiv zu rekonstruieren. So versteht er Referenzen wie „*die oben genannte
  Anforderung*“.

- **Hierarchisches Verständnis**: Wenn ein Agent ein sehr spezifisches Detail abruft, kann er die von der Pipeline
  erstellten „Eltern“-Verknüpfungen durchlaufen, um Zusammenfassungen der enthaltenden Abschnitte abzurufen. Dies hilft
  dem Agenten, den breiteren Kontext einer bestimmten Information zu verstehen und die Frage zu beantworten: „*Wo passt
  dieses Detail ins Gesamtbild?*“

- **Intelligenteres Multi-Hop-Retrieval**: Die reichhaltigen Metadaten und die von der Pipeline erstellte Struktur
  ermöglichen es dem Agenten, intelligentere Multi-Hop-Abfragen durchzuführen. Wenn der Agent feststellt, dass sein
  anfänglicher Kontext unzureichend ist, kann er die Struktur des Dokuments nutzen, um eine präzisere Folgeabfrage zu
  formulieren, zum Beispiel indem er gezielt einen anderen Abschnitt desselben Dokuments anspricht.
:::

Im Wesentlichen leistet die RAG Ingestion Pipeline die Vorarbeit. Sie investiert Rechenressourcen während der
Ingestionsphase, um eine hochpräzise Darstellung Ihres Wissens aufzubauen. Diese Investition zahlt sich jedes Mal aus,
wenn ein Benutzer eine Frage stellt, und ermöglicht es dem RAG-Agenten, mit einem Grad an Kontextverständnis und
Genauigkeit zu agieren, den einfachere Systeme nicht erreichen können.
