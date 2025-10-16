---
title: Die Infrastruktur-Schichten
index: 2
source_sha: "56bdd09ccc0c011e6aca468b2f8efc83f8ca509f953b9c6f5c65bf9ca2c05573"
---

# Die Infrastruktur-Schichten

::: warning
Diese Dokumentation richtet sich an Leser, die die in der Plattform enthaltenen Infrastrukturkomponenten und deren Rolle vollständig verstehen möchten. Dieses Verständnis ist nicht erforderlich, um die Plattform zu betreiben oder zu deployen, erweist sich aber als hilfreich, wenn Sie sie erweitern, skalieren oder modifizieren möchten. Die folgenden Abschnitte übersetzen die Business-Ebene in technische Implementierungsdetails.
:::

## Ebene 1: Kern-Infrastrukturkomponenten

![Tier 1 Architecture](../../../../media/architecture/low_level/tier_1.png)

Die Grundlage beginnt mit **OAuth2**, das die Authentifizierung übernimmt. Wenn Benutzer auf die Open-WebUI oder die Admin-UI zugreifen, validiert OAuth2 ihre Anmeldeinformationen gegenüber dem Identitätsanbieter Ihrer Organisation. Diese Komponente wurde gegenüber einfacheren Authentifizierungsmethoden gewählt, da sie sich in bestehende Unternehmenssysteme wie Azure AD oder Keycloak integriert, ohne Passwortsynchronisation oder benutzerdefinierte Benutzerverwaltung zu erfordern.

::: info
Die Architekturdiagramme vereinfachen bestimmte Aspekte zugunsten der Lesbarkeit. Mehrere Hilfsdatenbanken, die einige Tools benötigen, wurden weggelassen, und einige Verbindungen zwischen Komponenten wurden vereinfacht, um visuelle Unordnung zu vermeiden. Die Diagramme erfassen die konzeptionellen Beziehungen zwischen Infrastrukturkomponenten und nicht jedes technische Detail.
:::

Hinter der Authentifizierungsschicht dient **Traefik** als Reverse Proxy und API-Gateway. Jede HTTP-Anfrage läuft durch Traefik, das den Datenverkehr basierend auf Pfadmustern routet, die TLS-Terminierung verwaltet und Lastverteilung bietet, wenn Sie Komponenten horizontal skalieren. Die dynamischen Konfigurationsmöglichkeiten von Traefik ermöglichen es der Plattform, neue Services ohne Neustarts zu registrieren, was für das Hinzufügen benutzerdefinierter Agenten oder zusätzlicher UI-Komponenten entscheidend ist.

Die **API**-Schicht, basierend auf FastAPI, bietet mehr als einfaches Request-Routing. Sie unterhält WebSocket-Verbindungen für Echtzeit-Streaming, verwaltet den Sitzungsstatus für Konversationen, erzwingt Ratenbegrenzungen pro Benutzer und transformiert Anfragen zwischen verschiedenen Komponentenprotokollen. FastAPI wurde aufgrund seiner Async-Fähigkeiten, der automatischen Generierung von OpenAPI-Dokumentation und seiner hervorragenden Leistung unter gleichzeitiger Last ausgewählt.

**LiteLLM** fungiert als universelles LLM-Gateway. Anstatt separate Integrationen für OpenAI, Anthropic, Google und lokale Modelle zu implementieren, bietet LiteLLM eine vereinheitlichte Schnittstelle. Es übernimmt die Wiederholungslogik, wenn Modelle überlastet sind, verfolgt die Token-Nutzung zur Kostenverteilung, verwaltet verschiedene Ratenbegrenzungen über Anbieter hinweg und konvertiert zwischen unterschiedlichen modellspezifischen Formaten. Das Gateway-Muster ermöglicht den Wechsel von Modellen ohne Codeänderungen, was entscheidend ist, um einen Vendor Lock-in zu vermeiden.

Für modellspezifische Funktionen bietet **vLLM** eine Hochleistungs-Inferenz für lokal gehostete Modelle wie Mistral oder DeepSeek. Es verwendet PagedAttention für effizientes Speichermanagement, wodurch größere Modelle auf der verfügbaren Hardware ausgeführt werden können. **Presidio** fügt die Erkennung und Anonymisierung von PII (personenbezogenen Daten) hinzu, scannt Texte nach sensiblen Datenmustern, bevor diese an externe Modelle gesendet oder in Datenbanken gespeichert werden.

Die Speicherinfrastruktur nutzt **MinIO** für S3-kompatiblen Objektspeicher und **MongoDB** für Dokumentenspeicher. MinIO speichert hochgeladene Dateien, generierte Berichte und Modellartefakte mit Versionierungs- und Lebenszyklusrichtlinien. MongoDB speichert den Konversationsverlauf, Benutzerpräferenzen, Anwendungsdaten und den Ereignisverlauf dauerhaft. Diese Auswahl bietet Cloud-native Speichermuster, die identisch funktionieren, ob On-Premise oder in Cloud-Umgebungen bereitgestellt.

Die Plattform umfasst integrierte KI-Tools, die das Chat-Erlebnis verbessern. **Jupyter Lab** ermöglicht die Code-Interpretation und -Ausführung, wenn Benutzer das LLM bitten, Daten zu analysieren oder Berechnungen durchzuführen. Das LLM kann Python-Code schreiben, der sicher in einer isolierten Jupyter-Umgebung ausgeführt wird und die Ergebnisse direkt in der Konversation zurückgibt. **SearXNG** bietet Web-Suchfunktionen, wenn Benutzer aktuelle Informationen benötigen, indem es Ergebnisse von mehreren Suchmaschinen aggregiert und gleichzeitig die Privatsphäre wahrt. **Playwright** extrahiert Inhalte von über die Suche entdeckten Websites und den vollständigen Text, wenn Such-Snippets nicht ausreichen. **Docling** parst Dokumente, die Benutzer in den Chat hochladen, extrahiert Text und Struktur aus PDFs, Word-Dokumenten und Präsentationen, wobei Tabellen und Formatierungen für eine genaue Beantwortung von Fragen erhalten bleiben.

Die Beobachtbarkeit beginnt am ersten Tag damit, dass **OpenTelemetry** Metriken, Traces und Logs von jeder Komponente sammelt. Die Daten fließen zu den entsprechenden Backends: Metriken zu Prometheus, Traces zu Jaeger, Logs zu Loki. Dieser standardisierte Observability-Stack bietet vereinheitlichte Dashboards, verteiltes Tracing über Services hinweg und zentrale Log-Aggregation ohne Vendor Lock-in.

## Ebene 1+: Integrationsinfrastruktur

![Tier 1+ Architecture](../../../../media/architecture/low_level/tier_1_plus.png)

Das **Azure Bot Framework** bildet die Brücke zwischen der Plattform und externen Kommunikationskanälen. Wenn eine Nachricht von Teams, Slack oder Outlook eingeht, normalisiert das Bot Framework diese in ein standardisiertes Aktivitätsformat, handhabt die kanalspezifische Authentifizierung, verwaltet den Konversationskontext und leitet sie an den entsprechenden Handler in der API weiter.

Das Bot Framework wurde gegenüber der Entwicklung separater Integrationen gewählt, da es eine einzige Abstraktion über mehrere Kanäle bietet. Kanalspezifische Funktionen wie Teams Adaptive Cards oder Slack Blocks werden über dieselbe Schnittstelle gehandhabt. Das Framework verwaltet Konversationsreferenzen, wodurch die Plattform proaktive Nachrichten Stunden oder Tage nach der ersten Interaktion an Benutzer zurücksenden kann.

Die Verbindung zwischen dem Bot Framework und der Plattform-API erfolgt über Webhook-Endpunkte. Die API implementiert das Bot Framework-Protokoll, akzeptiert Aktivitäten und gibt entsprechende Antworten zurück. Diese lose Kopplung bedeutet, dass die Plattform andere Bot Frameworks oder direkte Integrationen ohne architektonische Änderungen unterstützen kann.

## Ebene 2: Wissens- und Agenten-Infrastruktur

![Tier 2 Architecture](../../../../media/architecture/low_level/tier_2.png)

**NATS** transformiert die Plattform von einer Request-Response- zu einer ereignisgesteuerten Architektur. Agenten abonnieren Ereignisströme, die API veröffentlicht Benutzernachrichten, und Komponenten kommunizieren asynchron ohne direkte Abhängigkeiten. NATS JetStream bietet persistente Nachrichtenwarteschlangen, die sicherstellen, dass bei Agenten-Neustarts keine Ereignisse verloren gehen. Die Wahl von NATS gegenüber Alternativen wie RabbitMQ oder Kafka resultiert aus seiner Einfachheit, eingebettetem Clustering und hervorragender Leistung für die in der Agentenkommunikation üblichen Small-Message-Muster.

Die Agenten-Infrastruktur unterstützt mehrere gleichzeitig laufende Agenten (Standard 1-3, Benutzerdefiniert 1-2 im Diagramm). Jeder Agent läuft als unabhängiger Service, abonniert relevante NATS-Topics und veröffentlicht Antworten. Agenten können ihren Zustand durch Wiedergabe des Ereignisverlaufs aufbauen, auf die Vektor-Speicher zugreifen und Telemetriedaten über OpenTelemetry melden. Dieses Microservice-Muster ermöglicht es, Agenten unabhängig voneinander zu entwickeln und zu skalieren sowie zu aktualisieren, ohne andere Agenten oder die Plattform zu beeinträchtigen.

**Dagster** orchestriert die Datenpipeline-Infrastruktur. Es plant die Dokumentenaufnahme aus Quellen wie SharePoint, überwacht den Zustand der Pipeline, verwaltet Abhängigkeiten zwischen Verarbeitungsschritten und bietet eine Web-UI zur Pipeline-Überwachung. Dagsters asset-basierter Ansatz behandelt jedes verarbeitete Dokument als verwaltetes Asset mit Lineage, Versionierung und Qualitätsprüfungen. Die Wahl von Dagster gegenüber Alternativen wie Airflow resultiert aus seiner überlegenen lokalen Entwicklungserfahrung und nativen Python-Integration.

Pipeline-Worker implementieren die eigentliche Dokumentenverarbeitung. Sie verbinden sich mit der Quelle, laden Dokumente zur Verarbeitung nach MinIO herunter, parsen Inhalte mit Docling, generieren Embeddings mit konfigurierten Modellen und speichern die Ergebnisse in der Vektordatenbank. Worker skalieren horizontal, wobei Dagster die Arbeit auf verfügbare Instanzen verteilt.

**Milvus** bietet Vektorspeicher für die semantische Suche. Es indiziert hochdimensionale Embeddings, führt ungefähre Nächste-Nachbarn-Suchen durch, unterstützt gefilterte Suchen, die Vektor- und Metadatenabfragen kombinieren, und skaliert durch Sharding auf Milliarden von Vektoren. Milvus wurde gegenüber Alternativen wie Pinecone oder Weaviate aufgrund seiner Open-Source-Natur, der On-Premise-Bereitstellungsoptionen und seiner hervorragenden Leistungsmerkmale ausgewählt.

**Redis** bietet einen schnellen Zustandsspeicher, den Agenten verwenden, um Daten unabhängig von Ereignissen zu persistieren. Agenten speichern ihren Zustand in Redis, wenn sie Daten benötigen, die über Konversationsrunden hinweg bestehen bleiben oder für andere Agenteninstanzen zugänglich sein sollen. Redis wurde aufgrund seiner extrem schnellen In-Memory-Performance und seiner Unabhängigkeit von Python-Prozessen gewählt, wodurch in jeder Sprache geschriebene Agenten auf denselben Zustandsspeicher zugreifen können.

**Phoenix** bietet KI-spezifische Beobachtbarkeit über OpenTelemetry hinaus. Es erfasst LLM-Interaktionen mit vollständigen Prompts und Antworten, verfolgt RAG-Retrievals, die zeigen, welche Dokumente verwendet wurden, analysiert die Embedding-Qualität und -Drift und bietet spezialisierte Dashboards für KI-Metriken. Phoenix integriert sich in die bestehende OpenTelemetry-Infrastruktur und fügt Standard-Traces KI-spezifischen Kontext hinzu.

**MCP (Model Context Protocol)** öffnet die Plattform für externe Tools. VSCode-Erweiterungen können sich zur Fehlerbehebung mit laufenden Agenten verbinden, externe KI-Systeme können mit unseren Agenten interagieren, und Automatisierungstools können Arbeitselemente an Prozesse übermitteln. MCP verwendet JSON-RPC über WebSockets und bietet einen sprachunabhängigen Integrationspunkt. Dieses Protokoll wurde speziell für den Swiss AI Hub entwickelt, um die Tool-Integration zu ermöglichen, ohne interne APIs freizulegen.

Über alle Ebenen hinweg kommunizieren Komponenten über klar definierte Schnittstellen. HTTP/REST für synchrone Anfragen, NATS für asynchrone Ereignisse und WebSockets/SSE für Echtzeit-Streaming. Dieser Polyglot-Ansatz verwendet für jeden Anwendungsfall das passende Protokoll, anstatt alles durch ein einziges Muster zu zwingen.

Die Infrastrukturwahl spiegelt betriebliche Anforderungen wider, die sich aus Produktions-Deployments ergeben haben. Jede Komponente kann in Containern ausgeführt werden, skaliert horizontal mit Lastverteilung, bietet Health Checks für Orchestrierungsplattformen, exponiert Metriken zur Überwachung und unterstützt die Konfiguration über Umgebungsvariablen. Diese operationellen Eigenschaften sind ebenso wichtig wie die funktionalen Fähigkeiten beim Aufbau einer Plattform, die für den Unternehmenseinsatz bestimmt ist.

## Ebene 3: Prozess-Orchestrierungs-Infrastruktur

![Tier 3 Architecture](../../../../media/architecture/low_level/tier_3.png)

Die **Process UI** führt ein neues Benutzeroberflächenparadigma ein, das für Workflow-Interaktion anstelle von Konversation konzipiert ist. Entwickelt mit Vue.js und verbunden über WebSockets, bietet es Echtzeit-Workflow-Visualisierung, Aufgabenwarteschlangen für menschliche Teilnehmer, Formulargeneratoren für strukturierte Eingaben und Audit-Trails für die Compliance. Die Trennung von der Chat-UI spiegelt die unterschiedlichen Interaktionsmuster wider: Chat ist explorativ und konversationell, während Prozessinteraktion strukturiert und aufgabenorientiert ist.

Die **Prozess-Orchestrierung** (Prozess 1 im Diagramm) läuft als separater Service, der den Workflow-Zustand verwaltet. Sie interpretiert in Python geschriebene Workflow-Definitionen, verwaltet den Prozessinstanzzustand in MongoDB, koordiniert die Arbeitsverteilung über NATS, handhabt Timeouts und Fehlerbedingungen und bietet Prozessanalysen. Der Orchestrator wurde kundenspezifisch entwickelt, anstatt bestehende BPMN-Engines zu verwenden, da die Integration von KI-Agenten Fähigkeiten erforderte, die über standardmäßige Geschäftsprozessmuster hinausgehen.

Externe Integrationen erweitern die Reichweite der Plattform. Die **Power Automate (PA)**-Integration erfolgt über die Microsoft Graph API, löst Flows aus und empfängt Callbacks. **n8n** bietet eine selbstgehostete Alternative für die Workflow-Automatisierung, die über ihre Node-Bibliothek Hunderte von Diensten verbindet. Die **UiPath**-Integration ermöglicht es RPA-Bots, an Prozessen teilzunehmen und Interaktionen mit Legacy-Systemen zu handhaben, die keine APIs besitzen. Diese Integrationen verwenden Webhook-Muster, wo möglich, und greifen auf Polling zurück, wenn Webhooks nicht verfügbar sind.
