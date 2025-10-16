---
title: Dokumentenrekonstruktion für Kontext
index: 2
source_sha: "8e0b85afe8548919a86b2a66172618bd9ff82ac72d273f8a67a8aa814fd74951"
---

# Vertiefung: Die RAG Ingestion Pipeline

Die Fähigkeit des RAG Agents, kontextbewusste, präzise Antworten zu liefern, ist keine Magie; sie ist das direkte Ergebnis der sorgfältigen Arbeit, die von der **RAG Ingestion Pipeline** geleistet wird. Diese Pipeline ist der automatisierte Prozess, der Ihre rohen, unstrukturierten Dokumente in eine hochstrukturierte und semantisch reiche Wissensbasis umwandelt.

Dieser Abschnitt befasst sich mit den einzelnen Phasen dieser Pipeline und erläutert, wie sie weit über die einfache Textextraktion hinausgeht, um eine Grundlage für wirklich intelligente Abrufe zu schaffen.

## Die Herausforderung: Roher Text ist kein Wissen

Einfaches Extrahieren von Text aus einem Dokument und das Ablegen in einer Datenbank reicht nicht aus, um eine nützliche Wissensbasis für eine KI zu schaffen. Roher Text entbehrt den kritischen Kontext und die Beziehungen, die ein menschlicher Leser intuitiv versteht. Für eine KI ist ein Absatz, der besagt „siehe das Diagramm in Abschnitt 3.2“, bedeutungslos, ohne zu wissen, was Abschnitt 3.2 enthält.

Die grundlegende Herausforderung für jedes RAG-System ist ein Kompromiss:
-   **Kleine Text-Chunks** eignen sich hervorragend für die präzise Suche, aber es fehlt ihnen an Kontext.
-   **Große Text-Chunks** bieten viel Kontext, sind aber schlecht für die präzise Suche und können das Speicherlimit eines LLM überschreiten.

Die RAG-Pipeline des Swiss AI Hub wurde entwickelt, um dieses Problem zu lösen, indem sie Dokumente nicht nur in Chunks zerlegt, sondern deren interne Struktur aktiv abbildet und bewahrt.

## Die Phasen der RAG-Pipeline

Die Pipeline verarbeitet jedes Dokument in einer Reihe ausgeklügelter Phasen und erstellt dabei eine reichhaltige, miteinander verbundene Repräsentation der Informationen.

### 1. Erfassung und Parsing
Der Prozess beginnt, wenn die Pipeline ein Dokument von einer verbundenen Quelle abruft. Sie verwendet dann fortschrittliche Parsing-Technologie, um nicht nur den Rohtext zu extrahieren, sondern auch Strukturelemente wie Überschriften, Tabellen, Listen und Abschnitte zu identifizieren. Dieses strukturelle Verständnis ist der erste Schritt zur Bewahrung des Kontexts.

### 2. Intelligentes Chunking
Als Nächstes zerlegt die Pipeline das Dokument in optimal große Text-Chunks oder „Nodes“. Dies ist ein entscheidender Schritt, der die Präzision des Abrufs mit dem Kontext in Einklang bringt. Das System verwendet semantische Chunking-Techniken, um sicherzustellen, dass diese Trennungen an natürlichen Themen- oder Abschnittsgrenzen erfolgen, wodurch zusammenhängende Gedanken beibehalten werden.

### 3. Anreicherung und Beziehungsabbildung
Dies ist die wichtigste Phase der Pipeline, in der sie eine einfache Liste von Chunks in einen „Wissensgraphen“ umwandelt. Anstatt jeden Chunk als isoliertes Datenelement zu behandeln, stellt die Pipeline explizite Beziehungen zwischen ihnen her.

**Bewahrung des sequentiellen Kontexts**
Die Pipeline analysiert die ursprüngliche Dokumentreihenfolge und erstellt eine bidirektionale Verknüpfung zwischen jedem aufeinanderfolgenden Chunk. Jeder Chunk kennt seinen Vorgänger und seinen Nachfolger. Dies verwandelt den Inhalt des Dokuments effektiv in eine verkettete Liste, die es einem Agenten ermöglicht, später ganze Passagen durch das Traversieren dieser Links zu rekonstruieren.

**Erfassung des hierarchischen Kontexts**
Bei komplexen Dokumenten mit Abschnitten und Unterabschnitten leistet die Pipeline noch mehr. Sie identifiziert die hierarchische Struktur und kann Zusammenfassungen auf jeder Ebene generieren (z. B. eine Zusammenfassung für Abschnitt 3 und eine weitere für Abschnitt 3.2). Anschließend verknüpft sie die einzelnen Text-Chunks mit ihren übergeordneten Zusammenfassungen. Ein Chunk aus Unterabschnitt 3.2.4 hat nun eine direkte Verknüpfung zur Zusammenfassung von 3.2, die wiederum mit der Zusammenfassung von Abschnitt 3 verknüpft ist.

### 4. Embedding und Indexierung
Schließlich wird jeder Chunk und jede Zusammenfassung in ein Vektor-Embedding umgewandelt und in der Vektordatenbank gespeichert. Der entscheidende Unterschied besteht darin, dass diese Vektoren *zusammen mit allen im vorherigen Schritt erstellten Beziehungsmetadaten* gespeichert werden.

::: tip Das Ergebnis: Eine strukturbewusste Wissensbasis
Das Endprodukt der RAG-Pipeline ist nicht nur ein durchsuchbarer Textindex. Es ist eine strukturbewusste Wissensbasis, in der jedes Informationselement seinen Platz innerhalb des Originaldokuments und seine Beziehung zum umgebenden Inhalt kennt. Diese reichhaltige Struktur ist der Schlüssel, der die erweiterten Fähigkeiten des RAG Agents freischaltet.
:::

## Wie die Pipeline den RAG Agent befähigt

Diese akribische Vorbereitung durch die Pipeline ermöglicht die anspruchsvollen Abruf- und Reasoning-Funktionen des RAG Agents. Wenn ein Agent die Wissensbasis abfragt, erhält er nicht nur eine Liste unzusammenhängender Textausschnitte zurück; er erhält einen Satz von Einstiegspunkten in einen reichhaltigen Wissensgraphen.

::: details Erschließung erweiterter Agenten-Fähigkeiten
-   **Dokumentenrekonstruktion**: Wenn der Agent einen relevanten Chunk abruft, kann er die von der Pipeline erstellten „Vorher-Nacher“-Links verwenden, um die umgebenden Chunks abzurufen und so den gesamten Absatz oder die Passage für den vollständigen Kontext effektiv zu rekonstruieren. So versteht er Referenzen wie „die oben genannte Anforderung“.

-   **Hierarchisches Verständnis**: Wenn ein Agent ein sehr spezifisches Detail abruft, kann er die von der Pipeline erstellten „Eltern“-Links durchlaufen, um Zusammenfassungen der enthaltenden Abschnitte abzurufen. Dies hilft dem Agenten, den breiteren Kontext einer spezifischen Information zu verstehen und die Frage zu beantworten: „Wo passt dieses Detail ins Gesamtbild?“

-   **Intelligenterer Multi-Hop-Abruf**: Die reichhaltigen Metadaten und die Struktur, die von der Pipeline erstellt werden, ermöglichen es dem Agenten, intelligentere Multi-Hop-Abfragen durchzuführen. Wenn der Agent feststellt, dass sein anfänglicher Kontext unzureichend ist, kann er die Struktur des Dokuments verwenden, um eine präzisere Folgeabfrage zu formulieren, indem er beispielsweise gezielt einen anderen Abschnitt desselben Dokuments anspricht.
:::

Im Wesentlichen leistet die RAG Ingestion Pipeline die Vorarbeit. Sie investiert Rechenressourcen während der Erfassungsphase, um eine hochpräzise Repräsentation Ihres Wissens aufzubauen. Diese Investition zahlt sich jedes Mal aus, wenn ein Benutzer eine Frage stellt, da sie es dem RAG Agent ermöglicht, mit einem Maß an kontextuellem Verständnis und Genauigkeit zu agieren, das einfachere Systeme nicht erreichen können.
