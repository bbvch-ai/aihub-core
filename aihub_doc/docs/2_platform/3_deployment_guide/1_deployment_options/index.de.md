---
title: Deployment-Optionen
source_sha: 754fc9dc9040a7df17636be298270e7ae121258d6d85398bdeceb504bff31dd5
---

# Deployment-Optionen

## Überblick

Der AI-Hub kann als einzelne isolierte Instanz für eine Organisation oder als mehrere isolierte Instanzen deployed
werden, die optional Backend-LLM-Ressourcen gemeinsam nutzen.

::: info Multi-Tenancy vs. Multi-Instancing
Dieses Kapitel beschreibt **Multi-Instancing** (mehrere isolierte AI-Hub-Instanzen). Für **Multi-Tenancy** (mehrere
organisatorische Grenzen innerhalb einer einzelnen Instanz) siehe [Multi-Tenancy](/de/docs/16_multi_tenancy/).

Beide Deployment-Modelle sind gültig und dienen unterschiedlichen Zwecken. Multi-Instancing bietet eine harte Isolation
zwischen Organisationen, während Multi-Tenancy eine logische Trennung innerhalb einer gemeinsam genutzten
Plattforminstanz ermöglicht.
:::

## Einzelinstanz-Deployment

### Isolierte Instanz

Ein Einzelinstanz-Deployment betreibt eine vollständige, eigenständige AI-Hub-Instanz. Die Organisation erhält eine
dedizierte Infrastruktur: separate Datenbanken, Vektor-Speicher, Dateispeicher und Anwendungs-Services.

Die Instanz umfasst die API, Agents, Pipelines, das Web-Interface und Bot-Integrationen. Sie verfügt über eigene
Datenbanken (FerretDB/PostgreSQL), Vektor-Speicher (Milvus oder Azure AI Search) und Dateispeicher (SeaweedFS oder Azure
Data Lake). Das Monitoring erfolgt über SigNoz und Langfuse. NATS wickelt das Event-Streaming ab. Die Instanz verfügt
über einen eigenen LiteLLM-Proxy für Kostenverfolgung und Versionskontrolle.

### LLM-Backend

Die Instanz verbindet sich über ihren LiteLLM-Proxy mit LLM-Services. Der Proxy kann sich mit Azure OpenAI, Google
Gemini, selbst gehosteten Modellen (vLLM, llama.cpp, HF-TEI) oder einer Mischung davon verbinden. Der Proxy handhabt
Modell-Auswahl, Budgets, Ratenbegrenzungen und Versionen. Alle Prompts, Antworten und Benutzerdaten bleiben innerhalb
der Instanz.

______________________________________________________________________

## Hosting-Optionen

Der AI-Hub kann je nach organisatorischen Anforderungen auf drei Arten gehostet werden.

### On-Premise (eigene Server)

Sie betreiben den AI-Hub auf Ihren eigenen Servern in Ihrem Rechenzentrum.

Sie benötigen x86_64-Server mit CPU, RAM und Speicher. NVIDIA GPUs funktionieren für selbst gehostete LLM-Inferenz. Für
den Netzwerkzugriff entweder ausgehende HTTPS-Verbindungen für Cloud-basierte LLM-Services oder Air-Gapped mit lokalen
Modellen.

Die Infrastruktur liegt unter Ihrer Kontrolle. Keine Cloud-Abhängigkeiten. Funktioniert in Air-Gapped-Umgebungen mit
selbst gehosteten LLMs.

______________________________________________________________________

### Private Cloud (eigene Cloud)

Sie betreiben den AI-Hub in Ihrer eigenen Cloud-Umgebung (Schweizer Cloud-Anbieter, Azure, AWS, GCP).

Die Daten bleiben in Ihrem Cloud-Konto unter Ihrer Kontrolle. Sie wählen die Region (z.B. Schweiz für die
Datenresidenz). Sie verwalten die Cloud-Ressourcen und -Kosten.

Cloud-Anbieter verfügen typischerweise über Sicherheits- und Compliance-Zertifizierungen. Sie benötigen
Internetverbindung für den LLM-Proxy-Zugriff (HTTPS), optional VPN für administrativen Zugriff und privates Netzwerk
zwischen Services (internes DNS).

______________________________________________________________________

### SaaS (Schweizer Cloud-Hosting)

bbv hostet und verwaltet den AI-Hub für Sie auf einer in der Schweiz basierenden Cloud-Infrastruktur.

bbv übernimmt die Infrastruktur-Bereitstellung, Updates, Backups, Monitoring und operative Aufgaben. Die Daten bleiben
in der Schweiz unter Schweizer Rechtsordnung. Sicherheits- und Compliance-Zertifizierungen vom Cloud-Anbieter.

Sie greifen über ein Web-Interface und APIs auf den AI-Hub zu. bbv bietet SLAs für Verfügbarkeit und Support. Weniger
operativer Aufwand für Ihr Team.

______________________________________________________________________

## Multi-Instanz-Deployment

::: tip Wann Multi-Instancing verwenden
Verwenden Sie mehrere isolierte Instanzen, wenn Sie eine **harte Trennung** zwischen Organisationen mit 0% Datenlecks
benötigen. Zum Beispiel eine Krankenversicherungsgesellschaft mit einer medizinischen Prüfungskommission, die streng
geheime Daten verarbeitet, die eine absolute Isolation von der Hauptversicherungsabteilung erfordern.

Selbst eine Fehlkonfiguration des AI-Hub kann keine Datenlecks zwischen Instanzen verursachen. Admins einer Instanz
können ohne separate Anmeldung keine andere Instanz konfigurieren oder darauf zugreifen.

Für die logische Trennung innerhalb einer gemeinsam genutzten Plattform verwenden Sie stattdessen
[Multi-Tenancy](/de/docs/16_multi_tenancy/).
:::

### Gemeinsames LLM-Backend

Beim Deployment mehrerer Instanzen können diese Backend-LLM-Ressourcen gemeinsam nutzen. Mehrere Instanzen verwenden
dasselbe Azure OpenAI-Abonnement, Google Gemini API-Schlüssel oder selbst gehostete Modelle. Sie können auch
Authentifizierungs-Infrastrukturen wie Azure AD oder Keycloak gemeinsam nutzen.

Jede Instanz hat weiterhin ihren eigenen LiteLLM-Proxy. Der Proxy handhabt Modell-Auswahl, Budgets, Ratenbegrenzungen
und Versionen pro Instanz. Die LLM-Nutzung wird pro Instanz verfolgt. Prompts, Antworten und Benutzerdaten bleiben
innerhalb jeder Instanz.

Die gemeinsam genutzten LLM-Backends sind zustandslos. Sie persistieren keine Prompts oder Antworten. Der
Konversationskontext und die Historie bleiben in der eigenen Infrastruktur jeder Instanz.

## Eigenschaften

### Datenisolation

Die Daten jeder Instanz bleiben isoliert. Es gibt keine gemeinsame Datenbank oder Vektor-Speicher. Daten können nicht
zwischen Organisationen austreten. Die Einrichtung erfüllt das Schweizer Datenschutzgesetz (revDSG), die
GDPR-Datenisolationsanforderungen und die Sicherheitsstandards des Schweizer öffentlichen Sektors.

::: info Multi-Tenancy innerhalb von Instanzen
Jede Instanz kann auch [Multi-Tenancy](/de/docs/16_multi_tenancy/) verwenden, um logische Grenzen für Abteilungen,
Kunden oder Projekte innerhalb dieser Instanz zu schaffen. Multi-Tenancy bietet eine flexible Zugriffssteuerung, während
die harte Isolation zwischen Instanzen erhalten bleibt.
:::

### Konfiguration

Jede Instanz kann unabhängig konfiguriert werden. Organisationen können benutzerdefinierte Agents, spezialisierte
Pipelines für ihre Datenquellen, ihre eigene Zugriffssteuerung (RBAC, OIDC mit lokalem IdP), benutzerdefinierte
Wissensdatenbanken und dedizierte Authentifizierungs-Provider wie Azure AD oder Keycloak deployen.

### Skalierung und Updates

Die Ressourcenzuweisung erfolgt pro Instanz. Sie skalieren Rechenleistung, Arbeitsspeicher und Speicher basierend auf
der tatsächlichen Nutzung. Jede Instanz kann Updates nach eigenem Zeitplan anwenden. Das Testen neuer Funktionen in
einer Instanz beeinflusst andere nicht. SLAs variieren je nach Vertrag.

### Compliance und Auditing

Auditoren können die Infrastruktur einer einzelnen Instanz überprüfen. Logs und Traces bleiben innerhalb der Instanz.
Backup-Aufbewahrungsrichtlinien können pro Instanz konfiguriert werden. Penetrationstests können auf einzelne Instanzen
zugeschnitten werden.

## Deployment-Modell

### Einzelinstanz-Infrastruktur

Ein Einzelinstanz-Deployment enthält:

```
AI-Hub Instance
├── Application Layer
│   ├── API Service (FastAPI + WebSocket gateway)
│   ├── Web Interface (Nuxt.js frontend)
│   ├── OpenWebUI (LLM chat interface)
│   ├── Agent Services (RAG, specialized agents)
│   ├── Pipeline Services (Dagster + custom pipelines)
│   └── Bot Service (MS Teams, Slack integrations)
│
├── Data Layer
│   ├── Database (FerretDB + PostgreSQL)
│   ├── Vector Store (Milvus or Azure AI Search)
│   ├── Document Store (SeaweedFS or Azure Data Lake)
│   └── Cache (Valkey)
│
├── LLM Layer
│   ├── LiteLLM Proxy
│   │   ├── Cost tracking and budgets
│   │   ├── Model routing configuration
│   │   ├── Rate limiting
│   │   └── Version control
│   └── Presidio (PII anonymization)
│
├── Observability Layer
│   ├── Langfuse (AI tracing and evaluation)
│   └── OpenTelemetry (distributed tracing)
│
└── Infrastructure Layer
    ├── NATS (message bus)
    ├── Docling (document processing)
    └── Traefik (reverse proxy + SSL termination)
```

Der LiteLLM-Proxy verbindet sich mit LLM-Services (Azure OpenAI, Google Gemini, selbst gehostete Modelle).

### Multi-Instanz-Infrastruktur

Beim Deployment mehrerer Instanzen erhält jede Instanz die oben gezeigte Infrastruktur. Sie können
Backend-LLM-Ressourcen gemeinsam nutzen:

```
Shared LLM Backend Resources
├── LLM API Subscriptions
│   ├── Azure OpenAI subscription (shared API keys)
│   ├── Google Gemini API keys
│   └── Other cloud provider credentials
│
├── Self-Hosted Model Infrastructure
│   ├── vLLM deployment (GPU cluster)
│   ├── llama.cpp servers
│   └── HF-TEI instances
│
└── Optional Shared Services
    ├── Central Authentication (Azure AD, Keycloak)
    └── Central Monitoring Dashboard (optional)
```

Netzwerk-Architektur:

- Jede Instanz hat ihren eigenen LiteLLM-Proxy
- Instanz-LiteLLM-Proxys verbinden sich mit gemeinsam genutzten LLM-Backends (Azure OpenAI, Gemini, selbst gehostete
  Modelle)
- Gemeinsam genutzte LLM-Backends verwenden gemeinsame API-Anmeldeinformationen (konfiguriert pro LiteLLM der Instanz)
- Keine direkte Kommunikation zwischen Instanzen
- Optional: Gemeinsamer Authentifizierungs-Provider (Azure AD, Keycloak)

Datenisolation und -souveränität. Unabhängige Skalierung und Ressourcenzuweisung. Benutzerdefinierte Konfigurationen pro
Instanz. Flexible Update-Zeitpläne. Klare Compliance-Grenzen.

______________________________________________________________________

## Architektur-Diagramme

### Einzelinstanz-Deployment

```mermaid
graph TB
    subgraph Instance["AI-Hub Instance"]
        Stack["Full Stack<br/>(API, Agents, DB, Vector Store)"]
        Proxy["LiteLLM Proxy"]
        Stack --- Proxy
    end

    Backend["LLM Backend<br/>(Azure OpenAI, Gemini, vLLM)"]

    Proxy -->|HTTPS| Backend

    classDef default font-size:16px,padding:20px
```

Die Instanz verbindet sich über ihren LiteLLM-Proxy mit LLM-Services.

### Multi-Instanz-Deployment mit gemeinsamem LLM-Backend

```mermaid
graph TB
    Backend["Shared LLM Backend<br/>(Azure OpenAI, Gemini, vLLM)"]

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

Jede Instanz hat ihren eigenen LiteLLM-Proxy (unabhängige Kostenverfolgung, Versionierung, Konfiguration). Alle
Instanz-LiteLLM-Proxys verbinden sich mit gemeinsam genutzten LLM-Backend-Ressourcen (Azure OpenAI-Abonnements, selbst
gehostete Modelle). Prompts, Antworten und Benutzerdaten bleiben innerhalb der Instanzgrenzen.

______________________________________________________________________

## Sicherheitsüberlegungen

### Instanz-Isolation

Instanzen kommunizieren nicht miteinander. Jede Instanz verfügt über separate Datenbanken, Vektor-Speicher und
Dateispeicher. Jede Instanz verbindet sich mit ihrem eigenen IdP (Azure AD, Keycloak) oder kann einen gemeinsamen IdP
mit separater Namespace-Isolation nutzen. LiteLLM erzwingt pro-Instanz API-Schlüssel und Quoten.

### LLM-Proxy-Sicherheit

LiteLLM persistiert keine Prompts oder Antworten (zustandsloser Betrieb). Das API-Schlüssel-Management umfasst sichere
Schlüsselgenerierung, -rotation und -widerruf. Pro-Instanz Anforderungslimits verhindern Missbrauch. Alle LLM-Anfragen
werden mit Instanz-ID, aber ohne Prompt-Inhalt protokolliert. Die Presidio-Integration ist optional für PII-Erkennung
und -Redaktion.

### Daten während der Übertragung

Alle Kommunikation ist mit TLS verschlüsselt (Instanz zu LLM-Proxy). Die Zertifikatsverwaltung verwendet Let's Encrypt
für die Produktion und mkcert für die Entwicklung. Die API-Authentifizierung verwendet Bearer-Tokens (OAuth 2.0, JWT).

### Daten im Ruhezustand

PostgreSQL verwendet transparente Datenverschlüsselung (TDE). Persistente Volumes sind verschlüsselt (LUKS, Azure Disk
Encryption). Secrets werden über Umgebungsvariablen, Azure Key Vault oder Docker-Secrets verwaltet.

______________________________________________________________________

## Nächste Schritte

- [Multi-Tenancy](/de/docs/16_multi_tenancy/) – Logische Trennung innerhalb einer einzelnen Instanz
- [Produktionskonfiguration](/de/docs/deployment_options/2_production_configuration/) – Konfigurationsanleitung für
  Produktions-Deployments
- [Skalierungsüberlegungen](/de/docs/deployment_options/3_scaling_considerations/) – Skalierung von Instanzen
- [Backup und Wiederherstellung](/de/docs/deployment_options/4_backup_and_recovery/) – Backup-Strategien für die
  Pro-Instanz-Architektur
- [Updates und Wartung](/de/docs/deployment_options/6_updates_and_maintenance/) – Verwaltung von Updates über mehrere
  Instanzen hinweg

______________________________________________________________________

## FAQ

::: details Können Instanzen Agents oder Pipelines gemeinsam nutzen?
Nein. Jede Instanz hat ihren eigenen isolierten Satz von Agents und Pipelines. Die gleichen Agent-Definitionen (Code)
können jedoch über mehrere Instanzen hinweg deployed werden. Anpassungen sind instanzspezifisch.

Zum Teilen von Agents innerhalb einer Organisation verwenden Sie [Multi-Tenancy](/de/docs/16_multi_tenancy/), um
logische Grenzen innerhalb einer einzelnen Instanz zu schaffen.
:::

::: details Was ist der Unterschied zwischen Multi-Instancing und Multi-Tenancy?
**Multi-Instancing** (dieses Kapitel) bedeutet den Betrieb mehrerer vollständig isolierter AI-Hub-Installationen. Jede
hat separate Datenbanken, Vektor-Speicher und Anwendungs-Server. Selbst eine Fehlkonfiguration kann keine Datenlecks
zwischen Instanzen verursachen. Verwenden Sie dies, wenn Sie absolute Isolation benötigen (z.B. verschiedene juristische
Entitäten, hochsensible Abteilungen).

**Multi-Tenancy** ([Kapitel 15](/de/docs/16_multi_tenancy/)) bedeutet die Schaffung organisatorischer Grenzen innerhalb
einer einzelnen AI-Hub-Instanz. Mehrere Mandanten teilen sich die Infrastruktur, haben aber eine logische Trennung durch
Zugriffssteuerung. Verwenden Sie dies für Abteilungen, Projekte oder Kunden innerhalb derselben Organisation.

Sie können beides kombinieren: Betreiben Sie mehrere Instanzen (harte Isolation), wobei jede Instanz Multi-Tenancy
(flexible Trennung innerhalb dieser Instanz) verwendet.
:::

::: details Welche Daten sieht das gemeinsam genutzte LLM-Backend?
Jede Instanz hat ihren eigenen LiteLLM-Proxy, sodass Prompts und Antworten innerhalb der Instanz bleiben. Die gemeinsam
genutzten LLM-Backends (Azure OpenAI, Gemini, selbst gehostete Modelle) sehen API-Anfragen von mehreren
Instanz-LiteLLM-Proxys (zustandslos, nicht persistent), Modell-Inferenzanfragen (Prompts und Completions nur während der
Übertragung), keine Instanzidentifikation oder Kontext und anonyme PII-Daten, falls aktiviert.

Sie sehen nicht, welche Instanz die Anfrage gestellt hat, die Konversationshistorie oder gespeicherte Daten. Der gesamte
Kontext bleibt im LiteLLM-Proxy und der Datenbank der Instanz.
:::

::: details Kann eine Instanz ausschliesslich selbst gehostete Modelle verwenden?
Ja. Für Air-Gapped- oder vollständig On-Premise-Deployments können Sie selbst gehostete LLMs (vLLM, llama.cpp, HF-TEI)
deployen, LiteLLM so konfigurieren, dass es an lokale Modelle weiterleitet, und ohne erforderliche ausgehende
Internetverbindung betreiben.
:::

::: details Wie werden Kosten pro Instanz verfolgt?
LiteLLM verfolgt die API-Nutzung pro Instanz und Benutzer: Token-Zählungen (Eingabe/Ausgabe), Modellnutzung (GPT-4,
Gemini usw.), Kostenberechnungen basierend auf Modellpreisen und monatliche Budgetdurchsetzung.

Die Daten sind im LiteLLM Admin-UI verfügbar und für die Abrechnung exportierbar.
:::

::: details Können Instanzen unterschiedlichen LLM-Zugriff haben?
Ja. Die LiteLLM-Konfiguration erlaubt den modellzugriff pro Instanz. Zum Beispiel könnte Instanz A nur GPT-4o für
strikte Compliance verwenden, Instanz B könnte GPT-4o plus Gemini 2.0 für mehr Flexibilität verwenden, und Instanz C
könnte ausschliesslich selbst gehostete Modelle für ein Air-Gapped-Deployment verwenden.
:::

::: details Was passiert, wenn der LLM-Proxy nicht verfügbar ist?
Instanzen werden eine Verschlechterung der LLM-abhängigen Funktionen erfahren. RAG-Agents können keine Antworten
generieren. Embeddings können für neue Dokumente nicht erstellt werden. Bestehende Daten und die UI bleiben jedoch
zugänglich, und Nicht-LLM-Funktionen (Dokumentenupload, RBAC, Observability) funktionieren weiterhin.

Abhilfe: Deployen Sie LiteLLM mit Hochverfügbarkeit (mehrere Replikate, Lastverteilung).
:::

::: details Wie verwalten Sie Updates über viele Instanzen hinweg?
Siehe [Updates und Wartung](/de/docs/deployment_options/6_updates_and_maintenance/) für Strategien, einschliesslich
gestaffelter Rollouts (Pilot zu Produktion), Blue-Green Deployments, automatisierter Update-Orchestrierung (Ansible,
Kubernetes-Operatoren) und pro-Instanz Update-Zeitplänen.
:::

## Verwandte Dokumentation

- [Multi-Tenancy](/de/docs/16_multi_tenancy/) – Schaffung organisatorischer Grenzen innerhalb einer Instanz
- [Kernkomponenten](/de/docs/2_architecture/1_core_components/) – AI-Hub-Architektur
- [Authentifizierung & Autorisierung](/de/docs/11_access_management/1_authentication_setup/) –
  Authentifizierungskonfiguration
- [Monitoring und Alerting](/de/docs/deployment_options/5_monitoring_and_alerting/) – Observability für
  Multi-Instanz-Deployments
- [Schweizer Datenschutz](/de/docs/21_compliance/3_dsg/) – revDSG-Compliance für den öffentlichen Sektor
