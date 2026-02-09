---
title: Deployment-Optionen
source_sha: "371d196f82c70d60c297c422eb3ba9d1c3ea782f925c6dae356c48bb9184b28b"
---

# Deployment-Optionen

## Übersicht

Der AI-Hub kann als einzelne, isolierte Instanz für eine Organisation oder als mehrere isolierte Instanzen, die optional Backend-LLM-Ressourcen gemeinsam nutzen, bereitgestellt werden.

::: info Multi-Tenancy vs. Multi-Instancing
Dieses Kapitel beschreibt **Multi-Instancing** (mehrere isolierte AI-Hub-Instanzen). Für **Multi-Tenancy** (mehrere organisatorische Grenzen innerhalb einer einzigen Instanz) siehe [Multi-Tenancy](../../16_multi_tenancy/).

Beide Deployment-Modelle sind gültig und dienen unterschiedlichen Zwecken. Multi-Instancing bietet eine strikte Isolation zwischen Organisationen, während Multi-Tenancy eine logische Trennung innerhalb einer gemeinsam genutzten Plattforminstanz ermöglicht.
:::

## Einzelinstanz-Deployment

### Isolierte Instanz

Ein Einzelinstanz-Deployment betreibt eine vollständige, eigenständige AI-Hub-Instanz. Die Organisation erhält eine dedizierte Infrastruktur: separate Datenbanken, Vektor-Datenbanken, Dateispeicher und Anwendungs-Services.

Die Instanz umfasst die API, Agents, Pipelines, das Webinterface und Bot-Integrationen. Sie verfügt über eigene Datenbanken (FerretDB/PostgreSQL), Vektor-Datenbanken (Milvus oder Azure AI Search) und Dateispeicher (SeaweedFS oder Azure Data Lake). Das Monitoring erfolgt über SigNoz und Phoenix. NATS übernimmt das Event-Streaming. Die Instanz besitzt einen eigenen LiteLLM-Proxy für Kostenverfolgung und Versionskontrolle.

### LLM-Backend

Die Instanz verbindet sich über ihren LiteLLM-Proxy mit LLM-Services. Der Proxy kann sich mit Azure OpenAI, Google Gemini, selbst gehosteten Modellen (vLLM, llama.cpp, HF-TEI) oder einer Mischung davon verbinden. Der Proxy verwaltet die Modellauswahl, Budgets, Ratenbegrenzungen und Versionen. Alle Prompts, Antworten und Benutzerdaten verbleiben innerhalb der Instanz.

---

## Hosting-Optionen

Der AI-Hub kann je nach organisatorischen Anforderungen auf drei Arten gehostet werden.

### On-Premise (Betrieb auf eigenen Servern)

Sie betreiben den AI-Hub auf Ihren eigenen Servern in Ihrem Rechenzentrum.

Sie benötigen x86_64-Server mit CPU, RAM und Speicherplatz. NVIDIA GPUs eignen sich für selbst gehostete LLM-Inferenz. Für den Netzwerkzugriff benötigen Sie entweder ausgehendes HTTPS für Cloud-basierte LLM-Services oder eine Air-Gapped-Umgebung mit lokalen Modellen.

Die Infrastruktur unterliegt Ihrer Kontrolle. Keine Cloud-Abhängigkeiten. Funktioniert in Air-Gapped-Umgebungen mit selbst gehosteten LLMs.

---

### Private Cloud (Betrieb in eigener Cloud-Umgebung)

Sie betreiben den AI-Hub in Ihrer eigenen Cloud-Umgebung (Schweizer Cloud-Anbieter, Azure, AWS, GCP).

Daten verbleiben in Ihrem Cloud-Konto unter Ihrer Kontrolle. Sie wählen die Region (z.B. Schweiz für Datenresidenz). Sie verwalten die Cloud-Ressourcen und -Kosten.

Cloud-Anbieter verfügen typischerweise über Sicherheits- und Compliance-Zertifizierungen. Sie benötigen Internetkonnektivität für den LLM-Proxy-Zugriff (HTTPS), optional VPN für den administrativen Zugriff und privates Networking zwischen Services (internes DNS).

---

### SaaS (Schweizer Cloud-Hosting)

bbv hostet und verwaltet den AI-Hub für Sie auf Schweizer Cloud-Infrastruktur.

bbv übernimmt die Infrastruktur-Bereitstellung, Updates, Backups, das Monitoring und operative Aufgaben. Daten verbleiben in der Schweiz unter Schweizer Rechtsprechung. Sicherheits- und Compliance-Zertifizierungen vom Cloud-Anbieter.

Sie greifen über ein Webinterface und APIs auf den AI-Hub zu. bbv bietet SLAs für Uptime und Support. Weniger operativer Aufwand für Ihr Team.

---

## Multi-Instanz-Deployment

::: tip Wann Multi-Instancing verwenden
Verwenden Sie mehrere isolierte Instanzen, wenn Sie eine **strikte Trennung** zwischen Organisationen benötigen, mit 0%iger Wahrscheinlichkeit eines Datenlecks. Zum Beispiel eine Krankenversicherung mit einer medizinischen Prüfungskommission, die streng geheime Daten verarbeitet und eine absolute Isolation von der Hauptversicherungsabteilung erfordert.

Selbst eine Fehlkonfiguration des AI-Hubs kann kein Datenleck zwischen Instanzen verursachen. Administratoren einer Instanz können eine andere Instanz ohne separate Anmeldung weder konfigurieren noch auf diese zugreifen.

Für die logische Trennung innerhalb einer gemeinsam genutzten Plattform verwenden Sie stattdessen [Multi-Tenancy](../../16_multi_tenancy/).
:::

### Gemeinsam genutztes LLM-Backend

Beim Deployment mehrerer Instanzen können diese Backend-LLM-Ressourcen gemeinsam nutzen. Mehrere Instanzen verwenden dieselbe Azure OpenAI-Subscription, Google Gemini API-Keys oder selbst gehostete Modelle. Sie können auch Authentifizierungsinfrastrukturen wie Azure AD oder Keycloak gemeinsam nutzen.

Jede Instanz verfügt weiterhin über einen eigenen LiteLLM-Proxy. Der Proxy verwaltet die Modellauswahl, Budgets, Ratenbegrenzungen und Versionen pro Instanz. Die LLM-Nutzung wird pro Instanz verfolgt. Prompts, Antworten und Benutzerdaten verbleiben in jeder Instanz.

Die gemeinsam genutzten LLM-Backends sind zustandslos. Sie speichern keine Prompts oder Antworten dauerhaft. Konversationskontext und -historie verbleiben in der eigenen Infrastruktur jeder Instanz.

## Eigenschaften

### Datenisolation

Die Daten jeder Instanz bleiben isoliert. Es gibt keine gemeinsame Datenbank oder Vektor-Datenbank. Daten können nicht zwischen Organisationen gelangen. Das Setup erfüllt das Schweizer Datenschutzgesetz (revDSG), die GDPR-Anforderungen für Datenisolation und die Sicherheitsstandards des Schweizer öffentlichen Sektors.

::: info Multi-Tenancy innerhalb von Instanzen
Jede Instanz kann auch [Multi-Tenancy](../../16_multi_tenancy/) verwenden, um logische Grenzen für Abteilungen, Kunden oder Projekte innerhalb dieser Instanz zu schaffen. Multi-Tenancy bietet eine flexible Zugriffssteuerung bei gleichzeitiger Beibehaltung einer strikten Isolation zwischen Instanzen.
:::

### Konfiguration

Jede Instanz kann unabhängig konfiguriert werden. Organisationen können benutzerdefinierte Agents, spezialisierte Pipelines für ihre Datenquellen, eigene Zugriffssteuerung (RBAC, OIDC mit lokalem IdP), benutzerdefinierte Wissensdatenbanken und dedizierte Authentifizierungsanbieter wie Azure AD oder Keycloak deployen.

### Skalierung und Updates

Die Ressourcenzuweisung erfolgt pro Instanz. Sie skalieren Rechenleistung, Speicher und Speicherplatz basierend auf der tatsächlichen Nutzung. Jede Instanz kann Updates nach eigenem Zeitplan anwenden. Das Testen neuer Funktionen in einer Instanz beeinflusst andere nicht. SLAs variieren je nach Vertrag.

### Compliance und Auditing

Auditoren können die Infrastruktur einer einzelnen Instanz prüfen. Logs und Traces verbleiben innerhalb der Instanz. Backup-Aufbewahrungsrichtlinien können pro Instanz konfiguriert werden. Penetrationstests können auf einzelne Instanzen zugeschnitten werden.

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
    ├── MinerU (document processing)
    └── Traefik (reverse proxy + SSL termination)
```

Der LiteLLM-Proxy verbindet sich mit LLM-Services (Azure OpenAI, Google Gemini, selbst gehostete Modelle).

### Multi-Instanz-Infrastruktur

Beim Deployment mehrerer Instanzen erhält jede Instanz dieselbe oben gezeigte Infrastruktur. Sie können Backend-LLM-Ressourcen gemeinsam nutzen:

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

- Jede Instanz verfügt über einen eigenen LiteLLM-Proxy
- Instanz-LiteLLM-Proxies verbinden sich mit gemeinsam genutzten LLM-Backends (Azure OpenAI, Gemini, selbst gehostete Modelle)
- Gemeinsam genutzte LLM-Backends verwenden gemeinsame API-Anmeldeinformationen (pro Instanz-LiteLLM konfiguriert)
- Keine direkte Kommunikation zwischen Instanzen
- Optional: Gemeinsamer Authentifizierungsanbieter (Azure AD, Keycloak)

Datenisolation und Souveränität. Unabhängige Skalierung und Ressourcenzuweisung. Benutzerdefinierte Konfigurationen pro Instanz. Flexible Update-Zeitpläne. Klare Compliance-Grenzen.

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

### Multi-Instanz-Deployment mit gemeinsam genutztem LLM-Backend

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

Jede Instanz verfügt über einen eigenen LiteLLM-Proxy (unabhängige Kostenverfolgung, Versionierung, Konfiguration). Alle Instanz-LiteLLM-Proxies verbinden sich mit gemeinsam genutzten LLM-Backend-Ressourcen (Azure OpenAI-Subscriptions, selbst gehostete Modelle). Prompts, Antworten und Benutzerdaten verbleiben innerhalb der Instanzgrenzen.

---

## Sicherheitsüberlegungen

### Instanzisolation

Instanzen kommunizieren nicht miteinander. Jede Instanz verfügt über separate Datenbanken, Vektor-Datenbanken und Dateispeicher. Jede Instanz verbindet sich mit ihrem eigenen IdP (Azure AD, Keycloak) oder kann einen gemeinsamen IdP mit separater Namespace-Isolation nutzen. LiteLLM erzwingt API-Keys und Quotas pro Instanz.

### LLM-Proxy-Sicherheit

LiteLLM speichert Prompts oder Antworten nicht dauerhaft (zustandsloser Betrieb). Die API-Key-Verwaltung umfasst die sichere Erzeugung, Rotation und den Widerruf von Schlüsseln. Pro-Instanz-Anfrage-Limits verhindern Missbrauch. Alle LLM-Anfragen werden mit Instanz-ID, aber ohne Prompt-Inhalt protokolliert. Die Presidio-Integration ist optional für die PII-Erkennung und -Redaktion.

### Daten während der Übertragung

Die gesamte Kommunikation wird mit TLS verschlüsselt (Instanz zum LLM-Proxy). Das Zertifikatmanagement verwendet Let's Encrypt für die Produktion und mkcert für die Entwicklung. Die API-Authentifizierung verwendet Bearer-Tokens (OAuth 2.0, JWT).

### Daten im Ruhezustand

PostgreSQL verwendet transparente Datenverschlüsselung (TDE). Persistente Volumes sind verschlüsselt (LUKS, Azure Disk Encryption). Secrets werden über Umgebungsvariablen, Azure Key Vault oder Docker Secrets verwaltet.

---

## Nächste Schritte

- [Multi-Tenancy](../../16_multi_tenancy/) - Logische Trennung innerhalb einer einzelnen Instanz
- [Produktionskonfiguration](../2_production_configuration/) - Konfigurationsanleitung für Produktions-Deployments
- [Skalierungsüberlegungen](../3_scaling_considerations/) - Skalierung von Instanzen
- [Backup und Wiederherstellung](../4_backup_and_recovery/) - Backup-Strategien für die Pro-Instanz-Architektur
- [Updates und Wartung](../6_updates_and_maintenance/) - Verwaltung von Updates über mehrere Instanzen

---

## FAQ

::: details Können Instanzen Agents oder Pipelines teilen?
Nein. Jede Instanz verfügt über einen eigenen, isolierten Satz von Agents und Pipelines. Die gleichen Agent-Definitionen (Code) können jedoch über mehrere Instanzen hinweg deployed werden. Anpassungen sind instanzspezifisch.

Um Agents innerhalb einer Organisation zu teilen, verwenden Sie [Multi-Tenancy](../../16_multi_tenancy/), um logische Grenzen innerhalb einer einzigen Instanz zu schaffen.
:::

::: details Was ist der Unterschied zwischen Multi-Instancing und Multi-Tenancy?
**Multi-Instancing** (dieses Kapitel) bedeutet, mehrere vollständig isolierte AI-Hub-Installationen zu betreiben. Jede verfügt über separate Datenbanken, Vektor-Datenbanken und Anwendungsserver. Selbst eine Fehlkonfiguration kann kein Datenleck zwischen Instanzen verursachen. Verwenden Sie dies, wenn Sie absolute Isolation benötigen (z.B. verschiedene juristische Einheiten, hochsensible Abteilungen).

**Multi-Tenancy** ([Kapitel 15](../../16_multi_tenancy/)) bedeutet, organisatorische Grenzen innerhalb einer einzigen AI-Hub-Instanz zu schaffen. Mehrere Mandanten teilen sich die Infrastruktur, verfügen aber über eine logische Trennung durch Zugriffssteuerung. Verwenden Sie dies für Abteilungen, Projekte oder Kunden innerhalb derselben Organisation.

Sie können beides kombinieren: Betreiben Sie mehrere Instanzen (strikte Isolation), wobei jede Instanz Multi-Tenancy (flexible Trennung innerhalb dieser Instanz) verwendet.
:::

::: details Welche Daten sieht das gemeinsam genutzte LLM-Backend?
Jede Instanz verfügt über einen eigenen LiteLLM-Proxy, sodass Prompts und Antworten innerhalb der Instanz verbleiben. Die gemeinsam genutzten LLM-Backends (Azure OpenAI, Gemini, selbst gehostete Modelle) sehen API-Anfragen von mehreren Instanz-LiteLLM-Proxies (zustandslos, nicht persistent), Modell-Inferenzanfragen (Prompts und Completions nur während der Übertragung), keine Instanzidentifikation oder Kontext und anonyme PII-Daten, falls aktiviert.

Sie sehen nicht, welche Instanz die Anfrage gestellt hat, die Konversationshistorie oder gespeicherte Daten. Der gesamte Kontext verbleibt im LiteLLM-Proxy und der Datenbank der Instanz.
:::

::: details Kann eine Instanz ausschließlich selbst gehostete Modelle verwenden?
Ja. Für Air-Gapped- oder vollständig On-Premise-Deployments können Sie selbst gehostete LLMs (vLLM, llama.cpp, HF-TEI) deployen, LiteLLM so konfigurieren, dass es an lokale Modelle weiterleitet, und dies ohne ausgehende Internetkonnektivität betreiben.
:::

::: details Wie werden Kosten pro Instanz verfolgt?
LiteLLM verfolgt die API-Nutzung pro Instanz und Benutzer: Token-Zähler (Input/Output), Modellnutzung (GPT-4, Gemini usw.), Kostenberechnungen basierend auf Modellpreisen und monatliche Budgetdurchsetzung.

Daten sind in der LiteLLM Admin UI verfügbar und für die Abrechnung exportierbar.
:::

::: details Können Instanzen unterschiedlichen LLM-Zugriff haben?
Ja. Die LiteLLM-Konfiguration erlaubt den Modellzugriff pro Instanz. Zum Beispiel könnte Instanz A nur GPT-4o für strikte Compliance verwenden, Instanz B könnte GPT-4o plus Gemini 2.0 für mehr Flexibilität nutzen und Instanz C könnte ausschließlich selbst gehostete Modelle für ein Air-Gapped-Deployment verwenden.
:::

::: details Was passiert, wenn der LLM-Proxy nicht verfügbar ist?
Instanzen werden eine LLM-abhängige Feature-Degradation erfahren. RAG-Agents können keine Antworten generieren. Embeddings können für neue Dokumente nicht erstellt werden. Bestehende Daten und die Benutzeroberfläche bleiben jedoch zugänglich, und nicht-LLM-Funktionen (Dokumenten-Upload, RBAC, Observability) funktionieren weiterhin.

Mitigation: LiteLLM mit hoher Verfügbarkeit deployen (mehrere Replikate, Load Balancing).
:::

::: details Wie verwalten Sie Updates über viele Instanzen hinweg?
Siehe [Updates und Wartung](../6_updates_and_maintenance/) für Strategien wie gestaffelte Rollouts (Pilot- zu Produktionsumgebung), Blue-Green-Deployments, automatisierte Update-Orchestrierung (Ansible, Kubernetes-Operatoren) und Update-Zeitpläne pro Instanz.
:::

## Verwandte Dokumentation

- [Multi-Tenancy](../../16_multi_tenancy/) - Logische Trennung innerhalb einer einzelnen Instanz
- [Kernkomponenten](../../2_architecture/1_core_components/) - AI-Hub-Architektur
- [Authentifizierung & Autorisierung](../../11_access_management/1_authentication_setup/) - Authentifizierungskonfiguration
- [Monitoring und Alerting](../5_monitoring_and_alerting/) - Observability für Multi-Instanz-Deployments
- [Schweizer Datenschutz](../../21_compliance/3_dsg/) - revDSG-Compliance für den öffentlichen Sektor
