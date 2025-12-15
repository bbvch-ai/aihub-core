# Kapitel 10: Deployment, Betrieb

Der Übergang von einem funktionierenden Prototypen zu einer stabilen Enterprise-Lösung markiert oft die kritischste
Phase in KI-Projekten. Während in der Entwicklungsphase Agilität und Schnelligkeit dominieren, erfordert der produktive
Betrieb («Day 2 Operations») Stabilität, Skalierbarkeit und die nahtlose Integration in bestehende IT-Landschaften. CIOs
und IT-Leiter stehen vor der Herausforderung, eine KI-Infrastruktur bereitzustellen, die nicht nur heute funktioniert,
sondern auch unter Last skaliert, Ausfälle toleriert und strengen Sicherheitsvorgaben genügt.

Dieses Kapitel beleuchtet die betrieblichen Aspekte des Swiss AI Hub. Es zeigt auf, wie die Architektur flexible
Bereitstellungsmodelle unterstützt – von der eigenen Private Cloud über Managed Services bis zum isolierten
Hochsicherheitsrechenzentrum – und wie moderne Container-Technologien einen wartungsarmen, hochverfügbaren 24/7-Betrieb
gewährleisten.

## Auf einen Blick

- **Infrastruktur-Agnostik:** Volle Flexibilität zwischen On-Premise, Private Cloud (BYOC) oder Schweizer SaaS-Hosting,
  ohne Anpassung der Applikationslogik.
- **Air-Gap-Fähigkeit:** Unterstützung für komplett isolierte Offline-Umgebungen ohne ausgehende Internetverbindung
  durch lokale LLM-Inferenz.
- **Skalierung durch Design:** Ereignisgesteuerte Architektur (Event-Driven) ermöglicht horizontale Skalierung von
  Workern für hohe Lastspitzen.
- **Zero-Downtime-Updates:** Trennung von Kernplattform und Kundencode erlaubt Updates ohne Unterbruch des laufenden
  Betriebs.
- **Vollständige Observability:** Native Integration von OpenTelemetry, SigNoz und Phoenix für lückenloses Monitoring
  von Infrastruktur und KI-Performance.

## Flexible Betriebsmodelle und Datensouveränität

### Geschäftlicher Nutzen

Es gibt im Schweizer Markt keine «One-Size-Fits-All»-Lösung für das Hosting. Eine Kantonalbank unterliegt anderen
regulatorischen Zwängen als ein Industrieunternehmen oder ein Start-up. Die Entscheidung über den Speicherort der Daten
und den Betrieb der Infrastruktur muss allein beim Kunden liegen und darf nicht durch die Architektur der Software
diktiert werden. Die Fähigkeit, die Plattform exakt dort zu betreiben, wo die Datenhoheit am besten gewahrt wird – sei
es im eigenen Keller oder in einer zertifizierten Schweizer Cloud – ist ein entscheidender Wettbewerbsvorteil. Sie
eliminiert Compliance-Risiken und ermöglicht den Einsatz von KI auch in Szenarien, die bisher aufgrund von
Cloud-Verboten undenkbar waren.

### Konzeptioneller Ansatz

Der Swiss AI Hub folgt dem Prinzip «Bring Your Own Infrastructure». Die Plattform ist als infrastruktur-agnostische
Lösung konzipiert. Dies bedeutet, dass die Software nicht an eine spezifische Hardware oder einen bestimmten
Cloud-Anbieter gebunden ist. Das Spektrum der unterstützten Betriebsmodelle umfasst drei Hauptszenarien:

1. **On-Premise / Private Cloud:** Der Betrieb erfolgt im eigenen Rechenzentrum oder in einer kontrollierten Umgebung
   bei Hyperscalern (Azure, AWS, GCP) unter voller Kontrolle der internen IT.
2. **SaaS (Schweizer Cloud-Hosting):** Ein Managed Service, gehostet auf einer in der Schweiz ansässigen Infrastruktur,
   bei dem Betrieb, Updates und Backups als Dienstleistung erbracht werden, die Datenhoheit jedoch in der Schweiz
   verbleibt.
3. **Air-Gapped:** Für höchste Sicherheitsanforderungen kann die Plattform vollständig offline ohne Internetverbindung
   betrieben werden.

### Technische Umsetzung im Swiss AI Hub

Technisch basiert die Bereitstellung auf Containerisierung mittels Docker. Dies abstrahiert die Anwendung von der
darunterliegenden Infrastruktur.

- **Standardisiertes Deployment:** Die gesamte Plattform lässt sich mit einem einzigen Orchestrierungs-Befehl
  (`docker compose up`) bereitstellen. Dies umfasst alle Komponenten wie API, Datenbanken (PostgreSQL/FerretDB),
  Vektorspeicher (Milvus) und das LLM-Gateway.
- **Profil-basiertes Setup:** Über spezifische Konfigurationsprofile (`docker-compose.latest.yml` für Produktion vs.
  `.local.yml` für Entwicklung) passt sich das System an. In der Produktion werden automatisch Let's Encrypt
  SSL-Zertifikate verwaltet, während lokal selbstsignierte Zertifikate (via mkcert) zum Einsatz kommen.
- **Netzwerk-Isolation:** Der Zugang erfolgt zentral über einen Reverse Proxy (Traefik) auf Port 443 (HTTPS). Alle
  internen Dienste kommunizieren in isolierten Docker-Netzwerken und sind nicht direkt exponiert.
- **Air-Gap-Fähigkeit:** Da die Plattform lokale Modelle (via vLLM, llama.cpp oder Hugging Face TEI) unterstützt, ist
  keine ausgehende Verbindung zu externen APIs notwendig. Der Betrieb erfolgt autark innerhalb des
  Sicherheitsperimeters.

## Skalierbarkeit und Performance unter Last

### Geschäftlicher Nutzen

KI-Systeme unterliegen oft stark schwankenden Lastprofilen. Ein Monatsabschluss, eine Marketingkampagne oder ein akutes
Ereignis können die Anfragen an das System kurzfristig vervielfachen. Eine starre Infrastruktur würde hier entweder zu
teuren Überkapazitäten im Leerlauf oder zu Systemabstürzen unter Last führen. Unternehmen benötigen eine Architektur,
die «atmet» – also Ressourcen dynamisch dort bereitstellt, wo sie benötigt werden, um Service-Level-Agreements (SLAs)
und Antwortzeiten stabil zu halten, ohne dass die Kosten explodieren.

### Konzeptioneller Ansatz

Die Skalierungsstrategie des Swiss AI Hub basiert auf einer ereignisgesteuerten Architektur (Event-Driven Architecture)
und Zustandslosigkeit (Statelessness). Anstatt monolithische Server zu betreiben, besteht die Plattform aus vielen
kleinen, spezialisierten Worker-Prozessen. Da die Agenten-Logik keinen Zustand lokal im Arbeitsspeicher hält (sondern in
der Datenbank persistiert), kann jede Anfrage von jedem beliebigen Worker verarbeitet werden. Dies eliminiert den
Koordinationsaufwand und ermöglicht eine horizontale Skalierung: Wenn die Warteschlange wächst, werden einfach mehr
Worker hinzugefügt.

### Technische Umsetzung im Swiss AI Hub

Zentrales Nervensystem für die Skalierung ist der Nachrichtendienst **NATS**.

- **Horizontale Skalierung:** Dienste wie die Dokumentenverarbeitung (Ingestion) oder die Agenten-Ausführung können
  mehrfach instanziiert werden. NATS verteilt die anfallenden Aufgaben (Events) automatisch auf die verfügbaren
  Instanzen (Load Balancing).
- **Asynchrone Verarbeitung:** Zeitintensive Aufgaben blockieren nicht den Webserver. Wenn ein Benutzer ein grosses PDF
  hochlädt, nimmt die API die Datei entgegen und übergibt die Verarbeitung an den Hintergrund. Der Benutzer kann sofort
  weiterarbeiten.
- **Ressourcen-Trennung:** Die Plattform unterstützt die Trennung von rechenintensiven Aufgaben. Inferenz-Server für
  lokale Modelle können auf GPU-Instanzen laufen, während die Verwaltungsdienste und die Business-Logik auf
  kostengünstigen CPU-Knoten operieren. Dies optimiert das Kosten-Nutzen-Verhältnis der Infrastruktur massgeblich.

## Hochverfügbarkeit und Disaster Recovery

### Geschäftlicher Nutzen

Für geschäftskritische Anwendungen ist Ausfallsicherheit (High Availability) keine Option, sondern Pflicht. Der Ausfall
einer KI-Komponente darf nicht dazu führen, dass Kundenservice-Mitarbeiter arbeitsunfähig sind oder Prozesse
stillstehen. IT-Verantwortliche benötigen Garantien für kurze Wiederherstellungszeiten (RTO) und minimale Datenverluste
(RPO). Ein robustes System muss Fehler auf Infrastrukturebene tolerieren und sich selbst heilen können, um einen
24/7-Betrieb zu gewährleisten.

### Konzeptioneller Ansatz

Der Ansatz zur Ausfallsicherheit beruht auf Redundanz und Isolation. Die Plattform unterscheidet zwischen
**Multi-Instancing** (physisch getrennte Installationen für maximale Isolation zwischen Mandanten) und Redundanz
innerhalb einer Instanz. Wichtige Komponenten wie Datenbanken und API-Gateways sind darauf ausgelegt, im Cluster-Betrieb
zu laufen. Die Backup-Strategie ermöglicht sowohl vollständige System-Snapshots als auch granulare
Komponentensicherungen.

### Technische Umsetzung im Swiss AI Hub

Die Plattform setzt auf bewährte Mechanismen zur Sicherung der Geschäftskontinuität:

- **Granulare Backup-Strategien:** Neben vollständigen VM-Snapshots unterstützt das System spezifische Backups für jede
  Kernkomponente:
  - **PostgreSQL/FerretDB:** Nutzung von `pg_basebackup` und WAL-Archivierung für Point-in-Time-Recovery der
    relationalen Daten.
  - **Milvus:** Export der Vektorsammlungen in S3-kompatiblen Speicher.
  - **SeaweedFS:** Sichern der physischen Dokumentenablage.
- **Daten-Persistenz:** Kritische Daten liegen auf persistenten, verschlüsselten Docker-Volumes (LUKS), die unabhängig
  vom Lebenszyklus der Container sind. Selbst bei einem Container-Absturz bleiben Daten erhalten.
- **Self-Healing:** Docker Health Checks und externe Load Balancer überwachen die Dienste kontinuierlich und starten
  nicht reagierende Container automatisch neu.
- **Isolierte Instanzen:** Bei einem Multi-Instanz-Setup («Shared Nothing») beeinflusst der Ausfall oder die Wartung
  einer Instanz (z.B. HR) nicht die Verfügbarkeit anderer Instanzen (z.B. Engineering).

## Updates und Wartung ohne Stillstand

### Geschäftlicher Nutzen

Die Innovationszyklen in der KI sind extrem kurz. Unternehmen müssen in der Lage sein, neue Funktionen,
Sicherheits-Patches und verbesserte Modelle schnell zu adaptieren, ohne den laufenden Betrieb zu stören. Monolithische
Updates, die lange Wartungsfenster am Wochenende erfordern, sind nicht mehr zeitgemäss. Eine moderne Plattform muss es
ermöglichen, Updates inkrementell und risikoarm einzuspielen, sodass die IT-Abteilung agil auf Geschäftsanforderungen
reagieren kann.

### Konzeptioneller Ansatz

Der Swiss AI Hub trennt architektonisch strikt zwischen der stabilen **Kernplattform** (Core) und dem flexiblen
**Kundencode** (Custom Agents). Beide Bereiche verfügen über unabhängige Lebenszyklen und Versionierungen. Dies
verhindert, dass ein Update der Basisinfrastruktur ungewollt die Geschäftslogik eines spezifischen Agenten bricht.
Updates können granular durchgeführt werden: Ein neuer Agent kann deployt werden, ohne die Datenbank neu zu starten.

### Technische Umsetzung im Swiss AI Hub

Das Update-Management nutzt semantische Versionierung und Container-Tags:

- **Unabhängige Versionierung:** Kundencode ist in der `pyproject.toml` an eine spezifische Core-Version gebunden
  (Pinned Dependency). Wenn die Plattform ein Update erhält (z.B. von v1.2 auf v1.3), läuft der bestehende Kundencode
  stabil weiter, bis er explizit migriert wird.
- **Rolling Updates:** In Container-Orchestrierungs-Umgebungen können neue Versionen von Diensten parallel zu alten
  gestartet werden. Der Verkehr wird erst umgeleitet, wenn die neue Instanz als «gesund» (healthy) gemeldet wird.
- **Rollback-Fähigkeit:** Da jede Version als immutables Docker-Image vorliegt, ist ein Rollback bei Fehlern trivial. Es
  genügt, das Versions-Tag in der `docker-compose.yml` zurückzusetzen und die Container neu zu starten.
- **Release-Kanäle:** Kunden können zwischen `stable` (für Produktion) und `nightly` (für Entwicklung) wählen, um neue
  Features frühzeitig in Staging-Umgebungen zu testen.

## Operative Transparenz und Monitoring

### Geschäftlicher Nutzen

«Man kann nicht managen, was man nicht misst.» Im Betrieb einer KI-Plattform ist Blindflug fatal. Performance-Engpässe,
schleichende Kostenanstiege oder Modell-Fehler müssen erkannt werden, bevor sie zum Problem werden. Ein integriertes
Monitoring reduziert die Mean Time to Resolution (MTTR) bei Vorfällen drastisch und liefert die Datenbasis für
Kapazitätsplanung und Budgetierung.

### Konzeptioneller Ansatz

Die Observability-Strategie der Plattform basiert auf den drei Säulen: **Health Checks** (Ist es an?), **Metriken** (Wie
schnell ist es?) und **Logs** (Was ist passiert?). Anstatt proprietäre Tools zu erzwingen, setzt der Swiss AI Hub auf
offene Standards. Dies ermöglicht eine nahtlose Integration in bestehende Enterprise-Monitoring-Lösungen wie Datadog
oder Splunk, liefert aber standardmässig einen vollständigen Open-Source-Stack mit.

### Technische Umsetzung im Swiss AI Hub

Das Monitoring-Fundament bildet **OpenTelemetry (OTel)**:

- **Integrierte Dashboards:** Out-of-the-box wird **SigNoz** als Visualisierungsplattform mitgeliefert. Administratoren
  sehen sofort CPU/RAM-Auslastung, API-Latenzen und Fehlerquoten.
- **KI-spezifisches Tracing:** Für die tiefe Analyse von LLM-Interaktionen ist **Phoenix** integriert. Es visualisiert
  Token-Verbrauch, Latenz und den vollständigen Kontext von RAG-Abfragen (Retrieval-Augmented Generation).
- **Proaktive Health Checks:** Jeder Dienst exponiert `/health`-Endpunkte. Docker nutzt diese für automatische Restarts,
  während externe Monitoring-Systeme sie für Verfügbarkeitsalarme abfragen können.
- **Exportierbarkeit:** Über den zentralen OTel-Collector können alle Telemetriedaten an bestehende Systeme
  weitergeleitet werden, ohne dass Code-Änderungen nötig sind.

## Technologische Unabhängigkeit (Model Agnostic)

### Geschäftlicher Nutzen

Die Abhängigkeit von einem einzelnen KI-Modell-Anbieter (Vendor Lock-in) ist ein strategisches Risiko. Preiserhöhungen,
Service-Änderungen oder Ausfälle eines US-Providers können direkte Auswirkungen auf das Schweizer Geschäft haben. Der
Swiss AI Hub mitigiert dieses Risiko durch technologische Neutralität. Die Plattform erlaubt es, Modelle wie Bausteine
auszutauschen oder redundant auszulegen, um die Verhandlungsmacht zu behalten und die Geschäftskontinuität zu sichern.

### Konzeptioneller Ansatz

Die Plattform fungiert als Abstraktionsschicht zwischen der Anwendung und der Intelligenz. Ein Agent kommuniziert nie
direkt mit «GPT-4» oder «Gemini», sondern mit dem internen LLM-Gateway. Dieses Gateway entscheidet anhand von Regeln,
welches Modell die Anfrage tatsächlich bearbeitet. Dies ermöglicht Failover-Szenarien: Fällt der primäre Provider aus,
kann der Verkehr automatisch auf einen sekundären Provider oder ein lokales Modell umgeleitet werden.

### Technische Umsetzung im Swiss AI Hub

Das **LiteLLM-Proxy** ist die zentrale Schaltstelle für diese Unabhängigkeit:

- **Unified API:** Alle Modelle werden über eine einheitliche, OpenAI-kompatible Schnittstelle angesprochen. Ein
  Modellwechsel erfordert lediglich eine Konfigurationsänderung, kein Umschreiben des Codes.
- **Multi-Provider-Support:** Die Plattform unterstützt parallel Azure OpenAI, Google Gemini, Anthropic, die Swiss LLM
  Cloud sowie lokale Modelle via vLLM.
- **Load Balancing & Failover:** Administratoren können mehrere API-Keys oder Endpunkte für dasselbe logische Modell
  hinterlegen. Das Gateway verteilt die Last und schaltet bei Fehlern automatisch auf gesunde Endpunkte um, was die
  Zuverlässigkeit der Gesamtanwendung massiv erhöht.
