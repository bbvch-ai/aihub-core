---
title: Die Infrastruktur-Schichten
source_sha: cbe968ff9f71c227670a16da25e2fce6505df1d5af94182eb5ea2ef9da765e73
---

# Die Infrastruktur-Schichten

::: warning
Diese Dokumentation richtet sich an Leser, die die in der Plattform enthaltenen Infrastrukturkomponenten und deren Rolle
vollständig verstehen möchten. Dieses Maß an Verständnis ist nicht erforderlich, um die Plattform zu betreiben oder zu
deployen, erweist sich jedoch als hilfreich, wenn Sie diese erweitern, skalieren oder modifizieren möchten. Die
folgenden Abschnitte übersetzen die Business-Ebene in technische Implementierungsdetails.
:::

## Tier 1: Kerninfrastrukturkomponenten

![Tier 1 Architektur](../../../../media/architecture/low_level/tier_1.png)

Das Fundament beginnt mit **OAuth2**, das die Authentifizierung handhabt. Wenn Benutzer auf Open-WebUI oder die Admin UI
zugreifen, validiert OAuth2 deren Anmeldeinformationen gegen den Identitätsanbieter Ihrer Organisation. Diese Komponente
wurde gegenüber einfacheren Authentifizierungsmethoden gewählt, da sie sich in bestehende Unternehmenssysteme wie Azure
AD oder Keycloak integrieren lässt, ohne Passwordsynchronisation oder benutzerdefinierte Benutzerverwaltung zu
erfordern.

::: info
Die Architekturdiagramme vereinfachen bestimmte Aspekte zugunsten der Lesbarkeit. Mehrere Hilfsdatenbanken, die einige
Tools erfordern, sind weggelassen, und einige Verbindungen zwischen Komponenten sind vereinfacht, um visuelle Unordnung
zu vermeiden. Die Diagramme erfassen die konzeptuellen Beziehungen zwischen Infrastrukturkomponenten und nicht jedes
technische Detail.
:::

Hinter der Authentifizierungsschicht dient **Traefik** als Reverse Proxy und API Gateway. Jede HTTP-Anfrage durchläuft
Traefik, das den Traffic basierend auf Pfadmustern routet, die TLS-Terminierung handhabt und Load Balancing
bereitstellt, wenn Sie Komponenten horizontal skalieren. Traefiks dynamische Konfigurationsfähigkeiten ermöglichen es
der Plattform, neue Services ohne Neustarts zu registrieren, was entscheidend für das Hinzufügen benutzerdefinierter
Agents oder zusätzlicher UI-Komponenten ist.

Die **API**-Schicht, basierend auf FastAPI, bietet mehr als einfaches Request Routing. Sie unterhält
WebSocket-Verbindungen für Echtzeit-Streaming, verwaltet den Session State für Konversationen, erzwingt Rate Limits pro
Benutzer und transformiert Requests zwischen verschiedenen Komponentenprotokollen. FastAPI wurde wegen seiner
Async-Fähigkeiten, der automatischen OpenAPI-Dokumentationsgenerierung und seiner exzellenten Performance unter
gleichzeitiger Last ausgewählt.

**LiteLLM** fungiert als universelles LLM-Gateway. Anstatt separate Integrationen für OpenAI, Anthropic, Google und
lokale Modelle zu implementieren, bietet LiteLLM eine vereinheitlichte Schnittstelle. Es handhabt die Retry Logic, wenn
Modelle überlastet sind, verfolgt die Token-Nutzung für die Kostenzuordnung, verwaltet verschiedene Rate Limits über
Anbieter hinweg und konvertiert zwischen verschiedenen modellspezifischen Formaten. Das Gateway-Pattern ermöglicht den
Wechsel von Modellen ohne Codeänderungen, was entscheidend ist, um Vendor Lock-in zu vermeiden.

Für modellspezifische Features bietet **vLLM** eine Hochleistungs-Inferenz für lokal gehostete Modelle wie Mistral oder
DeepSeek. Es verwendet PagedAttention für effizientes Memory Management, wodurch größere Modelle auf verfügbarer
Hardware ausgeführt werden können. **Presidio** fügt PII-Erkennung (Personal Identifiable Information) und
Anonymisierung hinzu, indem es Text auf sensible Datenmuster scannt, bevor dieser an externe Modelle gesendet oder in
Datenbanken gespeichert wird.

Die Speicherinfrastruktur verwendet **SeaweedFS** für S3-kompatiblen Objektspeicher und **MongoDB** für
Dokumentenspeicher. SeaweedFS speichert hochgeladene Dateien, generierte Reports und Modellartefakte mit Versionierungs-
und Lifecycle-Policies. Der SeaweedFS Filer verwendet **etcd** als sein Metadata Backend, was High-Availability
Deployments mit mehreren Filer-Instanzen ermöglicht. Die Plattform exposes zwei Schnittstellen: die **S3 API** unter
`s3.${DOMAIN}` mit AWS Signature Authentication für programmatischen Zugriff und die **Filer Web UI** unter
`datalake.${DOMAIN}` via OAuth2-Proxy für Entwickler zum Browsen und Debuggen von Dateien (erfordert die
AIHubDeveloper-Rolle). MongoDB persistiert Konversationshistorie, Benutzereinstellungen, Anwendungsdaten und
Event-Historie. Diese Entscheidungen bieten Cloud-Native Storage Patterns, die identisch funktionieren, egal ob
On-Premise oder in Cloud-Umgebungen deployed.

Die Plattform enthält integrierte AI-Tools, die das Chat-Erlebnis verbessern. **Jupyter Lab** ermöglicht
Code-Interpretation und -Ausführung, wenn Benutzer das LLM bitten, Daten zu analysieren oder Berechnungen durchzuführen.
Das LLM kann Python-Code schreiben, der sicher in einer isolierten Jupyter-Umgebung ausgeführt wird und die Ergebnisse
direkt in der Konversation zurückgibt. **SearXNG** bietet Web-Suchfunktionen, wenn Benutzer aktuelle Informationen
benötigen, indem es Ergebnisse aus mehreren Suchmaschinen aggregiert und gleichzeitig die Privatsphäre wahrt.
**Playwright** scraped Inhalte von Websites, die über die Suche entdeckt wurden, und extrahiert den vollständigen Text,
wenn Such-Snippets nicht ausreichen. **Docling** parst Dokumente, die Benutzer in den Chat hochladen, extrahiert Text
und Struktur aus PDFs, Word-Dokumenten und Präsentationen, wobei Tabellen und Formatierungen für eine genaue
Fragebeantwortung erhalten bleiben.

Observability beginnt vom ersten Tag an mit **OpenTelemetry**, das Metriken, Traces und Logs von jeder Komponente
sammelt. Die Daten fließen zu den entsprechenden Backends: Metriken zu Prometheus, Traces zu Jaeger, Logs zu Loki.
Dieser standardisierte Observability Stack bietet vereinheitlichte Dashboards, verteiltes Tracing über Services hinweg
und zentrale Log-Aggregation ohne Vendor Lock-in.

## Tier 1+: Integrationsinfrastruktur

![Tier 1+ Architektur](../../../../media/architecture/low_level/tier_1_plus.png)

Das **Azure Bot Framework** wird zur Brücke zwischen der Plattform und externen Kommunikationskanälen. Wenn eine
Nachricht von Teams, Slack oder Outlook eingeht, normalisiert das Bot Framework diese in ein Standard-Aktivitätsformat,
handhabt die kanalspezifische Authentifizierung, verwaltet den Konversationskontext und routet sie an den entsprechenden
Handler in der API.

Das Bot Framework wurde gegenüber dem Bau separater Integrationen gewählt, da es eine einzige Abstraktion über mehrere
Channels bietet. Kanalspezifische Features wie Teams Adaptive Cards oder Slack Blocks werden über dieselbe Schnittstelle
gehandhabt. Das Framework verwaltet Konversationsreferenzen, wodurch die Plattform proaktive Nachrichten Stunden oder
Tage nach der ersten Interaktion an Benutzer zurücksenden kann.

Die Verbindung zwischen dem Bot Framework und der Plattform-API erfolgt über Webhook-Endpoints. Die API implementiert
das Bot Framework Protokoll, akzeptiert Aktivitäten und gibt entsprechende Responses zurück. Diese lose Kopplung
bedeutet, dass die Plattform andere Bot Frameworks oder direkte Integrationen ohne architektonische Änderungen
unterstützen kann.

## Tier 2: Wissens- und Agent-Infrastruktur

![Tier 2 Architektur](../../../../media/architecture/low_level/tier_2.png)

**NATS** transformiert die Plattform von einer Request-Response- zu einer Event-Driven Architecture. Agents abonnieren
Event Streams, die API veröffentlicht Benutzernachrichten, und Komponenten kommunizieren asynchron ohne direkte
Abhängigkeiten. NATS JetStream bietet persistente Message Queues und stellt sicher, dass keine Events während
Agent-Restarts verloren gehen. Die Wahl von NATS gegenüber Alternativen wie RabbitMQ oder Kafka beruht auf seiner
Einfachheit, dem Embedded Clustering und der exzellenten Performance für die Small-Message Patterns, die in der
Agent-Kommunikation üblich sind.

Die Agent-Infrastruktur unterstützt mehrere gleichzeitige Agents (Standard 1-3, Custom 1-2 im Diagramm). Jeder Agent
läuft als unabhängiger Service, abonniert relevante NATS Topics und veröffentlicht Responses. Agents können ihren State
durch Replaying der Event-Historie konstruieren, auf die Vector Stores zugreifen und Telemetrie über OpenTelemetry
reporten. Dieses Microservice-Pattern ermöglicht es, Agents unabhängig zu entwickeln und zu skalieren sowie zu
aktualisieren, ohne andere Agents oder die Plattform zu beeinflussen.

**Dagster** orchestriert die Data Pipeline Infrastructure. Es plant die Dokumentenaufnahme aus Quellen wie SharePoint,
überwacht die Pipeline Health, verwaltet Abhängigkeiten zwischen Verarbeitungsschritten und bietet eine Web UI für das
Pipeline Monitoring. Dagsters Asset-basierter Ansatz behandelt jedes verarbeitete Dokument als ein Managed Asset mit
Lineage, Versionierung und Quality Checks. Die Wahl von Dagster gegenüber Alternativen wie Airflow beruht auf seiner
überlegenen Local Development Experience und nativen Python-Integration.

Pipeline Workers implementieren die eigentliche Dokumentenverarbeitung. Sie verbinden sich mit der Quelle, downloaden
Dokumente nach SeaweedFS zur Verarbeitung, parsen Inhalte mittels Docling, generieren Embeddings mithilfe konfigurierter
Modelle und speichern Ergebnisse in der Vektordatenbank. Workers skalieren horizontal, wobei Dagster die Arbeit auf die
verfügbaren Instanzen verteilt.

**Milvus** bietet Vektorspeicher für die semantische Suche. Es indiziert hochdimensionale Embeddings, führt Approximate
Nearest Neighbor Searches durch, unterstützt gefilterte Suchen, die Vektor- und Metadatenabfragen kombinieren, und
skaliert auf Milliarden von Vektoren durch Sharding. Milvus wurde gegenüber Alternativen wie Pinecone oder Weaviate
aufgrund seiner Open-Source-Natur, On-Premise-Deployment-Optionen und exzellenten Performance-Eigenschaften ausgewählt.

**Redis** bietet schnellen State Storage, den Agents verwenden, um Daten unabhängig von Events zu persistieren. Agents
speichern State in Redis, wenn sie Daten benötigen, die über Konversationsrunden hinweg bestehen bleiben oder für andere
Agent-Instanzen zugänglich sein müssen. Redis wurde aufgrund seiner extrem schnellen In-Memory-Performance und
Unabhängigkeit von Python-Prozessen gewählt, wodurch in jeder Sprache geschriebene Agents auf denselben State Store
zugreifen können.

**Phoenix** bietet AI-spezifische Observability über OpenTelemetry hinaus. Es erfasst LLM-Interaktionen mit
vollständigen Prompts und Responses, verfolgt RAG-Retrievals, die zeigen, welche Dokumente verwendet wurden, analysiert
Embedding-Qualität und -Drift und bietet spezialisierte Dashboards für AI-Metriken. Phoenix integriert sich in die
bestehende OpenTelemetry-Infrastruktur und fügt Standard-Traces AI-spezifischen Kontext hinzu.

**MCP (Model Context Protocol)** öffnet die Plattform für externe Tools. VSCode Extensions können sich für das Debugging
mit laufenden Agents verbinden, externe AI-Systeme können mit unseren Agents interagieren und Automation Tools können
Work Items an Prozesse übermitteln. MCP verwendet JSON-RPC über WebSockets und bietet einen sprachunabhängigen
Integrationspunkt. Dieses Protokoll wurde speziell für den Swiss AI Hub entwickelt, um die Tool-Integration zu
ermöglichen, ohne interne APIs freizulegen.

Über alle Tiers hinweg kommunizieren Komponenten über klar definierte Schnittstellen. HTTP/REST für synchrone Requests,
NATS für asynchrone Events und WebSockets/SSE für Echtzeit-Streaming. Dieser polyglotte Ansatz verwendet das richtige
Protokoll für jeden Anwendungsfall, anstatt alles durch ein einziges Pattern zu erzwingen.

Die Infrastruktur-Entscheidungen spiegeln operative Anforderungen wider, die durch Produktions-Deployments entdeckt
wurden. Jede Komponente kann in Containern laufen, skaliert horizontal mit Load Balancing, bietet Health Checks für
Orchestrierungsplattformen, exposes Metriken für Monitoring und unterstützt die Konfiguration über Environment
Variables. Diese operativen Eigenschaften sind ebenso wichtig wie die funktionalen Fähigkeiten, wenn eine Plattform für
den Enterprise-Deployment gebaut wird.

## Tier 3: Prozessorchestrierungs-Infrastruktur

![Tier 3 Architektur](../../../../media/architecture/low_level/tier_3.png)

Die **Process UI** führt ein neues User Interface Paradigm ein, das für Workflow-Interaktion statt für Konversation
konzipiert ist. Entwickelt mit Vue.js und über WebSockets verbunden, bietet sie Echtzeit-Workflow-Visualisierung, Task
Queues für menschliche Teilnehmer, Form Builder für strukturierte Eingaben und Audit Trails für Compliance. Die Trennung
von der Chat UI spiegelt die unterschiedlichen Interaktionsmuster wider: Chat ist explorativ und
konversationsorientiert, während Prozessinteraktion strukturiert und aufgabenorientiert ist.

Die **Prozessorchestrierung** (Process 1 im Diagramm) läuft als separater Service, der den Workflow State verwaltet. Sie
interpretiert in Python geschriebene Workflow-Definitionen, pflegt den Process Instance State in MongoDB, koordiniert
die Arbeitsverteilung über NATS, handhabt Timeouts und Fehlerbedingungen und bietet Prozessanalysen. Der Orchestrator
wurde kundenspezifisch gebaut, anstatt bestehende BPMN Engines zu verwenden, da die AI-Agent-Integration Fähigkeiten
erforderte, die über Standard-Business-Process-Patterns hinausgehen.

Externe Integrationen erweitern die Reichweite der Plattform. Die **Power Automate (PA)**-Integration erfolgt über die
Microsoft Graph API, wodurch Flows ausgelöst und Callbacks empfangen werden. **n8n** bietet eine Self-Hosted-Alternative
für Workflow-Automation, die über ihre Node Library Hunderte von Services verbindet. Die **UiPath**-Integration
ermöglicht es RPA-Bots, an Prozessen teilzunehmen und Legacy-System-Interaktionen zu handhaben, denen APIs fehlen. Diese
Integrationen verwenden, wo möglich, Webhook Patterns und greifen auf Polling zurück, wenn Webhooks nicht verfügbar
sind.
