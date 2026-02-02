# Kapitel 10: Deployment, Betrieb

Der Übergang von einem funktionierenden Prototypen zu einer stabilen Enterprise-Lösung markiert oft die kritischste
Phase in KI-Projekten. Während in der Entwicklungsphase Agilität und Schnelligkeit dominieren, erfordert der produktive
Betrieb («Day 2 Operations») Stabilität, Skalierbarkeit und die nahtlose Integration in bestehende IT-Landschaften. CIOs
und IT-Leiter stehen vor der Herausforderung, eine KI-Infrastruktur bereitzustellen, die nicht nur heute funktioniert,
sondern auch unter Last skaliert, Ausfälle toleriert und strengen Sicherheitsvorgaben genügt.

Dieses Kapitel beleuchtet die betrieblichen Aspekte des Swiss AI Hub. Es zeigt auf, wie die Architektur flexible
Bereitstellungsmodelle unterstützt – von der eigenen Private Cloud über Managed Services bis zum isolierten
Hochsicherheitsrechenzentrum – und wie moderne Container-Technologien einen wartungsarmen, hochverfügbaren 24/7-Betrieb
gewährleisten. Der Swiss AI Hub wird dabei nicht als blosses Framework, sondern als «Infrastruktur als Produkt»
bereitgestellt, das bereits gelöste Lösungen für Authentifizierung, Kostenkontrolle und Monitoring mitliefert.

## Auf einen Blick

- **Infrastruktur-Agnostik:** Volle Flexibilität zwischen On-Premise, Private Cloud (BYOC) oder Schweizer SaaS-Hosting,
  ohne Anpassung der Applikationslogik.
- **Harte Isolation:** Unterstützung für Multi-Instancing-Szenarien («Shared Nothing»), um maximale Datentrennung
  zwischen Organisationseinheiten technisch zu garantieren.
- **Air-Gap-Fähigkeit:** Vollständiger Offline-Betrieb ohne Internetverbindung durch lokale Inferenz-Server (vLLM,
  llama.cpp), um höchste Souveränitätsansprüche zu erfüllen.
- **Skalierung durch Design:** Ereignisgesteuerte Architektur (Event-Driven) via NATS ermöglicht die horizontale
  Skalierung von Workern für hohe Lastspitzen.
- **Vollständige Observability:** Native Integration von OpenTelemetry, SigNoz und Phoenix für ein lückenloses
  Monitoring von Infrastruktur, Kosten und KI-Performance.

## Flexible Betriebsmodelle und Datensouveränität

### Geschäftlicher Nutzen

Es gibt im Schweizer Markt keine «One-Size-Fits-All»-Lösung für das Hosting. Eine Kantonalbank unterliegt anderen
regulatorischen Zwängen als ein Industrieunternehmen oder eine Bundesbehörde. Die Entscheidung über den Speicherort der
Daten und den Betrieb der Infrastruktur muss allein beim Kunden liegen und darf nicht durch die Architektur der Software
diktiert werden. Die Fähigkeit, die Plattform exakt dort zu betreiben, wo die Datenhoheit am besten gewahrt wird – sei
es im eigenen Rechenzentrum oder in einer zertifizierten Schweizer Cloud – eliminiert Compliance-Risiken und ermöglicht
den Einsatz von KI auch in Szenarien, die bisher aufgrund von Cloud-Verboten undenkbar waren.

### Konzeptioneller Ansatz

Der Swiss AI Hub folgt dem Prinzip «Bring Your Own Infrastructure». Die Plattform ist als infrastruktur-agnostische
Lösung konzipiert, die als vollständiger Stack («Batteries-included») bereitgestellt wird. Das Spektrum der
unterstützten Betriebsmodelle umfasst drei Hauptszenarien: On-Premise (Betrieb auf eigener Hardware), Private Cloud
(Betrieb im eigenen Tenant bei Azure, AWS oder GCP) sowie SaaS via Schweizer Cloud-Hosting, bei dem die Datenresidenz in
der Schweiz rechtlich und physisch garantiert bleibt. Ein zentrales Konzept ist zudem das Multi-Instancing, welches eine
physische Trennung zwischen hochsensiblen Organisationseinheiten erlaubt, um Datenlecks technisch auszuschliessen.

### Technische Umsetzung im Swiss AI Hub

Technisch basiert die Bereitstellung auf Containerisierung mittels Docker. Die gesamte Plattform lässt sich mit einem
einzigen Orchestrierungs-Befehl (`docker compose up`) in etwa 30 Minuten bereitstellen.

- **Infrastruktur-Komponenten:** Das Deployment umfasst den gesamten Stack inklusive API (FastAPI), Vektorspeicherung
  (Milvus), Objektspeicher (SeaweedFS S3), Nachrichtenwarteschlange (NATS) und Datenbanken (PostgreSQL, FerretDB).
- **Ressourcen-Anforderungen:** Für einen stabilen Betrieb werden mindestens 8 CPU-Kerne und 32 GB RAM empfohlen, wobei
  SSD-Speicher für die Datenbankperformance essenziell ist.
- **Isolation:** Über spezifische Konfigurationsprofile passt sich das System an. Während im lokalen Deployment
  selbstsignierte Zertifikate (via mkcert) genutzt werden, verwaltet das System in der Produktion automatisch Let's
  Encrypt SSL-Zertifikate für bis zu sieben Subdomains (z. B. aihub, dagster, datalake).
- **Air-Gap-Support:** Da die Plattform lokale Modelle via vLLM oder Hugging Face TEI unterstützt, ist keine ausgehende
  Verbindung zu externen APIs notwendig.

## Sicherheitsarchitektur und Netzwerk-Isolation

### Geschäftlicher Nutzen

Die Sicherheit einer KI-Plattform darf nicht erst an der Applikationsgrenze beginnen. In einer Enterprise-Umgebung ist
es entscheidend, dass der Schadensradius bei einer potenziellen Kompromittierung einzelner Komponenten minimal bleibt.
IT-Verantwortliche benötigen die Sicherheit, dass Datenbanken und interne Logik-Bausteine niemals direkt aus dem
Internet erreichbar sind. Eine tiefgreifende Segmentierung der Infrastruktur schützt nicht nur vor externen Angriffen,
sondern verhindert auch unbefugte Datenflüsse innerhalb der Plattform, was die Einhaltung strengster Sicherheitsaudits
ermöglicht.

### Konzeptioneller Ansatz

Der Swiss AI Hub implementiert das Prinzip der «Defense-in-Depth» durch eine strikte Zonen-Einteilung auf Netzwerkebene.
Anstatt alle Container in einem flachen Netzwerk zu betreiben, werden Dienste in funktionale Gruppen unterteilt.
Kommunikation zwischen diesen Zonen ist nur über definierte Schnittstellen möglich. Ein zentrales Gateway (Reverse
Proxy) agiert als einziger «Entry Point» und übernimmt die Verschlüsselung sowie die Authentifizierung, bevor eine
Anfrage die internen Dienste erreicht.

### Technische Umsetzung im Swiss AI Hub

Die Plattform erzwingt eine Segmentierung in fünf isolierte Docker-Netzwerke:

- **Proxy-Netzwerk:** Beinhaltet Traefik als API-Gateway und nimmt externen Traffic auf Port 443 entgegen.
- **Backend-Netzwerk:** Isoliert Verarbeitungsdienste wie die API, KI-Agenten und die Dokumentenverarbeitung (Docling).
- **Data-Netzwerk:** Reserviert für persistente Datenspeicher (PostgreSQL, Milvus, Valkey) und den Message-Broker
  (NATS).
- **Storage-Netzwerk:** Dediziert für den verteilten Objektspeicher SeaweedFS.
- **Egress-Netzwerk:** Ein spezieller Bereich für Dienste, die Internetzugang benötigen (z. B. Web-Scraper), wobei die
  Inter-Container-Kommunikation (ICC) deaktiviert ist, um seitliche Bewegungen von Angreifern zu verhindern. Alle
  Container laufen als Nicht-Root-Benutzer (UID 1000), was die Systemsicherheit zusätzlich härtet.

## Skalierbarkeit und operative Resilienz

### Geschäftlicher Nutzen

KI-Systeme unterliegen oft stark schwankenden Lastprofilen. Ein Monatsabschluss oder eine neue Daten-Ingestion können
die Anfragen an das System kurzfristig vervielfachen. Eine starre Infrastruktur würde hier entweder zu teuren
Überkapazitäten im Leerlauf oder zu Systemabstürzen unter Last führen. Unternehmen benötigen eine Architektur, die
dynamisch mit den Anforderungen mitwächst, um Service-Level-Agreements (SLAs) stabil zu halten, ohne dass die
Betriebskosten unkontrolliert steigen.

### Konzeptioneller Ansatz

Die Skalierungsstrategie basiert auf einer ereignisgesteuerten Architektur (Event-Driven Architecture) und der
Zustandslosigkeit der Komponenten. Durch die Entkopplung von Anfrage und Verarbeitung über eine Nachrichtenwarteschlange
können rechenintensive Aufgaben asynchron abgearbeitet werden. Da die Agenten-Logik keinen lokalen Zustand hält, kann
jede Aufgabe von jedem verfügbaren Worker übernommen werden. Dies ermöglicht eine horizontale Skalierung: Bei steigender
Last werden einfach zusätzliche Instanzen der benötigten Dienste gestartet.

### Technische Umsetzung im Swiss AI Hub

Das zentrale Nervensystem für die Skalierung ist **NATS JetStream**.

- **Zustandslose Worker:** Dienste für die Dokumentenverarbeitung (Pipelines) oder die Agenten-Ausführung können
  mehrfach instanziiert werden. NATS verteilt die anfallenden Events automatisch auf die verfügbaren Instanzen (Load
  Balancing).
- **Asynchrone Ingestion:** Zeitintensive Prozesse wie das Parsing grosser Dokumentmengen via Docling blockieren nicht
  die Benutzeroberfläche. Die API nimmt Dokumente entgegen und übergibt sie an die Dagster-basierte
  Pipeline-Infrastruktur.
- **Optimierte Ressourcennutzung:** Inferenz-Server für lokale Modelle können auf GPU-Knoten ausgelagert werden, während
  die Verwaltungslogik auf kostengünstigen CPU-Knoten operiert. Dies erlaubt eine präzise Steuerung der
  Hardware-Investitionen.

## Hochverfügbarkeit und Disaster Recovery

### Geschäftlicher Nutzen

Für geschäftskritische Anwendungen ist Ausfallsicherheit keine Option, sondern Pflicht. Der Ausfall einer einzelnen
Komponente darf nicht zum Stillstand ganzer Geschäftsprozesse führen. IT-Verantwortliche benötigen Garantien für kurze
Wiederherstellungszeiten (RTO) und minimale Datenverluste (RPO). Ein robustes System muss Fehler auf Infrastrukturebene
tolerieren und sich selbst heilen können, um einen unterbrechungsfreien Betrieb zu gewährleisten.

### Konzeptioneller Ansatz

Der Ansatz zur Ausfallsicherheit beruht auf Redundanz und granularen Sicherungsverfahren. Die Plattform ist so
konzipiert, dass kritische Dienste im Cluster-Betrieb laufen können. Die Backup-Strategie verfolgt einen zweigleisigen
Weg: Vollständige System-Snapshots für eine schnelle Gesamtwiederherstellung und komponentenspezifische Backups für
maximale Flexibilität. Dies erlaubt es, im Notfall gezielt einzelne Datenbanken oder Vektorsammlungen
wiederherzustellen, ohne das Gesamtsystem zurücksetzen zu müssen.

### Technische Umsetzung im Swiss AI Hub

Die Plattform nutzt bewährte Mechanismen zur Sicherung der Geschäftskontinuität:

- **Granulare Backups:** Unterstützung für `pg_basebackup` und WAL-Archivierung (Write-Ahead Logging) für PostgreSQL
  sowie etcd-Snapshots für die Metadaten von SeaweedFS und Milvus.
- **Vektordaten-Sicherung:** Milvus-Kollektionen können direkt in den S3-Speicher exportiert werden.
- **Self-Healing:** Docker Health Checks überwachen kontinuierlich die Endpunkte (`/health`). Reagiert ein Dienst nicht
  mehr, wird der Container automatisch neu gestartet.
- **Daten-Persistenz:** Kritische Daten liegen auf verschlüsselten Docker-Volumes (LUKS), die vom Lebenszyklus der
  Container unabhängig sind.

## Updates und technologische Unabhängigkeit

### Geschäftlicher Nutzen

Die Innovationszyklen in der KI sind extrem kurz. Unternehmen müssen in der Lage sein, neue Funktionen,
Sicherheits-Patches und verbesserte Modelle schnell zu adaptieren, ohne den laufenden Betrieb zu stören. Gleichzeitig
ist die Abhängigkeit von einem einzelnen Modell-Anbieter (Vendor Lock-in) ein strategisches Risiko. Eine moderne
Plattform muss es ermöglichen, Modelle wie Bausteine auszutauschen oder redundant auszulegen, um die Verhandlungsmacht
zu behalten und die Geschäftskontinuität zu sichern.

### Konzeptioneller Ansatz

Der Swiss AI Hub trennt architektonisch strikt zwischen der stabilen Kernplattform (Core) und dem flexiblen Kundencode
(Agents/Pipelines). Beide Bereiche verfügen über unabhängige Lebenszyklen und Versionierungen. Das integrierte
LLM-Gateway (LiteLLM) fungiert als Abstraktionsschicht: Ein Agent kommuniziert nie direkt mit einem spezifischen Modell
eines US-Anbieters, sondern mit einer universellen Schnittstelle. Dies erlaubt automatisierte Failover-Szenarien und den
nahtlosen Wechsel zwischen Cloud-Modellen und lokalen Instanzen.

### Technische Umsetzung im Swiss AI Hub

Das Update-Management nutzt semantische Versionierung und Container-Tags (`latest`, `nightly`, `vX.Y.Z`).

- **Modell-Agnostik:** LiteLLM bietet eine OpenAI-kompatible API für über 100 Anbieter. Ein Modellwechsel erfordert
  lediglich eine Konfigurationsänderung in der YAML-Datei, kein Umschreiben des Agenten-Codes.
- **Kostenkontrolle:** Das Gateway trackt den Token-Verbrauch in Echtzeit. Administratoren können via Umgebungsvariablen
  wie `LITE_LLM_PROXY_USER_MAX_BUDGET` harte Budgets und Ratenlimits pro Benutzer oder Team erzwingen.
- **Geringe Downtime:** Durch die Nutzung von Container-Orchestrierung können neue Versionen parallel zu alten gestartet
  werden (Rolling Updates), wobei der Verkehr erst umgeleitet wird, wenn die neue Instanz als bereit gemeldet wird.

## Operative Transparenz und Monitoring

### Geschäftlicher Nutzen

In einer komplexen KI-Infrastruktur ist operative Blindheit fatal. Performance-Engpässe, schleichende Kostenanstiege
oder Modell-Fehler müssen erkannt werden, bevor sie die Benutzererfahrung beeinträchtigen. Ein integriertes Monitoring
reduziert die Zeit bis zur Fehlerbehebung (MTTR) drastisch und liefert die Datenbasis für Kapazitätsplanung und interne
Leistungsverrechnung (Chargeback). Transparenz schafft zudem Vertrauen bei den Stakeholdern, da der Nutzen und die
Kosten der KI objektiv messbar werden.

### Konzeptioneller Ansatz

Die Observability-Strategie basiert auf den drei Säulen: Health Checks, Metriken und Logs. Anstatt proprietäre Tools zu
erzwingen, setzt der Swiss AI Hub auf offene Standards wie **OpenTelemetry (OTel)**. Dies ermöglicht eine nahtlose
Integration in bestehende Enterprise-Monitoring-Lösungen (wie Datadog, Splunk oder Dynatrace), liefert aber
standardmässig einen vollständigen, vorkonfigurierten Analyse-Stack mit. Ein zentraler OTel-Collector dient dabei als
Hub, der Daten sammelt, filtert und an die entsprechenden Visualisierungswerkzeuge verteilt.

### Technische Umsetzung im Swiss AI Hub

Die Plattform bietet spezialisierte Ansichten für verschiedene operative Rollen:

- **SigNoz:** Dient als zentrales Dashboard für Infrastruktur-Metriken (CPU, RAM, Netzwerk) und aggregierte Logs. Hier
  werden auch Alarme bei Dienstausfällen oder Performance-Einbrüchen konfiguriert.
- **Phoenix:** Ermöglicht tiefes KI-Tracing. Es visualisiert den Token-Verbrauch, die Latenzen pro Modellaufruf und den
  vollständigen Kontext von RAG-Abfragen (Retrieval-Augmented Generation).
- **Integrierte Dashboards:** Traefik liefert Einblicke in das Request-Routing und den TLS-Status, während Dagster die
  Gesundheit und Historie aller Daten-Pipelines überwacht.
- **Audit-Trails:** Sämtliche Authentifizierungsereignisse und API-Aufrufe werden strukturiert erfasst, was die
  Einhaltung regulatorischer Anforderungen (revDSG) ohne Zusatzaufwand unterstützt.
