---
title: RAG-Aufnahmepipeline
source_sha: dd46e27e562d4bbac99229aebb918e8f63449c59df0a53e905c2c7d57eac3b6c
---

# RAG-Aufnahmepipeline

Die RAG-Pipeline (Retrieval-Augmented Generation) ist die Standard-Pipeline für die Dokumentenaufnahme. Sie
transformiert Dokumente aus dem Dateispeicher in durchsuchbare Wissensdatenbanken, die von Agenten abgefragt werden
können. Alle Dokumente, auf die Agenten zugreifen sollen, müssen diese Pipeline durchlaufen.

## Verarbeitungsstufen

Die Pipeline verarbeitet Dokumente in fünf Stufen:

1. Document Parsing extrahiert Textinhalte und -strukturen aus PDFs, Word-Dokumenten, PowerPoint-Präsentationen und
   anderen Formaten. Der Parser identifiziert Überschriften, Absätze, Listen und Tabellen, während die
   Dokumentorganisation erhalten bleibt.

2. Chunking teilt große Dokumente in kleinere Text-Chunks auf. Die Pipeline verwendet einen strukturellen Parser, der
   den Text an Überschriftengrenzen und Absatzumbrüchen statt an willkürlichen Zeichenanzahlen aufteilt, um
   sicherzustellen, dass jeder Chunk kohärente Informationen enthält.

3. Die Embedding-Generierung wandelt jeden Text-Chunk mithilfe eines KI-Modells in ein Vektor-Embedding um. Diese
   Embeddings erfassen die semantische Bedeutung und ermöglichen es Agenten, relevante Informationen auf der Grundlage
   von Konzepten und nicht durch Keyword-Matching zu finden.

4. Strukturelle Verlinkung (Structural Linking) erstellt zwei Arten von Verbindungen zwischen Chunks:

   - Sequentielle Links verbinden jeden Chunk mit den vorangehenden und nachfolgenden Chunks in Dokumentenreihenfolge.
     Wenn ein Agent einen relevanten Chunk findet, kann er umgebende Chunks für den vollständigen Kontext abrufen.
   - Hierarchische Links verbinden Chunks mit Abschnittszusammenfassungen basierend auf Überschriftenebenen. Wenn ein
     Chunk aus Unterabschnitt 3.2.4 (Überschriftenebene 4) stammt, verlinkt er zu einer Zusammenfassung von Abschnitt
     3.2 (Überschriftenebene 3), die wiederum zu einer Zusammenfassung von Abschnitt 3 (Überschriftenebene 2) verlinkt.

5. Die Zusammenfassungsgenerierung erstellt hierarchische Zusammenfassungen für Dokumentabschnitte. Diese
   Zusammenfassungen helfen Agenten, einen breiteren Kontext zu verstehen, wenn sie spezifische Details aus
   verschachtelten Abschnitten abrufen.

## Speicherung und Abruf

Nach der Verarbeitung speichert die Pipeline:

- Vektor-Embeddings in der Vektordatenbank für die semantische Suche
- Original-Text-Chunks mit Metadaten
- Sequentielle und hierarchische Links zwischen Chunks
- Abschnittszusammenfassungen auf jeder Überschriftenebene

Dies erstellt einen Wissensgraphen und nicht nur isolierte Textfragmente. Wenn ein Agent nach Informationen sucht, ruft
er relevante Chunks ab und kann über sequentielle und hierarchische Links navigieren, um einen vollständigen Kontext
aufzubauen.

## Dokumentenlebenszyklus

Die Pipeline verwaltet den vollständigen Dokumentenlebenszyklus:

Wenn ein Dokument hinzugefügt wird, verarbeitet die Pipeline es in allen fünf Stufen und speichert die Ergebnisse in der
Wissensdatenbank.

Wenn ein Dokument geändert wird, entfernt die Pipeline alle Daten der alten Version, bevor die neue Version erneut
verarbeitet wird.

Wenn ein Dokument gelöscht wird, entfernt die Pipeline alle zugehörigen Chunks, Embeddings, Links und Zusammenfassungen
aus der Wissensdatenbank.

Dies stellt sicher, dass Agenten niemals Informationen aus veralteten oder gelöschten Dokumenten abrufen.

## Vorteile der Dokumentorganisation

Strukturelle Verlinkung bietet den größten Nutzen für Dokumente mit klarer Organisation: technische Handbücher mit
Abschnitten und Unterabschnitten, juristische Dokumente mit nummerierten Artikeln, Richtliniendokumente mit
hierarchischen Verfahren und lange Berichte, bei denen der Kontext mehrere Abschnitte umfasst.

Dokumente ohne komplexe Struktur (Ankündigungen, E-Mails, kurze Artikel) profitieren dennoch von der semantischen Suche
und der sequentiellen Verlinkung.
