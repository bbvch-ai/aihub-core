---
title: Die Infrastrukturebenen
source_sha: "0c1015cfa4dc0e9a4b9b3896ea9e2c78cde6a09b7cf9d4e72b4681550abd76b6"
---

# Die Infrastrukturebenen

::: warning
Diese Dokumentation richtet sich an Leser, die ein umfassendes Verständnis der in der Plattform enthaltenen Infrastrukturkomponenten und der Rolle, die sie spielen, erlangen möchten. Dieses Verständnis ist nicht zwingend erforderlich, um die Plattform zu betreiben oder zu deployen, erweist sich jedoch als hilfreich, wenn Sie diese erweitern, skalieren oder modifizieren möchten. Die folgenden Abschnitte übersetzen die Business-Ebene in technische Implementierungsdetails.
:::

## Ebene 1: Kernkomponenten der Infrastruktur

![Tier 1 Architecture](../../../../media/architecture/low_level/tier_1.png)

Das Fundament beginnt mit der Authentifizierung durch **OAuth2**. Wenn Benutzer auf Open-WebUI oder das Admin UI zugreifen, validiert OAuth2 deren Anmeldedaten gegenüber dem Identitätsanbieter Ihrer Organisation. Diese Komponente wurde gegenüber einfacheren Authentifizierungsmethoden gewählt, da sie sich in bestehende Unternehmenssysteme wie Azure AD oder Keycloak integriert, ohne Passwortsynchronisierung oder eine benutzerdefinierte Benutzerverwaltung zu erfordern.

::: info
Die Architekturdiagramme vereinfachen bestimmte Aspekte zugunsten der Lesbarkeit. Mehrere Hilfsdatenbanken, die von einigen Tools benötigt werden, sind weggelassen, und einige Verbindungen zwischen Komponenten sind vereinfacht, um visuelle Unordnung zu vermeiden. Die Diagramme erfassen die konzeptionellen Beziehungen zwischen Infrastrukturkomponenten und nicht jedes technische Detail.
:::

Hinter der Authentifizierungsschicht dient **Traefik** als Reverse Proxy und API-Gateway. Jede HTTP-Anfrage durchläuft Traefik, welches den Traffic basierend auf Pfadmustern routet, die TLS-Terminierung handhabt und den Lastausgleich bereitstellt, wenn Sie Komponenten horizontal skalieren. Die dynamischen Konfigurationsmöglichkeiten von Traefik ermöglichen es der Plattform, neue Services ohne Neustarts zu registrieren, was entscheidend für das Hinzufügen benutzerdefinierter Agents oder zusätzlicher UI-Komponenten ist.

Die **API**-Schicht, aufgebaut auf FastAPI, bietet mehr als einfaches Request-Routing. Sie unterhält WebSocket-Verbindungen für Echtzeit-Streaming, verwaltet den Session-Status für Konversationen, erzwingt Ratenbegrenzungen pro Benutzer und transformiert Requests zwischen verschiedenen Komponentenprotokollen. FastAPI wurde aufgrund seiner asynchronen Fähigkeiten, der automatischen OpenAPI-Dokumentationsgenerierung und der exzellenten Performance unter gleichzeitiger Last ausgewählt.

**LiteLLM** fungiert als universelles LLM-Gateway. Anstatt separate Integrationen für OpenAI, Anthropic, Google und lokale Modelle zu implementieren, bietet LiteLLM eine einheitliche Schnittstelle. Es handhabt die Wiederholungslogik, wenn Modelle überlastet sind, verfolgt die Token-Nutzung für die Kostenallokation, verwaltet unterschiedliche Ratenbegrenzungen über Anbieter hinweg und konvertiert zwischen verschiedenen modellspezifischen Formaten. Das Gateway-Muster ermöglicht den Modellwechsel ohne Codeänderungen, was entscheidend ist, um Vendor Lock-in zu vermeiden.

Für modellspezifische Funktionen bietet **vLLM** eine Hochleistungs-Inferenz für lokal gehostete Modelle wie Mistral oder DeepSeek. Es verwendet PagedAttention für effizientes Speichermanagement, wodurch größere Modelle auf verfügbarer Hardware ausgeführt werden können. **Presidio** fügt PII-Erkennung und Anonymisierung hinzu, scannt Texte nach sensiblen Datenmustern, bevor sie an externe Modelle gesendet oder in Datenbanken gespeichert werden.

Die Speicherinfrastruktur nutzt **SeaweedFS** für S3-kompatiblen Objektspeicher und **MongoDB** für Dokumentenspeicher. SeaweedFS speichert hochgeladene Dateien, generierte Reports und Modell-Artefakte mit Versionierung und Lifecycle-Policies. Der SeaweedFS Filer verwendet **etcd** als sein Metadaten-Backend, was Hochverfügbarkeits-Deployments mit mehreren Filer-Instanzen ermöglicht. Die Plattform stellt zwei Schnittstellen bereit: die **S3 API** unter `s3.${DOMAIN}` mit AWS-Signaturauthentifizierung für den programmatischen Zugriff und das **Filer web UI** unter `datalake.${DOMAIN}` über einen OAuth2-Proxy für Entwickler, um Dateien zu durchsuchen und zu debuggen (erfordert die Rolle AIHubDeveloper). MongoDB persistiert den Konversationsverlauf, Benutzerpräferenzen, Anwendungsdaten und den Event-Verlauf. Diese Entscheidungen bieten Cloud-native Speicher-Muster, die identisch funktionieren, egal ob On-Premise oder in Cloud-Umgebungen deployed.

Die Plattform enthält integrierte KI-Tools, die das Chat-Erlebnis verbessern. **Jupyter Lab** ermöglicht die Code-Interpretation und -Ausführung, wenn Benutzer den LLM bitten, Daten zu analysieren oder Berechnungen durchzuführen. Der LLM kann Python-Code schreiben, der sicher in einer isolierten Jupyter-Umgebung ausgeführt wird und Ergebnisse direkt in der Konversation zurückgibt. **SearXNG** bietet Web-Suchfunktionen, wenn Benutzer aktuelle Informationen benötigen, indem es Ergebnisse von mehreren Suchmaschinen aggregiert und gleichzeitig die Privatsphäre wahrt. **Playwright** extrahiert Inhalte von Websites, die über die Suche entdeckt wurden, und holt den vollständigen Text, wenn Such-Snippets nicht ausreichen. **MinerU** parst Dokumente, die Benutzer in den Chat hochladen, extrahiert Text und Struktur aus PDFs, Word-Dokumenten und Präsentationen, wobei Tabellen und Formatierungen erhalten bleiben, die für eine genaue Beantwortung von Fragen erforderlich sind.

Observability beginnt vom ersten Tag an mit der Sammlung von Metriken, Traces und Logs aus jeder Komponente durch **OpenTelemetry**. Die Daten fließen zu den entsprechenden Backends: Metriken zu Prometheus, Traces zu Jaeger, Logs zu Loki. Dieser standardisierte Observability Stack bietet vereinheitlichte Dashboards, verteiltes Tracing über Services hinweg und zentralisierte Log-Aggregation ohne Vendor Lock-in.

## Ebene 1+: Integrationsinfrastruktur

![Tier 1+ Architecture](../../../../media/architecture/low_level/tier_1_plus.png)

Das **Azure Bot Framework** wird zur Brücke zwischen der Plattform und externen Kommunikationskanälen. Wenn eine Nachricht von Teams, Slack oder Outlook eintrifft, normalisiert das Bot Framework diese in ein Standard-Aktivitätsformat, handhabt die kanalspezifische Authentifizierung, verwaltet den Konversationskontext und leitet sie an den entsprechenden Handler in der API weiter.

Das Bot Framework wurde gegenüber dem Aufbau separater Integrationen gewählt, da es eine einzige Abstraktion über mehrere Kanäle bietet. Kanalspezifische Funktionen wie Teams adaptive cards oder Slack blocks werden über dieselbe Schnittstelle gehandhabt. Das Framework verwaltet Konversationsreferenzen, wodurch die Plattform proaktive Nachrichten Stunden oder Tage nach der anfänglichen Interaktion an Benutzer zurücksenden kann.

Die Verbindung zwischen dem Bot Framework und der Plattform-API erfolgt über Webhook-Endpunkte. Die API implementiert das Bot Framework-Protokoll, akzeptiert Aktivitäten und gibt entsprechende Antworten zurück. Diese lose Kopplung bedeutet, dass die Plattform andere Bot Frameworks oder direkte Integrationen ohne architektonische Änderungen unterstützen kann.

## Ebene 2: Wissens- und Agent-Infrastruktur

![Tier 2 Architecture](../../../../media/architecture/low_level/tier_2.png)

**NATS** transformiert die Plattform von einer Request-Response-Architektur zu einer Event-gesteuerten Architektur. Agents abonnieren Event-Streams, die API veröffentlicht Benutzernachrichten, und Komponenten kommunizieren asynchron ohne direkte Abhängigkeiten. NATS JetStream bietet persistente Nachrichtenwarteschlangen, die sicherstellen, dass keine Events während Agent-Restarts verloren gehen. Die Wahl von NATS gegenüber Alternativen wie RabbitMQ oder Kafka ergibt sich aus seiner Einfachheit, dem eingebetteten Clustering und der exzellenten Performance für die in der Agent-Kommunikation üblichen Small-Message-Muster.

Die Agent-Infrastruktur unterstützt mehrere gleichzeitige Agents (Standard 1-3, Custom 1-2 im Diagramm). Jeder Agent läuft als unabhängiger Service, abonniert relevante NATS-Topics und veröffentlicht Antworten. Agents können ihren Zustand durch das Replay des Event-Verlaufs konstruieren, auf die Vektor-Stores zugreifen und Telemetrie über OpenTelemetry melden. Dieses Microservice-Muster ermöglicht es, Agents unabhängig zu entwickeln und zu skalieren sowie zu aktualisieren, ohne andere Agents oder die Plattform zu beeinflussen.

**Dagster** orchestriert die Daten-Pipeline-Infrastruktur. Es plant die Dokumentenaufnahme aus Quellen wie SharePoint, überwacht die Pipeline-Gesundheit, verwaltet Abhängigkeiten zwischen Verarbeitungsschritten und bietet ein Web-UI zur Pipeline-Überwachung. Dagsters Asset-basierter Ansatz behandelt jedes verarbeitete Dokument als ein verwaltetes Asset mit Lineage, Versionierung und Qualitätsprüfungen. Die Wahl von Dagster gegenüber Alternativen wie Airflow resultiert aus seiner überlegenen lokalen Entwicklungserfahrung und nativen Python-Integration.

Pipeline-Worker implementieren die eigentliche Dokumentenverarbeitung. Sie verbinden sich mit der Quelle, laden Dokumente zur Verarbeitung in SeaweedFS herunter, parsen Inhalte mit MinerU, generieren Embeddings unter Verwendung konfigurierter Modelle und speichern Ergebnisse in der Vektordatenbank. Worker skalieren horizontal, wobei Dagster die Arbeit auf die verfügbaren Instanzen verteilt.

**Milvus** bietet Vektorspeicher für die semantische Suche. Es indiziert hochdimensionale Embeddings, führt ungefähre Nächster-Nachbar-Suchen durch, unterstützt gefilterte Suchen, die Vektor- und Metadatenabfragen kombinieren, und skaliert durch Sharding auf Milliarden von Vektoren. Milvus wurde gegenüber Alternativen wie Pinecone oder Weaviate aufgrund seines Open-Source-Charakters, der On-Premise-Deployment-Optionen und seiner exzellenten Performance-Eigenschaften ausgewählt.

**Redis** bietet einen schnellen Statusspeicher, den Agents nutzen, um Daten ereignisunabhängig zu persistieren. Agents speichern den Status in Redis, wenn sie Daten benötigen, die über Konversationsrunden hinweg bestehen bleiben oder für andere Agent-Instanzen zugänglich sein sollen. Redis wurde aufgrund seiner extrem schnellen In-Memory-Performance und Unabhängigkeit von Python-Prozessen gewählt, wodurch Agents, die in jeder Sprache geschrieben sind, auf denselben Statusspeicher zugreifen können.

**Phoenix** bietet KI-spezifische Observability jenseits von OpenTelemetry. Es erfasst LLM-Interaktionen mit vollständigen Prompts und Responses, verfolgt RAG-Retrievals, die zeigen, welche Dokumente verwendet wurden, analysiert die Embedding-Qualität und -Drift und bietet spezialisierte Dashboards für KI-Metriken. Phoenix integriert sich in die bestehende OpenTelemetry-Infrastruktur und fügt Standard-Traces KI-spezifischen Kontext hinzu.

**MCP (Model Context Protocol)** öffnet die Plattform für externe Tools. VSCode-Erweiterungen können sich mit laufenden Agents zum Debuggen verbinden, externe KI-Systeme können mit unseren Agents interagieren und Automatisierungstools können Arbeitsaufgaben an Prozesse übermitteln. MCP verwendet JSON-RPC über WebSockets und bietet einen sprachunabhängigen Integrationspunkt. Dieses Protokoll wurde speziell für den Swiss AI Hub entwickelt, um die Tool-Integration zu ermöglichen, ohne interne APIs freizulegen.

In allen Ebenen kommunizieren Komponenten über klar definierte Schnittstellen. HTTP/REST für synchrone Requests, NATS für asynchrone Events und WebSockets/SSE für Echtzeit-Streaming. Dieser polyglotte Ansatz verwendet das richtige Protokoll für jeden Anwendungsfall, anstatt alles durch ein einziges Muster zu zwingen.

Die Infrastrukturentscheidungen spiegeln operative Anforderungen wider, die durch Produktions-Deployments ermittelt wurden. Jede Komponente kann in Containern laufen, skaliert horizontal mit Lastausgleich, bietet Health Checks für Orchestrierungsplattformen, exponiert Metriken für das Monitoring und unterstützt die Konfiguration über Umgebungsvariablen. Diese operativen Eigenschaften sind beim Aufbau einer Plattform für den Enterprise-Deployment ebenso wichtig wie die funktionalen Fähigkeiten.

## Ebene 3: Prozessorchestrierungs-Infrastruktur

![Tier 3 Architecture](../../../../media/architecture/low_level/tier_3.png)

Das **Process UI** führt ein neues Benutzeroberflächen-Paradigma ein, das für Workflow-Interaktion und nicht für Konversation konzipiert ist. Aufgebaut mit Vue.js und über WebSockets verbunden, bietet es Echtzeit-Workflow-Visualisierung, Aufgabenwarteschlangen für menschliche Teilnehmer, Formular-Builder für strukturierte Eingaben und Audit-Trails für die Compliance. Die Trennung vom Chat UI spiegelt die unterschiedlichen Interaktionsmuster wider: Chat ist explorativ und konversationell, während Prozessinteraktion strukturiert und aufgabenorientiert ist.

**Prozessorchestrierung** (Prozess 1 im Diagramm) läuft als separater Service, der den Workflow-Status verwaltet. Sie interpretiert in Python geschriebene Workflow-Definitionen, verwaltet den Prozessinstanz-Status in MongoDB, koordiniert die Arbeitsverteilung über NATS, handhabt Timeouts und Fehlerbedingungen und bietet Prozessanalysen. Der Orchestrator wurde kundenspezifisch gebaut, anstatt bestehende BPMN-Engines zu verwenden, da die Integration von KI-Agents Fähigkeiten erforderte, die über Standard-Business-Prozessmuster hinausgehen.

Externe Integrationen erweitern die Reichweite der Plattform. Die Integration von **Power Automate (PA)** erfolgt über die Microsoft Graph API, wodurch Flows ausgelöst und Callbacks empfangen werden. **n8n** bietet eine selbstgehostete Alternative für die Workflow-Automatisierung, die sich über ihre Node-Bibliothek mit Hunderten von Services verbindet. Die **UiPath**-Integration ermöglicht RPA-Bots, an Prozessen teilzunehmen und Legacy-Systeminteraktionen zu handhaben, denen APIs fehlen. Diese Integrationen verwenden nach Möglichkeit Webhook-Muster und greifen auf Polling zurück, wenn Webhooks nicht verfügbar sind.
