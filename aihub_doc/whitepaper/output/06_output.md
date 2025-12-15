# Kapitel 06: Datenmanagement, Integration und Ingestion

Die Qualität einer KI-Lösung korreliert direkt mit der Qualität der Daten, auf die sie zugreift. Selbst das
leistungsfähigste Sprachmodell ist nutzlos, wenn es mit veralteten, fragmentierten oder unleserlichen Informationen
gefüttert wird. Während das vorherige Kapitel die Governance behandelte, fokussiert sich dieser Abschnitt auf den
technologischen Maschinenraum: Wie werden unstrukturierte Unternehmensdaten – von der PDF-Rechnung bis zum
SharePoint-Wiki – effizient, sicher und automatisiert in nutzbares Wissen für KI-Agenten transformiert?

Der Swiss AI Hub implementiert hierfür keine einfachen Upload-Skripte, sondern vollständige, industriell gefertigte
Daten-zu-Wissen-Pipelines. Dieser Ansatz garantiert, dass das Unternehmenswissen nicht als statischer Datenfriedhof
endet, sondern als dynamischer, semantisch durchsuchbarer Wissensgraph zur Verfügung steht.

## Auf einen Blick

- **Hierarchische Isolation:** Eine strikte Trennung von Daten in Wissensdatenbanken und Sammlungen verhindert
  Kontext-Vermischung und setzt Zugriffsbeschränkungen technisch durch.
- **Semantisches Verständnis:** Die Pipeline nutzt «Docling» und «Intelligent Chunking», um Layouts, Tabellen und
  Hierarchien in Dokumenten zu verstehen, statt nur rohen Text zu extrahieren.
- **Änderungsgetriebene Automatisierung:** Dank «Observable Assets» werden Pipelines nur bei tatsächlichen
  Datenänderungen angestossen, was Ressourcen spart und Aktualität garantiert.
- **Integrierte Sicherheit:** Jede Datei durchläuft strikte Validierungen (MIME-Type, Path Traversal), bevor sie
  verarbeitet wird, um die Integrität der Plattform zu schützen.
- **Strukturelle Verlinkung:** Dokumententeile werden logisch miteinander verknüpft (sequentiell und hierarchisch), um
  Agenten einen erweiterten Kontext für präzisere Antworten zu liefern.

## Strukturierte Wissensarchitektur und Isolation

### Geschäftlicher Nutzen

Ein häufiges Problem bei frühen RAG-Implementierungen (Retrieval-Augmented Generation) ist die «Kontext-Vermischung».
Wenn ein KI-Agent Zugriff auf alle Dokumente hat, antwortet der HR-Bot auf Fragen zur Lohnbuchhaltung möglicherweise mit
Informationen aus der IT-Budgetplanung. Dies führt zu Verwirrung und Sicherheitsrisiken. Unternehmen benötigen eine
strikte logische Trennung von Datenbeständen, die analog zu ihren Abteilungs- und Projektstrukturen funktioniert. Dies
stellt sicher, dass KI-Antworten präzise im richtigen Kontext verankert sind und Zugriffsrechte («Need-to-know») auch
auf Datenebene technisch durchgesetzt werden.

### Konzeptioneller Ansatz

Die Plattform organisiert Wissen in einer dreistufigen Hierarchie, die Isolation mit Flexibilität verbindet. Auf der
obersten Ebene stehen isolierte Container («Wissensdatenbanken»), die physisch und logisch getrennte Datenräume
darstellen. Innerhalb dieser Container werden Dokumente in thematische Gruppen («Sammlungen») unterteilt. Diese
Architektur ermöglicht ein präzises «Scoping»: Ein Administrator definiert exakt, welche Sammlungen ein spezifisches
Agenten-Profil sehen darf. Die KI sucht also nicht im gesamten Universum der Unternehmensdaten, sondern nur in den für
den Anwendungsfall autorisierten Sektoren.

### Technische Umsetzung im Swiss AI Hub

Die technische Realisierung erfolgt über **Wissensdatenbanken** und **Sammlungen**.

- **Wissensdatenbanken:** Diese fungieren als Top-Level-Container. Jede Datenbank verfügt über eigene Konfigurationen
  und Berechtigungen. Technisch werden diese oft pro Abteilung (z.B. «Legal», «Engineering») angelegt.
- **Sammlungen (Namespaces):** Innerhalb einer Datenbank werden Dokumente in Sammlungen gruppiert. Technisch handelt es
  sich dabei um Metadaten-Tags (Namespaces) in der Vektordatenbank (Milvus). Da diese Struktur flach und nicht
  verschachtelt ist, können Agenten hochperformant über mehrere Sammlungen hinweg suchen, ohne komplexe Ordnerpfade
  traversieren zu müssen.
- **Technische Isolation:** Die Datenhaltung erfolgt strikt getrennt. Vektoren liegen in Milvus, Metadaten in FerretDB
  und die Rohdaten in S3-kompatiblen Objektspeichern (SeaweedFS). Diese Trennung erlaubt eine unabhängige Skalierung der
  Komponenten.

## Von Daten zu Wissen: Die Verarbeitungspipeline

### Geschäftlicher Nutzen

Unstrukturierte Daten sind für Computer oft «tote» Materie. Ein gescanntes PDF, eine PowerPoint-Präsentation mit
komplexen Tabellen oder ein verschachteltes Word-Dokument stellen herkömmliche Suchalgorithmen vor massive Probleme.
Einfaches Text-Extrahieren zerstört oft den Kontext – eine Tabellenzelle ohne ihre Spaltenüberschrift ist wertlos.
Unternehmen benötigen eine Technologie, die das Layout und die Struktur von Dokumenten versteht, um sicherzustellen,
dass die KI nicht nur Wörter liest, sondern den Sinnzusammenhang erfasst. Nur so lassen sich Halluzinationen reduzieren,
die durch aus dem Zusammenhang gerissene Textfragmente entstehen.

### Konzeptioneller Ansatz

Der Swiss AI Hub verwendet eine hochentwickelte **Daten-zu-Wissen-Pipeline**, die weit über einfaches Text-Parsing
hinausgeht. Der Prozess transformiert Rohdokumente in einen semantischen Graphen. Das Konzept basiert auf «Intelligent
Chunking». Anstatt ein Dokument stur nach fester Zeichenanzahl abzuschneiden, analysiert das System die logische
Struktur (Kapitel, Absätze) und teilt den Text an sinngemässen Grenzen. Zusätzlich werden Metadaten (Autor, Datum)
extrahiert und der Inhalt durch Vektorembeddings für die semantische Suche zugänglich gemacht.

### Technische Umsetzung im Swiss AI Hub

Die Pipeline setzt auf einen mehrstufigen Prozess, der durch das SDK bereitgestellt und orchestriert wird:

- **Deep Parsing (Docling):** Die Plattform nutzt «Docling» für die Dokumentenanalyse. Dieses Tool extrahiert nicht nur
  Text, sondern erkennt Tabellenstrukturen, Überschriftenhierarchien und Bildunterschriften in PDFs und Office-Dateien.
  Das Layout wird rekonstruiert, um den Lesefluss beizubehalten.
- **Strukturelle Verlinkung:** Beim Chunking werden nicht nur isolierte Schnipsel erzeugt. Das System erstellt
  **sequentielle Links** (Verbindung zum vorherigen/nächsten Chunk) und **hierarchische Links** (Verbindung zur
  Zusammenfassung des übergeordneten Kapitels). Dies ermöglicht dem Agenten, bei einem Treffer den Kontext zu erweitern
  («Context Window Expansion»).
- **Vektorisierung und Summary Nodes:** Textknoten werden mittels Embedding-Modellen in Vektoren transformiert und in
  Milvus gespeichert. Die Pipeline unterstützt dabei automatisch die Generierung von hierarchischen Zusammenfassungen
  (Summary Nodes) via LLM, um Agenten einen schnellen Überblick über grosse Dokumentenmengen zu geben, bevor sie in
  Details eintauchen.

## Automatisierte Integration und Synchronisation

### Geschäftlicher Nutzen

In vielen Unternehmen scheitern Wissensmanagement-Initiativen daran, dass Dokumente manuell hochgeladen werden müssen.
Sobald die Datei auf der Plattform ist, ist sie oft schon veraltet («Stale Data»). Eine Enterprise-Lösung muss
sicherstellen, dass die Wissensbasis der KI stets synchron mit der «Source of Truth» (z.B. dem Fileserver, SharePoint
oder Intranet) ist. Manuelle Prozesse sind hier fehleranfällig und unwirtschaftlich. Die Anforderung lautet: «Set and
forget». Einmal konfiguriert, muss sich das System selbstständig aktualisieren.

### Konzeptioneller Ansatz

Der Swiss AI Hub verfolgt eine Strategie der **änderungsgetriebenen Automatisierung** (Change-Driven Automation).
Anstatt jede Nacht blind alle Dokumente neu zu verarbeiten (was Rechenleistung verschwendet und Kosten verursacht),
überwacht das System die Quellen intelligent. Nur wenn ein Dokument hinzugefügt, geändert oder gelöscht wurde, wird die
Verarbeitungskette angestossen. Dies garantiert Aktualität bei minimalem Ressourcenverbrauch. Das System unterscheidet
dabei zwischen manuell verwalteten Datenbanken für statische Inhalte und Auto-Sync-Datenbanken für dynamische
Unternehmensablagen.

### Technische Umsetzung im Swiss AI Hub

Die Orchestrierung erfolgt durch **Dagster**, eine spezialisierte Workflow-Engine für Data Engineering.

- **SharePoint-Konnektor:** Eine dedizierte Pipeline-Factory (`default_sharepoint_to_datalake_definitions`)
  synchronisiert Dateien aus SharePoint-Bibliotheken in den internen Data Lake (S3).
- **Beobachtbare Assets:** Die Pipeline nutzt das Konzept der «Observable Assets». Ein leichtgewichtiger Job prüft
  regelmässig die Quelle auf Änderungen anhand von Hashes und Zeitstempeln.
- **Ereignisgesteuerte Verarbeitung:** Sobald eine Änderung erkannt wird, löst ein Sensor (`default_automation_sensor`)
  oder eine `AutomationCondition` die nachgelagerte Verarbeitung (Parsing, Embedding) aus. Dies geschieht partitioniert
  pro Dokument, sodass ein Fehler in einer Datei nicht den gesamten Prozess stoppt.
- **Lebenszyklus-Management:** Bei Löschung eines Dokuments in der Quelle entfernt die Pipeline automatisch alle
  zugehörigen Artefakte (Chunks, Vektoren, Zusammenfassungen) aus der Wissensdatenbank, um zu verhindern, dass die KI
  auf veraltetes Wissen zugreift.

## Validierung und Sicherheit beim Import

### Geschäftlicher Nutzen

Die Funktion, beliebige Dokumente hochzuladen, ist ein potenzielles Einfallstor für Cyberangriffe. Bösartige Akteure
könnten versuchen, über manipulierte Dateien Schadcode einzuschleusen oder Systeme zum Absturz zu bringen. Zudem muss
verhindert werden, dass korrupte oder nicht lesbare Dateien die Qualität der Wissensdatenbank verwässern.
Sicherheitsverantwortliche (CISOs) verlangen daher, dass jede Datei validiert und bereinigt wird, *bevor* sie tiefere
Verarbeitungsschichten der Plattform erreicht.

### Konzeptioneller Ansatz

Sicherheit ist integraler Bestandteil der Ingestion-Pipeline («Secure by Design»). Der Ansatz basiert auf dem Prinzip
«Trust no Input». Jede Datei wird als potenziell feindlich betrachtet, bis sie validiert wurde. Dies umfasst die Prüfung
auf Dateitypen (Whitelisting), die Konsistenzprüfung von Metadaten und den Schutz vor Angriffen auf das Dateisystem.
Fehlerhafte Dateien werden isoliert und protokolliert, ohne den Gesamtprozess zu stoppen (Dokumentenebenen-Isolation).

### Technische Umsetzung im Swiss AI Hub

Die Plattform implementiert rigorose Sicherheitschecks an der Eingangs-Schleuse:

- **MIME-Type Validierung:** Es wird geprüft, ob der tatsächliche Inhalt einer Datei mit ihrer Erweiterung
  übereinstimmt, um «Extension Spoofing» (z.B. eine `.exe` getarnt als `.pdf`) zu verhindern.
- **Strikte Whitelist:** Nur definierte Formate (PDF, DOCX, TXT, MD, JSON etc.) werden akzeptiert. Die Liste umfasst ca.
  40 sichere Enterprise-Formate.
- **Path Traversal Schutz:** Dateinamen werden sanitisiert, um zu verhindern, dass Angreifer durch Sequenzen wie `../`
  auf geschützte Systemverzeichnisse zugreifen.
- **Ressourcen-Limits:** Grössenbeschränkungen und Validierungen verhindern «Denial of Service»-Attacken durch extrem
  grosse oder komplexe Dateien («Zip-Bomben»).
- **Audit-Trail:** Jeder Ingestion-Versuch, ob erfolgreich oder blockiert, wird via Dagster protokolliert, was eine
  vollständige Nachvollziehbarkeit der Datenherkunft und eventueller Sicherheitsvorfälle ermöglicht.
