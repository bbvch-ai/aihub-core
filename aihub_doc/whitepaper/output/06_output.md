# Kapitel 06: Datenmanagement, Integration und Ingestion

## Vom Dokumenten-Silo zum aktiven Unternehmenswissen

Die Leistungsfähigkeit einer generativen KI-Lösung korreliert direkt mit der Qualität, Aktualität und Struktur der
Daten, auf die sie zugreifen kann. In vielen Schweizer Unternehmen liegt wertvolles Wissen jedoch fragmentiert vor:
versteckt in PDF-Handbüchern auf Netzlaufwerken, verteilt in SharePoint-Bibliotheken oder isoliert in
E-Mail-Postfächern. Die Herausforderung für IT-Entscheider besteht nicht nur darin, diese Daten technisch zugänglich zu
machen, sondern sie so aufzubereiten, dass Sprachmodelle sie semantisch korrekt interpretieren können, ohne dabei
Sicherheitsgrenzen zu verletzen.

Der Swiss AI Hub begegnet dieser Herausforderung mit einer hochentwickelten Ingestion-Engine. Diese Komponente
transformiert passive Dokumentenablagen in eine aktive, abfragbare Wissensarchitektur. Dabei verlässt sich die Plattform
nicht auf simple Text-Extraktion, sondern implementiert intelligente Pipelines, die Layouts verstehen, hierarchische
Zusammenfassungen generieren und Daten kontinuierlich synchronisieren.

## Strukturierte Wissensarchitektur und Isolation

### Logische Trennung für maximale Sicherheit

Ein zentrales Risiko bei der Einführung von RAG-Systemen (Retrieval-Augmented Generation) ist die ungewollte Vermischung
von Kontexten. Ein Engineering-Bot sollte keine HR-Lohndaten indizieren, und ein öffentlicher Kunden-Bot darf keinen
Zugriff auf interne Strategiepapiere haben. Um dies zu verhindern, organisiert der Swiss AI Hub Unternehmensdaten in
einer strikten Hierarchie, die als unveränderliches Fundament für die Zugriffssteuerung dient.

Auf der obersten Ebene operieren **Wissensdatenbanken**. Diese fungieren als isolierte Container, typischerweise
getrennt nach Mandanten, Abteilungen oder hohen Sicherheitsklassifizierungen. Technisch sind diese Datenbanken
vollständig voneinander entkoppelt; sie besitzen eigene Berechtigungssets und separate Verarbeitungspipelines. Eine
Vermischung von Daten zwischen einer «HR-Datenbank» und einer «Engineering-Datenbank» ist architektonisch
ausgeschlossen. Das System nutzt hierfür eine konsistente Abbildung: Ein S3-Bucket im Backend (SeaweedFS) entspricht
einer Datenbank, was eine starke physische Datenisolation gewährleistet. Zudem unterstützt die Plattform explizit die
Mehrsprachigkeit (DE, EN, FR, IT) bei der Benennung dieser Strukturen, um den Anforderungen mehrsprachiger Schweizer
Organisationen gerecht zu werden.

Innerhalb dieser Datenbanken erfolgt die feinere Gliederung über **Sammlungen** (technisch: Namespaces). Diese
Sammlungen gruppieren thematisch zusammengehörige Dokumente, wie etwa «Produkthandbücher» oder «Vertragsentwürfe».
Technisch handelt es sich hierbei um flache Metadaten-Attribute, die direkt an jeden Dokumenten-Chunk im Vektor-Store
angeheftet werden. Dies erlaubt ein präzises **Collection-Scoping**: Administratoren konfigurieren KI-Agenten so, dass
sie exklusiv auf definierte Sammlungen zugreifen dürfen. Ein Support-Agent sieht somit nur Dokumente in der Sammlung
«Support-Richtlinien», selbst wenn in derselben Datenbank noch andere, für ihn gesperrte Sammlungen existieren.

Wichtig für die Governance ist die strikte Trennung der Modi: Eine Wissensdatenbank wird entweder manuell verwaltet
(Upload via UI) oder automatisch synchronisiert (Auto-Sync via Pipeline). Ein Mischbetrieb ist ausgeschlossen, um
Mehrdeutigkeiten bezüglich der «Source of Truth» zu verhindern.

## Automatisierte Pipelines und Integration

### Effizienz durch hybride Automatisierungsstrategie

In der Praxis scheitern viele Wissensmanagement-Projekte an der Veraltung der Daten oder explodierenden
Infrastrukturkosten durch ineffiziente Synchronisation. Der Swiss AI Hub setzt daher auf eine **hybride
Automatisierungsstrategie**, die externe Systeme (wie SharePoint oder Dateisysteme) zur Quelle der Wahrheit erklärt, die
Verarbeitung jedoch ressourcenschonend steuert.

Anstatt riesige Datenmengen jede Nacht blind neu zu verarbeiten, trennt die Plattform die Überwachung von der
Verarbeitung:

1. **Zeitgesteuerte Überwachung (Der Puls):** Ein leichtgewichtiger Job prüft periodisch die Quellsysteme. Er vergleicht
   lediglich Metadaten wie Zeitstempel und Inhalts-Hashes, um Änderungen zu erkennen.
2. **Ereignisgesteuerte Verarbeitung (Der Sensor):** Nur wenn dieser Job eine tatsächliche Änderung (Delta) registriert,
   löst ein Sensor die rechenintensiven Pipelines für Parsing und Embedding aus.

Dies erfolgt über das Muster der **Observable Assets**. Diese überwachen externe Quellen kontinuierlich. Sobald eine
Datei hinzugefügt oder modifiziert wird, startet die Verarbeitung exakt für dieses Dokument. Ändert sich ein
Quelldokument, entfernt die Pipeline automatisch alle veralteten Chunks, bevor die neue Version verarbeitet wird. Wird
ein Dokument gelöscht (z.B. in SharePoint), bereinigt das System restlos alle zugehörigen Vektoren und Metadaten, um
sicherzustellen, dass Agenten niemals auf veraltete Informationen zugreifen.

### Zweistufige Architektur mit Data Lake

Für maximale Robustheit im Enterprise-Umfeld implementiert das System standardmässig einen zweistufigen Prozess, der
über SDK-Factories (`default_sharepoint_to_datalake_definitions` und `default_definitions`) bereitgestellt wird.

In der ersten Phase synchronisiert ein Konnektor Dateien aus der Quelle in einen internen, zentralen S3-Data-Lake. In
der zweiten Phase überwacht die RAG-Pipeline diesen Data Lake und verarbeitet neue Dateien in durchsuchbare Vektoren.
Diese Entkopplung sorgt für Stabilität: Ein Ausfall der externen Quelle oder Netzwerkprobleme beeinträchtigen nicht die
Suchfähigkeit der bestehenden Daten. Die Steuerung dieser komplexen Datenflüsse übernimmt **Dagster** als
Orchestrierungs-Layer, der Planung, Retries und lückenlose Protokollierung zentral verwaltet.

## Intelligente Dokumentenverarbeitung

### Jenseits von reinem Text: Parsing, Linking und Summaries

Für eine KI ist ein PDF zunächst nur eine Ansammlung von Zeichen ohne Bedeutung. Die Qualität der Antwort hängt
massgeblich davon ab, wie gut das System die Struktur des Dokuments versteht. Der Swiss AI Hub nutzt eine mehrstufige
Daten-zu-Wissen-Pipeline, um aus unstrukturierten Dateien einen navigierbaren Wissensgraphen zu erstellen:

1. **Parsing mit Docling:** Die Technologie **Docling** analysiert das visuelle Layout und die logische Struktur.
   Überschriften, Listen, Tabellen und Abbildungen werden erkannt und in ihrem Kontext bewahrt, statt als reiner
   Textbrei extrahiert zu werden.
2. **Strukturelles Chunking:** Ein intelligenter Parser zerlegt Dokumente an logischen Grenzen (wie Kapitelenden oder
   Absatzumbrüchen) statt starr nach Zeichenanzahl. Dies bewahrt den Sinnzusammenhang innerhalb eines Textblocks.
3. **Strukturelle Verlinkung (Structural Linking):** Das System erstellt nicht nur isolierte Vektoren, sondern verknüpft
   diese aktiv. **Sequentielle Links** verbinden einen Chunk mit seinem Vorgänger und Nachfolger, um den Lesefluss
   abzubilden. **Hierarchische Links** verbinden Details mit der übergeordneten Kapitel-Zusammenfassung.
4. **Generierung von Summary Nodes:** Zusätzlich werden automatisch hierarchische Zusammenfassungen für
   Dokumentabschnitte erstellt. Dies hilft der KI, das «grosse Ganze» eines Abschnitts zu verstehen, bevor sie in
   spezifische Details eintaucht.

Diese tiefe semantische Strukturierung ermöglicht fortschrittliche RAG-Techniken. Wenn ein Agent einen relevanten
Textabschnitt findet, kann er über die Verlinkungen navigieren, um den vollständigen Kontext zu rekonstruieren, was die
Präzision der Antworten drastisch erhöht.

### Technische Umsetzung der Persistenz

Die Plattform realisiert diese Architektur durch spezialisierte Komponenten, die jeweils für ihre Aufgabe optimiert
sind: **SeaweedFS** dient als S3-kompatibler Objektspeicher für Rohdaten, **FerretDB** hält Metadaten und
Verarbeitungsstatus, während **Milvus** als Vektordatenbank die semantischen Embeddings speichert. Durch spezialisierte
**I/O Manager** innerhalb der Pipeline wird die Speicherlogik abstrahiert, was die Wartbarkeit und Erweiterbarkeit der
Architektur sichert.

## Integrität, Sicherheit und Nachvollziehbarkeit

### Validierung und Schutz der Datenbasis

Die Ingestion-Pipeline fungiert als erstes Bollwerk gegen korrupte oder schädliche Daten. Bevor Inhalte verarbeitet
werden, durchlaufen sie eine strenge **Eingabevalidierung**. Die Plattform erzwingt eine Whitelist von ca. 40
genehmigten Dateierweiterungen (PDF, Office, Markdown, Bilder, Audio, JSON/XML) und verifiziert, dass der tatsächliche
MIME-Typ mit der Endung übereinstimmt, um «Extension Spoofing» zu verhindern. Zudem werden Dateinamen auf
Path-Traversal-Angriffe geprüft und bereinigt.

Die Verarbeitung selbst erfolgt isoliert mittels **Partitionierung**. Jedes Dokument wird in einer eigenen Partition
verarbeitet. Ein Fehler in einer einzelnen Datei – beispielsweise ein korruptes PDF – führt lediglich zum Abbruch dieser
spezifischen Partition («Skipping»), ohne den Gesamtprozess für Tausende anderer Dokumente zu stoppen. Dies ermöglicht
zudem eine massive Parallelisierung der Verarbeitung durch Dagster.

### Transparenz durch Data Lineage

Für Compliance und Vertrauen ist es unerlässlich zu wissen, woher eine Information stammt. Der Swiss AI Hub generiert
bereits während der Aufnahme eine lückenlose **Data Lineage**. Metadaten wie Erstellungsdatum, Autor, Quellsystem,
Versionsnummer und der exakte Speicherort werden extrahiert und untrennbar mit den Vektordaten verknüpft.

Wenn ein RAG-Agent später eine Antwort generiert, greift er auf diese Metadaten zurück, um präzise Quellenangaben zu
liefern. Dies ermöglicht nicht nur die Überprüfung der Fakten durch den Nutzer, sondern stellt auch sicher, dass Agenten
Informationen korrekt zitieren können. Dank der Integration in Dagster ist zudem jeder Verarbeitungsschritt auditierbar:
Administratoren können exakt nachvollziehen, wann welches Dokument importiert, geparst und indexiert wurde.
