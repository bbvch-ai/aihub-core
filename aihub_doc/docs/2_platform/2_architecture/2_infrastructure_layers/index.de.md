---
title: Die Infrastruktur-Ebenen
source_sha: f122293aa50aef36fb0fc1b245cf40c035e53a0ca0893f829019546edc89b422
---

# Die Infrastruktur-Ebenen

::: warning
Diese Dokumentation richtet sich an Leser, die die in der Plattform enthaltenen Infrastrukturkomponenten und deren Rolle
vollständig verstehen möchten. Dieses Verständnis ist nicht erforderlich, um die Plattform auszuführen oder
bereitzustellen, erweist sich jedoch als hilfreich, wenn Sie sie erweitern, skalieren oder modifizieren möchten. Die
folgenden Abschnitte übersetzen die geschäftliche Sichtweise in technische Implementierungsdetails.
:::

## Tier 1: Kern-Infrastrukturkomponenten

![Tier 1 Architecture](../../../../media/architecture/low_level/tier_1.png)

Die Grundlage bildet **OAuth2**, das die Authentifizierung übernimmt. Wenn Benutzer auf Open-WebUI oder das Admin UI
zugreifen, validiert OAuth2 ihre Anmeldeinformationen gegenüber dem Identitätsprovider Ihrer Organisation. Diese
Komponente wurde gegenüber einfacheren Authentifizierungsmethoden gewählt, da sie sich in bestehende Unternehmenssysteme
wie Azure AD oder Keycloak integrieren lässt, ohne eine Passwortsynchronisierung oder eine benutzerdefinierte
Benutzerverwaltung zu erfordern.

::: info
Die Architekturdiagramme vereinfachen bestimmte Aspekte zugunsten der Lesbarkeit. Mehrere Hilfsdatenbanken, die von
einigen Tools benötigt werden, wurden weggelassen, und einige Verbindungen zwischen Komponenten wurden vereinfacht, um
visuelle Unordnung zu vermeiden. Die Diagramme erfassen die konzeptionellen Beziehungen zwischen
Infrastrukturkomponenten und nicht jedes technische Detail.
:::

Hinter der Authentifizierungsschicht dient **Traefik** als Reverse Proxy und API Gateway. Jede HTTP-Anfrage durchläuft
Traefik, das den Datenverkehr basierend auf Pfadmustern leitet, die TLS-Terminierung handhabt und den Lastausgleich
bereitstellt, wenn Sie Komponenten horizontal skalieren. Traefiks dynamische Konfigurationsmöglichkeiten ermöglichen es
der Plattform, neue Dienste ohne Neustarts zu registrieren, was für das Hinzufügen benutzerdefinierter Agenten oder
zusätzlicher UI-Komponenten entscheidend ist.

Die auf FastAPI basierende **API**-Schicht bietet mehr als nur einfaches Request-Routing. Sie verwaltet
WebSocket-Verbindungen für Echtzeit-Streaming, den Session-Status für Konversationen, erzwingt Ratenbegrenzungen pro
Benutzer und transformiert Anfragen zwischen verschiedenen Komponentenprotokollen. FastAPI wurde aufgrund seiner
asynchronen Fähigkeiten, der automatischen OpenAPI-Dokumentationsgenerierung und seiner hervorragenden Leistung unter
gleichzeitiger Last ausgewählt.

**LiteLLM** fungiert als universelles LLM-Gateway. Anstatt separate Integrationen für OpenAI, Anthropic, Google und
lokale Modelle zu implementieren, bietet LiteLLM eine einheitliche Schnittstelle. Es handhabt die Wiederholungslogik,
wenn Modelle überlastet sind, verfolgt die Token-Nutzung für die Kostenallokation, verwaltet verschiedene
Ratenbegrenzungen über Anbieter hinweg und konvertiert zwischen verschiedenen modellspezifischen Formaten. Das
Gateway-Muster ermöglicht den Wechsel von Modellen ohne Code-Änderungen, was entscheidend ist, um Vendor Lock-in zu
vermeiden.

Für modellspezifische Funktionen bietet **vLLM** eine hochperformante Inferenz für lokal gehostete Modelle wie Mistral
oder DeepSeek. Es nutzt PagedAttention für effizientes Speichermanagement, wodurch größere Modelle auf der verfügbaren
Hardware ausgeführt werden können. **Presidio** ergänzt PII-Erkennung und -Anonymisierung, indem es Text nach sensiblen
Datenmustern durchsucht, bevor dieser an externe Modelle gesendet oder in Datenbanken gespeichert wird.

Die Speicherinfrastruktur verwendet **MinIO** für S3-kompatiblen Objektspeicher und **MongoDB** für Dokumentspeicher.
MinIO speichert hochgeladene Dateien, generierte Berichte und Modellartefakte mit Versionierung und
Lifecycle-Richtlinien. MongoDB speichert den Konversationsverlauf, Benutzereinstellungen, Anwendungsdaten und den
Ereignisverlauf dauerhaft. Diese Auswahl bietet Cloud-native Speicher-Muster, die identisch funktionieren, egal ob
On-Premise oder in Cloud-Umgebungen bereitgestellt.

Die Plattform umfasst integrierte KI-Tools, die das Chat-Erlebnis verbessern. **Jupyter Lab** ermöglicht
Code-Interpretation und -Ausführung, wenn Benutzer das LLM bitten, Daten zu analysieren oder Berechnungen durchzuführen.
Das LLM kann Python-Code schreiben, der sicher in einer isolierten Jupyter-Umgebung ausgeführt wird und die Ergebnisse
direkt in die Konversation zurückführt. **SearXNG** bietet Web-Suchfunktionen, wenn Benutzer aktuelle Informationen
benötigen, indem es Ergebnisse von mehreren Suchmaschinen aggregiert und gleichzeitig die Privatsphäre wahrt.
**Playwright** extrahiert Inhalte von Websites, die über die Suche gefunden wurden, und extrahiert den vollständigen
Text, wenn Such-Snippets nicht ausreichen. **Docling** parst Dokumente, die Benutzer in den Chat hochladen, extrahiert
Text und Struktur aus PDFs, Word-Dokumenten und Präsentationen unter Beibehaltung von Tabellen und Formatierungen, die
für eine genaue Beantwortung von Fragen erforderlich sind.

Observability beginnt vom ersten Tag an mit **OpenTelemetry**, das Metriken, Traces und Logs von jeder Komponente
sammelt. Die Daten fließen zu den entsprechenden Backends: Metriken zu Prometheus, Traces zu Jaeger, Logs zu Loki.
Dieser standardisierte Observability-Stack bietet vereinheitlichte Dashboards, verteiltes Tracing über Dienste hinweg
und eine zentrale Log-Aggregation ohne Vendor Lock-in.

## Tier 1+: Integrationsinfrastruktur

![Tier 1+ Architecture](../../../../media/architecture/low_level/tier_1_plus.png)

Das **Azure Bot Framework** wird zur Brücke zwischen der Plattform und externen Kommunikationskanälen. Wenn eine
Nachricht von Teams, Slack oder Outlook eingeht, normalisiert das Bot Framework diese in ein standardmäßiges
Aktivitätsformat, handhabt die kanalspezifische Authentifizierung, verwaltet den Konversationskontext und leitet sie an
den entsprechenden Handler in der API weiter.

Das Bot Framework wurde gegenüber dem Aufbau separater Integrationen gewählt, da es eine einzige Abstraktion über
mehrere Kanäle hinweg bietet. Kanalspezifische Funktionen wie Teams Adaptive Cards oder Slack Blocks werden über
dieselbe Schnittstelle gehandhabt. Das Framework verwaltet Konversationsreferenzen und ermöglicht es der Plattform,
proaktive Nachrichten Stunden oder Tage nach der ersten Interaktion an die Benutzer zurückzusenden.

Die Verbindung zwischen dem Bot Framework und der Plattform-API erfolgt über Webhook-Endpunkte. Die API implementiert
das Bot Framework-Protokoll, akzeptiert Aktivitäten und liefert entsprechende Antworten. Diese lose Kopplung bedeutet,
dass die Plattform andere Bot Frameworks oder direkte Integrationen ohne architektonische Änderungen unterstützen kann.

## Tier 2: Wissens- und Agenten-Infrastruktur

![Tier 2 Architecture](../../../../media/architecture/low_level/tier_2.png)

**NATS** transformiert die Plattform von einer Request-Response-Architektur zu einer ereignisgesteuerten Architektur.
Agenten abonnieren Ereignis-Streams, die API veröffentlicht Benutzernachrichten, und Komponenten kommunizieren asynchron
ohne direkte Abhängigkeiten. NATS JetStream bietet persistente Nachrichtenwarteschlangen, die sicherstellen, dass keine
Ereignisse während Agenten-Neustarts verloren gehen. Die Wahl von NATS gegenüber Alternativen wie RabbitMQ oder Kafka
resultiert aus seiner Einfachheit, eingebettetem Clustering und hervorragender Leistung für die kleinen
Nachrichtenmuster, die in der Agentenkommunikation üblich sind.

Die Agenten-Infrastruktur unterstützt mehrere gleichzeitig laufende Agenten (Standard 1-3, Custom 1-2 im Diagramm).
Jeder Agent läuft als unabhängiger Dienst, abonniert relevante NATS-Themen und veröffentlicht Antworten. Agenten können
ihren Zustand durch das erneute Abspielen der Ereignishistorie konstruieren, auf die Vector Stores zugreifen und
Telemetriedaten über OpenTelemetry melden. Dieses Microservice-Muster ermöglicht es Agenten, unabhängig entwickelt und
skaliert sowie aktualisiert zu werden, ohne andere Agenten oder die Plattform zu beeinträchtigen.

**Dagster** orchestriert die Datenpipeline-Infrastruktur. Es plant die Dokumentenaufnahme aus Quellen wie SharePoint,
überwacht den Pipeline-Zustand, verwaltet Abhängigkeiten zwischen Verarbeitungsschritten und bietet ein Web-UI zur
Pipeline-Überwachung. Dagsters asset-basierter Ansatz behandelt jedes verarbeitete Dokument als verwaltetes Asset mit
Lineage, Versionierung und Qualitätsprüfungen. Die Wahl von Dagster gegenüber Alternativen wie Airflow resultiert aus
seiner überlegenen lokalen Entwicklungserfahrung und nativen Python-Integration.

Pipeline-Worker implementieren die eigentliche Dokumentenverarbeitung. Sie verbinden sich mit der Quelle, laden
Dokumente zur Verarbeitung nach SeaweedFS herunter, parsen Inhalte mit Docling, generieren Embeddings mithilfe
konfigurierter Modelle und speichern die Ergebnisse in der Vektordatenbank. Worker skalieren horizontal, wobei Dagster
die Arbeit auf verfügbare Instanzen verteilt.

**Milvus** bietet Vektorspeicherung für die semantische Suche. Es indiziert hochdimensionale Embeddings, führt ungefähre
Nächster-Nachbar-Suchen durch, unterstützt gefilterte Suchen, die Vektor- und Metadaten-Abfragen kombinieren, und
skaliert durch Sharding auf Milliarden von Vektoren. Milvus wurde gegenüber Alternativen wie Pinecone oder Weaviate
aufgrund seiner Open-Source-Natur, On-Premise-Bereitstellungsoptionen und hervorragenden Leistungsmerkmale ausgewählt.

**Redis** bietet schnellen Status-Speicher, den Agenten verwenden, um Daten unabhängig von Ereignissen zu persistieren.
Agenten speichern ihren Status in Redis, wenn sie Daten über Konversationsrunden hinweg benötigen oder wenn diese für
andere Agenten-Instanzen zugänglich sein sollen. Redis wurde aufgrund seiner extrem schnellen In-Memory-Performance und
seiner Unabhängigkeit von Python-Prozessen gewählt, was es Agenten, die in jeder Sprache geschrieben sind, ermöglicht,
auf denselben Status-Speicher zuzugreifen.

**Phoenix** bietet KI-spezifische Observability über OpenTelemetry hinaus. Es erfasst LLM-Interaktionen mit
vollständigen Prompts und Antworten, verfolgt RAG-Retrievals und zeigt, welche Dokumente verwendet wurden, analysiert
die Embedding-Qualität und -Drift und bietet spezialisierte Dashboards für KI-Metriken. Phoenix integriert sich in die
bestehende OpenTelemetry-Infrastruktur und fügt Standard-Traces KI-spezifischen Kontext hinzu.

**MCP (Model Context Protocol)** öffnet die Plattform für externe Tools. VSCode-Erweiterungen können sich mit laufenden
Agenten zum Debuggen verbinden, externe KI-Systeme können mit unseren Agenten interagieren, und Automatisierungstools
können Arbeitselemente an Prozesse übermitteln. MCP verwendet JSON-RPC über WebSockets und bietet einen
sprachunabhängigen Integrationspunkt. Dieses Protokoll wurde speziell für den Swiss AI Hub entwickelt, um die
Werkzeugintegration zu ermöglichen, ohne interne APIs freizulegen.

In allen Ebenen kommunizieren Komponenten über klar definierte Schnittstellen. HTTP/REST für synchrone Anfragen, NATS
für asynchrone Ereignisse und WebSockets/SSE für Echtzeit-Streaming. Dieser polyglotte Ansatz verwendet für jeden
Anwendungsfall das passende Protokoll, anstatt alles durch ein einziges Muster zu erzwingen.

Die Infrastrukturwahlen spiegeln die operativen Anforderungen wider, die durch Produktions-Deployments ermittelt wurden.
Jede Komponente kann in Containern ausgeführt werden, skaliert horizontal mit Lastausgleich, bietet Health Checks für
Orchestrierungsplattformen, exponiert Metriken für die Überwachung und unterstützt die Konfiguration über
Umgebungsvariablen. Diese operativen Eigenschaften sind ebenso wichtig wie die funktionalen Fähigkeiten beim Aufbau
einer Plattform, die für den Unternehmenseinsatz bestimmt ist.

## Tier 3: Prozess-Orchestrierungs-Infrastruktur

![Tier 3 Architecture](../../../../media/architecture/low_level/tier_3.png)

Das **Process UI** führt ein neues User-Interface-Paradigma ein, das für Workflow-Interaktion anstatt für Konversation
konzipiert ist. Mit Vue.js erstellt und über WebSockets verbunden, bietet es Echtzeit-Workflow-Visualisierung,
Aufgabenwarteschlangen für menschliche Teilnehmer, Formular-Builder für strukturierte Eingaben und Audit-Trails für
Compliance. Die Trennung vom Chat UI spiegelt die unterschiedlichen Interaktionsmuster wider: Chat ist explorativ und
konversationsbasiert, während Prozessinteraktion strukturiert und aufgabenorientiert ist.

Die **Prozess-Orchestrierung** (Prozess 1 im Diagramm) läuft als separater Dienst, der den Workflow-Status verwaltet.
Sie interpretiert in Python geschriebene Workflow-Definitionen, verwaltet den Prozessinstanz-Status in MongoDB,
koordiniert die Arbeitsverteilung über NATS, handhabt Timeouts und Fehlerbedingungen und bietet Prozessanalysen. Der
Orchestrator wurde kundenspezifisch entwickelt, anstatt bestehende BPMN-Engines zu verwenden, da die Integration von
KI-Agenten Fähigkeiten erforderte, die über Standard-Geschäftsprozessmuster hinausgehen.

Externe Integrationen erweitern die Reichweite der Plattform. Die **Power Automate (PA)**-Integration erfolgt über die
Microsoft Graph API, löst Flows aus und empfängt Callbacks. **n8n** bietet eine selbst gehostete Alternative für die
Workflow-Automatisierung, die über ihre Node-Bibliothek Hunderte von Diensten verbindet. Die **UiPath**-Integration
ermöglicht es RPA-Bots, an Prozessen teilzunehmen und Legacy-Systeminteraktionen zu handhaben, denen APIs fehlen. Diese
Integrationen verwenden, wo immer möglich, Webhook-Muster und greifen auf Polling zurück, wenn Webhooks nicht verfügbar
sind.
