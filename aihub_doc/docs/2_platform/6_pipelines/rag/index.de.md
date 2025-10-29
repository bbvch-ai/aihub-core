---
title: Dokumentenrekonstruktion für Kontext
source_sha: "eb99d477247a5ba7cb9e9aba8576eadc4e291ca8c83333ded856d43735132a57"
---

# Deep Dive: Die RAG-Ingestionspipeline

Die Fähigkeit des RAG-Agenten, kontextbezogene, präzise Antworten zu liefern, ist keine Magie; sie ist das direkte Ergebnis der sorgfältigen Arbeit, die von der **RAG-Ingestionspipeline** geleistet wird. Diese Pipeline ist der automatisierte Prozess, der Ihre rohen, unstrukturierten Dokumente in eine hochstrukturierte und semantisch reiche Wissensbasis umwandelt.

Dieser Abschnitt befasst sich mit den Stufen dieser Pipeline und erklärt, wie sie weit über die einfache Textextraktion hinausgeht, um eine Grundlage für wirklich intelligente Retrieval zu schaffen.

## Die Herausforderung: Roher Text ist kein Wissen

Das bloße Extrahieren von Text aus einem Dokument und das Einfügen in eine Datenbank reicht nicht aus, um eine nützliche Wissensbasis für eine KI zu schaffen. Rohem Text fehlen die kritischen Kontexte und Beziehungen, die ein menschlicher Leser intuitiv versteht. Für eine KI ist ein Absatz, der sagt „siehe das Diagramm in Abschnitt 3.2“, bedeutungslos, ohne zu wissen, was Abschnitt 3.2 enthält.

Die grundlegende Herausforderung für jedes RAG-System ist ein Kompromiss:
-   **Kleine Text-Chunks** eignen sich hervorragend für die präzise Suche, aber es fehlt ihnen an Kontext.
-   **Große Text-Chunks** bieten viel Kontext, sind aber schlecht für die präzise Suche und können die Speichergrenze eines LLM überschreiten.

Die RAG-Pipeline des Swiss AI Hubs wurde entwickelt, um dieses Problem zu lösen, indem sie Dokumente nicht nur chunked, sondern ihre interne Struktur aktiv abbildet und bewahrt.

## Die Stufen der RAG-Pipeline

Die Pipeline verarbeitet jedes Dokument in einer Reihe von ausgeklügelten Stufen und erstellt so eine reichhaltige, vernetzte Darstellung der Informationen.

### 1. Ingestion und Parsing
Der Prozess beginnt, wenn die Pipeline ein Dokument aus einer verbundenen Quelle abruft. Sie verwendet dann fortschrittliche Parsing-Technologie, um nicht nur den Roh-Text zu extrahieren, sondern auch strukturelle Elemente wie Überschriften, Tabellen, Listen und Abschnitte zu identifizieren. Dieses strukturelle Verständnis ist der erste Schritt zur Wahrung des Kontexts.

### 2. Intelligentes Chunking
Als Nächstes zerlegt die Pipeline das Dokument in optimal dimensionierte Text-Chunks oder „Knoten“. Dies ist ein entscheidender Schritt, der die Retrieval-Präzision mit dem Kontext in Einklang bringt. Das System verwendet semantische Chunking-Techniken, um sicherzustellen, dass diese Trennungen an natürlichen Themen- oder Abschnittsgrenzen erfolgen und kohärente Gedanken zusammenhält.

### 3. Anreicherung und Beziehungszuordnung
Dies ist die wichtigste Stufe der Pipeline, in der sie eine einfache Liste von Chunks in einen „Wissensgraphen“ umwandelt. Anstatt jeden Chunk als isoliertes Datenelement zu behandeln, stellt die Pipeline explizite Beziehungen zwischen ihnen her.

**Wahrung des sequenziellen Kontexts**
Die Pipeline analysiert die ursprüngliche Dokumentenreihenfolge und erstellt eine bidirektionale Verknüpfung zwischen jedem sequenziellen Chunk. Jeder Chunk kennt seinen Vorgänger und seinen Nachfolger. Dies verwandelt den Inhalt des Dokuments effektiv in eine verkettete Liste, sodass ein Agent später ganze Passagen durch das Traversieren dieser Links rekonstruieren kann.

**Erfassung des hierarchischen Kontexts**
Bei komplexen Dokumenten mit Abschnitten und Unterabschnitten leistet die Pipeline noch mehr. Sie identifiziert die hierarchische Struktur und kann Zusammenfassungen auf jeder Ebene generieren (z. B. eine Zusammenfassung für Abschnitt 3 und eine weitere für Abschnitt 3.2). Anschließend verknüpft sie die einzelnen Text-Chunks wieder mit ihren übergeordneten Zusammenfassungen. Ein Chunk aus Unterabschnitt 3.2.4 hat nun eine direkte Verknüpfung zur Zusammenfassung von 3.2, die wiederum zur Zusammenfassung von Abschnitt 3 verknüpft ist.

### 4. Embedding und Indexierung
Schließlich wird jeder Chunk und jede Zusammenfassung in ein Vektor-Embedding umgewandelt und in der Vektordatenbank gespeichert. Der entscheidende Unterschied besteht darin, dass diese Vektoren *zusammen mit allen im vorherigen Schritt erstellten Beziehungsmetadaten* gespeichert werden.

::: tip Die Ausgabe: Eine strukturbewusste Wissensbasis
Das Endprodukt der RAG-Pipeline ist nicht nur ein durchsuchbarer Textindex. Es ist eine strukturbewusste Wissensbasis, in der jedes Informationselement seinen Platz innerhalb des Originaldokuments und seine Beziehung zum umgebenden Inhalt kennt. Diese reiche Struktur ist der Schlüssel, der die fortgeschrittenen Fähigkeiten des RAG-Agenten freischaltet.
:::

## Wie die Pipeline den RAG-Agenten befähigt

Diese sorgfältige Vorbereitung durch die Pipeline ermöglicht die ausgeklügelten Retrieval- und Argumentationsfunktionen des RAG-Agenten. Wenn ein Agent die Wissensbasis abfragt, erhält er nicht nur eine Liste unverbundener Textausschnitte zurück; er erhält eine Reihe von Einstiegspunkten in einen reichhaltigen Wissensgraphen.

::: details Freischaltung fortgeschrittener Agenten-Funktionen
-   **Dokumentenrekonstruktion**: Wenn der Agent einen relevanten Chunk abruft, kann er die von der Pipeline erstellten „Vorher-Nächster“-Links verwenden, um die umgebenden Chunks abzurufen und so den vollständigen Absatz oder die Passage für den vollständigen Kontext zu rekonstruieren. So versteht er Verweise wie „die oben genannten Anforderung“.

-   **Hierarchisches Verständnis**: Wenn ein Agent ein sehr spezifisches Detail abruft, kann er die von der Pipeline erstellten „Eltern“-Links durchlaufen, um Zusammenfassungen der enthaltenden Abschnitte abzurufen. Dies hilft dem Agenten, den breiteren Kontext eines spezifischen Informationselements zu verstehen und die Frage zu beantworten: „Wo passt dieses Detail ins Gesamtbild?“

-   **Intelligenz bei Multi-Hop-Retrieval**: Die reichhaltigen Metadaten und die Struktur, die von der Pipeline erstellt werden, ermöglichen es dem Agenten, intelligentere Multi-Hop-Abfragen durchzuführen. Wenn der Agent feststellt, dass sein anfänglicher Kontext unzureichend ist, kann er die Struktur des Dokuments nutzen, um eine präzisere Folgeanfrage zu formulieren, zum Beispiel indem er gezielt einen anderen Abschnitt desselben Dokuments anvisiert.
:::

Im Wesentlichen erledigt die RAG-Ingestionspipeline die Vorarbeit. Sie investiert Rechenressourcen während der Ingestionsphase, um eine hochpräzise Darstellung Ihres Wissens aufzubauen. Diese Investition zahlt sich jedes Mal aus, wenn ein Benutzer eine Frage stellt, indem sie es dem RAG-Agenten ermöglicht, mit einem Maß an kontextuellem Verständnis und Präzision zu agieren, das einfachere Systeme nicht erreichen können.
