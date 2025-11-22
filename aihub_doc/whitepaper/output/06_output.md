# Kapitel 06: Datenmanagement, Integration und Ingestion

Die effektive Nutzung von Künstlicher Intelligenz (KI) in Schweizer Unternehmen hängt entscheidend von der Fähigkeit ab,
unternehmensrelevantes Wissen sicher, strukturiert und jederzeit aktuell für KI-gestützte Prozesse bereitzustellen.
Herausforderungen wie fragmentierte Datenlandschaften, der Mangel an automatisierten Integrationslösungen und die
Schwierigkeit, unstrukturierte Daten für die KI nutzbar zu machen, bremsen oft das volle Potenzial innovativer
Anwendungen. Dieses Kapitel beleuchtet, wie der Swiss AI Hub einen ganzheitlichen Ansatz für Datenmanagement,
Integration und Ingestion bietet, um diese Hürden zu überwinden und eine vertrauenswürdige, hochverfügbare Wissensbasis
für Ihre KI-Agenten zu schaffen.

## 1. Strukturierte Wissensarchitektur und kontrolliertes RAG-Scoping

Eine zentrale Herausforderung für Unternehmen ist die organisatorische Strukturierung ihres Wissens für KI-Anwendungen,
um sowohl die Effizienz des Zugriffs als auch die Einhaltung strenger Datenschutz- und Compliance-Anforderungen zu
gewährleisten. Unkontrollierte Datenzugriffe und mangelnde Trennung sensibler Informationen können gravierende
geschäftliche und rechtliche Risiken mit sich bringen.

### Mehrwert und Nutzen: Gezielter Zugriff und maximale Datensicherheit

Für C-Level-Führungskräfte bedeutet eine klare Wissensarchitektur die Gewissheit, dass KI-Systeme ausschliesslich auf
autorisierte Informationen zugreifen und somit Datenschutzrisiken minimiert werden. Dies stärkt das Vertrauen in
KI-gestützte Entscheidungen und unterstützt die Compliance mit Schweizer Datenschutzgesetzen. IT-Professionals
profitieren von einer intuitiven Struktur, die die Verwaltung von Wissensressourcen vereinfacht, die Skalierbarkeit
fördert und eine präzise Steuerung der Informationsflüsse ermöglicht, was die Wartbarkeit und Sicherheit der gesamten
KI-Plattform erheblich verbessert. Das gezielte "Collection-Scoping" gewährleistet, dass sensible Daten nicht
unbeabsichtigt von KI-Agenten verwendet werden, und erhöht somit die Sicherheit und Relevanz der generierten Antworten.

### Konzepte & Prozesse: Hierarchische Gliederung und Agenten-spezifische Wissenspools

Der Swiss AI Hub organisiert Unternehmenswissen in einer hierarchischen Struktur, die auf Governance, Skalierbarkeit und
klare Eigentumsgrenzen ausgelegt ist. Auf der höchsten Ebene können Organisationen mehrere isolierte
**Wissensdatenbanken** erstellen. Jede Datenbank repräsentiert einen eigenen Wissensbereich, eine Abteilung oder eine
spezifische Sicherheitsgrenze und gewährleistet eine vollständige Trennung von Daten, Berechtigungen und
Verarbeitungspipelines. Innerhalb jeder Wissensdatenbank wird das Wissen in **Namespaces** (in der Benutzeroberfläche
als „Sammlungen“ bezeichnet) organisiert. Diese logischen Container gruppieren verwandte Dokumente nach Thema, Projekt
oder Geschäftsfunktion. Wichtig ist hierbei, dass Namespaces als flache Metadatenattribute und nicht als verschachtelte
Ordnerstrukturen implementiert sind.

Ein entscheidendes Konzept ist das **kontrollierte RAG-Scoping** (Retrieval-Augmented Generation). Agenten werden so
konfiguriert, dass sie auf bestimmte Sammlungen zugreifen können. Wenn ein Benutzer mit einem solchen Agenten
interagiert, basieren die generierten Antworten ausschliesslich auf den Informationen aus diesen spezifischen,
vordefinierten Sammlungen. Dies stellt sicher, dass der Agent nur relevante und autorisierte Daten für seine Antworten
verwendet, was die Genauigkeit erhöht und unzulässige Informationsflüsse verhindert.

### Technische Umsetzung im Swiss AI Hub: Isolierte Wissensdatenbanken und Namespace-Filterung

Technisch gesehen ermöglichen Wissensdatenbanken eine vollständige Datenisolation und Trennung von
Verarbeitungs-Pipelines. Namespaces sind als Metadatenattribute an jeden Dokumenten-Chunk im Vektor-Store angehängt.
Diese Metadaten ermöglichen ein präzises Targeting bei Abrufoperationen. Die Zugriffskontrolle erfolgt primär auf
**Agenten-Ebene**: Ist ein Agent für den Zugriff auf spezifische Sammlungen konfiguriert, erhalten alle Benutzer, die
mit diesem Agenten interagieren, Antworten, die auf demselben, exakt definierten Wissensset basieren. Die Plattform
unterstützt zudem die Mehrsprachigkeit auf Ebene der organisatorischen Elemente (Datenbank- und
Namespace-Bezeichnungen), um eine konsistente Benutzererfahrung in Deutsch, Englisch, Französisch und Italienisch zu
gewährleisten. Berechtigungen können auf Datenbank- oder Namespace-Ebene über das RBAC-System (z.B.
`aihub.user.knowledge.hr_documents.policies`) zugewiesen werden.

## 2. Automatisierte Datenintegration und Lebenszyklusmanagement

Die manuelle Pflege und Aktualisierung von Wissensdatenbanken ist fehleranfällig, zeitaufwendig und führt schnell zu
veralteten Informationen, was die Effektivität von KI-Anwendungen mindert. Unternehmen benötigen eine nahtlose und
automatisierte Methode, um ihre unterschiedlichen Informationsquellen kontinuierlich in die KI-Wissensbasis
einzuspeisen.

### Mehrwert und Nutzen: Stets aktuelles Wissen und reduzierte Betriebskosten

Für C-Level-Führungskräfte bedeutet die automatisierte Integration einen erheblichen Wettbewerbsvorteil durch den
Zugriff auf stets aktuelles Unternehmenswissen, was schnellere und fundiertere Entscheidungen ermöglicht. Gleichzeitig
senkt sie die Betriebskosten durch die Eliminierung manueller Prozesse und die effiziente Nutzung von Rechenressourcen,
da die Verarbeitung nur bei tatsächlichen Datenänderungen stattfindet. IT-Abteilungen profitieren von einer
zuverlässigen, wartungsarmen Datenversorgung und standardisierten Schnittstellen, die den administrativen Aufwand
reduzieren und die Datenqualität sicherstellen. Die Plattform wandelt unstrukturierte Rohdaten in ein sofort
verwertbares, "lebendiges" Wissen um.

### Konzepte & Prozesse: Hybride Automatisierungsstrategie und kontinuierliche Synchronisation

Der Swiss AI Hub unterstützt die Dokumentenerfassung auf zwei Arten: über den manuellen Upload durch autorisierte
Benutzer für kontrollierte Workflows und über die automatisierte Synchronisierung. Letztere ist der Eckpfeiler für ein
dynamisches Wissensmanagement und basiert auf einer **hybriden Automatisierungsstrategie**:

1. **Zeitgesteuerte Überwachung**: Ein schlanker Job überprüft nach einem festen Zeitplan (z.B. täglich) die externen
   Datenquellen (z.B. einen S3-Bucket oder SharePoint) auf neue oder geänderte Dateien und protokolliert deren
   Versionen. Dieser Schritt ist ressourcenschonend, da er keine Dokumente verarbeitet.
2. **Änderungsgesteuerte Verarbeitung**: Nur wenn die Überwachung Änderungen feststellt, wird die ressourcenintensive
   Dokumentenverarbeitung durch einen Sensor oder eine `AutomationCondition` ausgelöst.

Diese ereignisgesteuerte Lebenszyklusmanagement stellt sicher, dass Dokumente, sobald sie hinzugefügt, geändert oder
gelöscht werden, automatisch durch die Verarbeitungskette geleitet und die Wissensdatenbank konsistent aktualisiert
wird.

### Technische Umsetzung im Swiss AI Hub: Vorkonfigurierte Konnektoren und Dagster-Orchestrierung

Die Plattform bietet vorkonfigurierte Konnektoren für eine Vielzahl gängiger Unternehmenssysteme. Dazu gehören
Enterprise-Kollaborationsplattformen wie Microsoft SharePoint und OneDrive, Dateisysteme (Netzlaufwerke, lokale
Speicher) sowie Cloud-Speicher wie Azure Blob Storage und S3-kompatible Object-Stores. Über entsprechende Konnektoren
können auch Inhalte von öffentlichen Websites erfasst werden. Die `default_sharepoint_to_datalake_definitions`-Factory
beispielsweise ermöglicht die nahtlose Synchronisation von SharePoint-Dokumenten in einen S3-Data-Lake.

Die zugrunde liegende Orchestrierung erfolgt mit **Dagster**. Hierbei wird ein `observable_source_asset` konfiguriert,
der die Datenquelle überwacht. `AutomationCondition.eager()` an den nachgelagerten Assets stellt sicher, dass die
eigentliche Verarbeitung nur bei erkannten Änderungen ausgeführt wird. Dokumente, die in externen Quellen gelöscht
werden, werden auch aus der Swiss AI Hub Wissensbasis entfernt.

## 3. Intelligente Dokumentenverarbeitung für KI-Bereitschaft

Unstrukturierte Daten – seien es gescannte PDFs, komplex formatierte Berichte oder Bilder – stellen eine grosse Hürde
für die KI-gestützte Analyse dar. Herkömmliche Methoden scheitern oft daran, den Inhalt und Kontext dieser Dokumente für
die semantische Suche nutzbar zu machen.

### Mehrwert und Nutzen: Umfassende Analyse und präzise KI-Antworten

Unternehmen benötigen die Gewissheit, dass alle relevanten Informationen, unabhängig von ihrem Format, für die KI
verfügbar und verständlich sind. Dies maximiert den Nutzen der KI und minimiert das Risiko von "Halluzinationen" durch
unvollständiges Wissen. Für C-Level-Führungskräfte bedeutet dies, dass wertvolle Daten in Geschäftsberichten oder
technischen Handbüchern, die zuvor unzugänglich waren, nun zur Entscheidungsfindung beitragen können. IT-Experten
erhalten eine robuste Engine, die die Komplexität der Datenaufbereitung abstrahiert und eine hohe Qualität der
Eingabedaten für KI-Modelle gewährleistet.

### Konzepte & Prozesse: Hochentwickelte Parsing-, Chunking- und Embedding-Pipeline

Sobald Dokumente erfasst sind, initiiert die Plattform eine hochentwickelte Verarbeitungspipeline, die Rohinhalte in
eine KI-bereite Wissensbasis transformiert. Dazu gehören fünf Verarbeitungsstufen:

1. **Dokumenten-Parsing**: Extraktion von Text, Struktur, Tabellen, Abbildungen und Metadaten aus verschiedenen
   Dateiformaten wie PDFs, Word-, Excel- und PowerPoint-Dokumenten. Dies beinhaltet die Verarbeitung komplexer Layouts,
   mehrspaltiger Seiten und eingebetteter Inhalte, während die logische Struktur erhalten bleibt.
2. **Chunking**: Dokumente werden in semantisch bedeutsame "Chunks" segmentiert, die den Kontext bewahren und
   gleichzeitig die Abrufleistung optimieren. Hierbei wird ein struktureller Parser verwendet, der den Text an
   Überschriften- und Absatzgrenzen aufteilt.
3. **Vektoreinbettung (Vector Embedding)**: Umwandlung der verarbeiteten Text-Chunks in hochdimensionale
   Vektordarstellungen, die eine semantische Suche ermöglichen, die über die reine Stichwortsuche hinausgeht.
4. **Strukturelle Verlinkung**: Es werden sequentielle Links zwischen benachbarten Chunks sowie hierarchische Links zu
   Abschnittszusammenfassungen auf übergeordneten Ebenen erstellt. Dies ermöglicht Agenten, einen vollständigen Kontext
   aufzubauen, indem sie umgebende oder übergeordnete Chunks abrufen.
5. **Zusammenfassungsgenerierung**: Erstellung hierarchischer Zusammenfassungen für Dokumentenabschnitte, um Agenten ein
   breiteres Kontextverständnis bei der Abfrage spezifischer Details zu ermöglichen.

### Technische Umsetzung im Swiss AI Hub: Docling, Vektordatenbanken und Wissensgraphen

Die Dokumentenverarbeitung nutzt **Docling** zur Extraktion von Inhalten aus verschiedenen Dateiformaten,
einschliesslich der Handhabung von gescannten PDFs, die durch Texterkennung zugänglich gemacht werden. Für das
semantische Chunking kommt ein struktureller Parser zum Einsatz. Anschliessend werden diese Chunks mittels KI-Modellen
in Vektoreinbettungen umgewandelt und zusammen mit den ursprünglichen Text-Chunks und Metadaten in einer Vektordatenbank
(z.B. **Milvus**) gespeichert. Dies bildet einen **Wissensgraphen**, der effiziente semantische Suchfunktionen
ermöglicht, indem er nicht nur isolierte Textfragmente, sondern auch deren strukturelle Beziehungen speichert. Die
`default_definitions`-Factory im SDK kapselt diesen mehrstufigen Verarbeitungs-Workflow und integriert ihn nahtlos in
die Gesamtplattform.

## 4. Skalierbare Ingestion-Pipelines und kontinuierliche Qualitätssicherung

Der Umgang mit sehr grossen Dateien und Millionen von Dokumenten stellt enorme Anforderungen an die Skalierbarkeit und
Zuverlässigkeit der Verarbeitungsinfrastruktur. Gleichzeitig ist eine lückenlose Nachvollziehbarkeit der Datenherkunft
für Compliance und Vertrauen in KI-generierte Antworten unerlässlich.

### Mehrwert und Nutzen: Performance, Auditierbarkeit und Vertrauen in KI-Antworten

C-Level-Führungskräfte benötigen die Gewissheit, dass die KI-Infrastruktur mit dem Unternehmenswachstum skaliert und
auch bei riesigen Datenmengen performant bleibt. Eine transparente Datenherkunft ist zudem entscheidend für die
Einhaltung regulatorischer Anforderungen und die Verteidigung von KI-generierten Entscheidungen. IT-Teams profitieren
von einem robusten, fehlertoleranten System, das eine massive Parallelisierung ermöglicht und gleichzeitig eine präzise
Rückverfolgbarkeit bis zur Quelle jeder Information bietet. Fehler in einem Dokument beeinträchtigen nicht die gesamte
Pipeline.

### Konzepte & Prozesse: Dagster-Orchestrierung, partitionsbasierte Verarbeitung und Data Lineage

Die Ingestion-Pipelines des Swiss AI Hub basieren auf **Dagster**, einem Industriestandard für Datenorchestration.
Dieses Framework ermöglicht die Definition von Pipelines als Code, was eine hohe Flexibilität für benutzerdefinierte
Verarbeitungslogik, bedingte Workflows und robuste Fehlerbehandlung bietet. Jedes Dokument wird in seiner eigenen
**Partition** verarbeitet, was eine isolierte und parallele Bearbeitung ermöglicht. Fehler in einem Dokument
beeinträchtigen nicht die gesamte Pipeline. Pipelines sind so konzipiert, dass sie **änderungsgesteuert** agieren:
Beobachtbare Quell-Assets erkennen neue, geänderte oder gelöschte Dateien und lösen die nachgelagerte Verarbeitung nur
bei Bedarf aus, was hocheffizient ist und Rechenressourcen spart.

Die Plattform gewährleistet zudem eine **lückenlose Datenherkunft (Data Lineage)**. Jede Aktion einer Pipeline wird
protokolliert, und für RAG-Antworten wird exakt festgehalten, welche spezifischen Quelldokumente, Dokumentversionen oder
Text-Chunks als Basis dienten.

### Technische Umsetzung im Swiss AI Hub: Dagster UI, OpenTelemetry und Lifecycle-Management

Dagster sorgt für die zuverlässige Planung, Auslösung und Fehlerbehandlung der Pipelines. Die Dagster UI bietet
Monitoring-Funktionen zur visuellen Verfolgung von Asset-Abstammung und -Abhängigkeiten. Asset-Materialisierungen werden
mit Metadaten angereichert (Dateigrösse, Verarbeitungszeit, Dokumentseiten, verwendete Parserversionen), die eine
lückenlose Dokumentation der Verarbeitungsschritte gewährleisten. Die Plattform kann Millionen von Dokumenten verwalten
und auch sehr grosse Einzeldateien effizient verarbeiten, indem sie auf die Parallelisierungsfähigkeiten von Dagster und
die partitionsbasierte Verarbeitung setzt, die durch `DynamicPartitionsDefinition` und `AutomationCondition.eager()`
realisiert wird. Ingestion-Durchläufe erfolgen änderungsgesteuert oder nach Zeitplan (z.B. nächtlich), wobei die
ressourcenintensive Verarbeitung nur bei tatsächlichen Datenänderungen ausgelöst wird. Die Quellenzuordnung wird durch
Metadaten im Vektor-Store sichergestellt. Jeder abgerufene Chunk verweist auf sein Quelldokument, was transparente
Zitierung und Überprüfung von KI-Antworten ermöglicht. Das Dokumenten-Lebenszyklusmanagement in der Pipeline
(Hinzufügen, Ändern, Löschen) sorgt dafür, dass veraltete Informationen konsistent entfernt werden, was auch die
Versionsverfolgung für regulatorische Dokumente unterstützt.

## 5. Sicherstellung der Datenintegrität und -sicherheit während der Aufnahme

Die Integrität der Wissensbasis ist von höchster Bedeutung. Das Einschleusen bösartiger oder fehlerhafter Dateien kann
die Sicherheit der gesamten KI-Infrastruktur gefährden und zu unzuverlässigen oder schädlichen KI-Antworten führen. Ein
robuster Schutzmechanismus am Daten-Ingress ist daher unerlässlich.

### Mehrwert und Nutzen: Minimierung von Sicherheitsrisiken und verlässliche Datenbasis

Für Unternehmen ist es entscheidend, die Wissensbasis vor externen Bedrohungen und internen Fehlern zu schützen. Dies
minimiert das Risiko von Datenlecks, Systemkompromittierungen und gewährleistet eine vertrauenswürdige Grundlage für
KI-Anwendungen. C-Level-Führungskräfte sichern damit die Compliance und den Schutz sensibler Unternehmensdaten.
IT-Sicherheitsteams profitieren von integrierten Validierungs- und Sicherheitsmechanismen, die die Angriffsfläche
reduzieren und die Datenintegrität während des gesamten Aufnahmeprozesses gewährleisten.

### Konzepte & Prozesse: Umfassende Eingabevalidierung und integrierte Sicherheitsprüfungen

Der Swiss AI Hub implementiert eine mehrstufige Eingabevalidierung, um die Wissensbasis vor gängigen Angriffsvektoren zu
schützen. Dies umfasst eine strikte Dateityp-Whitelist, die nur genehmigte Dateiformate zulässt, und eine
MIME-Typ-Validierung, um Verschleierungstaktiken zu verhindern. Dateinamen werden auf Path Traversal-Versuche,
Erweiterungs-Spoofing und Null-Bytes geprüft. Dateigrössenbeschränkungen verhindern zudem Ressourcenerschöpfung. Diese
Massnahmen stellen sicher, dass nur sichere und erwartungsgemässe Inhalte in das System gelangen. Pipelines können zudem
um Schritte für ein Security Scanning erweitert werden, um auf bösartige Inhalte oder Richtlinienverstösse zu prüfen,
bevor Dokumente verarbeitet werden.

### Technische Umsetzung im Swiss AI Hub: Strikte Validierungsregeln und Schutz vor Bedrohungen

Die Plattform beschränkt Dateiuploads auf etwa 40 genehmigte Dateierweiterungen, darunter gängige Dokument-, Bild-,
Audio- und strukturierte Datenformate. Die Validierung des MIME-Typs stellt sicher, dass der bereitgestellte Content-Typ
dem erwarteten MIME-Typ entspricht. Dateinamen müssen alphanumerisch beginnen und werden auf bösartige Muster wie `..`,
`/`, `\` oder Null-Bytes überprüft. Maximale Dateigrössenbeschränkungen werden auf Anwendungs- oder Reverse-Proxy-Ebene
durchgesetzt, um grosse, potenziell schädliche Dateien abzuwehren. Diese Schutzmassnahmen verhindern Path
Traversal-Angriffe, MIME-Typ-Verwechslung, Erweiterungs-Spoofing und das Hochladen ausführbarer Dateien. Die
Quelldokumentation beschreibt "Security Scanning" als eine optionale, in Pipelines integrierbare Qualitäts- und
Sicherheitskontrolle, nicht als eine standardmässig aktivierte Malware-Scan-Funktion der Basissystem-Ingestion.

Diese robusten Validierungsmechanismen tragen wesentlich zum Schutz vor Kompromittierungen und zur Sicherstellung der
Datenintegrität bei.
