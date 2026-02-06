---
title: Die Infrastruktur-Ebenen
source_sha: 9c716884726e899947c44c1f51968a8b343cb586c0185a48759bb2581a071778
---

# Die Infrastruktur-Ebenen

::: warning
Diese Dokumentation richtet sich an Leser, die die in der Plattform enthaltenen Infrastrukturkomponenten und deren Rolle
vollständig verstehen möchten. Dieses Verständnis ist nicht erforderlich, um die Plattform zu betreiben oder zu
deployen, erweist sich aber als hilfreich, wenn Sie sie erweitern, skalieren oder modifizieren möchten. Die folgenden
Abschnitte übersetzen die Geschäftsansicht in technische Implementierungsdetails.
:::

## Ebene 1: Kerninfrastrukturkomponenten

![Tier 1 Architecture](../../../../media/architecture/low_level/tier_1.png)

Die Grundlage beginnt mit **OAuth2**, das die Authentifizierung handhabt. Wenn Benutzer auf Open-WebUI oder die Admin UI
zugreifen, validiert OAuth2 deren Anmeldeinformationen gegenüber dem Identitätsanbieter Ihrer Organisation. Diese
Komponente wurde gegenüber einfacheren Authentifizierungsmethoden gewählt, da sie sich in bestehende Unternehmenssysteme
wie Azure AD oder Keycloak integrieren lässt, ohne Passwordsynchronisation oder kundenspezifisches Benutzermanagement zu
erfordern.

::: info
Die Architekturdiagramme vereinfachen bestimmte Aspekte zugunsten der Lesbarkeit. Mehrere Hilfsdatenbanken, die einige
Tools benötigen, sind weggelassen, und einige Verbindungen zwischen Komponenten sind vereinfacht, um visuelle Unordnung
zu vermeiden. Die Diagramme erfassen die konzeptionellen Beziehungen zwischen Infrastrukturkomponenten und nicht jedes
technische Detail.
:::

Hinter der Authentifizierungsschicht dient **Traefik** als Reverse Proxy und API Gateway. Jede HTTP-Anfrage passiert
Traefik, das den Datenverkehr basierend auf Pfadmustern routet, die TLS-Terminierung handhabt und den Lastausgleich
bereitstellt, wenn Sie Komponenten horizontal skalieren. Die dynamischen Konfigurationsmöglichkeiten von Traefik
ermöglichen es der Plattform, neue Services ohne Neustarts zu registrieren, was für das Hinzufügen benutzerdefinierter
Agents oder zusätzlicher UI-Komponenten entscheidend ist.

Die **API**-Schicht, die auf FastAPI basiert, bietet mehr als nur einfaches Anfrage-Routing. Sie unterhält
WebSocket-Verbindungen für Echtzeit-Streaming, verwaltet den Session-Zustand für Konversationen, erzwingt
Ratenbegrenzungen pro Benutzer und transformiert Anfragen zwischen verschiedenen Komponentenprotokollen. FastAPI wurde
aufgrund seiner asynchronen Fähigkeiten, der automatischen OpenAPI-Dokumentationsgenerierung und der hervorragenden
Leistung unter gleichzeitiger Last ausgewählt.

**LiteLLM** fungiert als universelles LLM-Gateway. Anstatt separate Integrationen für OpenAI, Anthropic, Google und
lokale Modelle zu implementieren, bietet LiteLLM eine einheitliche Schnittstelle. Es handhabt die Wiederholungslogik,
wenn Modelle überlastet sind, verfolgt die Token-Nutzung für die Kostenverteilung, verwaltet verschiedene
Ratenbegrenzungen über Anbieter hinweg und konvertiert zwischen verschiedenen modellspezifischen Formaten. Das
Gateway-Muster ermöglicht den Wechsel von Modellen ohne Codeänderungen, was entscheidend ist, um Vendor Lock-in zu
vermeiden.

Für modellspezifische Funktionen bietet **vLLM** eine Hochleistungs-Inferenz für lokal gehostete Modelle wie Mistral
oder DeepSeek. Es verwendet PagedAttention für effizientes Speichermanagement, wodurch größere Modelle auf der
verfügbaren Hardware ausgeführt werden können. **Presidio** fügt PII-Erkennung und Anonymisierung hinzu, indem es Texte
nach sensiblen Datenmustern scannt, bevor diese an externe Modelle gesendet oder in Datenbanken gespeichert werden.

Die Speicherinfrastruktur verwendet **SeaweedFS** für S3-kompatiblen Objektspeicher und **MongoDB** für
Dokumentenspeicher. SeaweedFS speichert hochgeladene Dateien, generierte Berichte und Modell-Artefakte mit
Versionierungs- und Lebenszyklusrichtlinien. Der SeaweedFS Filer verwendet **etcd** als sein Metadaten-Backend, was
hochverfügbare Deployments mit mehreren Filer-Instanzen ermöglicht. Die Plattform stellt zwei Schnittstellen bereit: die
**S3 API** unter `s3.${DOMAIN}` mit AWS-Signaturauthentifizierung für den programmatischen Zugriff und die **Filer web
UI** unter `datalake.${DOMAIN}` über einen OAuth2-Proxy für Entwickler zum Durchsuchen und Debuggen von Dateien
(erfordert die Rolle AIHubDeveloper). MongoDB speichert Konversationsverlauf, Benutzereinstellungen, Anwendungsdaten und
Ereignisverlauf. Diese Entscheidungen bieten Cloud-native Speicherstrategien, die identisch funktionieren, unabhängig
davon, ob sie On-Premise oder in Cloud-Umgebungen deployed werden.

Die Plattform beinhaltet integrierte KI-Tools, die das Chat-Erlebnis verbessern. **Jupyter Lab** ermöglicht die
Code-Interpretation und -Ausführung, wenn Benutzer das LLM bitten, Daten zu analysieren oder Berechnungen durchzuführen.
Das LLM kann Python-Code schreiben, der sicher in einer isolierten Jupyter-Umgebung ausgeführt wird und die Ergebnisse
direkt in der Konversation zurückgibt. **SearXNG** bietet Web-Suchfunktionen, wenn Benutzer aktuelle Informationen
benötigen, indem es Ergebnisse von mehreren Suchmaschinen aggregiert und gleichzeitig die Privatsphäre wahrt.
**Playwright** extrahiert Inhalte von Websites, die durch die Suche entdeckt wurden, und extrahiert den vollständigen
Text, wenn Suchausschnitte nicht ausreichen. **MinerU** parst Dokumente, die Benutzer in den Chat hochladen, und
extrahiert Text und Struktur aus PDFs, Word-Dokumenten und Präsentationen, wobei Tabellen und Formatierungen für eine
genaue Beantwortung von Fragen erhalten bleiben.

Observability beginnt vom ersten Tag an mit **OpenTelemetry**, das Metriken, Traces und Logs von jeder Komponente
sammelt. Die Daten fließen zu den entsprechenden Backends: Metriken zu Prometheus, Traces zu Jaeger, Logs zu Loki.
Dieser standardisierte Observability-Stack bietet vereinheitlichte Dashboards, verteiltes Tracing über Services hinweg
und zentrale Log-Aggregation ohne Vendor Lock-in.

## Ebene 1+: Integrationsinfrastruktur

![Tier 1+ Architecture](../../../../media/architecture/low_level/tier_1_plus.png)

Das **Azure Bot Framework** wird zur Brücke zwischen der Plattform und externen Kommunikationskanälen. Wenn eine
Nachricht von Teams, Slack oder Outlook eingeht, normalisiert das Bot Framework sie in ein Standard-Aktivitätsformat,
handhabt die kanalspezifische Authentifizierung, verwaltet den Konversationskontext und leitet sie an den entsprechenden
Handler in der API weiter.

Das Bot Framework wurde gegenüber dem Aufbau separater Integrationen gewählt, da es eine einzige Abstraktion über
mehrere Kanäle bietet. Kanalspezifische Funktionen wie Teams Adaptive Cards oder Slack Blocks werden über dieselbe
Schnittstelle gehandhabt. Das Framework verwaltet Konversationsreferenzen und ermöglicht es der Plattform, proaktive
Nachrichten Stunden oder Tage nach der ersten Interaktion an Benutzer zurückzusenden.

Die Verbindung zwischen dem Bot Framework und der Plattform-API erfolgt über Webhook-Endpunkte. Die API implementiert
das Bot Framework-Protokoll, akzeptiert Aktivitäten und gibt entsprechende Antworten zurück. Diese lose Kopplung
bedeutet, dass die Plattform andere Bot Frameworks oder direkte Integrationen ohne architektonische Änderungen
unterstützen kann.

## Ebene 2: Wissens- und Agent-Infrastruktur

![Tier 2 Architecture](../../../../media/architecture/low_level/tier_2.png)

**NATS** transformiert die Plattform von einer Request-Response-Architektur zu einer ereignisgesteuerten Architektur.
Agents abonnieren Ereignisströme, die API veröffentlicht Benutzernachrichten, und Komponenten kommunizieren asynchron
ohne direkte Abhängigkeiten. NATS JetStream bietet persistente Nachrichtenwarteschlangen und stellt sicher, dass während
Agent-Neustarts keine Ereignisse verloren gehen. Die Wahl von NATS gegenüber Alternativen wie RabbitMQ oder Kafka ergibt
sich aus seiner Einfachheit, dem eingebetteten Clustering und der hervorragenden Leistung für die in der
Agent-Kommunikation üblichen Klein-Nachrichten-Muster.

Die Agent-Infrastruktur unterstützt mehrere gleichzeitig laufende Agents (Standard 1-3, Custom 1-2 im Diagramm). Jeder
Agent läuft als unabhängiger Service, abonniert relevante NATS-Topics und veröffentlicht Antworten. Agents können ihren
Zustand durch Wiederholung des Ereignisverlaufs konstruieren, auf die Vector Stores zugreifen und Telemetriedaten über
OpenTelemetry melden. Dieses Microservice-Muster ermöglicht es Agents, unabhängig voneinander entwickelt und skaliert
sowie aktualisiert zu werden, ohne andere Agents oder die Plattform zu beeinträchtigen.

**Dagster** orchestriert die Daten-Pipeline-Infrastruktur. Es plant die Dokumentenaufnahme aus Quellen wie SharePoint,
überwacht die Pipeline-Integrität, verwaltet Abhängigkeiten zwischen Verarbeitungsschritten und bietet eine Web-UI für
die Pipeline-Überwachung. Dagsters asset-basierter Ansatz behandelt jedes verarbeitete Dokument als ein verwaltetes
Asset mit Lineage, Versionierung und Qualitätsprüfungen. Die Wahl von Dagster gegenüber Alternativen wie Airflow ergibt
sich aus seiner überragenden lokalen Entwicklungserfahrung und der nativen Python-Integration.

Pipeline-Worker implementieren die eigentliche Dokumentenverarbeitung. Sie verbinden sich mit der Quelle, laden
Dokumente zur Verarbeitung nach SeaweedFS herunter, parsen Inhalte mit MinerU, generieren Embeddings mit konfigurierten
Modellen und speichern die Ergebnisse in der Vektordatenbank. Worker skalieren horizontal, wobei Dagster die Arbeit auf
die verfügbaren Instanzen verteilt.

**Milvus** bietet Vektorspeicher für die semantische Suche. Es indiziert hochdimensionale Embeddings, führt
Näherungs-Nearest-Neighbor-Suchen durch, unterstützt gefilterte Suchen, die Vektor- und Metadatenabfragen kombinieren,
und skaliert durch Sharding auf Milliarden von Vektoren. Milvus wurde gegenüber Alternativen wie Pinecone oder Weaviate
aufgrund seiner Open-Source-Natur, der On-Premise-Deployment-Optionen und der hervorragenden Leistungsmerkmale
ausgewählt.

**Redis** bietet einen schnellen Zustandsspeicher, den Agents verwenden, um Daten unabhängig von Ereignissen persistent
zu speichern. Agents speichern ihren Zustand in Redis, wenn sie Daten benötigen, die über Konversationsrunden hinweg
bestehen bleiben oder von anderen Agent-Instanzen zugänglich sein sollen. Redis wurde aufgrund seiner extrem schnellen
In-Memory-Leistung und seiner Unabhängigkeit von Python-Prozessen gewählt, wodurch Agents, die in jeder Sprache
geschrieben sind, auf denselben Zustandsspeicher zugreifen können.

**Phoenix** bietet KI-spezifische Observability über OpenTelemetry hinaus. Es erfasst LLM-Interaktionen mit
vollständigen Prompts und Antworten, verfolgt RAG-Abfragen, die zeigen, welche Dokumente verwendet wurden, analysiert
die Embedding-Qualität und -Drift und bietet spezialisierte Dashboards für KI-Metriken. Phoenix integriert sich in die
bestehende OpenTelemetry-Infrastruktur und fügt Standard-Traces KI-spezifischen Kontext hinzu.

**MCP (Model Context Protocol)** öffnet die Plattform für externe Tools. VSCode-Erweiterungen können sich mit laufenden
Agents zum Debuggen verbinden, externe KI-Systeme können mit unseren Agents interagieren, und Automatisierungstools
können Arbeitsaufgaben an Prozesse übermitteln. MCP verwendet JSON-RPC über WebSockets und bietet einen
sprachunabhängigen Integrationspunkt. Dieses Protokoll wurde speziell für den Swiss AI Hub entwickelt, um die
Tool-Integration zu ermöglichen, ohne interne APIs freizulegen.

In allen Ebenen kommunizieren die Komponenten über klar definierte Schnittstellen. HTTP/REST für synchrone Anfragen,
NATS für asynchrone Ereignisse und WebSockets/SSE für Echtzeit-Streaming. Dieser polyglotte Ansatz verwendet für jeden
Anwendungsfall das richtige Protokoll, anstatt alles in ein einziges Muster zu pressen.

Die Infrastrukturentscheidungen spiegeln operative Anforderungen wider, die durch Produktions-Deployments entdeckt
wurden. Jede Komponente kann in Containern laufen, horizontal mit Lastausgleich skalieren, Bereitschaftsprüfungen für
Orchestrierungsplattformen bereitstellen, Metriken für die Überwachung exponieren und die Konfiguration über
Umgebungsvariablen unterstützen. Diese operativen Eigenschaften sind beim Aufbau einer Plattform für den
Unternehmenseinsatz ebenso wichtig wie funktionale Fähigkeiten.

## Ebene 3: Prozess-Orchestrierungs-Infrastruktur

![Tier 3 Architecture](../../../../media/architecture/low_level/tier_3.png)

Die **Process UI** führt ein neues User-Interface-Paradigma ein, das für die Workflow-Interaktion und nicht für
Konversationen konzipiert ist. Entwickelt mit Vue.js und über WebSockets verbunden, bietet es
Echtzeit-Workflow-Visualisierung, Aufgabenwarteschlangen für menschliche Teilnehmer, Formular-Builder für strukturierte
Eingaben und Audit-Trails für die Compliance. Die Trennung von der Chat UI spiegelt die unterschiedlichen
Interaktionsmuster wider: Chat ist explorativ und konversationell, während die Prozessinteraktion strukturiert und
aufgabenorientiert ist.

Die **Prozess-Orchestrierung** (Prozess 1 im Diagramm) läuft als separater Service und verwaltet den Workflow-Zustand.
Sie interpretiert in Python geschriebene Workflow-Definitionen, verwaltet den Zustand der Prozessinstanzen in MongoDB,
koordiniert die Arbeitsverteilung über NATS, handhabt Timeouts und Fehlerbedingungen und bietet Prozessanalysen. Der
Orchestrator wurde kundenspezifisch entwickelt, anstatt bestehende BPMN-Engines zu verwenden, da die Integration von
KI-Agents Fähigkeiten erforderte, die über Standard-Geschäftsprozessmuster hinausgehen.

Externe Integrationen erweitern die Reichweite der Plattform. Die **Power Automate (PA)**-Integration erfolgt über die
Microsoft Graph API, wodurch Flows ausgelöst und Callbacks empfangen werden. **n8n** bietet eine selbst gehostete
Alternative für die Workflow-Automatisierung, die über ihre Node-Bibliothek Hunderte von Services verbindet. Die
**UiPath**-Integration ermöglicht es RPA-Bots, an Prozessen teilzunehmen und Legacy-Systeminteraktionen zu handhaben,
denen APIs fehlen. Diese Integrationen verwenden, wo immer möglich, Webhook-Muster und greifen auf Polling zurück, wenn
Webhooks nicht verfügbar sind.
