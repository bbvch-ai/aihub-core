---
title: Paketzentrierte Ansichten
description: Architekturansichten für das Entwickler-Onboarding — eine pro proprietärem Paket, mit einer verständlichen Erklärung dessen, was es tut und welche L2-Oberfläche es berührt.
source_sha: "324fd1a26f3133d88b41b639bbd0a4e11ad960eebde9b4cfe1b80d6648b5c923"
---

# Paketzentrierte Ansichten

Diese Seite ist der Ausgangspunkt für Entwickler, die **innerhalb** eines Swiss AI Hub-Pakets arbeiten werden. Für jedes proprietäre Paket werden zwei Dinge gepaart:

1.  **Klartext-Prosa** — was das Paket tut, warum es existiert, welches Problem es löst und was es enthält.
2.  **Ein zentriertes Architekturdiagramm** — das Paket in der Mitte, mit jedem L2-Container und externen System, mit dem es kommuniziert (eingehend *und* ausgehend). Es beantwortet: *"Wenn ich dieses Paket anfasse, womit werde ich sonst noch interagieren?"*

Diese Ansichten sind bewusst getrennt vom Abschnitt [Code Deep Dive](../../../6_code_dive/), der die `README.md` jedes Pakets widerspiegelt – das Endbenutzerdokument, das auch auf PyPI und npm erscheint. Jenes Publikum installiert das Paket; dieses Publikum baut es. Für die geschichtete Plattform-Story (was im Data-Tier, LLM-Tier usw. lebt) siehe [Container](../2_containers/).

## API Gateway

**`packages/api`** ist die Brücke zwischen der Außenwelt und der Plattform. Alles, was ein Client tut — ein Browser, der die Admin UI lädt, OpenWebUI, das einen Chat streamt, ein Skript, das REST aufruft — gelangt hierüber in die Plattform. Innerhalb der Plattform kommunizieren Agents, Prozesse und Pipelines über NATS unter Verwendung des Swiss AI Agent Protokolls; die API übersetzt diese ereignisgesteuerte Welt in die Request/Response- und WebSocket-Idiome, die HTTP-Clients erwarten.

**Warum es existiert.** Die interne Kommunikation der Plattform ist asynchron und ereignisbasiert, was für Agents mächtig, aber für ein Frontend unhandlich ist. Die API fängt diese Diskrepanz auf: Sie veröffentlicht Control Events, abonniert die resultierenden Display Events und streamt diese über einen WebSocket zurück, damit die UI die Argumentation eines Agents live rendern kann. Sie ist auch verantwortlich für relationale Belange, die keinem einzelnen Agenten zugeordnet sind — Mandanten, Benutzer, Rollen, Metadaten von Wissensdatenbanken.

**Was es enthält.** Eine Reihe von zusammensetzbaren FastAPI-Controllern, die einer strengen Controller → Service → Entity-Schichtung folgen, plus eine eingebettete **Process Engine** (`packages/process` läuft hier In-Process, nicht als eigener Container), einen dynamischen Endpunkt-Erkennungsmechanismus, der online verfügbare Agents als REST-Routen anzeigt, und den WebSocket-Display-Event-Sender.

Da die API der am stärksten vernetzte proprietäre Container ist, ist ihre Ansicht zur besseren Lesbarkeit in ausgehende und eingehende Aufrufe unterteilt.

### Ausgehend — was die API aufruft

<likec4-view view-id="centered_api_outbound" style="display:block;height:560px"></likec4-view>

### Eingehend — wer die API aufruft

<likec4-view view-id="centered_api_inbound" style="display:block;height:480px"></likec4-view>

## Sysadmin API

**`packages/sysadmin-api`** ist die Systemadministrations-Ebene — die Endpunkte, die *oberhalb* eines einzelnen Mandanten operieren: Erstellen und Löschen von Mandanten, Zuweisen von plattformweiten Rollen und andere `AIHubSysAdmin`-geschützte Operationen. Sie läuft als eigener FastAPI-Service unter `sysadmin.${DOMAIN}/api/v1/*`.

**Warum es ein separates Paket ist.** Die Haupt-API wird unter Apache-2.0 ausgeliefert; die Sysadmin-Ebene ist der kommerzielle Mehrwert der Plattform und wird unter einer proprietären Lizenz ausgeliefert. Indem es ein physisch separates, separat lizenziertes Artefakt bleibt, wird verhindert, dass proprietäre Bedingungen in den Open-Source-Code gelangen. Es erzwingt auch eine harte Sicherheitsgrenze — jeder Endpunkt erfordert die `AIHubSysAdmin` Realm-Rolle.

**Was es enthält.** Einen eigenen `TenantAdminController` (Mandanten-Lebenszyklus), plus eine kuratierte Sammlung von Controllern, die von `packages/api` *re-mounted* wurden (Benutzer, Rolle, Konto, Auth-Provider), damit die geerbten Composables der Sysadmin UI same-origin auflösen. Die Code-Verantwortung verbleibt bei `packages/api`; dieses Paket wählt nur die benötigte Oberfläche aus und schützt sie.

<likec4-view view-id="centered_sysadmin_api" style="display:block;height:480px"></likec4-view>

## Admin UI

**`packages/web`** ist die Admin- und Verwaltungsoberfläche — wo Administratoren Agents konfigurieren, Wissensdatenbanken verwalten, Prozesse überwachen, Konversations-Threads inspizieren, Rollen zuweisen und Kosten verfolgen. Es ist eine Nuxt 3 SPA, die als wiederverwendbare Nuxt-Schicht veröffentlicht wird.

**Warum es existiert.** Die Plattform bietet eine große, sich entwickelnde Oberfläche; OpenWebUI deckt den Endbenutzer-Chat ab, aber die Konfiguration und der Betrieb der Plattform erfordert eine speziell entwickelte Verwaltungskonsole. Die UI konsumiert die API vollständig über ein generiertes TypeScript SDK, sodass Änderungen am Backend-Vertrag als Typfehler zur Build-Zeit anstatt als Laufzeitüberraschungen sichtbar werden.

**Was es enthält.** Domain-spezifische Seiten (Agents, Prozesse, Threads, Wissen, Modelle, Rollen, Benutzer, Kosten, Evaluationen), Pinia-Colada Query/Mutation Composables, eine WebSocket-Brücke, die Agent-Display-Events direkt in den Cache streamt, ein Event-Display-Komponentensystem, das jeden Agent-Event-Typ rendert, und ein PrimeVue + Tailwind Design-System.

<likec4-view view-id="centered_web" style="display:block;height:480px"></likec4-view>

## Sysadmin UI

**`packages/sysadmin-web`** ist die Systemadministrationskonsole — heute die Multi-Tenant-Verwaltungs-UI. Es ist eine Nuxt 3-Schicht, die `@swiss-ai-hub/web` *erweitert*, indem sie dessen Komponenten, Composables und Designsystem wiederverwendet und gleichzeitig Sysadmin-spezifische Seiten hinzufügt. Es wird unter `sysadmin.${DOMAIN}/*` gehostet.

**Warum es ein separates Paket ist.** Dieselbe Begründung wie bei der Sysadmin API: `packages/web` wird unter AGPL ausgeliefert, die Sysadmin-Ebene ist proprietär, daher muss es ein separat lizenziertes Artefakt sein. Der Nuxt Layer-Mechanismus ermöglicht es, fast alles von der Open-Source-UI zu erben, ohne Code zu kopieren, während die eigene Lizenzgrenze beibehalten wird.

**Was es enthält.** Mandanten-CRUD-Seiten und der Sysadmin-Routenwächter, geschichtet auf der geerbten Admin UI. Sein SDK und die meisten API-Aufrufe lösen same-origin gegen die Sysadmin API auf; der einzige Cross-Origin-Aufruf ist die Rollenprüfung, die einen Nicht-Sysadmin-Benutzer zurück zur Hauptanwendung leitet.

<likec4-view view-id="centered_sysadmin_web" style="display:block;height:480px"></likec4-view>

## Agent Runtime

**`packages/agent`** ist das SDK zum Erstellen von Agents — den transparenten, Workflow-basierten KI-Workern, die der Grund für die Existenz der Plattform sind. Ein Agent ist eine kleine, zustandslose Python-Klasse: Sie deklarieren einige `@step`-Methoden und die Ereignisse, die sie auslösen, und die Laufzeit erledigt den Rest.

**Warum es existiert.** Die meisten Agent-Frameworks sind undurchsichtig — ein Prompt geht hinein, eine Antwort kommt heraus, und die Argumentation ist eine Black Box. Swiss AI Hub-Agents sind von Natur aus auditierbar: Jeder Schritt ist ein Ereignis auf NATS JetStream, sodass ein Lauf wiederholt, verfolgt und inspiziert werden kann. Die Laufzeit macht Agents horizontal skalierbar und unabhängig deploybar — jede Agent-Klasse läuft als eigener Container und abonniert ihre eigenen Subjects.

**Was es enthält.** Den Dispatcher, der die Ereignishistorie wiedergibt, um zu entscheiden, welche Schritte ausgeführt werden sollen, den `@step`-Decorator und das Schrittregister, einen Dependency-Injektor, der Schrittparameter nach Typ auflöst, den Präkonditionsevaluator und die persistenten `RunContext` / `ThreadContext`-Zustandsspeicher (in Valkey). Zur Laufzeit greift ein Agent auf RAG (Milvus), Speicher (Neo4j), das LLM-Gateway (LiteLLM) und alle externen MCP-Tools zu, mit denen er konfiguriert ist.

<likec4-view view-id="centered_agent" style="display:block;height:560px"></likec4-view>

## Pipeline Orchestrator

**`packages/pipeline`** ist das Daten-Ingestion-SDK — es wandelt die Dokumente einer Organisation in die RAG-bereiten Vektoren um, die Agents durchsuchen. Wenn die Agent Runtime die Art und Weise ist, wie die Plattform Fragen *beantwortet*, dann ist die Pipeline die Art und Weise, wie das Wissen zur Beantwortung dieser Fragen *eingebracht wird*.

**Warum es existiert.** Nützliche Unternehmens-Agents benötigen einen organisatorischen Kontext, und dieser Kontext befindet sich in verstreuten, unübersichtlichen Dokumentenspeichern — SharePoint, OneDrive, S3, Netzlaufwerke. Dies in einen Vektorspeicher zu bekommen, ist ein mehrstufiges Problem: Änderungen erkennen, herunterladen, parsen (OCR, Layout-Extraktion), semantisch segmentieren, einbetten und indizieren — mit einer Herkunftsanalyse von jedem Vektor zurück zu seiner Quelle. Die Pipeline modelliert dies als einen Dagster-Asset-Graphen, sodass jede Phase beobachtbar und erneut ausführbar ist.

**Was es enthält.** Ein zweistufiges Factory-Muster: Quell-Konnektoren (Rclone für über 70 Backends, plus direkte MS Graph für SharePoint) speisen einen vereinheitlichten Verarbeitungs-Graphen (MinerU für Parsing, LiteLLM für Embeddings, Milvus für Speicherung). Es sendet `SourceUpdatedEvent` an NATS bei der Ingestion und postet Fehlerwarnungen an Benachrichtigungsziele über Apprise.

<likec4-view view-id="centered_pipeline" style="display:block;height:560px"></likec4-view>

## Bot Service

**`packages/bot`** bringt Agents zu den Benutzern, wo sie bereits arbeiten — Microsoft Teams, Slack und Web-Chat — anstatt von ihnen zu verlangen, eine dedizierte UI zu besuchen. Es basiert auf dem `microsoft-agents-*`-SDK (dem Nachfolger des Microsoft Bot Framework).

**Warum es existiert.** Die Akzeptanzschwierigkeiten sind real: Eine dedizierte KI-Schnittstelle ist ein weiteres Tool, zu dem gewechselt werden muss. Das Treffen von Benutzern innerhalb ihrer bestehenden Kollaborationsplattform beseitigt diese Reibung. Der Bot unterstützt auch *Bot-in-the-Loop* (BITL) — ein Agent kann mitten in einem Workflow dem Benutzer direkt in seinem Slack-Thread eine klärende Frage stellen und fortfahren, sobald dieser antwortet.

**Was es enthält.** Ein `BaseChatBot` + `CompletionHandler` Strategiemuster, das kanalspezifische Logik (Slack, Teams, Webex, E-Mail) von der Konversationslogik trennt, NATS-Brücken für Agent-Chat und BITL, eine pro-Nachricht-Identitätsauflösung gegen Keycloak und einen direkten LiteLLM-Pfad für einfache Nicht-Agent-Completions. Der Konversationszustand wird in FerretDB mit einem TTL gehalten.

<likec4-view view-id="centered_bot" style="display:block;height:560px"></likec4-view>

## Backup Service

**`packages/backup`** ist die Backup-, Wiederherstellungs- und PostgreSQL-Wartungsebene der Plattform — eine eigenständige Dagster-Instanz (unabhängig von der Ingestion-Pipeline), die jeden zustandsbehafteten Speicher in S3 sichert.

**Warum es existiert.** Die Plattform verteilt den Zustand auf sieben sehr unterschiedliche Speicher — PostgreSQL, FerretDB, Milvus, Neo4j, ClickHouse, Valkey und NATS JetStream — jeder mit seinem eigenen Backup-Mechanismus. Ein einziger, geplanter, auditierbarer Service, der weiß, wie jeder einzelne gesichert und wiederhergestellt wird, ist wesentlich sicherer als ad-hoc Skripte pro Speicher. Der Betrieb als eigene Dagster-Instanz hält die Backup-Planung unabhängig von den Pipeline-Workloads.

**Was es enthält.** Drei parallele Asset-Graphen (Backup, Wiederherstellung, Wartung), ein Handler pro zustandsbehaftetem Speicher, ein S3-Manager zum Schreiben von Artefakten in SeaweedFS und eine Container-Discovery-Logik. Es kommuniziert *direkt* mit dem Docker-Socket (nicht über den OIDC-Tier-Socket-Proxy, der nur Traefik-spezifisch ist), um Container während des Backups anzuhalten und zu steuern. etcd wird bewusst ausgeschlossen, da es als ephemer behandelt wird.

<likec4-view view-id="centered_backup" style="display:block;height:560px"></likec4-view>

## OpenWebUI

**OpenWebUI** ist die Open-Source-Chat-Schnittstelle — die primäre Endbenutzer-Oberfläche für die konversationelle Interaktion mit Agents. Es handelt sich um eine Drittanbieter-Anwendung, die wir ausliefern und integrieren, nicht um ein von uns erstelltes Paket, aber ihre Integration ist tief genug, um eine eigene Onboarding-Ansicht zu rechtfertigen.

**Warum es architektonisch relevant ist.** OpenWebUI ist der Ort, an dem die meisten Benutzer tatsächlich mit der Plattform sprechen, und seine Verbindung zu unserer API ist mehr als ein einfacher OpenAI-kompatibler Endpunkt. Eine **benutzerdefinierte `aihub-pipeline`** (eine in OpenWebUI gemountete Python-Funktion) überbrückt den Chat zum Swiss AI Agent Protokoll über SSE — wodurch reichhaltige Agent-Events (Argumentation, Tool-Aufrufe, Retrieval, Human-in-the-Loop) als strukturierte UI-Blöcke statt als flache Token-Streams erhalten bleiben.

**Was zu wissen ist.** Der benutzerdefinierte Pipeline-Pfad unterscheidet sich vom OpenAI-kompatiblen Fallback, das OpenWebUI für Nicht-Agent-Aufgaben verwendet (Bildgenerierung, Sprache, Embeddings, Dokumenten-Parsing — alles über unsere API proxied). OpenWebUI ruft auch Milvus direkt für seine eigene integrierte RAG-Funktion auf, speichert den Zustand in PostgreSQL, Dateien in SeaweedFS und authentifiziert sich über Keycloak. Die API wiederum stellt Agent-Modelle und Zugriff auf OpenWebUI über SCIM bereit.

<likec4-view view-id="centered_openwebui" style="display:block;height:560px"></likec4-view>
