```markdown
---
title: Deployment-Optionen
source_sha: "a6f4ab4c22b099e1dbcf4fe1432cad2d020c03e5c5ed2064d49a500804230a5f"
---

# Deployment-Optionen

## Überblick

Der Swiss AI Hub kann als einzelne, isolierte Instanz für eine Organisation oder als mehrere isolierte Instanzen
bereitgestellt (deployed) werden, die optional Backend-LLM-Ressourcen gemeinsam nutzen.

::: info Multi-Tenancy vs. Multi-Instancing
Dieses Kapitel beschreibt **Multi-Instancing** (mehrere isolierte Swiss AI Hub-Instanzen). Für **Multi-Tenancy**
(mehrere organisatorische Grenzen innerhalb einer einzelnen Instanz) siehe [Multi-Tenancy](../../16_multi_tenancy/).

Beide Deployment-Modelle sind gültig und dienen unterschiedlichen Zwecken. Multi-Instancing bietet eine harte Isolation zwischen
Organisationen, während Multi-Tenancy eine logische Trennung innerhalb einer gemeinsam genutzten Plattform-Instanz
ermöglicht.
:::

## Einzelinstanz-Deployment

### Isolierte Instanz

Ein Einzelinstanz-Deployment betreibt eine vollständige, eigenständige Swiss AI Hub-Instanz. Die Organisation erhält eine
dedizierte Infrastruktur: separate Datenbanken, Vektor-Stores, Dateispeicher und Applikations-Services.

Die Instanz umfasst die API, Agents, Pipelines, Weboberfläche und Bot-Integrationen. Sie verfügt über eigene Datenbanken
(FerretDB/PostgreSQL), Vektor-Stores (Milvus) und Dateispeicher (SeaweedFS). Das Monitoring erfolgt über Langfuse und
OpenTelemetry. NATS übernimmt das Event-Streaming. Die Instanz besitzt einen eigenen LiteLLM-Proxy für Kostenverfolgung und
Versionskontrolle.

### LLM-Backend

Die Instanz verbindet sich über ihren LiteLLM-Proxy mit LLM-Services. Nicht-GPU-Deployments werden über die Swiss LLM Cloud
(ein in der Schweiz gehosteter Anbieter) geleitet. GPU-Deployments führen alle Inferenzen lokal über vLLM auf einer
NVIDIA RTX 6000 Pro (96 GB VRAM) aus. Der Proxy verwaltet die Modellauswahl, Budgets, Rate Limits und Versionen. Alle
Prompts, Antworten und Benutzerdaten verbleiben innerhalb der Instanz.

______________________________________________________________________

## Hosting-Optionen

Der Swiss AI Hub kann je nach organisatorischen Anforderungen auf drei Arten gehostet werden.

### On-Premise (Betrieb auf eigenen Servern)

Sie betreiben den Swiss AI Hub auf Ihren eigenen Servern in Ihrem Rechenzentrum.

Sie benötigen x86_64-Server mit CPU, RAM und Speicher. NVIDIA-GPUs eignen sich für selbst gehostete LLM-Inferenzen. Für den
Netzwerkzugriff ist entweder ausgehendes HTTPS für Cloud-basierte LLM-Services oder ein Air-Gap mit lokalen Modellen
erforderlich.

Die Infrastruktur liegt in Ihrer Kontrolle. Keine Cloud-Abhängigkeiten. Funktioniert in Air-Gap-Umgebungen mit
selbst gehosteten LLMs.

______________________________________________________________________

### Private Cloud (Betrieb in eigener Cloud)

Sie betreiben den Swiss AI Hub in Ihrer eigenen Cloud-Umgebung (Schweizer Cloud-Anbieter, Azure, AWS, GCP).

Die Daten verbleiben in Ihrem Cloud-Konto unter Ihrer Kontrolle. Sie wählen die Region (z.B. Schweiz für die
Datenresidenz). Sie verwalten die Cloud-Ressourcen und -Kosten.

Cloud-Anbieter verfügen typischerweise über Sicherheits- und Compliance-Zertifizierungen. Sie benötigen eine
Internetverbindung für den LLM-Proxy-Zugriff (HTTPS), optional VPN für administrativen Zugriff und private Netzwerke
zwischen Services (internes DNS).

______________________________________________________________________

### SaaS (Schweizer Cloud-Hosting)

bbv hostet und verwaltet den Swiss AI Hub für Sie auf Schweizer Cloud-Infrastruktur.

bbv übernimmt die Infrastruktur-Bereitstellung, Updates, Backups, Monitoring und operativen Aufgaben. Daten
verbleiben in der Schweiz unter Schweizer Rechtsprechung. Sicherheits- und Compliance-Zertifizierungen des Cloud-Anbieters.

Sie greifen über eine Weboberfläche und APIs auf den Swiss AI Hub zu. bbv bietet SLAs für Uptime und Support. Weniger
operativer Aufwand für Ihr Team.

______________________________________________________________________

## Multi-Instanz-Deployment

::: tip Wann Multi-Instancing verwenden?
Verwenden Sie mehrere isolierte Instanzen, wenn Sie eine **harte Trennung** zwischen Organisationen mit einer 0%igen
Wahrscheinlichkeit von Datenlecks benötigen. Zum Beispiel eine Krankenversicherung mit einer medizinischen
Prüfungskommission, die streng geheime Daten verarbeitet und eine absolute Isolation von der Hauptversicherungsabteilung
erfordert.

Selbst eine Fehlkonfiguration des Swiss AI Hubs kann keine Datenlecks zwischen Instanzen verursachen. Admins einer
Instanz können eine andere Instanz ohne separaten Login weder konfigurieren noch darauf zugreifen.

Für eine logische Trennung innerhalb einer gemeinsam genutzten Plattform verwenden Sie stattdessen [Multi-Tenancy](../../16_multi_tenancy/).
:::

### Geteiltes LLM-Backend

Beim Deployment mehrerer Instanzen können diese Backend-LLM-Ressourcen gemeinsam nutzen. Mehrere Instanzen können
dieselben Swiss LLM Cloud-Zugangsdaten verwenden oder einen lokalen vLLM-GPU-Server gemeinsam nutzen. Sie können auch
die Authentifizierungsinfrastruktur wie Azure AD oder Keycloak gemeinsam nutzen.

Jede Instanz verfügt weiterhin über einen eigenen LiteLLM-Proxy. Der Proxy verwaltet die Modellauswahl, Budgets, Rate Limits
und Versionen pro Instanz. Die LLM-Nutzung wird pro Instanz erfasst. Prompts, Antworten und Benutzerdaten verbleiben
innerhalb jeder Instanz.

Die geteilten LLM-Backends sind zustandslos. Sie speichern keine Prompts oder Antworten. Konversationeller Kontext und
Historie verbleiben in der eigenen Infrastruktur jeder Instanz.

## Eigenschaften

### Datenisolation

Die Daten jeder Instanz bleiben isoliert. Es gibt keine gemeinsame Datenbank oder keinen gemeinsamen Vektor-Store.
Daten können nicht zwischen Organisationen austreten. Das Setup erfüllt das Schweizer Datenschutzgesetz (revDSG), die
GDPR-Anforderungen an die Datenisolation und die Schweizer Sicherheitsstandards für den öffentlichen Sektor.

::: info Multi-Tenancy innerhalb von Instanzen
Jede Instanz kann auch [Multi-Tenancy](../../16_multi_tenancy/) nutzen, um logische Grenzen für Abteilungen, Kunden
oder Projekte innerhalb dieser Instanz zu schaffen. Multi-Tenancy bietet flexible Zugriffskontrolle bei gleichzeitiger
Aufrechterhaltung einer harten Isolation zwischen den Instanzen.
:::

### Konfiguration

Jede Instanz kann unabhängig konfiguriert werden. Organisationen können benutzerdefinierte Agents, spezialisierte
Pipelines für ihre Datenquellen, eigene Zugriffskontrolle (RBAC, OIDC mit lokalem IdP), benutzerdefinierte Wissensbasen
und dedizierte Authentifizierungsanbieter wie Azure AD oder Keycloak deployen.

### Skalierung und Updates

Die Ressourcenzuweisung erfolgt pro Instanz. Sie skalieren Compute, Arbeitsspeicher und Speicherplatz basierend auf der
tatsächlichen Nutzung. Jede Instanz kann Updates nach eigenem Zeitplan anwenden. Das Testen neuer Funktionen in einer
Instanz beeinträchtigt andere nicht. SLAs variieren je nach Vertrag.

### Compliance und Auditing

Auditoren können die Infrastruktur einer einzelnen Instanz überprüfen. Logs und Traces verbleiben innerhalb der Instanz.
Backup-Aufbewahrungsrichtlinien können pro Instanz konfiguriert werden. Penetrationstests können auf einzelne Instanzen
zugeschnitten werden.

## Deployment-Modell

### Einzelinstanz-Infrastruktur

Ein Einzelinstanz-Deployment enthält:

```

Swiss AI Hub Instance ├── Application Layer │ ├── API Service (FastAPI + WebSocket gateway) │ ├── Web Interface (Nuxt.js
frontend) │ ├── OpenWebUI (LLM chat interface) │ ├── Agent Services (RAG, specialized agents) │ ├── Pipeline Services
(Dagster + custom pipelines) │ └── Bot Service (MS Teams, Slack integrations) │ ├── Data Layer │ ├── Database (FerretDB
\+ PostgreSQL) │ ├── Vector Store (Milvus) │ ├── Document Store (SeaweedFS) │ └── Cache (Valkey) │ ├── LLM Layer │ ├──
LiteLLM Proxy │ │ ├── Cost tracking and budgets │ │ ├── Model routing configuration │ │ ├── Rate limiting │ │ └──
Version control │ └── Presidio (PII anonymization) │ ├── Observability Layer │ ├── Langfuse (LLM tracing, cost tracking,
and evaluation) │ └── OpenTelemetry (distributed tracing) │ └── Infrastructure Layer ├── NATS (message bus) ├── MinerU
(document processing) └── Traefik (reverse proxy + SSL termination)

```

Der LiteLLM-Proxy verbindet sich mit LLM-Services (Swiss LLM Cloud für Nicht-GPU, lokales vLLM für GPU-Deployments).

### Multi-Instanz-Infrastruktur

Beim Deployment mehrerer Instanzen erhält jede Instanz die oben gezeigte Infrastruktur. Sie können Backend-LLM-Ressourcen
gemeinsam nutzen:

```

Shared LLM Backend Resources ├── Cloud LLM Provider │ ├── Swiss LLM Cloud credentials (shared API keys) │ └── Other
cloud provider credentials (optional) │ ├── Self-Hosted Model Infrastructure (GPU) │ └── vLLM deployment (NVIDIA RTX
6000 Pro, 96 GB VRAM) │ └── Optional Shared Services ├── Central Authentication (Azure AD, Keycloak) └── Central
Monitoring Dashboard (optional)

````

Netzwerkarchitektur:

- Jede Instanz verfügt über einen eigenen LiteLLM-Proxy
- Instanz-LiteLLM-Proxys verbinden sich mit geteilten LLM-Backends (Swiss LLM Cloud oder lokales vLLM)
- Geteilte LLM-Backends verwenden gemeinsame API-Zugangsdaten (konfiguriert pro Instanz-LiteLLM)
- Keine direkte Kommunikation zwischen Instanzen
- Optional: Geteilter Authentifizierungsanbieter (Azure AD, Keycloak)

Datenisolation und -souveränität. Unabhängige Skalierung und Ressourcenzuweisung. Benutzerdefinierte Konfigurationen pro
Instanz. Flexible Update-Zeitpläne. Klare Compliance-Grenzen.

______________________________________________________________________

## Architekturdiagramme

### Einzelinstanz-Deployment

```mermaid
graph TB
    subgraph Instance["Swiss AI Hub Instance"]
        Stack["Full Stack<br/>(API, Agents, DB, Vector Store)"]
        Proxy["LiteLLM Proxy"]
        Stack --- Proxy
    end

    Backend["LLM Backend<br/>(Swiss LLM Cloud or local vLLM)"]

    Proxy -->|HTTPS| Backend

    classDef default font-size:16px,padding:20px
````

Die Instanz verbindet sich über ihren LiteLLM-Proxy mit LLM-Services.

### Multi-Instanz-Deployment mit geteiltem LLM-Backend

```mermaid
graph TB
    Backend["Shared LLM Backend<br/>(Swiss LLM Cloud or local vLLM)"]

    subgraph Instance1["Instance 1"]
        I1Stack["Full Stack<br/>(API, Agents, DB, Vector Store)"]
        I1Proxy["LiteLLM Proxy"]
        I1Stack --- I1Proxy
    end

    subgraph Instance2["Instance 2"]
        I2Stack["Full Stack<br/>(API, Agents, DB, Vector Store)"]
        I2Proxy["LiteLLM Proxy"]
        I2Stack --- I2Proxy
    end

    subgraph Instance3["Instance 3"]
        I3Stack["Full Stack<br/>(API, Agents, DB, Vector Store)"]
        I3Proxy["LiteLLM Proxy"]
        I3Stack --- I3Proxy
    end

    I1Proxy -->|HTTPS| Backend
    I2Proxy -->|HTTPS| Backend
    I3Proxy -->|HTTPS| Backend

    classDef default font-size:16px,padding:20px
```

Jede Instanz verfügt über einen eigenen LiteLLM-Proxy (unabhängige Kostenverfolgung, Versionierung, Konfiguration). Alle
Instanz-LiteLLM-Proxys verbinden sich mit geteilten LLM-Backend-Ressourcen (Swiss LLM Cloud oder lokales vLLM). Prompts,
Antworten und Benutzerdaten verbleiben innerhalb der Instanzgrenzen.

______________________________________________________________________

## Sicherheitsüberlegungen

### Instanzisolation

Instanzen kommunizieren nicht miteinander. Jede Instanz verfügt über separate Datenbanken, Vektor-Stores und
Dateispeicher. Jede Instanz verbindet sich mit ihrem eigenen IdP (Azure AD, Keycloak) oder kann einen gemeinsamen IdP
mit separater Namespace-Isolation nutzen. LiteLLM erzwingt API-Schlüssel und Quoten pro Instanz.

### LLM-Proxy-Sicherheit

LiteLLM speichert keine Prompts oder Antworten persistent (zustandsloser Betrieb). Die API-Schlüsselverwaltung umfasst
sichere Schlüsselgenerierung, -rotation und -widerruf. Anfragelimits pro Instanz verhindern Missbrauch. Alle
LLM-Anfragen werden mit Instanz-ID, aber ohne Prompt-Inhalt protokolliert. Die Presidio-Integration ist optional für die
PII-Erkennung und -Redaktion.

### Daten während der Übertragung

Die gesamte Kommunikation ist mit TLS verschlüsselt (Instanz zum LLM-Proxy). Das Zertifikatsmanagement verwendet Let's
Encrypt für die Produktion und mkcert für die Entwicklung. Die API-Authentifizierung nutzt Bearer-Tokens (OAuth 2.0,
JWT).

### Daten im Ruhezustand

PostgreSQL verwendet transparente Datenverschlüsselung (TDE). Persistente Volumes sind verschlüsselt (LUKS, Azure Disk
Encryption). Secrets werden über Umgebungsvariablen, Azure Key Vault oder Docker Secrets verwaltet.

______________________________________________________________________

## Nächste Schritte

- [Multi-Tenancy](../../16_multi_tenancy/) – Logische Trennung innerhalb einer einzelnen Instanz
- [Produktionskonfiguration](../2_production_configuration/) – Konfigurationsanleitung für Produktions-Deployments
- [Skalierungsüberlegungen](../3_scaling_considerations/) – Skalierung von Instanzen
- [Backup und Wiederherstellung](../4_backup_and_recovery/) – Backup-Strategien für die Pro-Instanz-Architektur
- [Updates und Wartung](../6_updates_and_maintenance/) – Verwaltung von Updates über mehrere Instanzen

______________________________________________________________________

## FAQ

::: details Können Instanzen Agents oder Pipelines teilen?
Nein. Jede Instanz verfügt über einen eigenen, isolierten Satz von Agents und Pipelines. Dieselben Agent-Definitionen
(Code) können jedoch über mehrere Instanzen hinweg deployed werden. Anpassungen sind instanzspezifisch.

Um Agents innerhalb einer Organisation zu teilen, verwenden Sie [Multi-Tenancy](../../16_multi_tenancy/), um logische
Grenzen innerhalb einer einzelnen Instanz zu schaffen.
:::

::: details Was ist der Unterschied zwischen Multi-Instancing und Multi-Tenancy?
**Multi-Instancing** (dieses Kapitel) bedeutet den Betrieb mehrerer vollständig isolierter Swiss AI Hub-Installationen.
Jede verfügt über separate Datenbanken, Vektor-Stores und Applikationsserver. Selbst eine Fehlkonfiguration kann keine
Datenlecks zwischen Instanzen verursachen. Verwenden Sie dies, wenn Sie absolute Isolation benötigen (z.B. verschiedene
juristische Einheiten, hochsensible Abteilungen).

**Multi-Tenancy** ([Kapitel 15](../../16_multi_tenancy/)) bedeutet die Schaffung organisatorischer Grenzen innerhalb
einer einzelnen Swiss AI Hub-Instanz. Mehrere Mandanten teilen sich die Infrastruktur, verfügen aber über eine logische
Trennung durch Zugriffskontrolle. Verwenden Sie dies für Abteilungen, Projekte oder Kunden innerhalb derselben
Organisation.

Sie können beides kombinieren: Betreiben Sie mehrere Instanzen (harte Isolation), wobei jede Instanz Multi-Tenancy
(flexible Trennung innerhalb dieser Instanz) nutzt.
:::

::: details Welche Daten sieht das geteilte LLM-Backend?
Jede Instanz verfügt über einen eigenen LiteLLM-Proxy, sodass Prompts und Antworten innerhalb der Instanz verbleiben.
Die geteilten LLM-Backends (Swiss LLM Cloud oder lokales vLLM) sehen API-Anfragen von mehreren Instanz-LiteLLM-Proxys
(zustandslos, nicht persistent gespeichert), Modellinferenzanfragen (Prompts und Completions nur während der
Übertragung), keine Instanzidentifikation oder Kontext und anonyme PII-Daten, falls aktiviert.

Sie sehen nicht, welche Instanz die Anfrage gestellt hat, die Konversationshistorie oder gespeicherte Daten. Der gesamte
Kontext verbleibt im LiteLLM-Proxy und der Datenbank der Instanz.
:::

::: details Kann eine Instanz ausschliesslich selbst gehostete Modelle verwenden?
Ja. Für Air-Gap- oder vollständig On-Premise-Deployments verwenden Sie die GPU-Variante der docker-compose-Datei. Alle
Inferenzen laufen lokal über vLLM auf einer NVIDIA RTX 6000 Pro (96 GB VRAM), ohne dass eine ausgehende
Internetverbindung erforderlich ist.
:::

::: details Wie werden Kosten pro Instanz verfolgt?
LiteLLM verfolgt die API-Nutzung pro Instanz und Benutzer: Token-Zähler (Input/Output), Modellnutzung (GPT-4, Gemini
etc.), Kostenberechnungen basierend auf Modellpreisen und die Durchsetzung monatlicher Budgets.

Die Daten sind in der LiteLLM Admin UI verfügbar und für die Abrechnung exportierbar.
:::

::: details Können Instanzen unterschiedlichen LLM-Zugriff haben?
Ja. Die LiteLLM-Konfiguration erlaubt den modellbasierten Zugriff pro Instanz. Zum Beispiel könnte Instanz A die Swiss
LLM Cloud mit einem spezifischen Satz von Modellen verwenden, Instanz B eine andere Modellauswahl für Flexibilität
nutzen und Instanz C ausschliesslich lokales vLLM für ein Air-Gap-Deployment einsetzen.
:::

::: details Was passiert, wenn der LLM-Proxy nicht verfügbar ist?
Instanzen werden eine Verschlechterung LLM-abhängiger Funktionen erfahren. RAG-Agents können keine Antworten generieren.
Embeddings können nicht für neue Dokumente erstellt werden. Vorhandene Daten und die UI bleiben jedoch zugänglich, und
nicht-LLM-Funktionen (Dokumentenupload, RBAC, Observability) funktionieren weiterhin.

Mitigation: Deployen Sie LiteLLM mit hoher Verfügbarkeit (mehrere Replicas, Load Balancing).
:::

::: details Wie verwalten Sie Updates über viele Instanzen hinweg?
Siehe [Updates und Wartung](../6_updates_and_maintenance/) für Strategien wie gestaffelte Rollouts (Pilot bis
Produktion), Blue-Green Deployments, automatisierte Update-Orchestrierung (Ansible, Kubernetes Operators) und
instanzspezifische Update-Zeitpläne.
:::

## Verwandte Dokumentation

- [Multi-Tenancy](../../16_multi_tenancy/) – Schaffung organisatorischer Grenzen innerhalb einer Instanz
- [Kernkomponenten](../../2_architecture/1_core_components/) – Swiss AI Hub Architektur
- [Authentifizierung & Autorisierung](../../11_access_management/1_authentication_setup/) –
  Authentifizierungskonfiguration
- [Monitoring und Alerting](../5_monitoring_and_alerting/) – Observability für Multi-Instanz-Deployments
- [Schweizer Datenschutz](../../21_compliance/3_dsg/) – revDSG-Compliance für den öffentlichen Sektor

```
```
