---
title: Bereitstellungsoptionen
source_sha: c069c3758f7241b2a3c35e2c012de80aece1f72a2e0c75030bc3377ef418b7e4
---

# Bereitstellungsoptionen

## Übersicht

Der AI-Hub kann als einzelne isolierte Instanz für eine Organisation oder als mehrere isolierte Instanzen bereitgestellt
werden, die optional Backend-LLM-Ressourcen gemeinsam nutzen.

## Single-Tenant-Bereitstellung

### Isolierte Instanz

Eine Single-Tenant-Bereitstellung betreibt eine vollständige, eigenständige AI-Hub-Instanz. Die Organisation erhält eine
dedizierte Infrastruktur: separate Datenbanken, Vektorspeicher, Dateispeicher und Anwendungsdienste. Im Gegensatz zu
Multi-Tenant-SaaS-Plattformen, bei denen Kunden Datenbanken und Anwendungsserver gemeinsam nutzen, verfügt ein Mandant
über einen eigenen dedizierten Stack.

Die Instanz umfasst die API, Agents, Pipelines, die Weboberfläche und Bot-Integrationen. Sie verfügt über eigene
Datenbanken (FerretDB/PostgreSQL), Vektorspeicher (Milvus oder Azure AI Search) und Dateispeicher (SeaweedFS oder Azure
Data Lake). Das Monitoring erfolgt über SigNoz und Phoenix. NATS übernimmt das Event-Streaming. Die Instanz verfügt über
einen eigenen LiteLLM-Proxy zur Kostenverfolgung und Versionskontrolle.

### LLM-Backend

Die Instanz verbindet sich über ihren LiteLLM-Proxy mit LLM-Diensten. Der Proxy kann sich mit Azure OpenAI, Google
Gemini, selbst gehosteten Modellen (vLLM, llama.cpp, HF-TEI) oder einer Mischung aus diesen verbinden. Der Proxy
verwaltet die Modellauswahl, Budgets, Ratenbegrenzungen und Versionen. Alle Prompts, Antworten und Benutzerdaten
verbleiben innerhalb der Mandanteninstanz.

---

## Hosting-Optionen

Der AI-Hub kann je nach den Anforderungen der Organisation auf drei Arten gehostet werden.

### On-Premise (eigenen Server bereitstellen)

Sie betreiben den AI-Hub auf Ihren eigenen Servern in Ihrem Rechenzentrum.

Sie benötigen x86_64-Server mit CPU, RAM und Speicherplatz. NVIDIA GPUs eignen sich für die selbst gehostete
LLM-Inferenz. Für den Netzwerkzugriff benötigen Sie entweder ausgehendes HTTPS für Cloud-basierte LLM-Dienste oder eine
Air-Gap-Konfiguration mit lokalen Modellen.

Die Infrastruktur liegt unter Ihrer Kontrolle. Keine Cloud-Abhängigkeiten. Funktioniert in Air-Gap-Umgebungen mit selbst
gehosteten LLMs.

---

### Private Cloud (eigene Cloud bereitstellen)

Sie betreiben den AI-Hub in Ihrer eigenen Cloud-Umgebung (Schweizer Cloud-Anbieter, Azure, AWS, GCP).

Die Daten bleiben in Ihrem Cloud-Konto unter Ihrer Kontrolle. Sie wählen die Region (z. B. Schweiz für die
Datenresidenz). Sie verwalten die Cloud-Ressourcen und -Kosten.

Cloud-Anbieter verfügen in der Regel über Sicherheits- und Compliance-Zertifizierungen. Sie benötigen
Internetkonnektivität für den LLM-Proxy-Zugriff (HTTPS), optional VPN für den administrativen Zugriff und private
Netzwerke zwischen Diensten (internes DNS).

---

### SaaS (Schweizer Cloud-Hosting)

bbv hostet und verwaltet den AI-Hub für Sie auf Schweizer Cloud-Infrastruktur.

bbv übernimmt die Bereitstellung der Infrastruktur, Updates, Backups, Monitoring und operative Aufgaben. Die Daten
verbleiben in der Schweiz unter Schweizer Rechtshoheit. Sicherheits- und Compliance-Zertifizierungen vom Cloud-Anbieter.

Sie greifen über eine Weboberfläche und APIs auf den AI-Hub zu. bbv bietet SLAs für Verfügbarkeit und Support. Weniger
operativer Aufwand für Ihr Team.

---

## Multi-Tenant-Bereitstellung

### Gemeinsames LLM-Backend

Bei der Bereitstellung mehrerer Mandanteninstanzen können diese Backend-LLM-Ressourcen gemeinsam nutzen. Mehrere
Mandanten verwenden dasselbe Azure OpenAI-Abonnement, Google Gemini API-Schlüssel oder selbst gehostete Modelle. Sie
können auch Authentifizierungsinfrastrukturen wie Azure AD oder Keycloak gemeinsam nutzen.

Jeder Mandant verfügt weiterhin über einen eigenen LiteLLM-Proxy. Der Proxy verwaltet die Modellauswahl, Budgets,
Ratenbegrenzungen und Versionen pro Mandant. Die LLM-Nutzung wird pro Mandant verfolgt. Prompts, Antworten und
Benutzerdaten verbleiben in jeder Mandanteninstanz.

Die gemeinsam genutzten LLM-Backends sind zustandslos. Sie persistieren keine Prompts oder Antworten.
Konversationskontext und -historie verbleiben in der eigenen Infrastruktur jedes Mandanten.

## Eigenschaften

### Datenisolierung

Die Daten jedes Mandanten verbleiben in seiner Instanz. Es gibt keine gemeinsame Datenbank oder Vektorspeicher. Daten
können nicht zwischen Organisationen gelangen. Die Einrichtung erfüllt die Anforderungen des Schweizer
Datenschutzgesetzes (revDSG), die GDPR-Anforderungen an die Datenisolierung und die Sicherheitsstandards des Schweizer
öffentlichen Sektors.

### Konfiguration

Jede Instanz kann unabhängig konfiguriert werden. Mandanten können benutzerdefinierte Agents, spezialisierte Pipelines
für ihre Datenquellen, ihre eigene Zugriffskontrolle (RBAC, OIDC mit lokalem IdP), benutzerdefinierte Wissensdatenbanken
und dedizierte Authentifizierungsanbieter wie Azure AD oder Keycloak bereitstellen.

### Skalierung und Updates

Die Ressourcenzuweisung erfolgt pro Mandant. Sie skalieren Rechenleistung, Arbeitsspeicher und Speicherplatz basierend
auf der tatsächlichen Nutzung. Jeder Mandant kann Updates nach seinem eigenen Zeitplan anwenden. Das Testen neuer
Funktionen in einer Instanz hat keine Auswirkungen auf andere. SLAs variieren je nach Vertrag.

### Compliance und Auditierung

Auditoren können die Infrastruktur eines einzelnen Mandanten überprüfen. Protokolle und Traces verbleiben innerhalb der
Mandanteninstanz. Aufbewahrungsrichtlinien für Backups können pro Mandant konfiguriert werden. Penetrationstests können
auf einzelne Instanzen zugeschnitten werden.

## Bereitstellungsmodell

### Single-Tenant-Infrastruktur

Eine Single-Tenant-Bereitstellung enthält:

```
Tenant Instance
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

Der LiteLLM-Proxy verbindet sich mit LLM-Diensten (Azure OpenAI, Google Gemini, selbst gehostete Modelle).

### Multi-Tenant-Infrastruktur

Bei der Bereitstellung mehrerer Mandanten erhält jeder Mandant die gleiche oben gezeigte Infrastruktur. Sie können
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

- Jeder Mandant verfügt über eine eigene LiteLLM-Proxy-Instanz
- Die LiteLLM-Proxys der Mandanten verbinden sich mit gemeinsam genutzten LLM-Backends (Azure OpenAI, Gemini, selbst
  gehostete Modelle)
- Gemeinsam genutzte LLM-Backends verwenden gemeinsame API-Anmeldeinformationen (konfiguriert pro LiteLLM des Mandanten)
- Keine direkte Kommunikation zwischen Mandanteninstanzen
- Optional: Gemeinsamer Authentifizierungsanbieter (Azure AD, Keycloak)

Datenisolierung und -souveränität. Unabhängige Skalierung und Ressourcenzuweisung. Benutzerdefinierte Konfigurationen
pro Mandant. Flexible Update-Zeitpläne. Klare Compliance-Grenzen.

---

## Architekturdiagramme

### Single-Tenant-Bereitstellung

```mermaid
graph TB
    subgraph Tenant["Tenant Instance"]
        Stack["Full Stack<br/>(API, Agents, DB, Vector Store)"]
        Proxy["LiteLLM Proxy"]
        Stack --- Proxy
    end

    Backend["LLM Backend<br/>(Azure OpenAI, Gemini, vLLM)"]

    Proxy -->|HTTPS| Backend

    classDef default font-size:16px,padding:20px
```

Die Mandanteninstanz verbindet sich über ihren LiteLLM-Proxy mit LLM-Diensten.

### Multi-Tenant-Bereitstellung mit gemeinsamem LLM-Backend

```mermaid
graph TB
    Backend["Shared LLM Backend<br/>(Azure OpenAI, Gemini, vLLM)"]

    subgraph Tenant1["Tenant 1"]
        T1Stack["Full Stack<br/>(API, Agents, DB, Vector Store)"]
        T1Proxy["LiteLLM Proxy"]
        T1Stack --- T1Proxy
    end

    subgraph Tenant2["Tenant 2"]
        T2Stack["Full Stack<br/>(API, Agents, DB, Vector Store)"]
        T2Proxy["LiteLLM Proxy"]
        T2Stack --- T2Proxy
    end

    subgraph Tenant3["Tenant 3"]
        T3Stack["Full Stack<br/>(API, Agents, DB, Vector Store)"]
        T3Proxy["LiteLLM Proxy"]
        T3Stack --- T3Proxy
    end

    T1Proxy -->|HTTPS| Backend
    T2Proxy -->|HTTPS| Backend
    T3Proxy -->|HTTPS| Backend

    classDef default font-size:16px,padding:20px
```

Jeder Mandant verfügt über eine eigene LiteLLM-Proxy-Instanz (unabhängige Kostenverfolgung, Versionierung,
Konfiguration). Alle LiteLLM-Proxys der Mandanten verbinden sich mit gemeinsam genutzten LLM-Backend-Ressourcen (Azure
OpenAI-Abonnements, selbst gehostete Modelle). Prompts, Antworten und Benutzerdaten bleiben innerhalb der
Mandantengrenzen.

---

## Sicherheitsaspekte

### Mandantenisolierung

Mandanteninstanzen kommunizieren nicht miteinander. Jeder Mandant verfügt über separate Datenbanken, Vektorspeicher und
Dateispeicher. Jeder Mandant verbindet sich mit seinem eigenen IdP (Azure AD, Keycloak). LiteLLM erzwingt pro-Mandant
API-Schlüssel und Kontingente.

### Sicherheit des LLM-Proxys

LiteLLM persistiert keine Prompts oder Antworten (zustandsloser Betrieb). Die API-Schlüsselverwaltung umfasst sichere
Schlüsselgenerierung, -rotation und -widerruf. Pro-Mandant-Anfragelimits verhindern Missbrauch. Alle LLM-Anfragen werden
mit Mandanten-ID, aber ohne Prompt-Inhalt protokolliert. Die Presidio-Integration ist optional für die PII-Erkennung und
-Redaktion.

### Datenübertragung

Die gesamte Kommunikation wird mit TLS verschlüsselt (Mandant zum LLM-Proxy). Das Zertifikatsmanagement verwendet Let's
Encrypt für die Produktion und mkcert für die Entwicklung. Die API-Authentifizierung verwendet Bearer-Tokens (OAuth 2.0,
JWT).

### Datenruhe

PostgreSQL verwendet transparente Datenverschlüsselung (TDE). Persistente Volumes sind verschlüsselt (LUKS, Azure Disk
Encryption). Geheimnisse werden über Umgebungsvariablen, Azure Key Vault oder Docker Secrets verwaltet.

---

## Nächste Schritte

- [Produktionskonfiguration](../2_production_configuration/) – Konfigurationsleitfaden für Produktionsbereitstellungen
- [Skalierungsaspekte](../3_scaling_considerations/) – Skalierung von Mandanteninstanzen
- [Backup und Wiederherstellung](../4_backup_and_recovery/) – Backup-Strategien für die Pro-Mandant-Architektur
- [Updates und Wartung](../6_updates_and_maintenance/) – Verwaltung von Updates über mehrere Instanzen hinweg

---

## FAQ

::: details Können Mandanten Agents oder Pipelines teilen?
Nein. Jede Mandanteninstanz verfügt über einen eigenen isolierten Satz von Agents und Pipelines. Dieselben
Agent-Definitionen (Code) können jedoch über mehrere Mandanteninstanzen hinweg bereitgestellt werden. Anpassungen sind
mandantenspezifisch.
:::

::: details Welche Daten sieht das gemeinsame LLM-Backend?
Jeder Mandant verfügt über einen eigenen LiteLLM-Proxy, sodass Prompts und Antworten innerhalb der Mandanteninstanz
verbleiben. Die gemeinsam genutzten LLM-Backends (Azure OpenAI, Gemini, selbst gehostete Modelle) sehen API-Anfragen von
mehreren LiteLLM-Proxys der Mandanten (zustandslos, nicht persistent), Modellanfragen (Prompts und Vervollständigungen
nur während der Übertragung), keine Mandantenidentifikation oder Kontext und anonyme PII-Daten, falls aktiviert.

Sie sehen nicht, welcher Mandant die Anfrage gestellt hat, die Konversationshistorie oder gespeicherte Daten. Der
gesamte Kontext verbleibt im LiteLLM-Proxy und der Datenbank des Mandanten.
:::

::: details Kann ein Mandant ausschliesslich selbst gehostete Modelle verwenden?
Ja. Für Air-Gap- oder vollständig On-Premise-Bereitstellungen können Sie selbst gehostete LLMs (vLLM, llama.cpp, HF-TEI)
bereitstellen, LiteLLM so konfigurieren, dass es an lokale Modelle weiterleitet, und dies ohne erforderliche ausgehende
Internetverbindung betreiben.
:::

::: details Wie werden die Kosten pro Mandant verfolgt?
LiteLLM verfolgt die API-Nutzung pro Mandant und Benutzer: Token-Anzahl (Eingabe/Ausgabe), Modellnutzung (GPT-4, Gemini
usw.), Kostenberechnungen basierend auf der Modellpreisgestaltung und die Durchsetzung des monatlichen Budgets.

Daten sind in der LiteLLM-Admin-UI verfügbar und für die Abrechnung exportierbar.
:::

::: details Können Mandanten unterschiedlichen LLM-Zugriff haben?
Ja. Die LiteLLM-Konfiguration ermöglicht den Zugriff auf Modelle pro Mandant. Zum Beispiel könnte Mandant A nur GPT-4o
für strikte Compliance verwenden, Mandant B könnte GPT-4o plus Gemini 2.0 für mehr Flexibilität nutzen, und Mandant C
könnte ausschließlich selbst gehostete Modelle für eine Air-Gap-Bereitstellung verwenden.
:::

::: details Was passiert, wenn der LLM-Proxy nicht verfügbar ist?
Mandanteninstanzen werden eine Verschlechterung der LLM-abhängigen Funktionen erfahren. RAG-Agents können keine
Antworten generieren. Embeddings können nicht für neue Dokumente erstellt werden. Vorhandene Daten und die
Benutzeroberfläche bleiben jedoch zugänglich, und nicht-LLM-Funktionen (Dokumenten-Upload, RBAC, Observability)
funktionieren weiterhin.

Minderung: LiteLLM mit hoher Verfügbarkeit (mehrere Replikas, Lastausgleich) bereitstellen.
:::

::: details Wie verwalten Sie Updates über viele Mandanteninstanzen hinweg?
Siehe [Updates und Wartung](../6_updates_and_maintenance/) für Strategien, einschliesslich gestaffelter Rollouts (Pilot-
zu Produktionsumgebung), Blue-Green-Deployments, automatisierte Update-Orchestrierung (Ansible, Kubernetes-Operatoren)
und pro-Mandant-Update-Zeitpläne.
:::

## Verwandte Dokumentation

- [Kernkomponenten](/de/docs/2_platform/2_architecture/1_core_components/) – AI-Hub-Architektur
- [Authentifizierung & Autorisierung](/de/docs/2_platform/11_access_management/1_authentication_setup/) –
  Mandantenauthentifizierungskonfiguration
- [Monitoring und Alerting](../5_monitoring_and_alerting/) – Observability für Multi-Instanz-Bereitstellungen
- [Schweizer Datenschutz](/de/docs/2_platform/20_compliance/3_dsg/) – revDSG-Compliance für den öffentlichen Sektor
