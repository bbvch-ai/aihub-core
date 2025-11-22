# Kapitel 10: Deployment und Betrieb

Die effektive Nutzung Künstlicher Intelligenz (KI) in Unternehmensumgebungen hängt massgeblich von einer robusten,
flexiblen und zuverlässigen Betriebsführung ab. Schweizer Unternehmen, die höchste Anforderungen an Datensouveränität,
Ausfallsicherheit und Kostenkontrolle stellen, benötigen eine Plattform, die diese Kriterien von der Bereitstellung bis
zum täglichen Betrieb lückenlos erfüllt. Dieses Kapitel beleuchtet die betrieblichen Aspekte des Swiss AI Hub, die seine
Eignung für den unternehmenskritischen Einsatz untermauern. Es wird dargelegt, wie die Architektur flexible
Bereitstellungsmodelle unterstützt, Hochverfügbarkeit und Skalierbarkeit gewährleistet, herstellerunabhängiges
Modellmanagement ermöglicht und einen nahtlosen 24/7-Betrieb sicherstellt.

## 1. Flexible Bereitstellungsmodelle und Souveränität in der Cloud-Strategie

Die Wahl des richtigen Bereitstellungsmodells ist für Schweizer Unternehmen, insbesondere angesichts strenger
Datenschutzgesetze und spezifischer Sicherheitsrichtlinien, von strategischer Bedeutung. Der Swiss AI Hub bietet eine
Architektur, die maximale Flexibilität und Datensouveränität über verschiedene Hosting-Optionen hinweg gewährleistet.

### Mehrwert und Nutzen: Maximale Datenhoheit und Anpassungsfähigkeit

Für C-Level-Führungskräfte bietet die Auswahl aus verschiedenen Bereitstellungsmodellen die Gewissheit, dass die
Plattform den internen Compliance-Vorgaben und externen regulatorischen Anforderungen (wie revDSG und DSGVO) lückenlos
entspricht. Die Möglichkeit, die Datenhoheit vollständig in der Schweiz zu behalten, minimiert rechtliche Risiken und
stärkt das Vertrauen in KI-gestützte Prozesse. IT-Professionals profitieren von einer adaptiven Lösung, die sich nahtlos
in bestehende Infrastrukturlandschaften integrieren lässt, den administrativen Aufwand für die Einhaltung von
Datentransferbestimmungen reduziert und es ermöglicht, kritische Systeme auch ohne externe Abhängigkeiten zu betreiben.

### Konzepte & Prozesse: Single-Instanz-Isolation und Air-Gapped-Fähigkeit

Der Swiss AI Hub ist primär für **Einzelinstanz-Deployments** konzipiert, die auch als Multi-Instancing bekannt sind.
Jede Organisation erhält dabei eine vollständige, eigenständige Instanz der Plattform mit dedizierten Datenbanken,
Vektor-Stores, Dateispeichern und allen Anwendungsdiensten. Dies gewährleistet eine strikte Isolation der Daten und
Ressourcen, im Gegensatz zu Multi-Tenant-SaaS-Plattformen, bei denen Ressourcen oft geteilt werden. Diese Architektur
erlaubt auch den Betrieb in **Air-Gapped-Umgebungen**, d.h. die Plattform kann vollständig ohne ausgehende
Internetverbindung betrieben werden, sofern lokal gehostete Sprachmodelle (LLMs) verwendet werden. Bei
Multi-Instanz-Deployments teilen sich mehrere isolierte Instanzen optional gemeinsame, zustandslose
LLM-Backend-Ressourcen, wobei der konversationelle Kontext und Benutzerdaten stets innerhalb der jeweiligen
Tenant-Instanz verbleiben und somit eine harte Trennung mit 0% Datenlecks gewährleistet wird.

### Technische Umsetzung im Swiss AI Hub: On-Premise, Private Cloud und Schweizer SaaS

Der Swiss AI Hub kann flexibel in verschiedenen Umgebungen gehostet werden:

- **On-Premise (eigener Server):** Organisationen betreiben den AI Hub auf ihren eigenen x86_64-Servern in ihrem
  Rechenzentrum. Die gesamte Infrastruktur, einschliesslich CPU, RAM, Speicher und optional NVIDIA-GPUs für lokale
  LLM-Inferenz, liegt in der vollständigen Kontrolle des Kunden. Dies ermöglicht einen Air-Gapped-Betrieb und eliminiert
  jegliche Cloud-Abhängigkeit.
- **Private Cloud (eigene Cloud):** Die Bereitstellung erfolgt in der eigenen Cloud-Umgebung des Kunden, sei es bei
  einem Schweizer Cloud-Anbieter oder Hyperscaler wie Azure, AWS oder GCP. Dabei bleiben alle Daten im Cloud-Konto des
  Kunden und unter dessen Kontrolle, mit der Option, spezifische Regionen (z.B. Schweiz) für die Datenresidenz zu
  wählen. Cloud-Provider verfügen typischerweise über Sicherheits- und Compliance-Zertifizierungen.
- **SaaS (Schweizer Cloud-Hosting):** Als Alternative zu einer selbstverwalteten Bereitstellung bietet die bbv als
  Plattformanbieter das Hosting und die Verwaltung des AI Hub auf einer in der Schweiz ansässigen Cloud-Infrastruktur
  an. In diesem Fall übernimmt bbv Bereitstellung, Updates, Backups und Monitoring, wobei die Daten stets in der Schweiz
  und unter Schweizer Rechtshoheit verbleiben und SLAs angeboten werden.

Hybrid-Deployments sind ebenfalls konfigurierbar, indem beispielsweise die AI-Hub-Instanz On-Premise läuft, aber
bestimmte LLM-Dienste aus der Cloud genutzt werden. Die Datenisolation ist ein Kernmerkmal: Die Daten jeder Instanz
bleiben in der jeweiligen Installation isoliert. Es gibt keine gemeinsame Datenbank oder gemeinsamen Vektor-Store
zwischen Organisationen, was die Anforderungen des revDSG und der DSGVO an die Datenisolation vollständig erfüllt.

## 2. Schnelle Bereitstellung und Skalierbarkeit für wachsende Anforderungen

Die Agilität, KI-Lösungen schnell in Betrieb zu nehmen und bei steigendem Bedarf nahtlos zu skalieren, ist entscheidend
für den Geschäftserfolg. Der Swiss AI Hub wurde entwickelt, um diese Anforderungen mit minimalem Aufwand und maximaler
Effizienz zu erfüllen.

### Mehrwert und Nutzen: Rasche Wertschöpfung und Kostenoptimierung

Für Führungskräfte ermöglicht die schnelle Einsatzbereitschaft eine rasche Time-to-Value, beschleunigt die Einführung
von KI im Unternehmen erheblich und schafft einen Wettbewerbsvorteil. Die integrierte Skalierbarkeit stellt sicher, dass
Investitionen zukunftssicher sind und die Plattform mit dem Unternehmenswachstum Schritt halten kann, während die Kosten
durch effiziente Ressourcennutzung optimiert werden. IT-Teams profitieren von einem vereinfachten Deployment-Prozess,
der komplexe Infrastrukturkonfigurationen abstrahiert und eine mühelose Anpassung der Kapazitäten an wechselnde
Systemlasten erlaubt.

### Konzepte & Prozesse: One-Command Deployment und ereignisgesteuerte Skalierung

Die Plattform kann mit einem einzigen Befehl mittels Docker Compose bereitgestellt werden, was die initiale Einrichtung
einfach und schnell gestaltet. Die zugrunde liegende Architektur des Swiss AI Hub ist **ereignisgesteuert und
zustandslos**, was eine inhärente horizontale Skalierbarkeit und Systemresilienz ermöglicht. Die Agentenlogik enthält
keinen veränderbaren Zustand, wodurch jede Instanz jedes Ereignis verarbeiten kann. Ereignisse werden zur parallelen
Verarbeitung über mehrere Agenteninstanzen verteilt, und die Messaging-Infrastruktur gleicht die Arbeit automatisch aus.
Fehlgeschlagene Operationen werden durch Ereigniswiederholung erneut versucht, was eine hohe Systemresilienz
gewährleistet. Dies ermöglicht eine mühelose Skalierung zur Bewältigung schwankender Anforderungen, indem zusätzliche
Worker-Instanzen bereitgestellt werden, die Ereignisse aus denselben Streams verarbeiten und die Verarbeitungslast
automatisch verteilen.

### Technische Umsetzung im Swiss AI Hub: Docker Compose und horizontale Skalierung

Die Bereitstellung erfolgt über eine `docker compose`-Datei (`docker-compose.latest.yml` für Produktion,
`docker-compose.local.yml` für lokale Entwicklung). Nach dem Erstellen einer `.env`-Datei mit den notwendigen
Konfigurationen (Domain, Authentifizierung, LLM-Zugriff, Zugangsdaten) lässt sich die gesamte Plattform mit
`docker compose up -d` starten. Dieser Befehl lädt alle notwendigen Docker-Images herunter, erstellt Netzwerke und
Volumes und startet alle Dienste.

Die Plattform umfasst Kernkomponenten wie:

- Web-Interface (aihub-web) und API (aihub-api)
- Authentifizierungsdienste
- Datenbanken (FerretDB/PostgreSQL für persistente Daten, Valkey (Redis-kompatibel) für Caching/Sitzungsstatus)
- Vektordatenbank (Milvus)
- LLM-Proxy (LiteLLM)
- Dokumentenverarbeitung (Docling)
- Observability (Phoenix, OpenTelemetry)
- Message Queue (NATS)
- Speicher (SeaweedFS S3 Storage)

Der initiale Start dauert in der Regel **3-5 Minuten**, während sich die Services initialisieren und den Status
"healthy" erreichen. Für die Skalierung können zusätzliche Agenteninstanzen bereitgestellt werden, um ein erhöhtes
Verarbeitungsvolumen zu bewältigen. Die Plattform ist auf Containertechnologien aufgebaut, was im Kontext einer
Container-Orchestrierungsplattform wie Kubernetes **Auto-Scaling** prinzipiell ermöglicht, indem die Anzahl der
Worker-Instanzen dynamisch an die Last angepasst wird. Der Swiss AI Hub nutzt standardmässig PostgreSQL und FerretDB
(MongoDB-kompatibel); MSSQL oder Oracle werden in der Quelldokumentation nicht explizit als unterstützte Datenbanken
erwähnt. Nach dem Deployment wird der Login über Azure-Authentifizierung erwartet, woraufhin das Haupt-Dashboard
sichtbar wird.

## 3. Technologische Unabhängigkeit und intelligentes Modellmanagement

Die rasante Entwicklung im Bereich der Künstlichen Intelligenz erfordert von Unternehmen die Agilität, stets die besten
verfügbaren KI-Modelle einzusetzen, ohne dabei von einem einzelnen Anbieter abhängig zu sein. Der Swiss AI Hub begegnet
diesem Bedarf durch eine herstellerunabhängige Architektur.

### Mehrwert und Nutzen: Strategische Unabhängigkeit und Kostenoptimierung

Für C-Level-Führungskräfte eliminiert die Unabhängigkeit von einzelnen KI-Providern das Risiko des Vendor Lock-in und
sichert die langfristige strategische Handlungsfähigkeit des Unternehmens. Diese Flexibilität ermöglicht es, stets die
optimalen LLMs (proprietär oder Open Source) zu wählen, die den Anforderungen an Leistung, Kosten und Datensouveränität
am besten entsprechen. IT-Teams profitieren von einem zentralen Management-Gateway, das den Wechsel zwischen Modellen
vereinfacht, die Kosten über alle Anbieter hinweg transparent verfolgt und automatisierte Fallback-Mechanismen für
maximale Ausfallsicherheit bietet.

### Konzepte & Prozesse: Abstrahierte Modellschicht und Kostenverfolgung

Ein zentrales Element ist der **LiteLLM-Proxy**, der als vereinheitlichtes Gateway zu allen Sprachmodell-Anbietern
dient. Er abstrahiert anbieterspezifische APIs und ermöglicht es dem Plattform-Code, mit einer konsistenten
Schnittstelle zu interagieren, unabhängig vom zugrunde liegenden Modell. Das intelligente Routing leitet Anfragen
basierend auf Konfiguration, Kostenoptimierung oder Lastverteilung an die geeigneten Modelle weiter. Dies ermöglicht den
parallelen Einsatz und nahtlosen Wechsel zwischen kommerziellen Cloud-Modellen und lokal gehosteten Open-Source-LLMs.
Das Kostenmanagement verfolgt die Token-Nutzung pro Instanz und Benutzer über alle LLM-Anbieter hinweg und ermöglicht
die Durchsetzung von Budgets und Ratenbegrenzungen.

### Technische Umsetzung im Swiss AI Hub: LiteLLM und Multi-Provider-Unterstützung

Der LiteLLM-Proxy bietet eine OpenAI-kompatible API, die eine breite Palette von Modellen unterstützt. Dazu gehören
kommerzielle Anbieter wie **Azure OpenAI und Google Gemini**, aber auch selbst gehostete Open-Source-Modelle über
Lösungen wie **vLLM, llama.cpp oder HF-TEI**. Dies ermöglicht auch den Betrieb in Air-Gapped-Umgebungen ohne
Internetverbindung, indem nur lokale Modelle genutzt werden. Die Plattform kann problemlos mehrere LLM-Anbieter
gleichzeitig nutzen und Anfragen intelligent zwischen ihnen routen, beispielsweise für Kostenoptimierung oder den
Einsatz spezialisierter Modelle.

Automatisierte Failover-Routinen können konfiguriert werden, indem mehrere LLM-Provider oder lokale Instanzen parallel
genutzt werden. Fällt ein Dienst aus, kann LiteLLM Anfragen an einen verfügbaren alternativen Provider umleiten, was die
Ausfallsicherheit erheblich steigert. LiteLLM verfolgt detailliert die API-Nutzung pro Instanz und Benutzer,
einschliesslich Token-Anzahl, Modellnutzung und Kostenberechnungen. Dies ist über die LiteLLM-Admin-Benutzeroberfläche
einsehbar und für die Abrechnung exportierbar. Die einfache Konfiguration der Umgebungsvariablen ermöglicht den
schnellen Wechsel zwischen KI-Providern. Synergien mit Microsoft 365 Copilot sind in der bereitgestellten Dokumentation
nicht explizit aufgeführt.

## 4. Betriebliche Kontinuität, Wartung und Monitoring

Ein unternehmenskritischer Einsatz erfordert einen zuverlässigen 24/7-Betrieb, minimale Ausfallzeiten bei Wartungen und
eine proaktive Überwachung aller Systemkomponenten. Der Swiss AI Hub bietet umfassende Funktionen, um diese
Anforderungen zu erfüllen.

### Mehrwert und Nutzen: Garantierte Verfügbarkeit und proaktive Fehlerbehebung

Für C-Level-Führungskräfte sind hohe Uptime-SLAs und schnelle Wiederherstellungszeiten (RPO/RTO) entscheidend, um die
Geschäftskontinuität zu sichern und Vertrauen in die digitale Transformation zu schaffen. Die Plattform minimiert
Betriebsrisiken und schützt vor finanziellen Verlusten durch Systemausfälle. IT- und Operations-Teams profitieren von
automatisierten Wartungsprozessen, effizienten Backup-Strategien und einem umfassenden Monitoring-System, das eine
proaktive Problemerkennung und eine nahtlose Integration in bestehende IT-Operations-Prozesse ermöglicht.

### Konzepte & Prozesse: Disaster Recovery, Zero-Downtime-Updates und Observability

Die Plattform ist auf Hochverfügbarkeit ausgelegt, wobei ereignisgesteuerte und zustandslose Architekturen (wie in
Abschnitt 2 beschrieben) zur Fehlerwiederherstellung beitragen. **Disaster-Recovery-Verfahren** basieren auf
VM-Snapshots oder komponentenbasierten Backups für einzelne Datenspeicher. Updates sind so konzipiert, dass sie
inkrementell und möglichst ohne Dienstunterbrechung bereitgestellt werden können ("Zero-Downtime-Updates") durch
gestaffelte Rollouts und Blue-Green-Deployment-Strategien, die die Möglichkeit zum schnellen Rollback bieten.

Die operative Transparenz wird durch die drei Säulen der **Observability** gewährleistet:

- **Health Checks:** Kontinuierliche Überprüfung der Funktionsfähigkeit jeder Komponente (Native Docker Checks,
  Application Endpoint Checks, Synthetic Probes), um ein sofortiges Bild des Systemstatus zu liefern.
- **Metriken:** Quantitative Messungen verfolgen Leistung und Ressourcennutzung über die Zeit (Infrastruktur- und
  Anwendungsmetriken), unerlässlich für Trendanalysen, Kapazitätsplanung und die Identifizierung von Engpässen.
- **Logs:** Detaillierte, chronologische Aufzeichnungen jedes Ereignisses liefern Kontext für die Ursachenanalyse
  (Application, Container, Request, Security Logs), um Probleme schnell zu diagnostizieren.

### Technische Umsetzung im Swiss AI Hub: Backup-Mechanismen, Versionsverwaltung und OpenTelemetry

Jede Instanz verfügt über unabhängige Backups. Für **Backups** können entweder VM-Snapshots des gesamten Systems oder
komponentenbasiertes Backup der einzelnen Datenspeicher (PostgreSQL, FerretDB, Milvus, SeaweedFS, Valkey, NATS, etcd,
Konfiguration) verwendet werden. Für PostgreSQL wird `pg_basebackup` für vollständige Backups und WAL-Archivierung für
die Point-in-Time-Recovery empfohlen. Milvus-Vektor-Embeddings können aus S3-kompatiblem Speicher exportiert oder bei
Bedarf aus Quelldokumenten neu generiert werden. Die Sicherung der Konfiguration umfasst Umgebungsvariablen und
SSL-Zertifikate, wobei Backups verschlüsselt und Schlüssel separat gespeichert werden sollten. Konkrete
RPO/RTO-Garantien werden in der Dokumentation nicht explizit genannt, jedoch bilden die Backup-Strategien die Grundlage
für deren Definition.

Die Kernplattform und kundenspezifischer Code verwenden **semantische Versionierung** und können unabhängig aktualisiert
werden. Abwärtskompatible Updates (Patch- und Minor-Versionen) können durch Aktualisierung der Docker-Image-Tags und
Neustart der Services erfolgen, ohne dass der Kundencode geändert werden muss. Major Core-Updates mit Breaking Changes
erfordern hingegen koordinierte Updates von Core- und Kundencode. Für **Rollbacks** können VM-Snapshots verwendet
werden, um den gesamten Systemzustand wiederherzustellen, oder durch Zurücksetzen der Image-Tags auf vorherige
Versionen, sofern die Daten kompatibel sind. Die Häufigkeit von Updates und Patches wird durch den Release-Prozess
gesteuert (Major, Minor, Patch).

Das gesamte Überwachungs- und Alarmierungssystem basiert auf **OpenTelemetry (OTel)**, einem herstellerneutralen
Industriestandard. Ein zentraler **OpenTelemetry Collector** empfängt Logs, Metriken und Traces von allen Diensten und
exportiert sie sicher an die gewählten Ziele. Als offiziell unterstütztes Observability-Backend dient **SigNoz**, eine
Open-Source-, OpenTelemetry-native Plattform, die vereinheitlichte Logs, Metriken und Traces in einer Oberfläche
bereitstellt. SigNoz bietet Dashboards für Infrastruktur, KI-Operationen (Modellnutzung, Token-Verbrauch, Kosten pro
Operation), Anwendungsleistung und Log-Analyse. Flexible Alarmierungsfunktionen können für kritische Dienstausfälle,
Leistungsverschlechterung, Ressourcenlimits, Kostenmanagement (ungewöhnlich hoher Token-Verbrauch) und
Sicherheitsereignisse konfiguriert und an Kanäle wie E-Mail, Slack oder Microsoft Teams weitergeleitet werden. Durch die
OTel-Grundlage können Telemetriedaten auch an alternative OTLP-kompatible Backends wie Grafana, Datadog oder **Splunk
(SIEM-Systeme)** exportiert werden, indem lediglich die Collector-Konfiguration angepasst wird.

## 5. Netzwerkanforderungen und Sicherheit

Ein sicherer und reibungsloser Betrieb der KI-Plattform erfordert eine sorgfältige Konfiguration der
Netzwerkkonnektivität und Firewall-Regeln. Der Swiss AI Hub ist darauf ausgelegt, die Angriffsfläche zu minimieren und
gleichzeitig die notwendige Konnektivität für interne und externe Dienste zu gewährleisten.

### Mehrwert und Nutzen: Minimierte Angriffsfläche und geschützte Kommunikation

Für C-Level-Führungskräfte bedeutet eine strikte Netzwerksicherheit den Schutz vor Cyberangriffen und unbefugtem
Zugriff, was die Betriebskontinuität sichert und Compliance-Anforderungen erfüllt. Dies stärkt das Vertrauen in die
IT-Infrastruktur und minimiert finanzielle Risiken. IT-Professionals profitieren von klaren Richtlinien und einer
robusten Architektur, die durch eine minimale Anzahl exponierter Ports und verschlüsselte Kommunikation die Verwaltung
der Netzwerksicherheit vereinfacht und eine hohe Resilienz gewährleistet.

### Konzepte & Prozesse: Standardmässige Ablehnung und sichere Konnektivität

Das System verwendet eine standardmässige Ablehnungsrichtlinie (Default Deny Policy) auf Netzwerkebene, um alle
eingehenden Verbindungen ausser den explizit benötigten Ports zu blockieren. Alle externen Verbindungen zu KI-Modellen
und Unternehmenssystemen erfolgen ausschliesslich über HTTPS (Port 443) mit strikter Zertifikatsvalidierung. Die
Plattform unterstützt zudem die Anbindung an Microsoft-Dienste für Authentifizierung und Benutzerverwaltung über
bewährte Protokolle.

### Technische Umsetzung im Swiss AI Hub: Firewall, Traefik und sichere Endpunkte

Produktions-Deployments des Swiss AI Hub stellen nur wenige eingehende Ports bereit, um die Angriffsfläche zu
minimieren. **Eingehende Firewall-Regeln** beschränken den Zugriff typischerweise auf:

- Port 443 (TCP) für den primären Zugriff auf Web-UI und Chat-Oberfläche.
- Port 80 (TCP) für ACME/Let's Encrypt Validierung und HTTP-zu-HTTPS-Weiterleitung.
- Port 22 (TCP) für den administrativen SSH-Zugriff, wobei dieser auf bestimmte Administrator-IP-Adressen oder
  VPN-Bereiche beschränkt werden sollte.

**Ausgehende Firewall-Regeln** ermöglichen Verbindungen auf:

- Port 443 (TCP) für API-Aufrufe an LLM-Anbieter (wie Azure OpenAI, Google Gemini, Jina AI, Hugging Face) und andere
  externe Unternehmensdienste (wie SharePoint, Confluence, kundenspezifische REST/SOAP-APIs).
- Port 80 (TCP) für Let's Encrypt Zertifikatvalidierung.
- Port 53 (UDP) für DNS-Auflösung.

Der **Traefik Reverse Proxy** fungiert als einziger extern zugänglicher Entry Point. Er terminiert TLS, wendet Rate
Limiting zum Schutz vor Brute-Force- und einfachen Denial-of-Service (DoS)-Angriffen an. Die
**Benutzerauthentifizierung** und -verwaltung erfolgt über Microsoft Entra ID (`login.microsoftonline.com` für OAuth2,
`graph.microsoft.com` für Benutzerprofile). Alle Verbindungen von der AI-Hub-VM zu externen Diensten nutzen HTTPS (Port
443). Die interne Kommunikation zwischen Docker-Containern im internen Docker-Netzwerk ist durch Netzwerkisolation
geschützt, aber auf Anwendungsebene nicht standardmässig verschlüsselt, was bei Multi-Host-Deployments zusätzliche
Massnahmen erfordern könnte.
