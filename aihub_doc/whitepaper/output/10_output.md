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

### Konzepte & Prozesse: Single-Tenant-Isolation und Air-Gapped-Fähigkeit

Der Swiss AI Hub ist primär für **Single-Tenant-Bereitstellungen** konzipiert. Jede Organisation erhält dabei eine
vollständige, eigenständige Instanz der Plattform mit dedizierten Datenbanken, Vektor-Stores, Dateispeichern und allen
Anwendungsdiensten. Dies gewährleistet eine strikte Isolation der Daten und Ressourcen, im Gegensatz zu
Multi-Tenant-SaaS-Plattformen, bei denen Ressourcen oft geteilt werden. Diese Architektur erlaubt auch den Betrieb in
**Air-Gapped-Umgebungen**, d.h. die Plattform kann vollständig ohne ausgehende Internetverbindung betrieben werden,
sofern lokal gehostete Sprachmodelle (LLMs) verwendet werden. Bei **Multi-Tenant-Bereitstellungen** teilen sich mehrere
isolierte Instanzen optional gemeinsame, zustandslose LLM-Backend-Ressourcen, wobei der konversationelle Kontext und
Benutzerdaten stets innerhalb der jeweiligen Tenant-Instanz verbleiben.

### Technische Umsetzung im Swiss AI Hub: On-Premise, Private Cloud und Schweizer SaaS

Der Swiss AI Hub kann flexibel gehostet werden:

- **On-Premise (eigener Server):** Organisationen betreiben den AI Hub auf ihren eigenen Servern in ihrem Rechenzentrum.
  Die gesamte Infrastruktur, einschliesslich CPU, RAM, Speicher und optional NVIDIA-GPUs für lokale LLM-Inferenz, liegt
  in der vollständigen Kontrolle des Kunden. Dies ermöglicht einen Air-Gapped-Betrieb und eliminiert jegliche
  Cloud-Abhängigkeit.
- **Private Cloud (eigene Cloud):** Die Bereitstellung erfolgt in der eigenen Cloud-Umgebung des Kunden, sei es bei
  einem Schweizer Cloud-Anbieter oder Hyperscaler wie Azure, AWS oder GCP. Dabei bleiben alle Daten im Cloud-Konto des
  Kunden und unter dessen Kontrolle, mit der Option, spezifische Regionen (z.B. Schweiz) für die Datenresidenz zu
  wählen.
- **SaaS (Schweizer Cloud-Hosting):** Als Alternative zu einer selbstverwalteten Bereitstellung bietet die bbv als
  Plattformanbieter das Hosting und die Verwaltung des AI Hub auf einer Schweizer Cloud-Infrastruktur an. In diesem Fall
  kümmert sich bbv um Bereitstellung, Updates, Backups und Monitoring, wobei die Daten stets in der Schweiz und unter
  Schweizer Rechtshoheit verbleiben.

Hybrid-Deployments, bei denen beispielsweise die Datenaufnahme On-Premise erfolgt und bestimmte LLM-Dienste in der Cloud
genutzt werden, sind ebenfalls konfigurierbar. Die Datenisolation ist ein Kernmerkmal: Die Daten jedes Tenants bleiben
in der jeweiligen Instanz. Es gibt keine gemeinsame Datenbank oder gemeinsamen Vektor-Store zwischen Organisationen, was
die Anforderungen des revDSG und der DSGVO an die Datenisolation vollständig erfüllt.

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

Die Plattform kann mit einem einzigen Befehl mittels Docker Compose bereitgestellt werden. Dieser optimierte Prozess
macht die initiale Einrichtung einfach und schnell. Die zugrunde liegende Architektur des Swiss AI Hub ist
**ereignisgesteuert und zustandslos**, was eine inhärente horizontale Skalierbarkeit ermöglicht. Agentenlogiken
enthalten keinen veränderbaren Zustand, wodurch jede Instanz jedes Ereignis verarbeiten kann. Ereignisse werden zur
parallelen Verarbeitung über mehrere Agenteninstanzen verteilt, und die Messaging-Infrastruktur gleicht die Arbeit
automatisch aus. Fehlgeschlagene Operationen werden durch Ereigniswiederholung erneut versucht, was eine hohe
Systemresilienz gewährleistet.

### Technische Umsetzung im Swiss AI Hub: Docker Compose, Kernkomponenten und horizontale Skalierung

Die Bereitstellung erfolgt über eine `docker compose`-Datei (`docker-compose.latest.yml` für Produktion,
`docker-compose.local.yml` für lokale Entwicklung). Nach dem Erstellen einer `.env`-Datei mit den notwendigen
Konfigurationen (Domain, Authentifizierung, LLM-Zugriff, Zugangsdaten) lässt sich die gesamte Plattform mit
`docker compose up -d` starten. Dieser Befehl lädt alle notwendigen Docker-Images herunter, erstellt Netzwerke und
Volumes und startet alle Dienste.

Die Plattform umfasst Kernkomponenten wie:

- **Web Interface (aihub-web)**, **API (aihub-api)**
- **Authentifizierungsservices**
- **Datenbanken** (FerretDB/PostgreSQL für persistente Daten, Valkey (Redis-kompatibel) für Caching/Sitzungsstatus)
- **Vektordatenbank** (Milvus)
- **LLM-Proxy** (LiteLLM)
- **Dokumentenverarbeitung** (Docling)
- **Observability** (Phoenix, OpenTelemetry)
- **Message Queue** (NATS)
- **Speicher** (SeaweedFS S3 Storage)

Der initiale Start dauert in der Regel **3-5 Minuten**, wobei die Dienste initialisiert werden. Für die Skalierung
können zusätzliche Agenteninstanzen bereitgestellt werden, um ein erhöhtes Verarbeitungsvolumen zu bewältigen. Die
Plattform ist auf Containertechnologien aufgebaut, was im Kontext einer Kubernetes-Umgebung **Auto-Scaling** prinzipiell
ermöglicht, obwohl die bereitgestellte Dokumentation den `docker compose`-Ansatz als Standard hervorhebt und die
operative Skalierung durch das manuelle Hinzufügen von Worker-Instanzen beschreibt. Der Swiss AI Hub nutzt
standardmässig PostgreSQL und FerretDB (MongoDB-kompatibel); MSSQL oder Oracle werden in der Quelldokumentation nicht
explizit als unterstützte Datenbanken erwähnt.

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
Das Kostenmanagement verfolgt die Token-Nutzung pro Tenant und Benutzer über alle LLM-Anbieter hinweg und ermöglicht die
Durchsetzung von Budgets und Ratenbegrenzungen.

### Technische Umsetzung im Swiss AI Hub: LiteLLM und Multi-Provider-Unterstützung

Der LiteLLM-Proxy bietet eine OpenAI-kompatible API, die eine breite Palette von Modellen unterstützt. Dazu gehören
kommerzielle Anbieter wie **Azure OpenAI und Google Gemini**, aber auch selbst gehostete Open-Source-Modelle über
Lösungen wie **vLLM, llama.cpp oder HF-TEI**. Dies ermöglicht auch den Betrieb in Air-Gapped-Umgebungen ohne
Internetverbindung, indem nur lokale Modelle genutzt werden. Die Plattform kann problemlos mehrere LLM-Anbieter
gleichzeitig nutzen und Anfragen intelligent zwischen ihnen routen, beispielsweise für Kostenoptimierung oder den
Einsatz spezialisierter Modelle.

Automatisierte Failover-Routinen können konfiguriert werden, indem mehrere LLM-Provider oder lokale Instanzen parallel
genutzt werden. Fällt ein Dienst aus, kann LiteLLM Anfragen an einen verfügbaren alternativen Provider umleiten, was die
Ausfallsicherheit erheblich steigert. LiteLLM verfolgt detailliert die API-Nutzung pro Tenant und Benutzer,
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
  Application Endpoint Checks, Synthetic Probes).
- **Metriken:** Quantitative Messungen von Leistung und Ressourcennutzung (Infrastruktur- und Anwendungsmetriken).
- **Logs:** Detaillierte, chronologische Aufzeichnungen jedes Ereignisses für die Ursachenanalyse (Application,
  Container, Request, Security Logs).

### Technische Umsetzung im Swiss AI Hub: Backup-Mechanismen, Versionsverwaltung und OpenTelemetry

Jede Tenant-Instanz verfügt über unabhängige Backups. Für **Backups** können entweder VM-Snapshots des gesamten Systems
oder komponentenbasiertes Backup der einzelnen Datenspeicher (PostgreSQL, FerretDB, Milvus, SeaweedFS, Valkey, NATS,
etcd, Konfiguration) verwendet werden. Für PostgreSQL wird `pg_basebackup` für vollständige Backups und WAL-Archivierung
für Point-in-Time-Recovery empfohlen. Milvus-Vektor-Embeddings können aus S3-kompatiblem Speicher exportiert oder bei
Bedarf aus Quelldokumenten neu generiert werden. Die Sicherung der Konfiguration umfasst Umgebungsvariablen und
SSL-Zertifikate, wobei Backups verschlüsselt und Schlüssel separat gespeichert werden sollten. Konkrete
**RPO/RTO-Garantien** werden in der Dokumentation nicht explizit genannt, jedoch bilden die Backup-Strategien die
Grundlage für deren Definition.

Die Kernplattform und kundenspezifischer Code verwenden **semantische Versionierung** und können unabhängig aktualisiert
werden. Abwärtskompatible Updates können durch Aktualisierung der Docker-Image-Tags und Neustart der Services erfolgen.
Major-Updates mit Breaking Changes erfordern eine koordinierte Aktualisierung von Core- und kundenspezifischem Code. Für
**Rollbacks** können VM-Snapshots verwendet werden, um den gesamten Systemzustand wiederherzustellen, oder durch
Zurücksetzen der Image-Tags auf vorherige Versionen, sofern die Daten kompatibel sind. Die Häufigkeit von Updates und
Patches wird durch den Release-Prozess gesteuert (Major, Minor, Patch).

Das gesamte Überwachungs- und Alarmierungssystem basiert auf **OpenTelemetry (OTel)**. Ein zentraler OpenTelemetry
Collector empfängt Logs, Metriken und Traces von allen Diensten und exportiert sie sicher an die gewählten Ziele. Als
offiziell unterstütztes Observability-Backend dient **SigNoz**, eine Open-Source-, OpenTelemetry-native Plattform, die
vereinheitlichte Logs, Metriken und Traces in einer Oberfläche bereitstellt. SigNoz bietet Dashboards für Infrastruktur,
KI-Operationen (Modellnutzung, Token-Verbrauch, Kosten pro Operation), Anwendungsleistung und Log-Analyse. Flexible
Alarmierungsfunktionen für kritische Dienstausfälle, Leistungsverschlechterung, Ressourcenlimits, Kostenmanagement und
Sicherheitsereignisse können konfiguriert und an E-Mail, Slack oder Microsoft Teams weitergeleitet werden. Durch die
OTel-Grundlage können Telemetriedaten auch an alternative OTLP-kompatible Backends wie Grafana, Datadog oder **Splunk
(SIEM-Systeme)** exportiert werden, indem lediglich die Collector-Konfiguration angepasst wird.
