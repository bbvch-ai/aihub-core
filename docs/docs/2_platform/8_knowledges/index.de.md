---
title: Wissensmanagement
source_sha: 337c3246e70057fbaf878a3917f58526dd5963475b26c98010218882085927df
---

# Wissensmanagement

KI-Agents benötigen Zugriff auf relevante Informationen, um Fragen präzise zu beantworten. Das Wissensmanagementsystem
verarbeitet Ihre Dokumente und macht sie durch semantisches Retrieval durchsuchbar.

## Struktur

Wissen gliedert sich in drei Ebenen:

Wissensdatenbanken sind isolierte Container auf der obersten Ebene. Jede Datenbank verfügt über eigene Daten,
Berechtigungen und eine eigene Verarbeitungspipeline. Organisationen erstellen Datenbanken typischerweise pro Abteilung,
Projekt oder Sicherheitsklassifikation.

Namespaces (in der Benutzeroberfläche als „Sammlungen“ bezeichnet) gruppieren verwandte Dokumente innerhalb einer
Datenbank. Sie funktionieren wie Ordner, die nach Thema oder Zweck organisiert sind. Eine Produktdatenbank könnte
„Technik“-, „Anleitungen“- und „Fehlerbehebung“-Sammlungen enthalten.

Dokumente sind die eigentlichen Dateien – PDFs, Word-Dokumente, PowerPoint-Präsentationen. Das System verarbeitet sie
nach dem Upload automatisch.

::: info Mehrsprachige Unterstützung
Datenbanknamen, Namespace-Labels und Ordnerbeschreibungen unterstützen Deutsch, Englisch, Französisch und Italienisch.
Die Benutzeroberfläche zeigt Labels entsprechend der Sprachpräferenz des Benutzers an.
:::

## Inhalte verwalten

### Manuelle Verwaltung

Standardmäßig ermöglichen Datenbanken eine manuelle Kontrolle:

1. Sammlungen über die Weboberfläche erstellen
2. Dokumente in spezifische Sammlungen hochladen
3. Auf den nächsten geplanten Pipeline-Lauf warten

![Empty knowledge database](../../../media/knowledge/empty_knowledge_base.png)

Sie steuern, was hochgeladen wird und wo es sich befindet. Die Pipeline läuft nach einem Zeitplan (typischerweise für
die nächtliche Verarbeitung konfiguriert), um die Dokumentenverarbeitung und Indexierung zu übernehmen.

### Automatische Synchronisierung aus externen Quellen

Markieren Sie eine Datenbank für die automatische Synchronisierung, um sie mit externen Inhaltsquellen wie SharePoint zu
verbinden. Das System führt dann folgende Schritte aus:

- Synchronisiert Dateien von der externen Quelle nach einem Zeitplan (typischerweise nächtlich)
- Erstellt Sammlungen automatisch aus der Ordnerstruktur
- Verarbeitet neue Inhalte während des geplanten Pipeline-Laufs
- Deaktiviert manuelle Uploads über die Benutzeroberfläche

Das externe System wird zur Quelle der Wahrheit. Ihr Team arbeitet weiterhin in SharePoint, und die
Synchronisierungspipeline übernimmt die Änderungen gemäß dem konfigurierten Zeitplan in den Swiss AI Hub.

## Dokumentenverarbeitung

Das System verarbeitet jedes hochgeladene Dokument in mehreren Phasen:

Parsing: MinerU extrahiert Text, Tabellen, Abbildungen und Strukturen aus PDFs und Office-Dokumenten. Es verarbeitet
komplexe Layouts, mehrspaltige Seiten und eingebettete Inhalte, während die logische Struktur erhalten bleibt.

Chunking: Große Dokumente werden in kleinere Abschnitte (Chunks) unterteilt, die den Kontext bewahren. Ein 50-seitiges
Handbuch wird zu Hunderten von Chunks, wobei jeder seine Beziehung zum umgebenden Inhalt behält.

Metadatenextraktion: Das System erfasst Erstellungsdaten, Autoren, Quellinformationen und die erkannte Sprache. Agents
können Ergebnisse mithilfe dieser Metadaten filtern.

Vektor-Embedding: Text-Chunks werden in Vektorrepräsentationen umgewandelt, die die semantische Bedeutung erfassen.
Agents finden relevante Inhalte basierend auf Konzepten, nicht nur auf Keyword-Matching. Eine Abfrage zu
„Fahrzeuggeschwindigkeitsbegrenzungen“ findet Inhalte zu „maximalen Geschwindigkeitsbeschränkungen“.

## Inspektion und Fehlerbehebung

Das System bietet Einblicke in die Dokumentenverarbeitung:

Dokumentenrekonstruktion zeigt, wie der Parser Ihr Dokument interpretiert hat. Überprüfen Sie, ob Tabellen,
Seitenleisten und andere Strukturelemente korrekt identifiziert wurden.

Chunk-Inspektion zeigt, wie das System Inhalte segmentiert hat, welche Metadaten es extrahiert hat und wie es Chunks für
den Abruf darstellt. Nützlich, wenn Agents erwartete Inhalte nicht finden.

Verarbeitungsstatus zeigt an, ob Dokumente hochgeladen, verarbeitet oder bereit sind.

## Zugriffskontrolle

Das Berechtigungssystem steuert alle Wissensoperationen:

- Das Anzeigen von Datenbanken erfordert entsprechende Berechtigungen
- Der Zugriff auf Namespaces prüft die Benutzerautorisierung
- Das Hochladen von Dokumenten validiert Benutzerrechte
- Die Inspektion von Verarbeitungsdetails erfordert eine Berechtigung

Wissensdatenbanken bieten natürliche Isolationsgrenzen. Organisationen können separate Datenbanken pro Abteilung oder
Projekt erstellen und dann Berechtigungen verwenden, um den Zugriff auf jede Datenbank zu steuern.

## Agent-Integration

Agents verbinden sich mit spezifischen Sammlungen anstatt mit ganzen Datenbanken. Beim Konfigurieren eines Agents legen
Sie fest, welche Sammlungen er durchsuchen kann. Ein Kundensupport-Agent könnte auf „Produkte“ und „FAQ“ zugreifen, aber
nicht auf „Engineering“.

Sammlungsbezogenes Retrieval hält Agents auf relevante Inhalte fokussiert, wodurch sowohl die Geschwindigkeit als auch
die Genauigkeit verbessert werden.

Dokumente werden für Agents verfügbar, nachdem die Pipeline sie verarbeitet hat. Das System verfolgt, welche
Quelldokumente Agents verwendet haben, was die Zitierung und Verifizierung von Antworten ermöglicht.

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

Keine manuelle Chunk-Bearbeitung: Das System generiert Chunks automatisch aus Quelldokumenten. Um inkorrekte Chunks zu
korrigieren, aktualisieren Sie das Quelldokument und verarbeiten Sie es erneut.

Kein Datenbank-Merging: Datenbanken bleiben systembedingt isoliert. Eine Reorganisation erfordert die Erstellung neuer
Strukturen und die Migration von Dokumenten.
