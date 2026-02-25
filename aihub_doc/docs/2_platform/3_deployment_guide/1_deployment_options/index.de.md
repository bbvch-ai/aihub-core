---
title: Bereitstellungsoptionen
source_sha: 3d8e7b250dfada0c26f3b4828c12f0a90abdca46254fd6d7ea480c66e4af2edf
---

# Bereitstellungsoptionen

## Übersicht

Der AI-Hub kann als eine einzelne isolierte Instanz für eine Organisation oder als mehrere isolierte Instanzen
bereitgestellt werden, die optional Backend-LLM-Ressourcen gemeinsam nutzen.

::: info Multi-Tenancy vs. Multi-Instancing
Dieses Kapitel beschreibt **Multi-Instancing** (mehrere isolierte AI-Hub-Instanzen). Für **Multi-Tenancy** (mehrere
organisatorische Grenzen innerhalb einer einzigen Instanz) siehe [Multi-Tenancy](../../16_multi_tenancy/).

Beide Bereitstellungsmodelle sind gültig und dienen unterschiedlichen Zwecken. Multi-Instancing bietet eine strikte
Isolation zwischen Organisationen, während Multi-Tenancy eine logische Trennung innerhalb einer gemeinsam genutzten
Plattforminstanz ermöglicht.
:::

## Einzelinstanz-Deployment

### Isolierte Instanz

Ein Einzelinstanz-Deployment betreibt eine vollständige, eigenständige AI-Hub-Instanz. Die Organisation erhält eine
dedizierte Infrastruktur: separate Datenbanken, Vektor-Stores, Dateispeicher und Anwendungs-Services.

Die Instanz umfasst die API, Agents, Pipelines, die Weboberfläche und Bot-Integrationen. Sie verfügt über eigene
Datenbanken (FerretDB/PostgreSQL), Vektor-Stores (Milvus oder Azure AI Search) und Dateispeicher (SeaweedFS oder Azure
Data Lake). Das Monitoring erfolgt über SigNoz und Langfuse. NATS handhabt das Event-Streaming. Die Instanz verfügt über
einen eigenen LiteLLM-Proxy für Kostenverfolgung und Versionskontrolle.

### LLM-Backend

Die Instanz verbindet sich über ihren LiteLLM-Proxy mit LLM-Services. Der Proxy kann sich mit Azure OpenAI, Google
Gemini, selbst gehosteten Modellen (vLLM, llama.cpp, HF-TEI) oder einer Mischung davon verbinden. Der Proxy verwaltet
die Modellauswahl, Budgets, Ratenbegrenzungen und Versionen. Alle Prompts, Antworten und Benutzerdaten bleiben innerhalb
der Instanz.

______________________________________________________________________

## Hosting-Optionen

Der AI-Hub kann je nach organisatorischen Anforderungen auf drei Arten gehostet werden.

### On-Premise (eigener Server)

Sie betreiben den AI-Hub auf Ihren eigenen Servern in Ihrem Rechenzentrum.

Sie benötigen x86_64-Server mit CPU, RAM und Speicherplatz. NVIDIA GPUs eignen sich für selbst gehostete LLM-Inferenz.
Für den Netzwerkzugriff benötigen Sie entweder ausgehendes HTTPS für Cloud-basierte LLM-Services oder einen
Air-Gapped-Betrieb mit lokalen Modellen.

Die Infrastruktur liegt unter Ihrer Kontrolle. Keine Cloud-Abhängigkeiten. Funktioniert in Air-Gapped-Umgebungen mit
selbst gehosteten LLMs.

______________________________________________________________________

### Private Cloud (eigene Cloud)

Sie betreiben den AI-Hub in Ihrer eigenen Cloud-Umgebung (Schweizer Cloud-Anbieter, Azure, AWS, GCP).

Daten bleiben in Ihrem Cloud-Konto unter Ihrer Kontrolle. Sie wählen die Region (z.B. Schweiz für Datenresidenz). Sie
verwalten die Cloud-Ressourcen und Kosten.

Cloud-Anbieter verfügen typischerweise über Sicherheits- und Compliance-Zertifizierungen. Sie benötigen
Internetkonnektivität für den LLM-Proxy-Zugriff (HTTPS), optional VPN für den administrativen Zugriff und private
Netzwerke zwischen Services (internes DNS).

______________________________________________________________________

### SaaS (Schweizer Cloud-Hosting)

bbv hostet und verwaltet den AI-Hub für Sie auf einer Schweizer Cloud-Infrastruktur.

bbv übernimmt die Infrastruktur-Bereitstellung, Updates, Backups, Monitoring und operationale Aufgaben. Daten verbleiben
in der Schweiz unter Schweizer Rechtshoheit. Sicherheits- und Compliance-Zertifizierungen vom Cloud-Anbieter.

Sie greifen über eine Weboberfläche und APIs auf den AI-Hub zu. bbv bietet SLAs für Verfügbarkeit und Support. Weniger
operativer Aufwand für Ihr Team.

______________________________________________________________________

## Multi-Instanz-Deployment

::: tip Wann Multi-Instancing verwenden
Verwenden Sie mehrere isolierte Instanzen, wenn Sie eine **strikte Trennung** zwischen Organisationen benötigen, mit
einer 0%igen Chance auf Datenlecks. Zum Beispiel eine Krankenversicherung mit einer medizinischen Gutachterkommission,
die streng geheime Daten verarbeitet und eine absolute Isolation von der Hauptversicherungsabteilung erfordert.

Selbst eine Fehlkonfiguration des AI-Hub kann keine Datenlecks zwischen Instanzen verursachen. Administratoren einer
Instanz können eine andere Instanz ohne separate Anmeldung weder konfigurieren noch auf diese zugreifen.

Für die logische Trennung innerhalb einer gemeinsam genutzten Plattform verwenden Sie stattdessen
[Multi-Tenancy](../../16_multi_tenancy/).
:::

### Gemeinsam genutztes LLM-Backend

Beim Deployment mehrerer Instanzen können diese Backend-LLM-Ressourcen gemeinsam nutzen. Mehrere Instanzen verwenden
dieselbe Azure OpenAI-Subscription, Google Gemini API-Keys oder selbst gehostete Modelle. Sie können auch
Authentifizierungsinfrastrukturen wie Azure AD oder Keycloak gemeinsam nutzen.

Jede Instanz hat weiterhin ihren eigenen LiteLLM-Proxy. Der Proxy verwaltet die Modellauswahl, Budgets,
Ratenbegrenzungen und Versionen pro Instanz. Die LLM-Nutzung wird pro Instanz verfolgt. Prompts, Antworten und
Benutzerdaten bleiben innerhalb jeder Instanz.

Die gemeinsam genutzten LLM-Backends sind zustandslos. Sie persistieren keine Prompts oder Antworten.
Konversationskontext und -historie verbleiben in der eigenen Infrastruktur jeder Instanz.

## Merkmale

### Datenisolation

Die Daten jeder Instanz bleiben isoliert. Es gibt keine gemeinsame Datenbank oder Vektor-Store. Daten können nicht
zwischen Organisationen austreten. Die Einrichtung erfüllt das Schweizer Datenschutzgesetz (revDSG), die
GDPR-Anforderungen an die Datenisolation und die Sicherheitsstandards des Schweizer öffentlichen Sektors.

::: info Multi-Tenancy innerhalb von Instanzen
Jede Instanz kann auch [Multi-Tenancy](../../16_multi_tenancy/) verwenden, um logische Grenzen für Abteilungen, Kunden
oder Projekte innerhalb dieser Instanz zu schaffen. Multi-Tenancy bietet flexible Zugriffssteuerung bei gleichzeitiger
Aufrechterhaltung einer strikten Isolation zwischen Instanzen.
:::

### Konfiguration

Jede Instanz kann unabhängig konfiguriert werden. Organisationen können benutzerdefinierte Agents, spezialisierte
Pipelines für ihre Datenquellen, eine eigene Zugriffssteuerung (RBAC, OIDC mit lokalem IdP), benutzerdefinierte
Wissensdatenbanken und dedizierte Authentifizierungsanbieter wie Azure AD oder Keycloak deployen.

### Skalierung und Updates

Die Ressourcenzuweisung erfolgt pro Instanz. Sie skalieren Rechenleistung, Speicher und Storage basierend auf der
tatsächlichen Nutzung. Jede Instanz kann Updates nach ihrem eigenen Zeitplan anwenden. Das Testen neuer Features in
einer Instanz beeinflusst andere nicht. SLAs variieren je nach Vertrag.

### Compliance und Auditing

Auditoren können die Infrastruktur einer einzelnen Instanz überprüfen. Logs und Traces verbleiben innerhalb der Instanz.
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
│   ├── Langfuse (LLM tracing, cost tracking, and evaluation)
│   └── OpenTelemetry (distributed tracing)
│
└── Infrastructure Layer
    ├── NATS (message bus)
    ├── MinerU (document processing)
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

Netzwerkarchitektur:

- Jede Instanz hat ihren eigenen LiteLLM-Proxy
- LiteLLM-Proxies der Instanzen verbinden sich mit gemeinsam genutzten LLM-Backends (Azure OpenAI, Gemini, selbst
  gehostete Modelle)
- Gemeinsam genutzte LLM-Backends verwenden gemeinsame API-Zugangsdaten (konfiguriert pro LiteLLM der Instanz)
- Keine direkte Kommunikation zwischen Instanzen
- Optional: Gemeinsamer Authentifizierungsanbieter (Azure AD, Keycloak)

Datenisolation und -souveränität. Unabhängige Skalierung und Ressourcenzuweisung. Benutzerdefinierte Konfigurationen pro
Instanz. Flexible Update-Zeitpläne. Klare Compliance-Grenzen.

______________________________________________________________________

## Sicherheitsüberlegungen

### Instanz-Isolation

Instanzen kommunizieren nicht miteinander. Jede Instanz verfügt über separate Datenbanken, Vektor-Stores und
Dateispeicher. Jede Instanz verbindet sich mit ihrem eigenen IdP (Azure AD, Keycloak) oder kann einen gemeinsamen IdP
mit separater Namespace-Isolation nutzen. LiteLLM erzwingt pro-Instanz API-Keys und Quotas.

### LLM-Proxy-Sicherheit

LiteLLM persistiert keine Prompts oder Antworten (zustandsloser Betrieb). Die API-Key-Verwaltung umfasst sichere
Key-Generierung, Rotation und Widerruf. Pro-Instanz-Anfragebegrenzungen verhindern Missbrauch. Alle LLM-Anfragen werden
mit Instanz-ID, aber ohne Prompt-Inhalt protokolliert. Die Presidio-Integration ist optional für die PII-Erkennung und
-Redaktion.

### Daten während der Übertragung

Die gesamte Kommunikation ist mit TLS verschlüsselt (Instanz zu LLM-Proxy). Das Zertifikatsmanagement verwendet Let's
Encrypt für die Produktion und mkcert für die Entwicklung. Die API-Authentifizierung verwendet Bearer-Tokens (OAuth 2.0,
JWT).

### Daten im Ruhezustand

PostgreSQL verwendet transparente Datenverschlüsselung (TDE). Persistente Volumes sind verschlüsselt (LUKS, Azure Disk
Encryption). Secrets werden über Umgebungsvariablen, Azure Key Vault oder Docker Secrets verwaltet.

______________________________________________________________________

## Nächste Schritte

- [Multi-Tenancy](../../16_multi_tenancy/) - Logische Trennung innerhalb einer einzelnen Instanz
- [Produktionskonfiguration](../2_production_configuration/) - Konfigurationsanleitung für Produktions-Deployments
- [Skalierungsüberlegungen](../3_scaling_considerations/) - Skalierung von Instanzen
- [Backup und Wiederherstellung](../4_backup_and_recovery/) - Backup-Strategien für die Pro-Instanz-Architektur
- [Updates und Wartung](../6_updates_and_maintenance/) - Verwaltung von Updates über mehrere Instanzen hinweg

______________________________________________________________________

## FAQ

::: details Können Instanzen Agents oder Pipelines teilen?
Nein. Jede Instanz verfügt über ihren eigenen isolierten Satz an Agents und Pipelines. Dieselben Agent-Definitionen
(Code) können jedoch über mehrere Instanzen hinweg deployed werden. Anpassungen sind instanzspezifisch.

Um Agents innerhalb einer Organisation zu teilen, verwenden Sie [Multi-Tenancy](../../16_multi_tenancy/), um logische
Grenzen innerhalb einer einzelnen Instanz zu schaffen.
:::

::: details Was ist der Unterschied zwischen Multi-Instancing und Multi-Tenancy?
**Multi-Instancing** (dieses Kapitel) bedeutet den Betrieb mehrerer vollständig isolierter AI-Hub-Installationen. Jede
verfügt über separate Datenbanken, Vektor-Stores und Anwendungsserver. Selbst eine Fehlkonfiguration kann keine
Datenlecks zwischen Instanzen verursachen. Verwenden Sie dies, wenn Sie eine absolute Isolation benötigen (z.B.
verschiedene juristische Einheiten, hochsensible Abteilungen).

**Multi-Tenancy** ([Kapitel 15](../../16_multi_tenancy/)) bedeutet die Schaffung organisatorischer Grenzen innerhalb
einer einzelnen AI-Hub-Instanz. Mehrere Mandanten teilen sich die Infrastruktur, verfügen jedoch über eine logische
Trennung durch Zugriffssteuerung. Verwenden Sie dies für Abteilungen, Projekte oder Kunden innerhalb derselben
Organisation.

Sie können beides kombinieren: Betreiben Sie mehrere Instanzen (strikte Isolation), wobei jede Instanz Multi-Tenancy
(flexible Trennung innerhalb dieser Instanz) verwendet.
:::

::: details Welche Daten sieht das gemeinsam genutzte LLM-Backend?
Jede Instanz hat ihren eigenen LiteLLM-Proxy, sodass Prompts und Antworten innerhalb der Instanz verbleiben. Die
gemeinsam genutzten LLM-Backends (Azure OpenAI, Gemini, selbst gehostete Modelle) sehen API-Anfragen von mehreren
LiteLLM-Proxies der Instanzen (zustandslos, nicht persistent), Modellinferenzanfragen (nur Prompts und Completions
während der Übertragung), keine Instanzidentifikation oder Kontext und anonyme PII-Daten, falls aktiviert.

Sie sehen nicht, welche Instanz die Anfrage gestellt hat, die Konversationshistorie oder gespeicherte Daten. Der gesamte
Kontext verbleibt im LiteLLM-Proxy und in der Datenbank der Instanz.
:::

::: details Kann eine Instanz ausschließlich selbst gehostete Modelle verwenden?
Ja. Für Air-Gapped- oder vollständig On-Premise-Deployments können Sie selbst gehostete LLMs (vLLM, llama.cpp, HF-TEI)
deployen, LiteLLM so konfigurieren, dass es an lokale Modelle weiterleitet, und dies ohne erforderliche ausgehende
Internetverbindung betreiben.
:::

::: details Wie werden Kosten pro Instanz verfolgt?
LiteLLM verfolgt die API-Nutzung pro Instanz und Benutzer: Token-Zählungen (Input/Output), Modellnutzung (GPT-4, Gemini
usw.), Kostenberechnungen basierend auf der Modellpreisgestaltung und monatliche Budgetdurchsetzung.

Daten sind in der LiteLLM-Admin-UI verfügbar und für die Abrechnung exportierbar.
:::

::: details Können Instanzen unterschiedlichen LLM-Zugriff haben?
Ja. Die LiteLLM-Konfiguration ermöglicht pro-Instanz-Modellzugriff. Zum Beispiel könnte Instanz A nur GPT-4o für strikte
Compliance verwenden, Instanz B könnte GPT-4o plus Gemini 2.0 für mehr Flexibilität verwenden und Instanz C könnte
ausschließlich selbst gehostete Modelle für ein Air-Gapped-Deployment verwenden.
:::

::: details Was passiert, wenn der LLM-Proxy nicht verfügbar ist?
Instanzen werden eine Beeinträchtigung LLM-abhängiger Features erfahren. RAG-Agents können keine Antworten generieren.
Embeddings können nicht für neue Dokumente erstellt werden. Vorhandene Daten und die UI bleiben jedoch zugänglich, und
nicht-LLM-Features (Dokumenten-Upload, RBAC, Observability) funktionieren weiterhin.

Abhilfe: Deployen Sie LiteLLM mit hoher Verfügbarkeit (mehrere Replicas, Load Balancing).
:::

::: details Wie verwalten Sie Updates über viele Instanzen hinweg?
Siehe [Updates und Wartung](../6_updates_and_maintenance/) für Strategien wie gestaffelte Rollouts (Pilot bis
Produktion), Blue-Green-Deployments, automatisierte Update-Orchestrierung (Ansible, Kubernetes-Operatoren) und
pro-Instanz-Update-Zeitpläne.
:::

## Verwandte Dokumentation

- [Multi-Tenancy](../../16_multi_tenancy/) - Schaffung organisatorischer Grenzen innerhalb einer Instanz
- [Kernkomponenten](../../2_architecture/1_core_components/) - AI-Hub-Architektur
- [Authentifizierung & Autorisierung](../../11_access_management/1_authentication_setup/) -
  Authentifizierungskonfiguration
- [Monitoring und Alerting](../5_monitoring_and_alerting/) - Observability für Multi-Instanz-Deployments
- [Schweizer Datenschutz](../../21_compliance/3_dsg/) - revDSG-Compliance für den öffentlichen Sektor
