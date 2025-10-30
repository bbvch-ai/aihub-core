---
title: Die Infrastruktur-Schichten
source_sha: 784d8f5ece36c60507bab6a031b505edc257b78f0b05559e059b62361b03626d
---

# Die Infrastruktur-Schichten

::: warning
Diese Dokumentation richtet sich an Leser, die die in der Plattform enthaltenen Infrastrukturkomponenten und deren Rolle
vollständig verstehen möchten. Dieses Verständnis ist nicht erforderlich, um die Plattform zu betreiben oder
bereitzustellen, erweist sich aber als hilfreich, wenn Sie sie erweitern, skalieren oder modifizieren möchten. Die
folgenden Abschnitte übersetzen die Business-Ebene in technische Implementierungsdetails.
:::

## Schicht 1: Kerninfrastrukturkomponenten

![Architektur der Schicht 1](../../../../media/architecture/low_level/tier_1.png)

Das Fundament bildet **OAuth2**, das die Authentifizierung übernimmt. Wenn Benutzer auf Open-WebUI oder die Admin UI
zugreifen, validiert OAuth2 ihre Anmeldeinformationen gegenüber dem Identitätsanbieter Ihrer Organisation. Diese
Komponente wurde gegenüber einfacheren Authentifizierungsmethoden gewählt, da sie sich in bestehende Unternehmenssysteme
wie Azure AD oder Keycloak integrieren lässt, ohne eine Passwortsynchronisation oder eine benutzerdefinierte
Benutzerverwaltung zu erfordern.

::: info
Die Architekturdiagramme vereinfachen bestimmte Aspekte zugunsten der Lesbarkeit. Mehrere Hilfsdatenbanken, die einige
Tools benötigen, werden weggelassen, und einige Verbindungen zwischen Komponenten werden vereinfacht, um visuelle
Unübersichtlichkeit zu vermeiden. Die Diagramme erfassen die konzeptionellen Beziehungen zwischen
Infrastrukturkomponenten und nicht jedes technische Detail.
:::

Hinter der Authentifizierungsebene dient **Traefik** als Reverse Proxy und API Gateway. Jede HTTP-Anfrage durchläuft
Traefik, das den Datenverkehr basierend auf Pfadmustern routet, die TLS-Terminierung handhabt und den Lastausgleich
bereitstellt, wenn Sie Komponenten horizontal skalieren. Die dynamischen Konfigurationsmöglichkeiten von Traefik
ermöglichen es der Plattform, neue Services ohne Neustarts zu registrieren, was für das Hinzufügen von
benutzerdefinierten Agenten oder zusätzlichen UI-Komponenten entscheidend ist.

Die **API**-Schicht, die auf FastAPI basiert, bietet mehr als nur einfaches Request-Routing. Sie unterhält
WebSocket-Verbindungen für Echtzeit-Streaming, verwaltet den Sitzungsstatus für Konversationen, erzwingt
Ratenbegrenzungen pro Benutzer und transformiert Anfragen zwischen verschiedenen Komponentenprotokollen. FastAPI wurde
aufgrund seiner asynchronen Fähigkeiten, der automatischen Generierung von OpenAPI-Dokumentationen und der exzellenten
Leistung unter gleichzeitiger Last ausgewählt.

**LiteLLM** fungiert als universelles LLM-Gateway. Anstatt separate Integrationen für OpenAI, Anthropic, Google und
lokale Modelle zu implementieren, bietet LiteLLM eine einheitliche Schnittstelle. Es handhabt die Wiederholungslogik,
wenn Modelle überlastet sind, verfolgt die Token-Nutzung zur Kostenverteilung, verwaltet unterschiedliche
Ratenbegrenzungen über Anbieter hinweg und konvertiert zwischen verschiedenen modellspezifischen Formaten. Das
Gateway-Muster ermöglicht den Modellwechsel ohne Codeänderungen, was entscheidend ist, um einen Anbieter-Lock-in zu
vermeiden.

Für modellspezifische Funktionen bietet **vLLM** eine hochperformante Inferenz für lokal gehostete Modelle wie Mistral
oder DeepSeek. Es verwendet PagedAttention für effizientes Speichermanagement, wodurch größere Modelle auf der
verfügbaren Hardware ausgeführt werden können. **Presidio** fügt PII-Erkennung und -Anonymisierung hinzu, scannt Texte
nach sensiblen Datenmustern, bevor diese an externe Modelle gesendet oder in Datenbanken gespeichert werden.

Die Speicherinfrastruktur nutzt **MinIO** für S3-kompatiblen Objektspeicher und **MongoDB** für Dokumentenspeicher.
MinIO speichert hochgeladene Dateien, generierte Berichte und Modell-Artefakte mit Versionierungs- und
Lebenszyklusrichtlinien. MongoDB speichert den Konversationsverlauf, Benutzereinstellungen, Anwendungsdaten und den
Ereignisverlauf. Diese Entscheidungen bieten Cloud-native Speicherstrategien, die On-Premise oder in Cloud-Umgebungen
identisch funktionieren.

Die Plattform umfasst integrierte KI-Tools, die das Chat-Erlebnis verbessern. **Jupyter Lab** ermöglicht die
Code-Interpretation und -Ausführung, wenn Benutzer den LLM bitten, Daten zu analysieren oder Berechnungen durchzuführen.
Der LLM kann Python-Code schreiben, der sicher in einer isolierten Jupyter-Umgebung ausgeführt wird und die Ergebnisse
direkt in der Konversation zurückgibt. **SearXNG** bietet Web-Suchfunktionen, wenn Benutzer aktuelle Informationen
benötigen, indem es Ergebnisse aus mehreren Suchmaschinen aggregiert und gleichzeitig die Privatsphäre wahrt.
**Playwright** extrahiert Inhalte von über die Suche entdeckten Websites und gewinnt den vollständigen Text, wenn
Such-Snippets nicht ausreichen. **Docling** parst Dokumente, die Benutzer in den Chat hochladen, extrahiert Text und
Struktur aus PDFs, Word-Dokumenten und Präsentationen unter Beibehaltung von Tabellen und Formatierungen, die für eine
präzise Beantwortung von Fragen erforderlich sind.

Die Observability beginnt vom ersten Tag an mit **OpenTelemetry**, das Metriken, Traces und Logs von jeder Komponente
sammelt. Die Daten fließen zu den entsprechenden Backends: Metriken zu Prometheus, Traces zu Jaeger, Logs zu Loki.
Dieser standardisierte Observability-Stack bietet vereinheitlichte Dashboards, verteiltes Tracing über Services hinweg
und zentralisierte Log-Aggregation ohne Anbieterbindung.

## Schicht 1+: Integrationsinfrastruktur

![Architektur der Schicht 1+](../../../../media/architecture/low_level/tier_1_plus.png)

Das **Azure Bot Framework** wird zur Brücke zwischen der Plattform und externen Kommunikationskanälen. Wenn eine
Nachricht von Teams, Slack oder Outlook eintrifft, normalisiert das Bot Framework sie in ein Standard-Aktivitätsformat,
handhabt die kanalspezifische Authentifizierung, verwaltet den Konversationskontext und leitet sie an den entsprechenden
Handler in der API weiter.

Das Bot Framework wurde gegenüber dem Bau separater Integrationen gewählt, da es eine einzige Abstraktion über mehrere
Kanäle bietet. Kanalspezifische Funktionen wie Teams Adaptive Cards oder Slack Blocks werden über dieselbe Schnittstelle
gehandhabt. Das Framework verwaltet Konversationsreferenzen und ermöglicht es der Plattform, proaktive Nachrichten
Stunden oder Tage nach der ersten Interaktion an Benutzer zurückzusenden.

Die Verbindung zwischen dem Bot Framework und der Plattform-API erfolgt über Webhook-Endpunkte. Die API implementiert
das Bot Framework-Protokoll, akzeptiert Aktivitäten und gibt entsprechende Antworten zurück. Diese lose Kopplung
bedeutet, dass die Plattform andere Bot Frameworks oder direkte Integrationen ohne architektonische Änderungen
unterstützen kann.

## Schicht 2: Wissens- und Agenteninfrastruktur

![Architektur der Schicht 2](../../../../media/architecture/low_level/tier_2.png)

**NATS** transformiert die Plattform von einer Request-Response- zu einer ereignisgesteuerten Architektur. Agenten
abonnieren Ereignisströme, die API veröffentlicht Benutzernachrichten, und Komponenten kommunizieren asynchron ohne
direkte Abhängigkeiten. NATS JetStream bietet persistente Nachrichtenwarteschlangen, die sicherstellen, dass keine
Ereignisse während des Agenten-Neustarts verloren gehen. Die Wahl von NATS gegenüber Alternativen wie RabbitMQ oder
Kafka resultiert aus seiner Einfachheit, eingebetteten Clustering-Fähigkeit und exzellenten Leistung für die kleinen
Nachrichtenmuster, die in der Agentenkommunikation üblich sind.

Die Agenteninfrastruktur unterstützt mehrere gleichzeitig laufende Agenten (Standard 1-3, Benutzerdefiniert 1-2 im
Diagramm). Jeder Agent läuft als unabhängiger Dienst, abonniert relevante NATS-Topics und veröffentlicht Antworten.
Agenten können ihren Zustand durch Wiedergabe der Ereignishistorie aufbauen, auf die Vektorspeicher zugreifen und
Telemetriedaten über OpenTelemetry melden. Dieses Microservice-Muster ermöglicht es, Agenten unabhängig zu entwickeln
und zu skalieren sowie zu aktualisieren, ohne andere Agenten oder die Plattform zu beeinträchtigen.

**Dagster** orchestriert die Datenpipeline-Infrastruktur. Es plant die Dokumentenaufnahme aus Quellen wie SharePoint,
überwacht die Pipeline-Integrität, verwaltet Abhängigkeiten zwischen Verarbeitungsschritten und bietet eine Web-UI für
die Pipeline-Überwachung. Dagsters asset-basierter Ansatz behandelt jedes verarbeitete Dokument als verwaltetes Asset
mit Herkunft, Versionierung und Qualitätsprüfungen. Die Wahl von Dagster gegenüber Alternativen wie Airflow resultiert
aus seiner überlegenen lokalen Entwicklungserfahrung und nativen Python-Integration.

Pipeline-Worker implementieren die eigentliche Dokumentenverarbeitung. Sie verbinden sich mit der Quelle, laden
Dokumente zur Verarbeitung nach SeaweedFS herunter, parsen Inhalte mit Docling, generieren Embeddings mit konfigurierten
Modellen und speichern die Ergebnisse in der Vektordatenbank. Worker skalieren horizontal, wobei Dagster die Arbeit auf
verfügbare Instanzen verteilt.

**Milvus** bietet Vektorspeicher für die semantische Suche. Es indiziert hochdimensionale Embeddings, führt ungefähre
Nächste-Nachbar-Suchen durch, unterstützt gefilterte Suchen, die Vektor- und Metadatenabfragen kombinieren, und skaliert
auf Milliarden von Vektoren durch Sharding. Milvus wurde gegenüber Alternativen wie Pinecone oder Weaviate aufgrund
seiner Open-Source-Natur, On-Premise-Bereitstellungsoptionen und exzellenten Leistungsmerkmale ausgewählt.

**Redis** bietet einen schnellen Zustandsspeicher, den Agenten verwenden, um Daten unabhängig von Ereignissen zu
persistieren. Agenten speichern den Zustand in Redis, wenn sie Daten benötigen, die über Konversationsrunden hinweg
bestehen bleiben oder für andere Agenteninstanzen zugänglich sein sollen. Redis wurde aufgrund seiner extrem schnellen
In-Memory-Leistung und seiner Unabhängigkeit von Python-Prozessen gewählt, was es Agenten, die in jeder Sprache
geschrieben sind, ermöglicht, auf denselben Zustandsspeicher zuzugreifen.

**Phoenix** bietet KI-spezifische Observability über OpenTelemetry hinaus. Es erfasst LLM-Interaktionen mit
vollständigen Prompts und Antworten, verfolgt RAG-Abrufe, die zeigen, welche Dokumente verwendet wurden, analysiert die
Embedding-Qualität und -Drift und bietet spezialisierte Dashboards für KI-Metriken. Phoenix integriert sich in die
bestehende OpenTelemetry-Infrastruktur und fügt Standard-Traces KI-spezifischen Kontext hinzu.

**MCP (Model Context Protocol)** öffnet die Plattform für externe Tools. VSCode-Erweiterungen können sich mit laufenden
Agenten zum Debuggen verbinden, externe KI-Systeme können mit unseren Agenten interagieren, und Automatisierungstools
können Arbeitselemente an Prozesse übermitteln. MCP verwendet JSON-RPC über WebSockets und bietet einen
sprachunabhängigen Integrationspunkt. Dieses Protokoll wurde speziell für den Swiss AI Hub entwickelt, um die
Tool-Integration zu ermöglichen, ohne interne APIs freizulegen.

In allen Schichten kommunizieren die Komponenten über klar definierte Schnittstellen. HTTP/REST für synchrone Anfragen,
NATS für asynchrone Ereignisse und WebSockets/SSE für Echtzeit-Streaming. Dieser vielseitige Ansatz verwendet für jeden
Anwendungsfall das passende Protokoll, anstatt alles durch ein einziges Muster zu erzwingen.

Die Infrastrukturwahlen spiegeln operationelle Anforderungen wider, die durch Produktionsbereitstellungen entdeckt
wurden. Jede Komponente kann in Containern ausgeführt werden, skaliert horizontal mit Lastausgleich, bietet Health
Checks für Orchestrierungsplattformen, exponiert Metriken für die Überwachung und unterstützt die Konfiguration über
Umgebungsvariablen. Diese operationellen Eigenschaften sind ebenso wichtig wie die funktionalen Fähigkeiten beim Aufbau
einer Plattform, die für den Unternehmenseinsatz bestimmt ist.

## Schicht 3: Prozessorchestrierungs-Infrastruktur

![Architektur der Schicht 3](../../../../media/architecture/low_level/tier_3.png)

Die **Process UI** führt ein neues Benutzeroberflächenparadigma ein, das für die Workflow-Interaktion und nicht für
Konversationen konzipiert ist. Mit Vue.js erstellt und über WebSockets verbunden, bietet sie
Echtzeit-Workflow-Visualisierung, Aufgabenwarteschlangen für menschliche Teilnehmer, Formulargeneratoren für
strukturierte Eingaben und Audit-Trails zur Einhaltung von Vorschriften. Die Trennung von der Chat-UI spiegelt die
unterschiedlichen Interaktionsmuster wider: Chat ist explorativ und konversationsorientiert, während die
Prozessinteraktion strukturiert und aufgabenorientiert ist.

Die **Prozessorchestrierung** (Prozess 1 im Diagramm) läuft als separater Dienst, der den Workflow-Zustand verwaltet.
Sie interpretiert in Python geschriebene Workflow-Definitionen, verwaltet den Prozessinstanzzustand in MongoDB,
koordiniert die Arbeitsverteilung über NATS, handhabt Timeouts und Fehlerbedingungen und bietet Prozessanalysen. Der
Orchestrator wurde kundenspezifisch entwickelt, anstatt bestehende BPMN-Engines zu verwenden, da die Integration von
KI-Agenten Fähigkeiten erforderte, die über Standard-Geschäftsprozessmuster hinausgehen.

Externe Integrationen erweitern die Reichweite der Plattform. Die **Power Automate (PA)**-Integration erfolgt über die
Microsoft Graph API, löst Flows aus und empfängt Callbacks. **n8n** bietet eine selbst gehostete Alternative für die
Workflow-Automatisierung und verbindet sich über seine Node-Bibliothek mit Hunderten von Services. Die
**UiPath**-Integration ermöglicht es RPA-Bots, an Prozessen teilzunehmen und Legacy-Systeminteraktionen zu handhaben,
denen APIs fehlen. Diese Integrationen verwenden nach Möglichkeit Webhook-Muster und greifen auf Polling zurück, wenn
Webhooks nicht verfügbar sind.
