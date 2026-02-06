---
title: Wissensmanagement
source_sha: 87bfef83579665975ab2f7a3433afe044ee8176efa87f937f552aff04d9ac877
---

# Wissensmanagement

KI-Agenten benötigen Zugriff auf relevante Informationen, um Fragen präzise beantworten zu können. Das
Wissensmanagementsystem verarbeitet Ihre Dokumente und macht sie durch semantische Abfrage durchsuchbar.

## Struktur

Wissen gliedert sich in drei Ebenen:

Wissensdatenbanken sind isolierte Container auf der obersten Ebene. Jede Datenbank hat ihre eigenen Daten,
Berechtigungen und eine eigene Verarbeitungspipeline. Organisationen erstellen Datenbanken typischerweise pro Abteilung,
Projekt oder Sicherheitsklassifizierung.

Namespaces (in der Benutzeroberfläche als „Sammlungen“ bezeichnet) gruppieren zusammengehörige Dokumente innerhalb einer
Datenbank. Sie funktionieren wie Ordner, die nach Thema oder Zweck organisiert sind. Eine Produktdatenbank könnte
Sammlungen wie „technical“, „guides“ und „troubleshooting“ enthalten.

Dokumente sind die eigentlichen Dateien – PDFs, Word-Dokumente, PowerPoint-Präsentationen. Das System verarbeitet sie
nach dem Hochladen automatisch.

::: info Mehrsprachige Unterstützung
Datenbanknamen, Namespace-Bezeichnungen und Ordnerbeschreibungen unterstützen Deutsch, Englisch, Französisch und
Italienisch. Die Benutzeroberfläche zeigt die Bezeichnungen entsprechend der Spracheinstellung des Benutzers an.
:::

## Inhalte verwalten

### Manuelle Verwaltung

Standardmäßig ermöglichen Datenbanken eine manuelle Kontrolle:

1. Sammlungen über die Weboberfläche erstellen
2. Dokumente in bestimmte Sammlungen hochladen
3. Auf den nächsten geplanten Pipeline-Durchlauf warten

![Empty knowledge database](../../../media/knowledge/empty_knowledge_base.png)

Sie steuern, was hochgeladen wird und wo es sich befindet. Die Pipeline läuft nach einem Zeitplan (üblicherweise für die
nächtliche Verarbeitung konfiguriert), um die Dokumentenverarbeitung und -indizierung zu übernehmen.

### Automatische Synchronisierung aus externen Quellen

Markieren Sie eine Datenbank als „auto-sync“, um sie mit externen Inhaltsquellen wie SharePoint zu verbinden. Das System
führt dann folgende Schritte aus:

- Synchronisiert Dateien aus der externen Quelle nach einem Zeitplan (typischerweise nächtlich)
- Erstellt Sammlungen automatisch aus der Ordnerstruktur
- Verarbeitet neue Inhalte während des geplanten Pipeline-Durchlaufs
- Deaktiviert manuelle Uploads über die Benutzeroberfläche

Das externe System wird zur Quelle der Wahrheit. Ihr Team arbeitet weiterhin in SharePoint, und die Sync-Pipeline
überträgt Änderungen nach dem konfigurierten Zeitplan in den AI-Hub.

## Dokumentenverarbeitung

Das System verarbeitet jedes hochgeladene Dokument in mehreren Phasen:

Parsing: MinerU extrahiert Text, Tabellen, Abbildungen und Strukturen aus PDFs und Office-Dokumenten. Es verarbeitet
komplexe Layouts, mehrspaltige Seiten und eingebettete Inhalte, während die logische Struktur erhalten bleibt.

Chunking: Große Dokumente werden in kleinere Abschnitte (Chunks) aufgeteilt, die den Kontext bewahren. Ein 50-seitiges
Handbuch wird zu Hunderten von Chunks, wobei jeder seine Beziehung zum umgebenden Inhalt beibehält.

Metadatenextraktion: Das System erfasst Erstellungsdaten, Autoren, Quellinformationen und die erkannte Sprache. Agenten
können Ergebnisse mithilfe dieser Metadaten filtern.

Vektor-Embedding: Text-Chunks werden in Vektorrepräsentationen umgewandelt, die die semantische Bedeutung erfassen.
Agenten finden relevante Inhalte basierend auf Konzepten, nicht nur auf Keyword-Matching. Eine Abfrage zu
„Geschwindigkeitsbegrenzungen für Fahrzeuge“ stimmt mit Inhalten über „maximale Geschwindigkeitsbeschränkungen“ überein.

## Inspektion und Debugging

Das System bietet Einblick in die Dokumentenverarbeitung:

Die Dokumentenrekonstruktion zeigt, wie der Parser Ihr Dokument interpretiert hat. Überprüfen Sie, ob Tabellen,
Seitenleisten und andere Strukturelemente korrekt identifiziert wurden.

Die Chunk-Inspektion zeigt, wie das System Inhalte segmentiert, welche Metadaten es extrahiert und wie es Chunks für den
Abruf darstellt. Nützlich, wenn Agenten erwartete Inhalte nicht finden.

Der Verarbeitungsstatus zeigt an, ob Dokumente hochgeladen, verarbeitet oder bereit sind.

## Zugriffssteuerung

Das Berechtigungssystem steuert alle Wissensoperationen:

- Das Anzeigen von Datenbanken erfordert entsprechende Berechtigungen
- Der Zugriff auf Namespaces überprüft die Benutzerautorisierung
- Das Hochladen von Dokumenten validiert Benutzerrechte
- Die Überprüfung von Verarbeitungsdetails erfordert eine Berechtigung

Wissensdatenbanken bieten natürliche Isolationsgrenzen. Organisationen können separate Datenbanken pro Abteilung oder
Projekt erstellen und dann Berechtigungen verwenden, um zu steuern, wer auf jede Datenbank zugreift.

## Agentenintegration

Agenten verbinden sich mit bestimmten Sammlungen anstatt mit ganzen Datenbanken. Beim Konfigurieren eines Agenten geben
Sie an, welche Sammlungen er durchsuchen kann. Ein Kundensupport-Agent könnte auf „products“ und „faq“ zugreifen, aber
nicht auf „engineering“.

Die auf Sammlungen beschränkte Abfrage hält Agenten auf relevante Inhalte fokussiert und verbessert sowohl die
Geschwindigkeit als auch die Genauigkeit.

Dokumente werden für Agenten verfügbar, nachdem die Pipeline sie verarbeitet hat. Das System verfolgt, welche
Quelldokumente Agenten verwendet haben, was die Zitation und Überprüfung von Antworten ermöglicht.

## Technische Implementierung

Die Architektur verwendet:

- FerretDB für Dokumentenmetadaten und Verarbeitungsstatus
- Milvus für Vektorspeicherung und semantische Suche
- MinerU für Dokumenten-Parsing und Strukturextraktion
- SeaweedFS für S3-kompatiblen Dateispeicher
- LlamaIndex für Chunking- und Embedding-Orchestrierung

Verarbeitungsmetadaten befinden sich in FerretDB, Vektor-Embeddings in Milvus, Rohdateien in SeaweedFS. Diese Trennung
optimiert jede Komponente für ihre spezifische Aufgabe.

## Einschränkungen

Keine gemischten Modi: Eine Datenbank wird entweder manuell verwaltet oder automatisch synchronisiert, nicht beides.
Dies verhindert Mehrdeutigkeiten bezüglich der Inhaltsquellen.

Keine manuelle Chunk-Bearbeitung: Das System generiert Chunks automatisch aus Quelldokumenten. Um fehlerhafte Chunks zu
korrigieren, aktualisieren Sie das Quelldokument und verarbeiten Sie es erneut.

Kein Datenbank-Merging: Datenbanken bleiben designbedingt isoliert. Eine Reorganisation erfordert das Erstellen neuer
Strukturen und das Migrieren von Dokumenten.
