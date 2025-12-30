---
title: Deployment-Optionen
source_sha: e7111cdf8eca6cf23dd8fcc8e9f72a59acce6f872abc6ab038f76d64cf6c2e7b
---

# Deployment-Optionen

## Überblick

Der AI-Hub kann als eine einzelne isolierte Instanz für eine Organisation deployed werden, oder als mehrere isolierte
Instanzen, die optional Backend-LLM-Ressourcen teilen.

::: info Multi-Tenancy vs. Multi-Instancing
Dieses Kapitel beschreibt **Multi-Instancing** (mehrere isolierte AI-Hub-Instanzen). Für **Multi-Tenancy** (mehrere
organisatorische Grenzen innerhalb einer einzelnen Instanz), siehe [Multi-Tenancy](../../15_multi_tenancy/).

Beide Deployment-Modelle sind gültig und dienen unterschiedlichen Zwecken. Multi-Instancing bietet eine harte Isolation
zwischen Organisationen, während Multi-Tenancy eine logische Trennung innerhalb einer gemeinsam genutzten
Plattforminstanz ermöglicht.
:::

## Einzelinstanz-Deployment

### Isolierte Instanz

Ein Einzelinstanz-Deployment betreibt eine vollständige, eigenständige AI-Hub-Instanz. Die Organisation erhält eine
dedizierte Infrastruktur: separate Datenbanken, Vector Stores, Dateispeicher und Anwendungs-Services.

Die Instanz umfasst die API, Agents, Pipelines, das Webinterface und Bot-Integrationen. Sie verfügt über eigene
Datenbanken (FerretDB/PostgreSQL), Vector Stores (Milvus oder Azure AI Search) und Dateispeicher (SeaweedFS oder Azure
Data Lake). Das Monitoring erfolgt über SigNoz und Phoenix. NATS wickelt das Event Streaming ab. Die Instanz besitzt
einen eigenen LiteLLM-Proxy für Kosten-Tracking und Versionskontrolle.

### LLM-Backend

Die Instanz verbindet sich über ihren LiteLLM-Proxy mit LLM-Services. Der Proxy kann sich mit Azure OpenAI, Google
Gemini, selbst gehosteten Modellen (vLLM, llama.cpp, HF-TEI) oder einer Mischung davon verbinden. Der Proxy handhabt die
Modellauswahl, Budgets, Ratenbegrenzungen und Versionen. Alle Prompts, Responses und Benutzerdaten verbleiben innerhalb
der Instanz.

---

## Hosting-Optionen

Der AI-Hub kann je nach den organisatorischen Anforderungen auf drei Arten gehostet werden.

### On-Premise (Eigene Server)

Sie betreiben den AI-Hub auf Ihren eigenen Servern in Ihrem Rechenzentrum.

Sie benötigen x86_64-Server mit CPU, RAM und Speicherplatz. NVIDIA GPUs eignen sich für selbst gehostete LLM-Inferenz.
Für den Netzwerkzugriff entweder ausgehendes HTTPS für Cloud-basierte LLM-Services oder Air-Gapped mit lokalen Modellen.

Die Infrastruktur liegt unter Ihrer Kontrolle. Keine Cloud-Abhängigkeiten. Funktioniert in Air-Gapped-Umgebungen mit
selbst gehosteten LLMs.

---

### Private Cloud (Eigene Cloud)

Sie betreiben den AI-Hub in Ihrer eigenen Cloud-Umgebung (Schweizer Cloud-Provider, Azure, AWS, GCP).

Daten verbleiben in Ihrem Cloud-Konto unter Ihrer Kontrolle. Sie wählen die Region (z.B. Schweiz für Datenresidenz). Sie
verwalten die Cloud-Ressourcen und -Kosten.

Cloud-Provider verfügen typischerweise über Sicherheits- und Compliance-Zertifizierungen. Sie benötigen
Internetkonnektivität für den LLM-Proxy-Zugriff (HTTPS), optional VPN für administrativen Zugriff und privates Netzwerk
zwischen Services (internes DNS).

---

### SaaS (Schweizer Cloud-Hosting)

bbv hostet und verwaltet den AI-Hub für Sie auf einer in der Schweiz ansässigen Cloud-Infrastruktur.

bbv übernimmt die Infrastrukturbereitstellung, Updates, Backups, das Monitoring und die operativen Aufgaben. Die Daten
verbleiben in der Schweiz unter Schweizer Rechtsprechung. Sicherheits- und Compliance-Zertifizierungen des
Cloud-Providers.

Sie greifen über ein Webinterface und APIs auf den AI-Hub zu. bbv bietet SLAs für Uptime und Support. Weniger
operationaler Overhead für Ihr Team.

---

## Multi-Instanz-Deployment

::: tip Wann Multi-Instancing verwenden
Verwenden Sie mehrere isolierte Instanzen, wenn Sie eine **harte Trennung** zwischen Organisationen mit 0% Datenlecks
benötigen. Zum Beispiel eine Krankenversicherung mit einer medizinischen Prüfungskommission, die streng geheime Daten
verarbeitet, die eine absolute Isolation von der Hauptversicherungsabteilung erfordern.

Selbst eine Fehlkonfiguration des AI-Hubs kann keine Datenlecks zwischen Instanzen verursachen. Admins einer Instanz
können ohne separate Anmeldung keine andere Instanz konfigurieren oder darauf zugreifen.

Für eine logische Trennung innerhalb einer gemeinsamen Plattform verwenden Sie stattdessen
[Multi-Tenancy](../../15_multi_tenancy/).
:::

### Geteiltes LLM-Backend

Beim Deployment mehrerer Instanzen können diese Backend-LLM-Ressourcen teilen. Mehrere Instanzen nutzen dasselbe Azure
OpenAI-Abonnement, Google Gemini API-Keys oder selbst gehostete Modelle. Sie können auch
Authentifizierungsinfrastrukturen wie Azure AD oder Keycloak teilen.

Jede Instanz hat weiterhin ihren eigenen LiteLLM-Proxy. Der Proxy handhabt die Modellauswahl, Budgets, Ratenbegrenzungen
und Versionen pro Instanz. Die LLM-Nutzung wird pro Instanz verfolgt. Prompts, Responses und Benutzerdaten verbleiben
innerhalb jeder Instanz.

Die geteilten LLM-Backends sind zustandslos. Sie persistieren keine Prompts oder Responses. Der Konversationskontext und
die Historie bleiben in der eigenen Infrastruktur jeder Instanz.

## Eigenschaften

### Datenisolation

Die Daten jeder Instanz bleiben isoliert. Es gibt keine geteilte Datenbank oder keinen geteilten Vector Store. Daten
können nicht zwischen Organisationen austreten. Das Setup erfüllt das Schweizer Datenschutzgesetz (revDSG),
GDPR-Datenisolierungsanforderungen und Schweizer Sicherheitsstandards für den öffentlichen Sektor.

::: info Multi-Tenancy innerhalb von Instanzen
Jede Instanz kann auch [Multi-Tenancy](../../15_multi_tenancy/) nutzen, um logische Grenzen für Abteilungen, Kunden oder
Projekte innerhalb dieser Instanz zu schaffen. Multi-Tenancy bietet flexible Zugriffssteuerung bei gleichzeitiger
Aufrechterhaltung einer harten Isolation zwischen Instanzen.
:::

### Konfiguration

Jede Instanz kann unabhängig konfiguriert werden. Organisationen können benutzerdefinierte Agents, spezialisierte
Pipelines für ihre Datenquellen, ihre eigene Zugriffssteuerung (RBAC, OIDC mit lokalem IdP), benutzerdefinierte
Wissensdatenbanken und dedizierte Authentifizierungs-Provider wie Azure AD oder Keycloak deployen.

### Skalierung und Updates

Die Ressourcenzuweisung erfolgt pro Instanz. Sie skalieren Compute, Arbeitsspeicher und Speicher basierend auf der
tatsächlichen Nutzung. Jede Instanz kann Updates nach ihrem eigenen Zeitplan anwenden. Das Testen neuer Funktionen in
einer Instanz beeinflusst andere nicht. SLAs variieren je nach Vertrag.

### Compliance und Auditierung

Auditoren können die Infrastruktur einer einzelnen Instanz überprüfen. Logs und Traces verbleiben innerhalb der Instanz.
Richtlinien zur Backup-Aufbewahrung können pro Instanz konfiguriert werden. Penetration Testing kann auf einzelne
Instanzen zugeschnitten werden.

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
│   ├── Phoenix (AI tracing and evaluation)
│   └── OpenTelemetry (distributed tracing)
│
└── Infrastructure Layer
    ├── NATS (message bus)
    ├── Docling (document processing)
    └── Traefik (reverse proxy + SSL termination)
```

Der LiteLLM-Proxy verbindet sich mit LLM-Services (Azure OpenAI, Google Gemini, selbst gehostete Modelle).

### Multi-Instanz-Infrastruktur

Beim Deployment mehrerer Instanzen erhält jede Instanz dieselbe oben gezeigte Infrastruktur. Sie können
Backend-LLM-Ressourcen teilen:

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

Netzwerkarchitektur:

- Jede Instanz hat ihren eigenen LiteLLM-Proxy
- Instanz-LiteLLM-Proxys verbinden sich mit geteilten LLM-Backends (Azure OpenAI, Gemini, selbst gehostete Modelle)
- Geteilte LLM-Backends verwenden gemeinsame API-Zugangsdaten (konfiguriert pro LiteLLM der Instanz)
- Keine direkte Kommunikation zwischen Instanzen
- Optional: Geteilter Authentifizierungs-Provider (Azure AD, Keycloak)

Datenisolation und -souveränität. Unabhängige Skalierung und Ressourcenzuweisung. Benutzerdefinierte Konfigurationen pro
Instanz. Flexible Update-Zeitpläne. Klare Compliance-Grenzen.

---

## Architekturdiagramme

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

### Multi-Instanz-Deployment mit geteiltem LLM-Backend

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

Jede Instanz hat ihren eigenen LiteLLM-Proxy (unabhängiges Kosten-Tracking, Versionierung, Konfiguration). Alle
Instanz-LiteLLM-Proxys verbinden sich mit geteilten LLM-Backend-Ressourcen (Azure OpenAI-Abonnements, selbst gehostete
Modelle). Prompts, Responses und Benutzerdaten verbleiben innerhalb der Instanzgrenzen.

---

## Sicherheitsüberlegungen

### Instanz-Isolation

Instanzen kommunizieren nicht miteinander. Jede Instanz hat separate Datenbanken, Vector Stores und Dateispeicher. Jede
Instanz verbindet sich mit ihrem eigenen IdP (Azure AD, Keycloak) oder kann einen gemeinsamen IdP mit separater
Namespace-Isolation teilen. LiteLLM erzwingt API-Keys und Quotas pro Instanz.

### LLM-Proxy-Sicherheit

LiteLLM persistiert keine Prompts oder Responses (zustandsloser Betrieb). Das API-Key-Management umfasst die sichere
Key-Generierung, Rotation und den Widerruf. Instanzspezifische Anforderungslimits verhindern Missbrauch. Alle
LLM-Anfragen werden mit Instanz-ID, aber ohne Prompt-Inhalt, protokolliert. Die Presidio-Integration ist optional für
die PII-Erkennung und -Redaktion.

### Daten während der Übertragung

Die gesamte Kommunikation ist mit TLS (Instanz zum LLM-Proxy) verschlüsselt. Das Zertifikatsmanagement verwendet Let's
Encrypt für die Produktion und mkcert für die Entwicklung. Die API-Authentifizierung verwendet Bearer Tokens (OAuth 2.0,
JWT).

### Daten im Ruhezustand

PostgreSQL verwendet transparente Datenverschlüsselung (TDE). Persistente Volumes sind verschlüsselt (LUKS, Azure Disk
Encryption). Secrets werden über Umgebungsvariablen, Azure Key Vault oder Docker Secrets verwaltet.

---

## Nächste Schritte

- [Multi-Tenancy](../../15_multi_tenancy/) – Logische Trennung innerhalb einer einzelnen Instanz
- [Produktionskonfiguration](../2_production_configuration/) – Konfigurationsanleitung für Produktions-Deployments
- [Überlegungen zur Skalierung](../3_scaling_considerations/) – Skalierung von Instanzen
- [Backup und Wiederherstellung](../4_backup_and_recovery/) – Backup-Strategien für die Pro-Instanz-Architektur
- [Updates und Wartung](../6_updates_and_maintenance/) – Verwaltung von Updates über mehrere Instanzen hinweg

---

## FAQ

::: details Können Instanzen Agents oder Pipelines teilen?
Nein. Jede Instanz hat ihren eigenen isolierten Satz von Agents und Pipelines. Dieselben Agent-Definitionen (Code)
können jedoch über mehrere Instanzen hinweg deployed werden. Anpassungen sind instanzspezifisch.

Für das Teilen von Agents innerhalb einer Organisation verwenden Sie [Multi-Tenancy](../../15_multi_tenancy/), um
logische Grenzen innerhalb einer einzelnen Instanz zu schaffen.
:::

::: details Was ist der Unterschied zwischen Multi-Instancing und Multi-Tenancy?
**Multi-Instancing** (dieses Kapitel) bedeutet, mehrere vollständig isolierte AI-Hub-Installationen zu betreiben. Jede
hat separate Datenbanken, Vector Stores und Application Server. Selbst eine Fehlkonfiguration kann keine Datenlecks
zwischen Instanzen verursachen. Verwenden Sie dies, wenn Sie eine absolute Isolation benötigen (z.B. verschiedene
juristische Einheiten, hochsensible Abteilungen).

**Multi-Tenancy** ([Kapitel 15](../../15_multi_tenancy/)) bedeutet, organisatorische Grenzen innerhalb einer einzelnen
AI-Hub-Instanz zu schaffen. Mehrere Tenants teilen die Infrastruktur, haben aber eine logische Trennung durch
Zugriffssteuerung. Verwenden Sie dies für Abteilungen, Projekte oder Kunden innerhalb derselben Organisation.

Sie können beides kombinieren: Betreiben Sie mehrere Instanzen (harte Isolation), wobei jede Instanz Multi-Tenancy
(flexible Trennung innerhalb dieser Instanz) verwendet.
:::

::: details Welche Daten sieht das geteilte LLM-Backend?
Jede Instanz hat ihren eigenen LiteLLM-Proxy, sodass Prompts und Responses innerhalb der Instanz verbleiben. Die
geteilten LLM-Backends (Azure OpenAI, Gemini, selbst gehostete Modelle) sehen API-Anfragen von mehreren
Instanz-LiteLLM-Proxys (zustandslos, nicht persistent), Modellinferenz-Anfragen (nur Prompts und Completions während der
Übertragung), keine Instanzidentifikation oder Kontext und anonymisierte PII-Daten, falls aktiviert.

Sie sehen nicht, welche Instanz die Anfrage gestellt hat, keine Konversationshistorie oder gespeicherte Daten. Der
gesamte Kontext verbleibt im LiteLLM-Proxy und in der Datenbank der Instanz.
:::

::: details Kann eine Instanz ausschliesslich selbst gehostete Modelle verwenden?
Ja. Für Air-Gapped- oder vollständig On-Premise-Deployments können Sie selbst gehostete LLMs (vLLM, llama.cpp, HF-TEI)
deployen, LiteLLM so konfigurieren, dass es an lokale Modelle weiterleitet, und dies ohne erforderliche ausgehende
Internetkonnektivität betreiben.
:::

::: details Wie werden Kosten pro Instanz verfolgt?
LiteLLM verfolgt die API-Nutzung pro Instanz und Benutzer: Token-Anzahlen (Input/Output), Modellnutzung (GPT-4, Gemini
usw.), Kostenberechnungen basierend auf Modellpreisen und die monatliche Budgetdurchsetzung.

Daten sind in der LiteLLM-Admin-UI verfügbar und für die Abrechnung exportierbar.
:::

::: details Können Instanzen unterschiedlichen LLM-Zugriff haben?
Ja. Die LiteLLM-Konfiguration ermöglicht den Modellzugriff pro Instanz. Zum Beispiel könnte Instanz A nur GPT-4o für
strikte Compliance verwenden, Instanz B GPT-4o plus Gemini 2.0 für mehr Flexibilität und Instanz C ausschliesslich
selbst gehostete Modelle für ein Air-Gapped-Deployment.
:::

::: details Was passiert, wenn der LLM-Proxy nicht verfügbar ist?
Instanzen werden eine Beeinträchtigung LLM-abhängiger Funktionen erfahren. RAG-Agents können keine Antworten generieren.
Embeddings können für neue Dokumente nicht erstellt werden. Vorhandene Daten und die Benutzeroberfläche bleiben jedoch
zugänglich, und Nicht-LLM-Funktionen (Dokumentenupload, RBAC, Observability) funktionieren weiterhin.

Abhilfe: Deployen Sie LiteLLM mit hoher Verfügbarkeit (mehrere Replikas, Load Balancing).
:::

::: details Wie verwalten Sie Updates über viele Instanzen hinweg?
Siehe [Updates und Wartung](../6_updates_and_maintenance/) für Strategien wie gestaffelte Rollouts (Pilot bis
Produktion), Blue-Green-Deployments, automatisierte Update-Orchestrierung (Ansible, Kubernetes-Operatoren) und
instanzspezifische Update-Zeitpläne.
:::

## Verwandte Dokumentation

- [Multi-Tenancy](../../15_multi_tenancy/) – Schaffung organisatorischer Grenzen innerhalb einer Instanz
- [Kernkomponenten](../../2_architecture/1_core_components/) – AI-Hub-Architektur
- [Authentifizierung & Autorisierung](../../11_access_management/1_authentication_setup/) –
  Authentifizierungskonfiguration
- [Monitoring und Alerting](../5_monitoring_and_alerting/) – Observability für Multi-Instanz-Deployments
- [Schweizer Datenschutz](../../20_compliance/3_dsg/) – revDSG-Compliance für den öffentlichen Sektor
