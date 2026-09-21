---
title: Paketzentrierte Ansichten
description: Architekturansichten für das Developer-Onboarding – eine pro First-Party-Paket, mit einer verständlichen Erklärung dessen, was es tut und welche L2-Schnittstellen es berührt.
source_sha: aecd6f1455d38e836770b0b8db68ff9bbfb92668a092d4727b3290c11fa79ff5
---

# Paketzentrierte Ansichten

Diese Seite ist der Ausgangspunkt für einen Entwickler, der **innerhalb** eines Swiss AI Hub-Pakets arbeiten möchte. Für
jedes First-Party-Paket werden zwei Dinge miteinander kombiniert:

1. **Klartextprosa** — was das Paket tut, warum es existiert, welches Problem es löst und was es enthält.
2. **Ein zentriertes Architekturdiagramm** — das Paket in der Mitte, mit jedem L2-Container und externen System, mit dem
   es kommuniziert (eingehend *und* ausgehend). Es beantwortet die Frage: *"Wenn ich dieses Paket anfasse, womit werde
   ich sonst noch interagieren?"*

Diese Ansichten sind bewusst getrennt vom Abschnitt [Code Deep Dive](../../../6_code_deep_dive/), der die `README.md`
jedes Pakets widerspiegelt – das Endbenutzerdokument, das auch auf PyPI und npm erscheint. Jenes Publikum installiert
das Paket; dieses Publikum entwickelt es. Für die geschichtete Plattform-Story (was in der Data-Tier, der LLM-Tier und
so weiter angesiedelt ist) siehe [Container](../2_containers/).

## API Gateway

**`packages/api`** ist die Brücke zwischen der Außenwelt und der Plattform. Alles, was ein Client tut – ein Browser, der
die Admin-UI lädt, OpenWebUI, das einen Chat streamt, ein Skript, das REST aufruft – gelangt hierüber in die Plattform.
Innerhalb der Plattform kommunizieren Agents, Prozesse und Pipelines über NATS unter Verwendung des Swiss AI Agent
Protocol; die API übersetzt diese ereignisgesteuerte Welt in die Request/Response- und WebSocket-Idiome, die
HTTP-Clients erwarten.

**Warum es existiert.** Die interne Kommunikation der Plattform ist asynchron und ereignisbasiert, was für Agents
leistungsfähig, aber für ein Frontend unhandlich ist. Die API absorbiert diese Diskrepanz: Sie veröffentlicht Control
Events, abonniert die resultierenden Display Events und streamt diese über einen WebSocket zurück, damit die UI die
Argumentation eines Agents live rendern kann. Sie ist auch für die relationalen Anliegen zuständig, die keinem einzelnen
Agent gehören – Mandanten, Benutzer, Rollen, Metadaten der Wissensbasis.

**Was es enthält.** Eine Reihe von zusammensetzbaren FastAPI-Controllern, die einer strikten Controller → Service →
Entity-Schichtung folgen, plus eine eingebettete **Process Engine** (`packages/process` läuft hier In-Process, nicht als
eigener Container), einen dynamischen Endpunkt-Entdeckungsmechanismus, der Online-Agents als REST-Routen verfügbar
macht, und den WebSocket-Display-Event-Sender.

Da die API der am stärksten vernetzte First-Party-Container ist, ist ihre Ansicht zur besseren Lesbarkeit in Outbound
und Inbound aufgeteilt.

### Outbound — was die API aufruft

<likec4-view view-id="centered_api_outbound" style="display:block;height:560px"></likec4-view>

### Inbound — wer die API aufruft

<likec4-view view-id="centered_api_inbound" style="display:block;height:480px"></likec4-view>

## Sysadmin API

**`packages/sysadmin-api`** ist die Systemadministrations-Ebene – die Endpunkte, die *oberhalb* eines einzelnen
Mandanten operieren: Erstellen und Löschen von Mandanten, Zuweisen von Plattform-Ebenen-Rollen und andere
`AIHubSysAdmin`-geschützte Operationen. Sie läuft als eigener FastAPI-Service unter `sysadmin.${DOMAIN}/api/v1/*`.

**Warum es ein separates Paket ist.** Die Haupt-API wird unter Apache-2.0 ausgeliefert; die Sysadmin-Ebene unter
AGPL-3.0-or-later (Netzwerk-Copyleft). Wenn es ein physisch getrenntes, separat lizenziertes Artefakt bleibt, verhindert
dies, dass AGPL-Bedingungen auf den Apache-2.0-Code übergehen. Es erzwingt auch eine strikte Sicherheitsgrenze – jeder
Endpunkt erfordert die `AIHubSysAdmin`-Realm-Rolle.

**Was es enthält.** Einen eigenen `TenantAdminController` (Mandanten-Lebenszyklus) sowie eine kuratierte Menge von
Controllern, die von `packages/api` *re-mounted* wurden (Benutzer, Rolle, Konto, Auth-Provider), damit die geerbten
Composables der Sysadmin-UI dieselbe Origin auflösen. Die Code-Ownership bleibt bei `packages/api`; dieses Paket wählt
nur die benötigte Oberfläche aus und schützt sie.

<likec4-view view-id="centered_sysadmin_api" style="display:block;height:480px"></likec4-view>

## Admin-UI

**`packages/web`** ist die Admin- und Management-Oberfläche – wo Administratoren Agents konfigurieren, Wissensbasen
verwalten, Prozesse überwachen, Konversationsstränge überprüfen, Rollen zuweisen und Kosten verfolgen. Es ist eine Nuxt
3 SPA, die als wiederverwendbarer Nuxt Layer veröffentlicht wird.

**Warum es existiert.** Die Plattform bietet eine große, sich entwickelnde Oberfläche; OpenWebUI deckt den
Endbenutzer-Chat ab, aber die Konfiguration und der Betrieb der Plattform erfordern eine speziell entwickelte
Management-Konsole. Die UI konsumiert die API vollständig über ein generiertes TypeScript SDK, sodass
Backend-Vertragsänderungen zur Build-Zeit als Typfehler und nicht als Laufzeitüberraschungen auftreten.

**Was es enthält.** Domänenbezogene Seiten (Agents, Prozesse, Threads, Wissen, Modelle, Rollen, Benutzer, Kosten,
Evaluationen), Pinia-Colada Query/Mutation Composables, eine WebSocket-Brücke, die Agent-Display-Events direkt in den
Cache streamt, ein Event-Display-Komponentensystem, das jeden Agent-Event-Typ rendert, und ein PrimeVue + Tailwind
Design-System.

<likec4-view view-id="centered_web" style="display:block;height:480px"></likec4-view>

## Sysadmin-UI

**`packages/sysadmin-web`** ist die Systemadministrationskonsole – heute die Multi-Mandanten-Management-UI. Es ist ein
Nuxt 3 Layer, der `@swiss-ai-hub/web` *erweitert* und dessen Komponenten, Composables und Design-System wiederverwendet,
während er nur Sysadmin-Seiten hinzufügt. Es wird unter `sysadmin.${DOMAIN}/*` gehostet.

**Warum es ein separates Paket ist.** Dieselbe Begründung wie bei der Sysadmin API: Es ist ein separates
Deployment-Artefakt mit einer eigenen Sicherheitsgrenze auf der Subdomain `sysadmin.${DOMAIN}`. Sowohl `packages/web`
als auch die Sysadmin-Ebene werden unter AGPL-3.0-or-later ausgeliefert, sodass die Trennung eher architektonischer
Natur ist als eine Lizenzgrenze. Der Nuxt Layer Mechanismus ermöglicht es, fast alles von der Open-Source-UI zu erben,
ohne Code zu kopieren.

**Was es enthält.** Mandanten-CRUD-Seiten und der Sysadmin-Route-Guard, geschichtet über der geerbten Admin-UI. Sein SDK
und die meisten API-Aufrufe lösen Same-Origin gegenüber der Sysadmin API auf; der einzige Cross-Origin-Aufruf ist die
Rollenprüfung, die einen Nicht-Sysadmin-Benutzer zurück zur Haupt-App leitet.

<likec4-view view-id="centered_sysadmin_web" style="display:block;height:480px"></likec4-view>

## Agent-Laufzeit

**`packages/agent`** ist das SDK zum Bau von Agents – den transparenten, workflowbasierten KI-Workern, die der Grund für
die Existenz der Plattform sind. Ein Agent ist eine kleine, zustandslose Python-Klasse: Sie deklarieren einige
`@step`-Methoden und die Ereignisse, die sie auslösen, und die Laufzeit erledigt den Rest.

**Warum es existiert.** Die meisten Agent-Frameworks sind undurchsichtig – ein Prompt geht rein, eine Antwort kommt
raus, und die Argumentation ist eine Black Box. Swiss AI Hub-Agents sind von Haus aus auditierbar: Jeder Schritt ist ein
Ereignis auf NATS JetStream, sodass ein Lauf wiederholt, nachverfolgt und inspiziert werden kann. Die Laufzeit macht
Agents horizontal skalierbar und unabhängig deploybar – jede Agent-Klasse läuft als eigener Container und abonniert ihre
eigenen Subjects.

**Was es enthält.** Den Dispatcher, der die Ereignishistorie wiederholt, um zu entscheiden, welche Schritte ausgeführt
werden sollen, den `@step`-Decorator und das Schrittregister, einen Dependency Injector, der Schrittparameter nach Typ
auflöst, den Präkonditions-Evaluator und die persistenten `RunContext` / `ThreadContext` State Stores (in Valkey). Zur
Laufzeit greift ein Agent auf RAG (Milvus), Memory (Neo4j), das LLM-Gateway (LiteLLM) und alle externen MCP-Tools zu,
mit denen er konfiguriert ist.

<likec4-view view-id="centered_agent" style="display:block;height:560px"></likec4-view>

## Pipeline-Orchestrator

**`packages/pipeline`** ist das Data-Ingestion-SDK – es wandelt die Dokumente einer Organisation in RAG-bereite Vektoren
um, die Agents durchsuchen. Wenn die Agent-Laufzeit die Art und Weise ist, wie die Plattform Fragen *beantwortet*, dann
ist die Pipeline die Art und Weise, wie das Wissen zur Beantwortung dieser Fragen *eingebracht wird*.

**Warum es existiert.** Nützliche Unternehmens-Agents benötigen einen organisatorischen Kontext, und dieser Kontext
befindet sich in verstreuten, unübersichtlichen Dokumentenspeichern – SharePoint, OneDrive, S3, Netzlaufwerke. Das
Einbringen in einen Vektor-Store ist ein mehrstufiges Problem: Änderungen erkennen, herunterladen, parsen (OCR,
Layout-Extraktion), semantisch chunking, einbetten und indizieren – mit einer Herkunftsanalyse von jedem Vektor zurück
zu seiner Quelle. Die Pipeline modelliert dies als Dagster Asset Graph, sodass jede Stufe beobachtbar und wiederholbar
ist.

**Was es enthält.** Ein zweistufiges Factory Pattern: Quellkonnektoren (Rclone für über 70 Backends, plus direktes MS
Graph für SharePoint) speisen einen vereinheitlichten Verarbeitungs-Graph (MinerU für Parsing, LiteLLM für Embeddings,
Milvus für Speicher). Es sendet `SourceUpdatedEvent` an NATS beim Ingest und postet Fehlermeldungen an
Benachrichtigungsziele über Apprise.

<likec4-view view-id="centered_pipeline" style="display:block;height:560px"></likec4-view>

## Bot-Service

**`packages/bot`** bringt Agents zu den Benutzern, wo sie bereits arbeiten – Microsoft Teams, Slack und Web-Chat –
anstatt von ihnen zu verlangen, eine dedizierte UI zu besuchen. Es basiert auf dem `microsoft-agents-*`-SDK (dem
Nachfolger des Microsoft Bot Framework).

**Warum es existiert.** Akzeptanzhürden sind real: Eine dedizierte KI-Oberfläche ist ein weiteres Tool, zu dem
gewechselt werden muss. Die Interaktion mit Benutzern innerhalb ihrer bestehenden Kollaborationsplattformen beseitigt
diese Hürde. Der Bot unterstützt auch *Bot-in-the-Loop* (BITL) – ein Agent kann mitten im Workflow dem Benutzer direkt
in seinem Slack-Thread eine klärende Frage stellen und fortfahren, sobald der Benutzer antwortet.

**Was es enthält.** Ein `BaseChatBot` + `CompletionHandler`-Strategie-Pattern, das kanalspezifische Logik (Slack, Teams,
Webex, E-Mail) von der Konversationslogik trennt, NATS-Brücken für Agent-Chat und BITL, eine
pro-Nachricht-Identitätsauflösung gegen Keycloak und einen direkten LiteLLM-Pfad für einfache Non-Agent-Completions. Der
Konversationszustand wird in FerretDB mit einer TTL gehalten.

<likec4-view view-id="centered_bot" style="display:block;height:560px"></likec4-view>

## Backup-Service

**`packages/backup`** ist die Backup-, Wiederherstellungs- und PostgreSQL-Wartungsebene der Plattform – eine
eigenständige Dagster-Instanz (unabhängig von der Ingestion-Pipeline), die jeden zustandsbehafteten Store in S3 sichert.

**Warum es existiert.** Die Plattform verteilt ihren Zustand auf sieben sehr unterschiedliche Stores – PostgreSQL,
FerretDB, Milvus, Neo4j, ClickHouse, Valkey und NATS JetStream – jeder mit seinem eigenen Backup-Mechanismus. Ein
einziger, geplanter, auditierbarer Service, der weiß, wie jeder einzelne gesichert und wiederhergestellt wird, ist
wesentlich sicherer als ad-hoc Skripte pro Store. Der Betrieb als eigene Dagster-Instanz hält die Backup-Planung
unabhängig von den Pipeline-Workloads.

**Was es enthält.** Drei parallele Asset Graphs (Backup, Restore, Maintenance), einen Handler pro zustandsbehaftetem
Store, einen S3-Manager zum Schreiben von Artefakten nach SeaweedFS und Container-Discovery-Logik. Es kommuniziert
*direkt* mit dem Docker-Socket (nicht über den OIDC-Tier-Socket-Proxy, der nur Traefik-fähig ist), um Container während
des Backups zu beruhigen und zu steuern. Es schließt etcd bewusst aus, das als ephemer behandelt wird.

<likec4-view view-id="centered_backup" style="display:block;height:560px"></likec4-view>

## OpenWebUI

**OpenWebUI** ist die Open-Source-Chat-Oberfläche – die primäre Endbenutzer-Oberfläche für die konversationelle
Interaktion mit Agents. Es ist eine Drittanbieteranwendung, die wir ausliefern und integrieren, kein Paket, das wir
selbst entwickeln, aber ihre Integration ist tief genug, um eine eigene Onboarding-Ansicht zu rechtfertigen.

**Warum es architektonisch wichtig ist.** OpenWebUI ist der Ort, an dem die meisten Benutzer tatsächlich mit der
Plattform sprechen, und seine Verbindung zu unserer API ist mehr als ein einfacher OpenAI-kompatibler Endpunkt. Eine
**benutzerdefinierte `aihub-pipeline`** (eine in OpenWebUI gemountete Python-Funktion) überbrückt den Chat zum Swiss AI
Agent Protocol über SSE – wobei umfangreiche Agent-Ereignisse (Argumentation, Tool-Aufrufe, Retrieval,
Human-in-the-Loop) als strukturierte UI-Blöcke statt als flache Token-Streams erhalten bleiben.

**Was man wissen sollte.** Der benutzerdefinierte Pipeline-Pfad unterscheidet sich vom OpenAI-kompatiblen Fallback, den
OpenWebUI für Nicht-Agent-Aufgaben verwendet (Bilderzeugung, Sprache, Embeddings, Dokumentenparsing – alles über unsere
API proxiiert). OpenWebUI ruft Milvus auch direkt für seine eigene eingebaute RAG-Funktion auf, speichert den Zustand in
PostgreSQL, Dateien in SeaweedFS und authentifiziert über Keycloak. Die API wiederum stellt Agent-Modelle und Zugriff in
OpenWebUI über SCIM bereit.

<likec4-view view-id="centered_openwebui" style="display:block;height:560px"></likec4-view>
