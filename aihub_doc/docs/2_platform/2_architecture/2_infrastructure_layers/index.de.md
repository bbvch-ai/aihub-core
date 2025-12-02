---
title: Die Infrastruktur-Ebenen
source_sha: "349223976ea6d539856877703062de35ab3453524e2ea74c0676401fb8b97220"
---

# Die Infrastruktur-Ebenen

::: warning
Diese Dokumentation richtet sich an Leser, die die in der Plattform enthaltenen Infrastrukturkomponenten und deren Rolle vollständig verstehen möchten. Dieses Verständnisniveau ist nicht erforderlich, um die Plattform zu betreiben oder zu deployen, erweist sich jedoch als hilfreich, wenn Sie diese erweitern, skalieren oder modifizieren möchten. Die folgenden Abschnitte übersetzen die Business-Ebene-Ansicht in technische Implementierungsdetails.
:::

## Tier 1: Kerninfrastrukturkomponenten

![Tier 1 Architecture](../../../../media/architecture/low_level/tier_1.png)

Die Grundlage beginnt mit **OAuth2** zur Authentifizierung. Wenn Benutzer auf Open-WebUI oder die Admin UI zugreifen, validiert OAuth2 deren Anmeldeinformationen gegen den Identitätsprovider Ihrer Organisation. Diese Komponente wurde gegenüber einfacheren Authentifizierungsmethoden gewählt, da sie sich in bestehende Unternehmenssysteme wie Azure AD oder Keycloak integrieren lässt, ohne Passwordsynchronisierung oder benutzerdefinierte Benutzerverwaltung zu erfordern.

::: info
Die Architekturdiagramme vereinfachen bestimmte Aspekte zugunsten der Lesbarkeit. Mehrere Hilfsdatenbanken, die einige Tools erfordern, wurden weggelassen, und einige Verbindungen zwischen Komponenten wurden vereinfacht, um visuelle Unordnung zu vermeiden. Die Diagramme erfassen die konzeptionellen Beziehungen zwischen Infrastrukturkomponenten und nicht jedes technische Detail.
:::

Hinter der Authentifizierungsebene dient **Traefik** als Reverse Proxy und API-Gateway. Jede HTTP-Anfrage passiert Traefik, das den Datenverkehr basierend auf Pfadmustern routet, die TLS-Terminierung handhabt und Lastverteilung bietet, wenn Sie Komponenten horizontal skalieren. Traefiks dynamische Konfigurationsmöglichkeiten ermöglichen es der Plattform, neue Services ohne Neustarts zu registrieren, was für das Hinzufügen benutzerdefinierter Agents oder zusätzlicher UI-Komponenten entscheidend ist.

Die **API**-Ebene, basierend auf FastAPI, bietet mehr als einfache Anfragenweiterleitung. Sie unterhält WebSocket-Verbindungen für Echtzeit-Streaming, verwaltet den Sitzungszustand für Konversationen, erzwingt Ratenbegrenzungen pro Benutzer und transformiert Anfragen zwischen verschiedenen Komponentenprotokollen. FastAPI wurde aufgrund seiner asynchronen Fähigkeiten, der automatischen OpenAPI-Dokumentationsgenerierung und seiner hervorragenden Leistung unter gleichzeitiger Last ausgewählt.

**LiteLLM** fungiert als universelles LLM-Gateway. Anstatt separate Integrationen für OpenAI, Anthropic, Google und lokale Modelle zu implementieren, bietet LiteLLM eine einheitliche Schnittstelle. Es handhabt Wiederholungslogik, wenn Modelle überlastet sind, verfolgt die Token-Nutzung für die Kostenallokation, verwaltet unterschiedliche Ratenbegrenzungen über Anbieter hinweg und konvertiert zwischen verschiedenen modellspezifischen Formaten. Das Gateway-Muster ermöglicht den Modellwechsel ohne Codeänderungen, was für die Vermeidung von Anbieterbindung entscheidend ist.

Für modellspezifische Funktionen bietet **vLLM** eine Hochleistungs-Inferenz für lokal gehostete Modelle wie Mistral oder DeepSeek. Es verwendet PagedAttention für effizientes Speichermanagement, wodurch größere Modelle auf der verfügbaren Hardware ausgeführt werden können. **Presidio** fügt PII-Erkennung und -Anonymisierung hinzu, scannt Texte nach sensiblen Datenmustern, bevor diese an externe Modelle gesendet oder in Datenbanken gespeichert werden.

Die Speicherinfrastruktur nutzt **SeaweedFS** für S3-kompatiblen Objektspeicher und **MongoDB** für Dokumentenspeicher. SeaweedFS speichert hochgeladene Dateien, generierte Berichte und Modell-Artefakte mit Versionierung und Lifecycle-Policies. Der SeaweedFS Filer verwendet **etcd** als Metadaten-Backend und ermöglicht so Hochverfügbarkeits-Deployments mit mehreren Filer-Instanzen. Die S3-API wird unter `s3.${DOMAIN}` mit AWS-Signaturauthentifizierung exponiert, während die Filer-Web-UI intern bleibt. MongoDB speichert Konversationsverläufe, Benutzereinstellungen, Anwendungsdaten und Ereignisverläufe. Diese Auswahl bietet Cloud-native Speicher-Muster, die identisch funktionieren, ob On-Premise oder in Cloud-Umgebungen deployed.

Die Plattform umfasst integrierte KI-Tools, die das Chat-Erlebnis verbessern. **Jupyter Lab** ermöglicht die Code-Interpretation und -Ausführung, wenn Benutzer das LLM bitten, Daten zu analysieren oder Berechnungen durchzuführen. Das LLM kann Python-Code schreiben, der sicher in einer isolierten Jupyter-Umgebung ausgeführt wird und die Ergebnisse direkt in der Konversation zurückgibt. **SearXNG** bietet Web-Suchfunktionen, wenn Benutzer aktuelle Informationen benötigen, indem es Ergebnisse von mehreren Suchmaschinen aggregiert und gleichzeitig die Privatsphäre wahrt. **Playwright** extrahiert Inhalte von über die Suche entdeckten Websites und holt den vollständigen Text, wenn Such-Snippets nicht ausreichen. **Docling** parst Dokumente, die Benutzer in den Chat hochladen, extrahiert Text und Struktur aus PDFs, Word-Dokumenten und Präsentationen, wobei Tabellen und Formatierungen für eine präzise Fragenbeantwortung erhalten bleiben.

Observability beginnt vom ersten Tag an mit **OpenTelemetry**, das Metriken, Traces und Logs von jeder Komponente sammelt. Die Daten fließen zu den entsprechenden Backends: Metriken zu Prometheus, Traces zu Jaeger, Logs zu Loki. Dieser standardisierte Observability-Stack bietet einheitliche Dashboards, verteiltes Tracing über Services hinweg und zentralisierte Log-Aggregation ohne Anbieterbindung.

## Tier 1+: Integrationsinfrastruktur

![Tier 1+ Architecture](../../../../media/architecture/low_level/tier_1_plus.png)

Das **Azure Bot Framework** wird zur Brücke zwischen der Plattform und externen Kommunikationskanälen. Wenn eine Nachricht von Teams, Slack oder Outlook eingeht, normalisiert das Bot Framework diese in ein standardmäßiges Aktivitätsformat, handhabt kanalspezifische Authentifizierung, verwaltet den Konversationskontext und leitet sie an den entsprechenden Handler in der API weiter.

Das Bot Framework wurde gegenüber dem Bau separater Integrationen gewählt, da es eine einzige Abstraktion über mehrere Kanäle bietet. Kanalspezifische Funktionen wie Teams adaptive cards oder Slack blocks werden über dieselbe Schnittstelle gehandhabt. Das Framework verwaltet Konversationsreferenzen, wodurch die Plattform proaktive Nachrichten Stunden oder Tage nach der ersten Interaktion an Benutzer zurücksenden kann.

Die Verbindung zwischen dem Bot Framework und der Plattform-API erfolgt über Webhook-Endpunkte. Die API implementiert das Bot Framework-Protokoll, akzeptiert Aktivitäten und gibt entsprechende Antworten zurück. Diese lose Kopplung bedeutet, dass die Plattform andere Bot-Frameworks oder direkte Integrationen ohne architektonische Änderungen unterstützen kann.

## Tier 2: Wissens- und Agent-Infrastruktur

![Tier 2 Architecture](../../../../media/architecture/low_level/tier_2.png)

**NATS** transformiert die Plattform von einer Request-Response- zu einer Event-Driven-Architektur. Agents abonnieren Event-Streams, die API veröffentlicht Benutzernachrichten, und Komponenten kommunizieren asynchron ohne direkte Abhängigkeiten. NATS JetStream bietet persistente Message-Queues, die sicherstellen, dass keine Events während Agent-Restarts verloren gehen. Die Wahl von NATS gegenüber Alternativen wie RabbitMQ oder Kafka ergibt sich aus seiner Einfachheit, eingebetteten Clustering-Fähigkeit und hervorragenden Performance für die Small-Message-Muster, die in der Agentenkommunikation üblich sind.

Die Agent-Infrastruktur unterstützt mehrere gleichzeitige Agents (Standard 1-3, Benutzerdefiniert 1-2 im Diagramm). Jeder Agent läuft als unabhängiger Service, abonniert relevante NATS-Topics und veröffentlicht Antworten. Agents können ihren Zustand durch Replay der Event-Historie konstruieren, auf die Vektor-Stores zugreifen und Telemetrie über OpenTelemetry melden. Dieses Microservice-Muster ermöglicht es, Agents unabhängig zu entwickeln und zu skalieren sowie zu aktualisieren, ohne andere Agents oder die Plattform zu beeinträchtigen.

**Dagster** orchestriert die Datenpipeline-Infrastruktur. Es plant die Dokumentenaufnahme aus Quellen wie SharePoint, überwacht die Pipeline-Gesundheit, verwaltet Abhängigkeiten zwischen Verarbeitungsschritten und bietet eine Web-UI zur Pipeline-Überwachung. Dagsters asset-basierter Ansatz behandelt jedes verarbeitete Dokument als verwaltetes Asset mit Lineage, Versionierung und Qualitätsprüfungen. Die Wahl von Dagster gegenüber Alternativen wie Airflow ergibt sich aus seiner überlegenen lokalen Entwicklungserfahrung und nativen Python-Integration.

Pipeline-Worker implementieren die eigentliche Dokumentenverarbeitung. Sie verbinden sich mit der Quelle, laden Dokumente zur Verarbeitung in SeaweedFS herunter, parsen Inhalte mit Docling, generieren Embeddings mit konfigurierten Modellen und speichern Ergebnisse in der Vektordatenbank. Worker skalieren horizontal, wobei Dagster die Arbeit auf die verfügbaren Instanzen verteilt.

**Milvus** bietet Vektorspeicherung für die semantische Suche. Es indiziert hochdimensionale Embeddings, führt ungefähre Nächste-Nachbarn-Suchen durch, unterstützt gefilterte Suchen, die Vektor- und Metadatenabfragen kombinieren, und skaliert durch Sharding auf Milliarden von Vektoren. Milvus wurde gegenüber Alternativen wie Pinecone oder Weaviate aufgrund seiner Open-Source-Natur, On-Premise-Deployment-Optionen und hervorragenden Leistungsmerkmale ausgewählt.

**Redis** bietet schnellen Status-Speicher, den Agents verwenden, um Daten unabhängig von Events zu persistieren. Agents speichern den Zustand in Redis, wenn sie Daten benötigen, die über Konversationsrunden hinweg bestehen bleiben oder von anderen Agent-Instanzen zugänglich sein sollen. Redis wurde aufgrund seiner extrem schnellen In-Memory-Performance und seiner Unabhängigkeit von Python-Prozessen gewählt, wodurch Agents, die in jeder Sprache geschrieben sind, auf denselben Status-Store zugreifen können.

**Phoenix** bietet KI-spezifische Observability jenseits von OpenTelemetry. Es erfasst LLM-Interaktionen mit vollständigen Prompts und Responses, verfolgt RAG-Retrievals, die zeigen, welche Dokumente verwendet wurden, analysiert die Embedding-Qualität und -Drift und bietet spezialisierte Dashboards für KI-Metriken. Phoenix integriert sich in die bestehende OpenTelemetry-Infrastruktur und fügt standardmäßigen Traces KI-spezifischen Kontext hinzu.

**MCP (Model Context Protocol)** öffnet die Plattform für externe Tools. VSCode-Extensions können sich mit laufenden Agents zum Debugging verbinden, externe KI-Systeme können mit unseren Agents interagieren, und Automatisierungstools können Arbeitselemente an Prozesse übermitteln. MCP verwendet JSON-RPC über WebSockets und bietet einen sprachunabhängigen Integrationspunkt. Dieses Protokoll wurde speziell für den Swiss AI Hub entwickelt, um die Tool-Integration zu ermöglichen, ohne interne APIs freizulegen.

Über alle Tiers hinweg kommunizieren Komponenten über klar definierte Schnittstellen. HTTP/REST für synchrone Anfragen, NATS für asynchrone Events und WebSockets/SSE für Echtzeit-Streaming. Dieser polyglotte Ansatz verwendet für jeden Anwendungsfall das richtige Protokoll, anstatt alles durch ein einziges Muster zu zwingen.

Die Infrastruktur-Entscheidungen spiegeln die operativen Anforderungen wider, die sich aus Produktions-Deployments ergeben haben. Jede Komponente kann in Containern ausgeführt werden, skaliert horizontal mit Load Balancing, bietet Health Checks für Orchestrierungsplattformen, exponiert Metriken für das Monitoring und unterstützt die Konfiguration über Umgebungsvariablen. Diese operativen Eigenschaften sind beim Aufbau einer Plattform für Unternehmens-Deployments ebenso wichtig wie die funktionalen Fähigkeiten.

## Tier 3: Prozess-Orchestrierungs-Infrastruktur

![Tier 3 Architecture](../../../../media/architecture/low_level/tier_3.png)

Die **Process UI** führt ein neues User Interface-Paradigma ein, das für Workflow-Interaktion anstatt Konversation konzipiert ist. Mit Vue.js erstellt und über WebSockets verbunden, bietet es Echtzeit-Workflow-Visualisierung, Aufgabenwarteschlangen für menschliche Teilnehmer, Formular-Builder für strukturierte Eingaben und Audit-Trails für Compliance. Die Trennung von der Chat UI spiegelt die unterschiedlichen Interaktionsmuster wider: Chat ist explorativ und konversationell, während Prozessinteraktion strukturiert und aufgabenorientiert ist.

Die **Prozess-Orchestrierung** (Prozess 1 im Diagramm) läuft als separater Service, der den Workflow-Zustand verwaltet. Sie interpretiert in Python geschriebene Workflow-Definitionen, verwaltet den Prozessinstanzzustand in MongoDB, koordiniert die Arbeitsverteilung über NATS, handhabt Timeouts und Fehlerbedingungen und bietet Prozessanalysen. Der Orchestrator wurde kundenspezifisch entwickelt, anstatt bestehende BPMN-Engines zu verwenden, da die KI-Agent-Integration Fähigkeiten erforderte, die über Standard-Geschäftsprozessmuster hinausgehen.

Externe Integrationen erweitern die Reichweite der Plattform. Die **Power Automate (PA)**-Integration erfolgt über die Microsoft Graph API, wodurch Flows ausgelöst und Callbacks empfangen werden. **n8n** bietet eine selbst gehostete Alternative für die Workflow-Automatisierung, die über ihre Node-Bibliothek Hunderte von Services verbindet. Die **UiPath**-Integration ermöglicht es RPA-Bots, an Prozessen teilzunehmen, um Legacy-System-Interaktionen zu handhaben, die keine APIs besitzen. Diese Integrationen verwenden Webhook-Muster, wo möglich, und greifen auf Polling zurück, wenn Webhooks nicht verfügbar sind.
