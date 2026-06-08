---
title: Die Infrastruktur-Ebenen
source_sha: f051cd57ca616c34d6d019af0ccd811a1ea230404bdb00e5b79870dfb229ed5a
---

# Die Infrastruktur-Ebenen

::: warning
Diese Dokumentation richtet sich an Leser, die die in der Plattform enthaltenen Infrastrukturkomponenten und deren Rolle
vollständig verstehen möchten. Dieses Verständnis ist nicht erforderlich, um die Plattform zu betreiben oder zu
deployen, erweist sich aber als hilfreich, wenn Sie sie erweitern, skalieren oder modifizieren möchten. Die folgenden
Abschnitte übersetzen die geschäftliche Sichtweise in technische Implementierungsdetails.
:::

## Ebene 1: Kerninfrastrukturkomponenten

![Tier 1 Architecture](../../../media/architecture/low_level/tier_1.svg)

Die Grundlage beginnt mit **OAuth2**, das die Authentifizierung handhabt. Wenn Benutzer auf Open-WebUI oder die Admin UI
zugreifen, validiert OAuth2 deren Anmeldeinformationen gegenüber dem Identitätsprovider Ihrer Organisation. Diese
Komponente wurde gegenüber einfacheren Authentifizierungsmethoden gewählt, da sie sich in bestehende Unternehmenssysteme
wie Azure AD oder Keycloak integrieren lässt, ohne Passwordsynchronisierung oder benutzerdefinierte Benutzerverwaltung
zu erfordern.

::: info
Die Architekturdiagramme vereinfachen bestimmte Aspekte zugunsten der Lesbarkeit. Mehrere Hilfsdatenbanken, die einige
Tools benötigen, sind weggelassen, und einige Verbindungen zwischen Komponenten sind vereinfacht, um visuelle Unordnung
zu vermeiden. Die Diagramme erfassen die konzeptionellen Beziehungen zwischen Infrastrukturkomponenten und nicht jedes
technische Detail.
:::

Hinter der Authentifizierungsschicht dient **Traefik** als Reverse Proxy und API Gateway. Jede HTTP-Anfrage läuft durch
Traefik, das den Datenverkehr basierend auf Pfadmustern routet, die TLS-Terminierung handhabt und Lastverteilung bietet,
wenn Sie Komponenten horizontal skalieren. Traefiks dynamische Konfigurationsfähigkeiten ermöglichen der Plattform, neue
Services ohne Neustarts zu registrieren, was entscheidend für das Hinzufügen benutzerdefinierter Agents oder
zusätzlicher UI-Komponenten ist.

Die auf FastAPI basierende **API**-Schicht bietet mehr als einfaches Request-Routing. Sie unterhält
WebSocket-Verbindungen für Echtzeit-Streaming, verwaltet den Session-Zustand für Konversationen, erzwingt
Ratenbegrenzungen pro Benutzer und transformiert Anfragen zwischen verschiedenen Komponentenprotokollen. FastAPI wurde
aufgrund seiner Async-Fähigkeiten, der automatischen OpenAPI-Dokumentationsgenerierung und der exzellenten Performance
unter gleichzeitiger Last ausgewählt.

**LiteLLM** fungiert als universelles LLM-Gateway. Anstatt separate Integrationen für OpenAI, Anthropic, Google und
lokale Modelle zu implementieren, bietet LiteLLM eine einheitliche Schnittstelle. Es handhabt die Wiederholungslogik,
wenn Modelle überlastet sind, verfolgt die Token-Nutzung für die Kostenverteilung, verwaltet verschiedene
Ratenbegrenzungen über Anbieter hinweg und konvertiert zwischen verschiedenen modellspezifischen Formaten. Das
Gateway-Muster ermöglicht den Modellwechsel ohne Codeänderungen, was entscheidend ist, um Vendor Lock-in zu vermeiden.

Für modellspezifische Features bietet **vLLM** eine Hochleistungs-Inferenz für lokal gehostete Modelle wie Mistral oder
DeepSeek. Es verwendet PagedAttention für effizientes Speichermanagement, wodurch größere Modelle auf verfügbarer
Hardware ausgeführt werden können. **Presidio** fügt PII-Erkennung und Anonymisierung hinzu, indem es Texte auf sensible
Datenmuster scannt, bevor sie an externe Modelle gesendet oder in Datenbanken gespeichert werden.

Die Speicherinfrastruktur nutzt **SeaweedFS** für S3-kompatiblen Objektspeicher und **MongoDB** für Dokumentspeicher.
SeaweedFS speichert hochgeladene Dateien, generierte Berichte und Modell-Artefakte mit Versionierung und
Lifecycle-Richtlinien. Der SeaweedFS Filer verwendet **etcd** als sein Metadaten-Backend, was
Hochverfügbarkeits-Deployments mit mehreren Filer-Instanzen ermöglicht. Die Plattform stellt zwei Schnittstellen bereit:
die **S3 API** unter `s3.${DOMAIN}` mit AWS-Signaturauthentifizierung für den programmatischen Zugriff und die **Filer
Web UI** unter `datalake.${DOMAIN}` über einen OAuth2-Proxy für Entwickler zum Durchsuchen und Debuggen von Dateien
(erfordert die Rolle AIHubDeveloper). MongoDB speichert den Konversationsverlauf, Benutzerpräferenzen, Anwendungsdaten
und den Ereignisverlauf dauerhaft. Diese Auswahl bietet Cloud-native Speichermuster, die identisch funktionieren, ob
On-Premise oder in Cloud-Umgebungen deployed.

Die Plattform enthält integrierte KI-Tools, die das Chat-Erlebnis verbessern. **Jupyter Lab** ermöglicht die
Code-Interpretation und -Ausführung, wenn Benutzer das LLM bitten, Daten zu analysieren oder Berechnungen durchzuführen.
Das LLM kann Python-Code schreiben, der sicher in einer isolierten Jupyter-Umgebung ausgeführt wird und Ergebnisse
direkt in die Konversation zurückgibt. **SearXNG** bietet Web-Suchfunktionen, wenn Benutzer aktuelle Informationen
benötigen, indem es Ergebnisse von mehreren Suchmaschinen aggregiert und gleichzeitig die Privatsphäre wahrt.
**Playwright** scraped Inhalte von Websites, die über die Suche gefunden wurden, und extrahiert den vollständigen Text,
wenn Such-Snippets nicht ausreichen. **MinerU** parst Dokumente, die Benutzer in den Chat hochladen, extrahiert Text und
Struktur aus PDFs, Word-Dokumenten und Präsentationen, wobei Tabellen und Formatierungen erhalten bleiben, die für eine
genaue Fragebeantwortung erforderlich sind.

Observability beginnt vom ersten Tag an mit **OpenTelemetry**, das Metriken, Traces und Logs von jeder Komponente
sammelt. Die Daten fließen zu den entsprechenden Backends: Metriken zu Prometheus, Traces zu Jaeger, Logs zu Loki.
Dieser standardisierte Observability-Stack bietet vereinheitlichte Dashboards, verteiltes Tracing über Services hinweg
und zentralisierte Log-Aggregation ohne Vendor Lock-in.

## Ebene 1+: Integrationsinfrastruktur

![Tier 1+ Architecture](../../../media/architecture/low_level/tier_1_plus.svg)

Das **Azure Bot Framework** wird zur Brücke zwischen der Plattform und externen Kommunikationskanälen. Wenn eine
Nachricht von Teams, Slack oder Outlook eingeht, normalisiert das Bot Framework sie in ein Standardaktivitätsformat,
handhabt die kanalspezifische Authentifizierung, verwaltet den Konversationskontext und leitet sie an den entsprechenden
Handler in der API weiter.

Das Bot Framework wurde gegenüber dem Aufbau separater Integrationen gewählt, da es eine einzige Abstraktion über
mehrere Kanäle hinweg bietet. Kanalspezifische Funktionen wie Teams Adaptive Cards oder Slack Blocks werden über
dieselbe Schnittstelle gehandhabt. Das Framework verwaltet Konversationsreferenzen, wodurch die Plattform proaktive
Nachrichten Stunden oder Tage nach der ursprünglichen Interaktion an Benutzer zurücksenden kann.

Die Verbindung zwischen dem Bot Framework und der Plattform-API erfolgt über Webhook-Endpunkte. Die API implementiert
das Bot Framework-Protokoll, akzeptiert Aktivitäten und gibt entsprechende Antworten zurück. Diese lose Kopplung
bedeutet, dass die Plattform andere Bot Frameworks oder direkte Integrationen ohne architektonische Änderungen
unterstützen kann.

## Ebene 2: Wissens- und Agent-Infrastruktur

![Tier 2 Architecture](../../../media/architecture/low_level/tier_2.svg)

**NATS** transformiert die Plattform von einer Request-Response- zu einer ereignisgesteuerten Architektur. Agents
abonnieren Ereignisströme, die API veröffentlicht Benutzernachrichten, und Komponenten kommunizieren asynchron ohne
direkte Abhängigkeiten. NATS JetStream bietet persistente Nachrichtenwarteschlangen, die sicherstellen, dass bei
Agent-Neustarts keine Ereignisse verloren gehen. Die Wahl von NATS gegenüber Alternativen wie RabbitMQ oder Kafka ergibt
sich aus seiner Einfachheit, dem eingebetteten Clustering und der exzellenten Performance für die in der
Agent-Kommunikation üblichen Muster kleiner Nachrichten.

Die Agent-Infrastruktur unterstützt mehrere gleichzeitige Agents (Standard 1-3, Benutzerdefiniert 1-2 im Diagramm).
Jeder Agent läuft als unabhängiger Service, abonniert relevante NATS-Topics und veröffentlicht Antworten. Agents können
ihren Zustand durch Wiederholung der Ereignishistorie aufbauen, auf die Vektorspeicher zugreifen und Telemetriedaten
über OpenTelemetry melden. Dieses Microservice-Muster ermöglicht es, Agents unabhängig zu entwickeln und zu skalieren
sowie zu aktualisieren, ohne andere Agents oder die Plattform zu beeinträchtigen.

**Dagster** orchestriert die Datenpipeline-Infrastruktur. Es plant die Dokumentenaufnahme aus Quellen wie SharePoint,
überwacht den Pipeline-Zustand, verwaltet Abhängigkeiten zwischen Verarbeitungsschritten und bietet eine Web-UI für die
Pipeline-Überwachung. Dagsters Asset-basierter Ansatz behandelt jedes verarbeitete Dokument als verwaltetes Asset mit
Lineage, Versionierung und Qualitätsprüfungen. Die Wahl von Dagster gegenüber Alternativen wie Airflow resultiert aus
seiner überlegenen lokalen Entwicklungserfahrung und nativen Python-Integration.

Pipeline Worker implementieren die eigentliche Dokumentenverarbeitung. Sie verbinden sich mit der Quelle, laden
Dokumente zur Verarbeitung nach SeaweedFS herunter, parsen Inhalte mit MinerU, generieren Embeddings mit konfigurierten
Modellen und speichern Ergebnisse in der Vektordatenbank. Worker skalieren horizontal, wobei Dagster die Arbeit auf die
verfügbaren Instanzen verteilt.

**Milvus** bietet Vektorspeicher für die semantische Suche. Es indiziert hochdimensionale Embeddings, führt ungefähre
Nächste-Nachbarn-Suchen durch, unterstützt gefilterte Suchen, die Vektor- und Metadatenabfragen kombinieren, und
skaliert durch Sharding auf Milliarden von Vektoren. Milvus wurde gegenüber Alternativen wie Pinecone oder Weaviate
aufgrund seiner Open-Source-Natur, On-Premise-Deployment-Optionen und exzellenten Performance-Eigenschaften ausgewählt.

**Redis** bietet einen schnellen Zustandsspeicher, den Agents verwenden, um Daten unabhängig von Ereignissen persistent
zu speichern. Agents speichern den Zustand in Redis, wenn sie Daten benötigen, die über Konversationsrunden hinweg
bestehen bleiben oder für andere Agent-Instanzen zugänglich sein sollen. Redis wurde aufgrund seiner extrem schnellen
In-Memory-Performance und Unabhängigkeit von Python-Prozessen gewählt, wodurch Agents, die in jeder Sprache geschrieben
sind, auf denselben Zustandsspeicher zugreifen können.

**Langfuse** bietet KI-spezifische Observability über OpenTelemetry hinaus. Es erfasst LLM-Interaktionen mit
vollständigen Prompts und Antworten, verfolgt RAG-Retrievals, die zeigen, welche Dokumente verwendet wurden, verfolgt
Kosten pro Trace und pro Benutzer und bietet Dataset-Management mit Experimentbewertung. Langfuse integriert sich in die
bestehende OpenTelemetry-Infrastruktur und fügt Standard-Traces KI-spezifischen Kontext hinzu. Es unterstützt Azure AD
SSO für die Zugriffskontrolle in der Produktion.

**MCP (Model Context Protocol)** öffnet die Plattform für externe Tools. VSCode-Erweiterungen können sich mit laufenden
Agents zum Debuggen verbinden, externe KI-Systeme können mit unseren Agents interagieren, und Automatisierungstools
können Arbeitselemente an Prozesse übermitteln. MCP verwendet JSON-RPC über WebSockets und bietet einen
sprachunabhängigen Integrationspunkt. Dieses Protokoll wurde speziell für den Swiss AI Hub entwickelt, um die
Tool-Integration zu ermöglichen, ohne interne APIs freizulegen.

In allen Ebenen kommunizieren Komponenten über klar definierte Schnittstellen. HTTP/REST für synchrone Anfragen, NATS
für asynchrone Ereignisse und WebSockets/SSE für Echtzeit-Streaming. Dieser polyglotte Ansatz verwendet das richtige
Protokoll für jeden Anwendungsfall, anstatt alles durch ein einziges Muster zu zwingen.

Die Infrastruktur-Entscheidungen spiegeln operative Anforderungen wider, die durch Produktions-Deployments entdeckt
wurden. Jede Komponente kann in Containern laufen, skaliert horizontal mit Load Balancing, bietet Health Checks für
Orchestrierungsplattformen, stellt Metriken für die Überwachung bereit und unterstützt die Konfiguration über
Umgebungsvariablen. Diese operativen Eigenschaften sind ebenso wichtig wie funktionale Fähigkeiten, wenn eine Plattform
für den Unternehmenseinsatz gebaut wird.

## Ebene 3: Prozessorchestrierungs-Infrastruktur

![Tier 3 Architecture](../../../media/architecture/low_level/tier_3.svg)

Die **Process UI** führt ein neues Benutzeroberflächenparadigma ein, das für Workflow-Interaktion und nicht für
Konversationen konzipiert ist. Mit Vue.js erstellt und über WebSockets verbunden, bietet sie
Echtzeit-Workflow-Visualisierung, Aufgabenwarteschlangen für menschliche Teilnehmer, Formulargeneratoren für
strukturierte Eingaben und Audit-Trails für die Compliance. Die Trennung von der Chat UI spiegelt die unterschiedlichen
Interaktionsmuster wider: Chat ist explorativ und konversationell, während Prozessinteraktion strukturiert und
aufgabenorientiert ist.

**Prozessorchestrierung** (Prozess 1 im Diagramm) läuft als separater Service, der den Workflow-Zustand verwaltet. Sie
interpretiert in Python geschriebene Workflow-Definitionen, verwaltet den Prozessinstanzzustand in MongoDB, koordiniert
die Arbeitsverteilung über NATS, handhabt Timeouts und Fehlerbedingungen und bietet Prozessanalysen. Der Orchestrator
wurde kundenspezifisch entwickelt, anstatt bestehende BPMN-Engines zu verwenden, da die Integration von KI-Agents
Fähigkeiten erforderte, die über Standard-Geschäftsprozessmuster hinausgehen.

Externe Integrationen erweitern die Reichweite der Plattform. Die **Power Automate (PA)** Integration erfolgt über die
Microsoft Graph API, wodurch Flows ausgelöst und Callbacks empfangen werden. **n8n** bietet eine selbst gehostete
Alternative für die Workflow-Automatisierung, die über ihre Node-Bibliothek Hunderte von Services verbindet. Die
**UiPath**-Integration ermöglicht RPA-Bots die Teilnahme an Prozessen, wodurch Interaktionen mit Legacy-Systemen
gehandhabt werden, denen APIs fehlen. Diese Integrationen verwenden nach Möglichkeit Webhook-Muster und greifen auf
Polling zurück, wenn Webhooks nicht verfügbar sind.
