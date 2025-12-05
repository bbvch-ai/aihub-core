# Kapitel 10: Deployment, Betrieb

## Betriebliche Exzellenz und architektonische Flexibilität

Die Entscheidung für eine Enterprise-KI-Plattform wird nicht allein durch deren Funktionsumfang getroffen, sondern
massgeblich durch ihre Betriebsfähigkeit bestimmt. Für CIOs und IT-Leiter stellt sich die fundamentale Frage, wie sich
eine komplexe KI-Infrastruktur in die bestehende IT-Landschaft integrieren lässt, ohne dabei Sicherheitsstandards zu
kompromittieren oder operative Risiken zu erhöhen. Eine Lösung, die in der Pilotphase glänzt, aber im Rechenzentrum
schwerfällig ist, wird langfristig scheitern.

Der Swiss AI Hub adressiert diese Anforderung durch einen konsequenten «Operations-First»-Ansatz. Die Plattform ist
darauf ausgelegt, vom ersten Tag an als robustes, wartbares Produktivsystem zu fungieren. Sie bricht mit der starren
Doktrin reiner SaaS-Angebote und bietet stattdessen eine flexible Architektur, die sich den Infrastruktur-Vorgaben des
Kunden anpasst. Dies beginnt bereits bei der Initialisierung: Die gesamte Infrastruktur – bestehend aus Datenbanken,
Vektorspeichern und API-Diensten – lässt sich dank optimierter Docker-Compose-Konfigurationen mit einem einzigen Befehl
bereitstellen. Dieser «One-Command Deployment»-Ansatz reduziert die «Time-to-Value» von Wochen auf Minuten, indem er
komplexe Abhängigkeiten automatisiert auflöst.

## Flexible Deployment-Modelle für maximale Souveränität

### Vom Managed Service bis zum Air-Gap

Unterschiedliche Branchen unterliegen höchst diversen regulatorischen Drücken und strategischen Zielen. Ein
Medienunternehmen priorisiert möglicherweise Geschwindigkeit und Skalierbarkeit, während eine Strafverfolgungsbehörde
absolute Isolation benötigt. Ein «One-Size-Fits-All»-Ansatz ist hier zum Scheitern verurteilt. Die Wahl des
Deployment-Modells ist daher kein rein technisches Detail, sondern eine strategische Entscheidung über
Datensouveränität.

Der Swiss AI Hub unterstützt dieses Spektrum durch drei primäre Hosting-Optionen, die auf einer einheitlichen
containerisierten Architektur basieren:

1. **On-Premise (Eigene Server):** Für Organisationen mit strikten Datenresidenz-Vorgaben läuft die Plattform auf
   Standard-x86_64-Servern im Unternehmens-Rechenzentrum. Hierbei entfallen externe Cloud-Abhängigkeiten. Für
   Hochsicherheitsbereiche unterstützt die Plattform **Air-Gapped-Deployments**. In diesem Szenario ist das System
   physisch vom Internet getrennt. Anstelle externer APIs kommen lokal gehostete Sprachmodelle (wie Llama, Mistral oder
   DeepSeek) zum Einsatz, die über interne Inferenz-Server (z.B. vLLM oder llama.cpp) und GPU-Ressourcen bereitgestellt
   werden.
2. **Private Cloud (Bring Your Own Cloud):** Die Infrastruktur wird in der eigenen Cloud-Subscription des Kunden (z.B.
   Azure Switzerland, AWS Zurich oder GCP) provisioniert. Governance-Richtlinien und Sicherheitsperimeter greifen
   nahtlos, während die Skalierbarkeit der Hyperscaler genutzt wird. Die Datenhoheit verbleibt dabei durch eigene
   Verschlüsselungsschlüssel (BYOK) beim Kunden.
3. **SaaS (Schweizer Cloud-Hosting):** Als Managed Service übernimmt der Anbieter den Betrieb, die Updates und das
   Monitoring auf einer in der Schweiz ansässigen Cloud-Infrastruktur. Dies reduziert den operativen Aufwand für das
   interne IT-Team auf ein Minimum, während die Daten rechtssicher in der Schweiz verbleiben.

### Multi-Instancing für harte Isolation

Sicherheit durch Architektur bedeutet auch, dass interne Grenzen respektiert werden. Während Multi-Tenancy eine logische
Trennung innerhalb einer Software bietet, benötigen bestimmte Szenarien eine physische Isolation, um das Risiko von
Datenlecks («Spillover») vollständig zu eliminieren.

Der Swiss AI Hub implementiert hierfür das Konzept des **Multi-Instancings**. Anstatt alle Mandanten in eine riesige
Datenbank zu zwingen, können Organisationen mehrere vollständig isolierte Instanzen der Plattform parallel betreiben.
Jede Instanz verfügt über eigene Datenbanken (PostgreSQL, FerretDB), Vektor-Speicher (Milvus oder Azure AI Search) und
Dateispeicher (SeaweedFS). Eine Instanz für die Forschung kann somit völlig getrennt von einer Instanz für HR-Daten
laufen. Dennoch erlaubt die Architektur Synergien: Verschiedene Instanzen können über ihren jeweiligen LiteLLM-Proxy auf
ein geteiltes, zustandsloses LLM-Backend zugreifen. Dies ermöglicht eine zentrale Verwaltung von API-Schlüsseln und
Ressourcen, während die sensiblen Nutzdaten (Prompts, Dokumente, Vektoren) strikt innerhalb der isolierten
Instanzgrenzen verbleiben.

## Hochverfügbarkeit und Skalierung

### Ereignisgesteuerte Architektur als Skalierungsfaktor

KI-Workloads sind naturgemäss volatil. Die Lastkurve eines Chatbots oder einer Daten-zu-Wissen-Pipeline ist selten
linear; sie ist geprägt von Spitzenlasten und Ruhephasen. Eine starre Architektur würde in Spitzenzeiten kapitulieren
und in Ruhephasen unnötig Ressourcen binden. Die betriebliche Anforderung lautet daher Elastizität: Das System muss
atmen können.

Der Swiss AI Hub löst dies durch eine asynchrone, ereignisgesteuerte Architektur. Komponenten wie KI-Agenten oder
Ingestion-Pipelines sind zustandslos («stateless») konzipiert. Sie halten keinen lokalen State, der bei einem Absturz
verloren gehen könnte, sondern verarbeiten Ereignisse aus einer zentralen Message Queue (NATS). Dies ermöglicht eine
horizontale Skalierung ohne komplexe Synchronisation. Wenn die Warteschlange für zu verarbeitende Dokumente anwächst,
können automatisiert oder manuell zusätzliche Worker-Container gestartet werden. Diese übernehmen sofort Arbeitspakete,
ohne dass Load-Balancer neu konfiguriert werden müssen.

### Resilienz und Selbstheilung

Betriebsstabilität bedeutet auch, dass der Ausfall einer einzelnen Komponente nicht zum Stillstand des Gesamtsystems
führen darf. Durch die Container-Orchestrierung verfügt die Plattform über native Selbstheilungskräfte («Self-Healing»).

Health Checks überwachen kontinuierlich auf mehreren Ebenen:

1. **Native Docker Checks:** Prüfen, ob der Prozess physisch läuft («Liveness»).
2. **Applikations-Checks:** Validieren über dedizierte Endpunkte (`/health`), ob der Service bereit ist, Anfragen zu
   verarbeiten («Readiness»).
3. **Synthetische Probes:** Testen aktiv die Funktionalität komplexer Abhängigkeiten, etwa die Erreichbarkeit der
   Vektordatenbank.

Ein abgestürzter Agent-Prozess wird automatisch neu gestartet. Da die Verarbeitung via NATS JetStream auf einer
«At-Least-Once»-Logik basiert, gehen dabei keine Aufgaben verloren: Ein Auftrag, der durch einen Absturz unterbrochen
wurde, wird von der Queue erneut an die nächste freie Instanz zugewiesen (Retry-Mechanismus).

## Modell-Unabhängigkeit und Vendor-Neutralität

### Vermeidung des Vendor-Lock-ins im Betrieb

Eine der grössten operativen Gefahren im KI-Betrieb ist die Abhängigkeit von einem einzigen Modell-Anbieter. Fällt
dieser Anbieter aus, ändert er seine Preise oder seine Nutzungsbedingungen, steht der Betrieb still. Eine robuste
Betriebsstrategie erfordert daher Diversifikation und Abstraktion.

Der Swiss AI Hub integriert einen leistungsfähigen Abstraktionslayer, das **LLM-Gateway** (implementiert durch LiteLLM).
Dieses fungiert als zentraler Proxy für alle Modell-Anfragen. Aus Sicht der Applikation ist es irrelevant, ob im
Hintergrund Azure OpenAI, Google Gemini oder ein lokales Open-Source-Modell antwortet. Dies ermöglicht im laufenden
Betrieb ein nahtloses Routing und Failover. Sollte der primäre Provider Performance-Probleme haben, kann der Traffic
durch eine Konfigurationsänderung auf einen alternativen Anbieter umgeleitet werden, ohne dass Code angepasst oder
Deployments durchgeführt werden müssen.

Zusätzlich ermöglicht dies eine Kostenoptimierung durch intelligentes Routing: Einfache Aufgaben werden an günstige
Modelle geleitet, während komplexe Anfragen an leistungsfähigere «Flagship-Modelle» gehen. Administratoren behalten
durch diese zentrale Komponente stets die Kontrolle über Budgets und Quotas pro Instanz und Nutzer.

## Updates, Wartung und Lifecycle-Management

### Entkopplung von Kern und Individualisierung

Ein häufiges Problem bei Enterprise-Software ist die «Update-Angst»: Systeme werden nicht aktualisiert, weil befürchtet
wird, dass individuelle Anpassungen überschrieben werden oder Inkompatibilitäten auftreten. Dies führt zu veralteten,
unsicheren Systemen.

Der Swiss AI Hub begegnet diesem Risiko durch eine strikte architektonische Trennung von **Core Platform** und
**Customer Code**. Die Kernkomponenten (API, Web-UI, Workflow-Engine) werden als standardisierte Docker-Images
bereitgestellt. Kundenspezifische Anpassungen – wie eigene Agenten-Baupläne oder spezialisierte Pipelines – residieren
in separaten Repositories. Über `pyproject.toml` wird der Kundencode explizit an spezifische Core-Versionen gepinnt.
Dies garantiert Stabilität: Die Plattform-Basis kann für Sicherheitsupdates gepatcht werden, ohne die Business-Logik zu
gefährden.

Das System nutzt dabei semantische Versionierung. Breaking Changes werden klar in Major-Releases isoliert, während
Patch-Updates risikolos eingespielt werden können.

### Zero-Downtime-Strategien und Rollbacks

Für den produktiven Betrieb unterstützt die Architektur moderne Deployment-Strategien. Da die Services zustandslos sind,
können Updates im Rolling-Update-Verfahren eingespielt werden, bei dem Container nacheinander ausgetauscht werden, um
Downtimes zu minimieren. Sollte ein Update dennoch Probleme verursachen, ermöglicht die Containerisierung ein sofortiges
Rollback auf die vorherige Version durch einfaches Ändern des Image-Tags in der Konfiguration. Die Datenpersistenz
bleibt davon unberührt, da Datenbanken auf persistenten Volumes liegen, die vom Applikations-Lifecycle entkoppelt sind.

## Observability: Transparenz bis in die Tiefe

### Mehr als nur «Up» oder «Down»

In einer komplexen KI-Architektur reicht es nicht zu wissen, ob der Server läuft. Operative Teams müssen verstehen,
*wie* das System performt. Der Swiss AI Hub integriert hierfür einen vollständigen **Observability Stack** basierend auf
dem Industriestandard OpenTelemetry (OTel).

Das Monitoring deckt vier kritische Ebenen ab:

1. **Infrastruktur-Metriken:** CPU, RAM, Disk I/O und Netzwerk-Durchsatz der Container geben Aufschluss über die
   Ressourcenauslastung.
2. **Applikations-Logs:** Strukturierte Logs aller Services werden zentral aggregiert. Dies verhindert das mühsame
   Suchen in verteilten Server-Logs.
3. **Distributed Tracing:** Jede Anfrage erhält eine Trace-ID. Dies erlaubt es, den Weg einer Nutzeranfrage über das
   API-Gateway bis hin zur Datenbank millisekundengenau nachzuverfolgen.
4. **KI-Observability:** Spezialisierte Tools (wie Phoenix) überwachen die Qualität der KI-Antworten, die Token-Nutzung
   und die RAG-Retrieval-Performance.

Als zentrales Dashboard dient standardmässig **SigNoz**, welches Health-Daten, Metriken und Logs visualisiert. Da
OpenTelemetry ein offener Standard ist, lassen sich diese Daten jedoch auch nahtlos in bestehende
Unternehmens-Monitoringsysteme wie Datadog, Splunk oder Grafana exportieren.

## Netzwerksicherheit, Backup und Disaster Recovery

### Minimierte Angriffsfläche

Sicherheit im Betrieb beginnt beim Netzwerk. Die Plattform verfolgt eine strikte «Default Deny»-Politik für eingehende
Verbindungen. Lediglich Port 443 (HTTPS) ist für den regulären Zugriff geöffnet (optional Port 80 für Redirects und Port
22 für SSH-Administration). Alle internen Dienste (Datenbanken, LLM-Proxy) kommunizieren in einem isolierten Netzwerk
und sind niemals direkt dem Internet ausgesetzt.

### Strategien zur Wiederherstellung

Datenverlust ist keine Option. Die Backup-Strategie des Swiss AI Hubs unterstützt zwei Ansätze, die je nach Recovery
Time Objective (RTO) gewählt werden können:

1. **VM-Snapshots:** Einfrieren des gesamten Systemzustands für eine schnelle «Bare-Metal»-Wiederherstellung. Dies ist
   ideal für Disaster Recovery Szenarien, bei denen die gesamte Instanz wiederhergestellt werden muss.
2. **Komponentenspezifische Backups:** Für granulare Wiederherstellung bietet die Plattform spezifische Routinen:
   Relationale Daten werden via `pg_basebackup` gesichert, Vektor-Indizes (Milvus) und Dokumenten-Speicher (SeaweedFS)
   werden auf S3-kompatible Ziele repliziert.

Da die gesamte Infrastruktur als Code (Infrastructure as Code via Docker Compose) definiert ist, lässt sich im
Katastrophenfall die Applikationsumgebung innerhalb kürzester Zeit auf neuer Hardware provisionieren. Die
Wiederherstellung wird dabei primär durch die Datenmenge, nicht durch komplexe Installationsprozesse bestimmt.
