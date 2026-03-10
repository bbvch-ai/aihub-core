---
title: Swiss AI Agent Protokoll
source_sha: 299414a98b821a45a06a9ba511609da67234ff2edf4d08937191393ed3d8993f
---

# Swiss AI Agent Protokoll

Die Infrastruktur-Layer der Plattform stellen die Kernkomponenten bereit, wie den Message Bus und Datenbanken. Das Swiss
AI Agent Protokoll definiert die Regeln und Verträge, die deren Zusammenarbeit als kohärentes System ermöglichen. Es ist
ein internes, ereignisgesteuertes Modell, das steuert, wie Agents agieren, ihren Zustand verwalten und mit der Plattform
kommunizieren. Jeder mit dem SDK erstellte Agent hält sich an dieses Protokoll, und jede Komponente, die mit einem Agent
interagiert, von der API bis zur Benutzeroberfläche, verlässt sich darauf.

Das Folgende beschreibt die abstrakten Regeln dieses Protokolls, nicht die spezifische Python-Implementierung. Diese
Prinzipien bilden die Grundlage für den Entwurf transparenter, skalierbarer und robuster Agents.

## Warum ein Protokoll? Engineering für autonome KI

KI-Operationen sind oft mehrstufige, asynchrone Prozesse, die mehrere Modelle, langlaufende Aufgaben und menschliche
Interaktion umfassen können. Eine traditionelle Architektur, in der interne Komponenten über synchrone APIs
kommunizieren, kann zu einer engen Kopplung führen. Dies erschwert die Skalierung, Beobachtung und Modifikation des
Systems, da eine Änderung in einer Komponente kaskadierende Effekte auf andere haben kann.

Das Swiss AI Agent Protokoll begegnet diesen Herausforderungen, indem es einen standardisierten, ereignisgesteuerten
Vertrag für asynchrone Kommunikation definiert. Es bietet eine gemeinsame Sprache für alle Plattformteilnehmer und
stellt sicher, dass Interaktionen vorhersehbar und entkoppelt sind.

### Jenseits von Chatbots: Eine Welt autonomer Agents

Agents innerhalb der Plattform sind nicht auf konversationelle, Anfrage-Antwort-Aufgaben beschränkt. Sie sind als
persistente, autonome Entitäten konzipiert, die unabhängig von direkter Benutzerinteraktion agieren können. Ein Agent
könnte eine Datenquelle überwachen, einen Geschäftsprozess verwalten, der Tage bis zur Fertigstellung benötigt, oder
eine geplante Analyse durchführen.

Da die operative Lebensdauer eines Agent nicht an eine einzelne Benutzeranfrage gebunden ist, kann er Minuten, Stunden
oder sogar Monate lang laufen. Diese persistente und autonome Natur führt zu einer Komplexität, die ein formelles
Kommunikationsprotokoll erfordert, um den Zustand zu verwalten, Sicherheit zu gewährleisten und über lange Zeiträume
eine klare Beobachtbarkeit zu bieten.

### Die Notwendigkeit eines granularen, interoperablen Vertrags

Das Protokoll ist ein granularer Vertrag, bei dem jede bedeutsame Aktion, jeder Gedanke oder jede Zustandsänderung als
ein eigenständiges Ereignis definiert ist. Dieser Ansatz bietet eine hochauflösende Ansicht der Agent-Operationen, was
für detailliertes Tracing und Debugging notwendig ist.

Diese Granularität ermöglicht auch Interoperabilität. Die Plattform kann ihren reichhaltigen internen Ereignisstrom
übersetzen, um externe Protokolle wie die OpenAI API zu unterstützen. Ein Adapter kann auf spezifische Ereignisse, wie
`ChunkEvent` oder `StopEvent`, hören und diese als OpenAI-kompatible Server-Sent Events umformatieren. Dieser Prozess
verwirft alle protokollspezifischen Informationen, die das externe System nicht versteht, wodurch Clients mit der
Plattform unter Verwendung vertrauter Standards interagieren können.

## Die Protokollteilnehmer und ihre Rollen

Das Protokoll definiert die Kommunikationsregeln für eine Reihe von Teilnehmern, nicht nur für die Agents. Jeder
Teilnehmer hat eine eigenständige Rolle und interagiert auf spezifische Weise mit dem Ereignisstrom.

### Der Agent

Der Agent ist der autonome Arbeiter des Ökosystems. Seine Rolle ist es, Geschäftslogik und komplexe Schlussfolgerungen
auszuführen. Er konsumiert `Control Events`, um seine Arbeit zu starten oder fortzusetzen. Er erzeugt neue
`Control Events`, um seinen internen Workflow voranzutreiben oder Aufgaben zu delegieren, sowie einen reichhaltigen
Strom von `Display Events`, um seinen Status, seine Schlussfolgerungen und Ergebnisse zu melden.

### Das API Gateway

Das API Gateway dient als sicherer Zugangspunkt für alle externen Clients. Seine Aufgabe ist es, zwischen externen
Kommunikationsformaten wie HTTP und dem internen Protokoll zu übersetzen. Das API Gateway ist der exklusive Erzeuger
initialer `Control Events`, die von außerhalb des Systems stammen. Es validiert die Benutzeridentität und
Berechtigungen, bevor es ein Ereignis an den Message Bus veröffentlicht.

### Das Frontend

Die Benutzeroberfläche bietet eine Echtzeitansicht der Operationen eines Agenten. Sie ist primär ein Konsument von
`Display Events`. Das Frontend nutzt diesen Ereignisstrom, um die Aktivität des Agenten darzustellen, z. B. durch
Anzeige von Streaming-Text oder internen Denkschritten. Es erzeugt nicht direkt Ereignisse, sondern initiiert Aktionen,
indem es Anfragen an das API Gateway sendet.

### Der Prozess-Orchestrator

Der Prozess-Orchestrator verwaltet hochrangige Geschäftsprozesse, die mehrere Agents, menschliche Aufgaben und externe
Systeme umfassen können. Er fungiert als spezialisierter Agent. Seine Protokollinteraktion besteht darin,
`Control Events` zu konsumieren, oft das `StopEvent` eines Worker-Agents, und dann ein neues `Control Event` zu
erzeugen, um den nächsten Teilnehmer im Prozess auszulösen.

Das folgende Diagramm veranschaulicht einen typischen Interaktionsfluss zwischen diesen Teilnehmern.

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API Gateway
    participant Event Bus
    participant Agent

    User->>+Frontend: Sends message
    Frontend->>+API Gateway: POST /chat/completions
    API Gateway->>+Event Bus: Publishes UserMessageEvent (Control Event)
    API Gateway-->>-Frontend: HTTP 200 OK (acknowledges request)
    Event Bus->>+Agent: Delivers UserMessageEvent
    
    Agent->>+Event Bus: Publishes ChunkEvent (Display Event)
    Event Bus->>+Frontend: Streams ChunkEvent
    Frontend->>User: Displays "Hello,"

    Agent->>+Event Bus: Publishes ChunkEvent (Display Event)
    Event Bus->>+API Gateway: Streams ChunkEvent
    Frontend->>User: Displays " how can I help?"

    Agent-->>-Event Bus: Publishes StopEvent (Control & Display Event)
    Event Bus->>+Frontend: Streams StopEvent
    Frontend-->>-User: Signals completion of response
```

## Scoping und Sicherheit: der hierarchische Kontext

Um langlaufende Interaktionen zu verwalten und Sicherheit zu gewährleisten, wird jedes Ereignis innerhalb des Protokolls
in einer dreistufigen Hierarchie eingeordnet. Diese Struktur ist direkt im Topic jedes im Message Bus veröffentlichten
Ereignisses kodiert und ermöglicht so eine granulare Kontrolle über Sichtbarkeit und Zugriff.

### Die drei Scopes eines Ereignisses

- **`Run`-Kontext**

  - **Definition:** Der granularste Scope. Ein „Run“ ist eine einzelne, nachverfolgbare Ausführung eines Workflows,
    definiert durch die Abfolge von Ereignissen zwischen einem `StartEvent` und einem korrespondierenden `StopEvent`
    oder `ExceptionEvent`.
  - **Zweck:** Er liefert einen eindeutigen Identifikator für eine einzelne, vollständige Agent-Operation. Dieser Scope
    ist entscheidend für Tracing und Debugging, da er die Ereignisse einer spezifischen Aufgabe isoliert.

- **`Display`-Kontext**

  - **Definition:** Ein Scope, der entwickelt wurde, um mehrere `Run`s zur Präsentation in einer Benutzeroberfläche zu
    gruppieren. Er kann sich über mehrere Agents erstrecken.
  - **Zweck:** Er verwaltet, was ein Endbenutzer oder Beobachter sieht. Wenn ein Agent Arbeit an einen anderen Agent
    delegiert, kann er wählen, seinen `Display`-Kontext weiterzugeben. Falls er dies tut, zeigt das Frontend, das diesen
    Kontext abonniert, die Ereignisse beider Agents als Teil einer einzigen, nahtlosen Interaktion an. Wenn der primäre
    Agent einen neuen `Display`-Kontext für die delegierte Aufgabe erstellt, wird diese Arbeit in dieser spezifischen
    UI-Ansicht „verborgen“.

- **`Thread`-Kontext**

  - **Definition:** Der Scope der höchsten Ebene, der mehrere `Display`-Kontexte und `Run`s gruppiert, die zu einem
    einzigen, übergreifenden Ziel oder einer Konversation gehören.
  - **Zweck:** Er verwaltet die langfristige Historie und den Zustand eines Prozesses. Eine Chat-Konversation ist ein
    `Thread`. Ein autonomer Agent, der Rechnungen für einen ganzen Monat verarbeitet, könnte innerhalb eines einzigen
    `Thread` für die Arbeit dieses Monats operieren.

Das folgende Diagramm veranschaulicht diese hierarchische Struktur.

```mermaid
graph TD
    subgraph User Scope
        User("👤 User")
    end

    subgraph Platform Scope
        subgraph Thread [Thread: a-b-c]
            direction LR
            subgraph Display Context 123
                direction TB
                RunA1("Run A1 <br/> (Start -> ... -> Stop)")
                RunB1("Run B1 <br/> (Start -> ... -> Stop)")
            end

            subgraph Display Context 456
                direction TB
                RunC1("Run C1 <br/> (Start -> ... -> Stop)")
            end
        end

        subgraph Agents
           AgentA("🤖 Agent A")
           AgentB("🤖 Agent B")
           AgentC("🤖 Agent C")
        end

    end

    User -- has access to --> Thread;
    AgentA ==> RunA1;
    AgentB ==> RunB1;
    AgentC ==> RunC1;

    style Thread fill:#e6f7ff,stroke:#91d5ff,stroke-width:2px
    style User fill:#fffbe6,stroke:#ffd666,stroke-width:2px
```

::: details Erklärung
- Die gesamte Interaktion ist in einem einzigen `Thread` enthalten, auf den der `User` Zugriff hat.
- Innerhalb dieses Threads gibt es zwei separate `Display`-Kontexte. Ein Benutzer, der `Display Context 123` beobachtet,
  würde einen nahtlosen Aktivitätsfluss sowohl von `Run A1` (ausgeführt von Agent A) als auch von `Run B1` (ausgeführt
  von Agent B) sehen. Dies ist typisch, wenn ein Agent eine Aufgabe an einen anderen delegiert.
- Der Benutzer würde keine Ereignisse von `Run C1` sehen, da es zu einem anderen `Display`-Kontext gehört und diese
  Operation effektiv von dieser spezifischen Ansicht isoliert.
:::

### Sicherheit durch Scoping

Dieses hierarchische Scoping ist die Grundlage des Sicherheitsmodells der Plattform. Der Zugriff wird auf der
**`Thread`**-Ebene gewährt. Ein Benutzer kann Ereignisse nur von Threads beobachten, deren Mitglied er ist.

Agents können auch in Threads ohne menschliche Mitglieder agieren. In diesem Fall können nur Administratoren mit
ausreichenden Berechtigungen für die teilnehmenden Agents die Ereignisse innerhalb dieses Threads beobachten. Dies
stellt sicher, dass autonome Backend-Prozesse sicher und isoliert bleiben.

## Die Sprache: eine Bibliothek standardisierter Ereignisse

### Das Ereignis: ein unveränderlicher Faktennachweis

Die grundlegende Kommunikationseinheit im Protokoll ist das **Ereignis**. Ein Ereignis ist ein strukturierter,
typisierter und unveränderlicher Datensatz, der einen eingetretenen Fakt repräsentiert. Jede Kommunikation besteht aus
zwei unterschiedlichen Teilen:

1. **Das Topic:** Die Adresse auf dem Message Bus, wo das Ereignis veröffentlicht wird. Das Topic liefert den
   vollständigen Kontext des Ereignisses, einschließlich seines Scopes (Thread, Display, Run) und Ursprungs.
2. **Das Payload:** Ein eigenständiges JSON-Objekt, das die spezifischen Daten für dieses Ereignis enthält.

Das System kombiniert dieses kontextuelle Topic und Daten-Payload, um eine vollständige, verständliche Kommunikation zu
bilden.

#### Die Topic-Struktur

Das Topic ist eine hierarchische Zeichenkette, die Routing- und Scoping-Informationen bereitstellt. Jedes Ereignis wird
auf einem Topic veröffentlicht, das dieser Struktur folgt.

::: details Beispiel
**Topic:**

`agent.RAGAgent.wiki_agent.t948a201-....d135bfc9-....r4fg68bb-....display_event.UserMessageEvent.r4fg68bb-...`

| Segment       | Beispielwert    | Beschreibung                                                      |
| :------------ | :-------------- | :---------------------------------------------------------------- |
| `agent_class` | `RAGAgent`      | Die Klasse des Agents, der veröffentlicht oder angesprochen wird. |
| `agent_id`    | `wiki_agent`    | Der eindeutige Identifikator der spezifischen Agent-Instanz.      |
| `thread_id`   | `t948a201-...`  | Der Identifikator für den High-Level Thread-Kontext.              |
| `display_id`  | `d135bfc9-...`  | Der Identifikator für den UI-orientierten Display-Kontext.        |
| `run_id`      | `r4fg68bb-...`  | Der Identifikator für den spezifischen Run-Kontext.               |
| `event_type`  | `display_event` | Die primäre Kategorie (`control_event` oder `display_event`).     |
| `event_name`  | `ChunkEvent`    | Der spezifische Name des Ereignisses.                             |
| `event_id`    | `r4fg68bb-...`  | Ein eindeutiger Identifikator für diese einzelne Ereignisinstanz. |
:::

##### Das Ereignis-Payload

Das Payload sind die mit dem Ereignis verbundenen Daten. Seine Struktur wird durch den Ereignistyp definiert. Alle
Ereignisse teilen jedoch eine gemeinsame Menge von Kernattributen.

::: details JSON
**Beispiel `UserMessageEvent` Payload:**

```json
{
  "event_id": "e423",
  "created_at": 1755015355940833270,
  "_event_name": "UserMessageEvent",
  "_parent_event_names": [
    "UserMessageEvent",
    "StartEvent",
    "ControlAndDisplayEvent",
    "ControlEvent",
    "DisplayEvent"
  ],
  "display_name": { "en": "User Request", "de": "Benutzeranfrage", "...": "..." },
  "display_description": { "en": "The agent has received a message...", "...": "..." },
  "locale": "de",
  "user": {
    "id": "cc4af21b-981a-4a76-826d-e722715082e0",
    "name": "Joel Barmettler",
    "...": "..."
  },
  "messages": [
    { "role": "system", "...": "..." },
    { "role": "user", "...": "..." }
  ]
}
```
:::

| Kern-Payload-Attribut | Beschreibung                                                                                                                                         |
| :-------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------- |
| `event_id`            | Ein eindeutiger Identifikator für das Ereignis, passend zu dem im Topic.                                                                             |
| `created_at`          | Ein Zeitstempel mit Nanosekundenpräzision, der den Zeitpunkt der Erstellung des Ereignisses markiert.                                                |
| `_event_name`         | Der spezifische Klassenname des Ereignisses. Dieser wird von Abonnenten verwendet, um das Payload in das korrekte Datenobjekt zu deserialisieren.    |
| `_parent_event_names` | Eine Liste der Elterntypen des Ereignisses in seiner Vererbungshierarchie, die das Filtern und Routen basierend auf breiteren Kategorien ermöglicht. |
| `display_name`        | Ein menschenlesbarer Name für das Ereignis, mit Unterstützung für mehrere Lokalisierungen.                                                           |
| `display_description` | Eine menschenlesbare Beschreibung dessen, was das Ereignis repräsentiert, mit Unterstützung für mehrere Lokalisierungen.                             |

Die verbleibenden Felder im Payload sind spezifisch für den Ereignistyp. Für dieses `UserMessageEvent` beinhaltet das
Payload `locale`, `user`-Identität und die `messages`-Historie. Andere Ereignistypen werden unterschiedliche Datenfelder
haben, die für ihren Zweck relevant sind.

### Die Kernkategorien: Control vs. Display

Um sicherzustellen, dass Agent-Workflows vorhersehbar sind und die Beobachtung die Ausführung nicht beeinträchtigt,
kategorisiert das Protokoll jedes Ereignis streng. Das Payload jedes Ereignisses enthält eine
`_parent_event_names`-Liste, die deklariert, ob es zur Kategorie `ControlEvent` oder `DisplayEvent` gehört, oder zu
beiden.

#### Control Events (Anweisungen)

Control Events steuern den Workflow und verursachen Zustandsänderungen. Das Protokoll schreibt vor, dass **nur ein
`Control Event` die Ausführung eines Agent-Schritts auslösen kann.** Sie repräsentieren Befehle, abgeschlossene Aufgaben
oder Antworten, die den Agent dazu auffordern, mit der nächsten logischen Operation fortzufahren.

- **Beispiel:** Ein `UserMessageEvent` ist ein `Control Event`, weil es einen Agent anweist, einen neuen Run zu starten.
  Ein `HumanInTheLoopResponseEvent` ist ein `Control Event`, weil es die notwendige Eingabe liefert, damit ein
  pausierter Workflow fortgesetzt werden kann.

#### Display Events (Kommentar)

Display Events sind rein informativ und für die Beobachtung durch Benutzer oder Überwachungssysteme bestimmt. Das
Protokoll schreibt vor, dass **ein `Display Event` niemals den logischen Fluss des Workflows eines Agenten beeinflussen
darf.** Ihr Zweck ist es, eine Echtzeit-Darstellung des internen Zustands des Agenten, seines Denkprozesses oder
partieller Ergebnisse zu liefern. Diese Trennung stellt sicher, dass ein Fehler in einer UI- oder Logging-Komponente die
Kernlogik des Agenten nicht unterbrechen kann.

- **Beispiel:** Ein `ThoughtEvent` bietet einen Einblick in die Schlussfolgerungen des Agenten. Ein `ChunkEvent` streamt
  einen Teil einer Textantwort an die Benutzeroberfläche.

Einige Ereignisse können beide Funktionen erfüllen. Zum Beispiel ist ein `StopEvent` ein `Control Event`, weil es den
Workflow-Run beendet, aber es ist auch ein `Display Event`, weil die Benutzeroberfläche darüber informiert werden muss,
dass der Prozess abgeschlossen ist. Solche Ereignisse halten sich an die Regeln beider Kategorien.

### Die Kernereignisbibliothek

Das Protokoll definiert eine Standardbibliothek von Ereignistypen für gängige Operationen in KI- und Agenten-Systemen.
Während Entwickler benutzerdefinierte Ereignisse zur Handhabung domänenspezifischer Logik erstellen können, bietet diese
Kernbibliothek die wesentlichen Bausteine für die Verwaltung von Workflow-Lebenszyklen, die Interaktion mit Benutzern
und die Gewährleistung der Beobachtbarkeit.

Die folgenden Tabellen dienen als Referenz für die häufigsten Ereignisse, kategorisiert nach ihrer Funktion.

#### Lifecycle-Ereignisse

Diese Ereignisse verwalten den Zustand eines einzelnen Workflow-`Run`.

| Ereignis             | Kategorie         | Zweck                                                                                                      |
| :------------------- | :---------------- | :--------------------------------------------------------------------------------------------------------- |
| **`StartEvent`**     | Control & Display | Signalisiert den Beginn eines neuen Workflow-Runs und trägt dessen initialen Kontext.                      |
| **`StopEvent`**      | Control & Display | Signalisiert den erfolgreichen Abschluss eines Workflow-Runs. Keine weiteren Schritte werden ausgeführt.   |
| **`ExceptionEvent`** | Control & Display | Signalisiert, dass während eines Runs ein nicht behebbarer Fehler aufgetreten ist, der zum Abbruch führte. |

#### Benutzerinteraktions-Ereignisse

Diese Ereignisse verarbeiten direkte Eingaben von menschlichen Benutzern.

| Ereignis               | Kategorie         | Zweck                                                                                                                                                                |
| :--------------------- | :---------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`UserMessageEvent`** | Control & Display | Ein spezialisiertes `StartEvent`, das durch das Senden einer Nachricht eines Benutzers ausgelöst wird. Es enthält die Nachrichtenhistorie und die Benutzeridentität. |

#### Streaming- und Reasoning-Ereignisse

Diese `Display Events` liefern Echtzeit-Updates an Benutzeroberflächen über die interne Verarbeitung eines Agenten.

| Ereignis           | Kategorie | Zweck                                                                                                                                            |
| :----------------- | :-------- | :----------------------------------------------------------------------------------------------------------------------------------------------- |
| **`ChunkEvent`**   | Display   | Enthält einen kleinen Teil einer größeren Textantwort, was Token-für-Token-Streaming an die UI ermöglicht.                                       |
| **`ThoughtEvent`** | Display   | Bietet eine textuelle Beschreibung der internen Argumentation oder der aktuellen Aktion des Agenten und schafft Transparenz über seinen Prozess. |

##### **Observability- und Tracing-Ereignisse**

Diese Ereignisse liefern detaillierte Telemetriedaten für Überwachung, Debugging und Kostenmanagement. Sie sind
typischerweise `Display Events`, können aber manchmal auch `Control Events` sein.

| Ereignis             | Kategorie         | Zweck                                                                                                                   |
| :------------------- | :---------------- | :---------------------------------------------------------------------------------------------------------------------- |
| **`LLMEvent`**       | Control & Display | Zeichnet die Details eines Aufrufs an ein Large Language Model auf, einschließlich Prompt, Antwort und Aufrufparameter. |
| **`RetrieverEvent`** | Control & Display | Zeichnet die Ergebnisse einer Retrieval-Operation aus einer Wissensbasis auf, einschließlich der abgerufenen Dokumente. |
| **`LLMCostEvent`**   | Display           | Zeichnet die berechneten Kosten einer LLM-Interaktion auf, einschließlich Token-Anzahlen und zugehöriger Ausgaben.      |

#### Asynchrone Interaktionsmuster-Ereignisse

Diese Ereignisse verwalten komplexe, mehrstufige Interaktionen, die das Anhalten und Wiederaufnehmen eines Workflows
erfordern.

| Ereignis                          | Kategorie         | Zweck                                                                                                             |
| :-------------------------------- | :---------------- | :---------------------------------------------------------------------------------------------------------------- |
| **`HumanInTheLoopRequestEvent`**  | Control & Display | Pausiert den Workflow und sendet eine Anfrage an einen menschlichen Benutzer für Eingabe oder Genehmigung.        |
| **`HumanInTheLoopResponseEvent`** | Control & Display | Trägt die Antwort eines menschlichen Benutzers, wodurch der pausierte Workflow fortgesetzt werden kann.           |
| **`AgentInTheLoopRequestEvent`**  | Control & Display | Pausiert den Workflow und delegiert eine Aufgabe an einen anderen Agenten.                                        |
| **`AgentInTheLoopResponseEvent`** | Control & Display | Trägt das finale `StopEvent` vom delegierten Agenten, wodurch der ursprüngliche Workflow fortgesetzt werden kann. |

## Protokoll in Aktion: Sequenzdiagramme

Dieser Abschnitt bietet schrittweise Erklärungen gängiger Interaktionen, um zu veranschaulichen, wie die Teilnehmer und
Ereignisse des Protokolls in der Praxis zusammenwirken. Die folgenden Sequenzdiagramme visualisieren den Ereignisfluss
zwischen den Teilnehmern während dieser Interaktionen.

::: warning
`ThreadId`, `DisplayId`, `RunId` und `EventId` sind ObjectIds. Für die Zwecke dieser Dokumentation werden sie jedoch als
Strings dargestellt, die mit dem Präfix `t` für Thread, `d` für Display, `r` für Run und `e` für Event beginnen.
:::

### Beispiel: eine einfache Benutzeranfrage

Dieses Szenario zeichnet den Lebenszyklus einer einzelnen Benutzernachricht nach, von der initialen HTTP-Anfrage bis zur
finalen gestreamten Antwort. Es demonstriert, wie eine synchrone Anfrage durch den asynchronen, ereignisgesteuerten Kern
der Plattform verarbeitet wird.

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API Gateway
    participant Event Bus
    participant Agent

    User->>+Frontend: Submits "Hello"
    Frontend->>+API Gateway: POST .../stream with JSON payload
    Note right of API Gateway: Das API Gateway hält die HTTP-Verbindung offen, <br/> um die Antwort zurückzustreamen.
    
    API Gateway->>+Event Bus: Publishes UserMessageEvent (Control Event)
    Event Bus->>+Agent: Delivers UserMessageEvent

    Agent->>+Event Bus: Publishes ChunkEvent (Display Event)
    Event Bus->>+API Gateway: Streams ChunkEvent back
    API Gateway->>+Frontend: Streams SSE data
    Frontend->>User: Renders "Hello! "

    Agent->>+Event Bus: Publishes ChunkEvent (Display Event)
    Event Bus->>+API Gateway: Streams ChunkEvent back
    API Gateway->>+Frontend: Streams SSE data
    Frontend->>User: Renders "How can I help?"

    Agent->>+Event Bus: Publishes StopEvent (Control & Display Event)
    Event Bus->>+API Gateway: Streams StopEvent back
    API Gateway-->>-Frontend: Streams final SSE data and closes connection
    Frontend-->>-User: Finalizes the response
```

#### Schritt 1: Der Benutzer sendet eine Nachricht

Der Benutzer tippt „Hello“ in die Chat-Oberfläche. Das Frontend verpackt dies in eine HTTP-Anfrage an einen dynamischen
Endpunkt des API Gateway. Das Suffix `/stream` zeigt an, dass der Client eine Streaming-Antwort erwartet.

::: details Anfrage / Antwort Details
**HTTP-Anfrage:** `POST /agents/MyChatAgent/dev_agent/UserMessageEvent/stream`

**Anfragekörper:**

```json
{
  "messages": [
    { "role": "user", "content": "Hello" }
  ]
}
```
:::

#### Schritt 2: Das API Gateway initiiert den Workflow

Das API Gateway authentifiziert den Benutzer, erstellt einen neuen `Run`- und `Display`-Kontext und übersetzt die
HTTP-Anfrage in ein `UserMessageEvent`. Anschließend veröffentlicht es dieses `Control Event` auf einem präzise
strukturierten Topic im Event Bus.

::: details NATS Topic & Ereignis-Payload
**NATS Topic:** `agent.MyChatAgent.dev_agent.t948.d135.r4fg.control_event.UserMessageEvent.e423`

**Ereignis-Payload:**

```json
{
  "event_id": "e423",
  "created_at": 1755015355940833270,
  "_event_name": "UserMessageEvent",
  "_parent_event_names": ["UserMessageEvent", "StartEvent", "ControlAndDisplayEvent", "ControlEvent", "DisplayEvent"],
  "locale": "en",
  "user": { "id": "cc4af21b-981a-4a76-826d-e722715082e0", "name": "Test User" },
  "messages": [{ "role": "user", "content": "Hello" }]
}
```
:::

Eine `Agent`-Instanz, die diesen Topic abonniert hat, konsumiert das Ereignis, was den Start ihres Workflows auslöst.

#### Schritt 3: Der Agent streamt die Antwort zurück

Während der Agent die Anfrage verarbeitet, generiert er Ergebnisse und veröffentlicht `Display Events`, sobald diese
verfügbar sind. Das API Gateway empfängt diese Ereignisse vom Bus und streamt nur deren Payload als Server-Sent Events
(SSE) zurück an das Frontend.

::: details NATS Topic & Ereignis-Payload (Erster Chunk)
**NATS Topic:**

`agent.MyChatAgent.dev_agent.t948.d135.r4fg.display_event.ChunkEvent.e453`

**SSE-Stream an Frontend:**

```
data: {"event_id":"e453","created_at":1755015356940833271,"_event_name":"ChunkEvent","_parent_event_names":["ChunkEvent","DisplayEvent"],"display_name":{"en":"Chunk"},"display_description":{"en":"A chunk of a larger response."},"content":"Hello! "}\n\n
```
:::

::: details NATS Topic & Ereignis-Payload (Zweiter Chunk)
**NATS Topic:**

`agent.MyChatAgent.dev_agent.t948.d135.r4fg.display_event.ChunkEvent.e545`

**SSE-Stream an Frontend:**

```
data: {"event_id":"e545","created_at":1755015357940833272,"_event_name":"ChunkEvent","_parent_event_names":["ChunkEvent","DisplayEvent"],"display_name":{"en":"Chunk"},"display_description":{"en":"A chunk of a larger response."},"content":"How can I help?"}\n\n
```
:::

#### Schritt 4: Der Agent schließt den Run ab

Sobald der Agent seine Antwort generiert hat, veröffentlicht er ein finales `StopEvent`.

::: details NATS Topic & Ereignis-Payload
**NATS Topic:**

`agent.MyChatAgent.dev_agent.t948.d135.r4fg.display_event.StopEvent.e598`

**SSE-Stream an Frontend:**

```
data: {"event_id":"e598","created_at":1755015358940833273,"_event_name":"StopEvent","_parent_event_names":["StopEvent","ControlAndDisplayEvent","ControlEvent","DisplayEvent"],"display_name":{"en":"Stop"},"display_description":{"en":"Signals the end of a run."}}\n\n
```
:::

Nach dem Streaming dieses finalen Ereignisses schließt das API Gateway die HTTP-Verbindung. Das Frontend finalisiert die
Anzeige, und die Interaktion ist abgeschlossen.

### Beispiel: ein Agent mit einem internen Workflow

Dieses Szenario demonstriert, wie ein Agent einen mehrstufigen internen Prozess ausführen kann, ohne seine
Zwischenschritte dem Endbenutzer preiszugeben. Der Benutzer sendet eine einzelne Anfrage und erhält eine einzelne,
finale Antwort. Dies wird durch die Verwendung von `Control Events` für interne Zustandsübergänge und ein finales
`Display Event` für das Ergebnis erreicht.

```mermaid
sequenceDiagram
    participant User
    participant API Gateway
    participant Event Bus
    participant Agent

    User->>+API Gateway: POST .../UserMessageEvent with JSON payload
    API Gateway->>+Event Bus: Publishes UserMessageEvent (Control Event)
    Event Bus->>+Agent: Delivers UserMessageEvent
    
    Note over Agent, Event Bus: Der Agent beginnt nun seinen internen Workflow. <br/> Diese Ereignisse dienen nur dem Kontrollfluss und werden dem Benutzer nicht angezeigt.

    Agent->>+Event Bus: Publishes CondenseQuestionEvent (Control Event)
    Event Bus->>+Agent: Delivers CondenseQuestionEvent to next step

    Agent->>+Event Bus: Publishes RetrieveEvent (Control Event)
    Event Bus->>+Agent: Delivers RetrieveEvent to next step

    Agent->>+Event Bus: Publishes StopEvent (Control & Display Event)
    Event Bus->>+API Gateway: Delivers StopEvent
    API Gateway-->>-User: Returns final HTTP 200 response with JSON payload
```

#### Schritt 1: Der Benutzer sendet eine Anfrage

Der Benutzer stellt eine Frage, die den Agent dazu auffordert, Informationen abzurufen. Der Client sendet eine
standardmäßige, nicht-streaming HTTP-Anfrage.

::: details Anfrage / Antwort Details
**HTTP-Anfrage:**

```
POST /agents/RAGAgent/prod_rag/UserMessageEvent
```

**Anfragekörper:**

```json
{
  "messages": [
    { "role": "user", "content": "What is the Swiss AI Hub?" }
  ]
}
```
:::

#### Schritt 2: Das API Gateway initiiert den Workflow

Das Gateway erstellt die notwendigen Kontexte und veröffentlicht das `UserMessageEvent`. Das API Gateway hält die
HTTP-Verbindung offen und wartet auf ein finales Ereignis, um die Antwort zu bilden.

::: details NATS Topic & Ereignis-Payload
**NATS Topic:**

`agent.RAGAgent.prod_rag.t948.d135.r4fg.control_event.UserMessageEvent.e423`

**Ereignis-Payload:**

```json
{
  "event_id": "e423",
  "created_at": 1755015355940833270,
  "_event_name": "UserMessageEvent",
  "_parent_event_names": ["UserMessageEvent", "StartEvent", "ControlAndDisplayEvent", "ControlEvent", "DisplayEvent"],
  "messages": [{ "role": "user", "content": "What is the Swiss AI Hub?" }]
}
```
:::

#### Schritt 3: Der Agent führt seinen internen Workflow aus

Der Agent konsumiert das `UserMessageEvent` und beginnt eine Abfolge interner Schritte. Jeder Schritt kommuniziert mit
dem nächsten, indem er ein `Control Event` veröffentlicht.

::: details NATS Topic & Ereignis-Payload (Erster interner Schritt)
**Frage kondensieren:** **NATS Topic:**

`agent.RAGAgent.prod_rag.t948.d135.r4fg.control_event.CondenseQuestionEvent.e453`

**Ereignis-Payload:**

```json
{
  "event_id": "e453",
  "created_at": 1755015356940833271,
  "_event_name": "CondenseQuestionEvent",
  "_parent_event_names": ["CondenseQuestionEvent", "ControlEvent"],
  "condensed_question": "Definition and purpose of the Swiss AI Hub"
}
```
:::

::: details NATS Topic & Ereignis-Payload (Zweiter interner Schritt)
**Dokumente abrufen:** **NATS Topic:**

`agent.RAGAgent.prod_rag.t948.d135.r4fg.control_event.RetrieveEvent.e545`

**Ereignis-Payload:**

```json
{
  "event_id": "e545",
  "created_at": 1755015357940833272,
  "_event_name": "RetrieveEvent",
  "_parent_event_names": ["RetrieveEvent", "ControlEvent"],
  "nodes": [ { "id": "doc-1", "content": "The Swiss AI Hub is an open..." } ]
}
```
:::

Da dies **nur `Control Events`** und keine `Display Events` sind, werden sie nicht an das API Gateway oder irgendeinen
beobachtenden Client gestreamt. Sie existieren nur auf dem internen Event Bus, um die Logik des Agenten zu
orchestrieren.

#### Schritt 4: Der Agent liefert das Endergebnis zurück

Nach dem letzten internen Schritt generiert der Agent eine vollständige Antwort und veröffentlicht sie innerhalb eines
`StopEvent`. Dieses Ereignis ist sowohl ein `Control Event` (beendet den Run) als auch ein `Display Event`.

::: details NATS Topic & Ereignis-Payload
**NATS Topic:**

`agent.RAGAgent.prod_rag.t948.d135.r4fg.display_event.StopEvent.e598`

**Ereignis-Payload:**

```json
{
  "event_id": "e598",
  "created_at": 1755015358940833273,
  "_event_name": "StopEvent",
  "_parent_event_names": ["StopEvent", "ControlAndDisplayEvent", "ControlEvent", "DisplayEvent"],
  "content": "The Swiss AI Hub is an open AI platform that you own and control."
}
```
:::

Das API Gateway empfängt dieses einzelne `Display Event`, verwendet dessen Payload, um die finale HTTP-Antwort zu
konstruieren, und sendet sie an den Client zurück, wobei die Verbindung geschlossen wird.

::: details HTTP-Antwortkörper
**HTTP-Antwortkörper:**

```json
{
  "event_id": "e598",
  "created_at": 1755015358940833273,
  "_event_name": "StopEvent",
  "_parent_event_names": ["StopEvent", "ControlAndDisplayEvent", "ControlEvent", "DisplayEvent"],
  "content": "The Swiss AI Hub is an open AI platform that you own and control."
}
```
:::

## Agent2Agent Protokoll

Um die Designentscheidungen hinter dem Swiss AI Agent Protokoll besser zu verstehen, ist es nützlich, es mit anderen
Standards im Agenten-Ökosystem zu vergleichen. Das Agent2Agent (A2A) Protokoll, ein offener Standard für die
Kommunikation zwischen unabhängigen KI-Agenten, dient als ausgezeichneter Referenzpunkt. Während beide Protokolle
ereignisgesteuert und für asynchrone Operationen konzipiert sind, lösen sie unterschiedliche Probleme und agieren auf
verschiedenen Ebenen.

### Kernphilosophie und Geltungsbereich

Der fundamentalste Unterschied liegt in ihrem beabsichtigten Geltungsbereich.

- **Das A2A Protokoll** ist für **externe Interoperabilität** konzipiert. Sein primäres Ziel ist es, Agents, die von
  verschiedenen Anbietern auf verschiedenen Plattformen erstellt wurden, die Kommunikation untereinander über das
  öffentliche Internet oder innerhalb eines Unternehmensnetzwerks zu ermöglichen. Es behandelt jeden Agenten als einen
  undurchsichtigen, unabhängigen Dienst.

- **Das Swiss AI Agent Protokoll** ist für **interne Kohäsion** konzipiert. Es ist die private, interne Sprache, die
  alle Komponenten *innerhalb* einer einzigen, kohärenten Swiss AI Hub Instanz orchestriert. Seine primären Ziele sind
  die extreme Entkopplung interner Komponenten, tiefe Beobachtbarkeit und die Verwaltung langlaufender, autonomer
  Prozesse innerhalb der sicheren Grenze der Plattform.

### Architekturmodell

Die beiden Protokolle basieren auf unterschiedlichen Architekturmustern.

- **A2A** verwendet ein **Client-Server-Modell** über Standard-Webtransporte (HTTP mit JSON-RPC, gRPC oder REST). Ein
  A2A-Client sendet eine direkte Anfrage an einen A2A-Server, der dann eine spezifische `Task` verwaltet. Dies ist ein
  Punkt-zu-Punkt-Interaktionsmodell.

- **Das Swiss AI Agent Protokoll** verwendet ein **Publish-Subscribe-Modell** über einen zentralen Message Bus (NATS).
  Teilnehmer veröffentlichen Ereignisse an den Bus, ohne Kenntnis der Abonnenten. Beliebig viele andere Teilnehmer –
  seien es andere Agents, das API Gateway oder Logging-Dienste – können diese Ereignisse abonnieren. Dies ist ein
  broadcast-basiertes, Viele-zu-Viele-Interaktionsmodell.

### Zustandsverwaltung

Ihre Ansätze zur Verwaltung des Operationszustands unterscheiden sich erheblich.

- **In A2A** ist der serverseitige Agent **zustandsbehaftet (stateful)**. Er erstellt und verwaltet ein `Task`-Objekt,
  das einen definierten Lebenszyklus durchläuft (`submitted`, `working`, `completed` usw.). Der Zustand der Interaktion
  wird vom Remote-Agent gehalten.

- **Im Swiss AI Agent Protokoll** ist der Code des Agenten **zustandslos (stateless)**. Der Zustand eines `Run` wird
  externalisiert und von der Plattforminfrastruktur verwaltet. Die Ereignishistorie wird unveränderlich im Stream des
  Message Bus (JetStream) gespeichert, und der ephemere Kontext wird in einem verteilten Speicher (Redis) gehalten. Dies
  ermöglicht es jeder verfügbaren Agent-Instanz, jedes Ereignis in einem Workflow zu verarbeiten, was hohe
  Skalierbarkeit und Resilienz ermöglicht.

### Datenmodell und Granularität

Die Struktur der Kommunikation selbst spiegelt ihre unterschiedlichen Ziele wider.

- **A2A** definiert eine Reihe von RPC-Methoden (`message/send`, `tasks/get`) und Datenobjekten (`Task`, `Message`,
  `Part`, `Artifact`). Diese Struktur ist gut geeignet für ein Remote Procedure Call System, bei dem ein Client eine
  Aufgabe auf einem Server verwaltet.

- **Das Swiss AI Agent Protokoll** ist granularer und konzentriert sich auf die strikte Unterscheidung zwischen
  `Control Events` und `Display Events`. Dieser hochauflösende Ereignisstrom ist für maximale interne Beobachtbarkeit
  ausgelegt. Jeder interne Schritt, Gedanke und Zustandsübergang kann ein individuelles Ereignis sein und bietet einen
  vollständigen Audit-Trail der Agent-Ausführung.

### Entdeckungsmechanismus

Wie Teilnehmer voneinander erfahren, ist ein weiterer wesentlicher Unterschied.

- **A2A** basiert auf einer statischen **`AgentCard`**. Dies ist ein JSON-Dokument, oft unter einer bekannten URI
  gehostet, das als digitale Visitenkarte dient und die Fähigkeiten, den Endpunkt und die
  Authentifizierungsanforderungen des Agenten beschreibt.

- **Das Swiss AI Agent Protokoll** verwendet **dynamische Echtzeit-Discovery**. Das API Gateway sendet periodisch eine
  Discovery-Anfrage über den internen Message Bus. Alle laufenden Agents antworten, wodurch das Gateway dynamisch eigene
  sichere, typsichere REST-Endpunkte generieren und registrieren kann.

### Zusammenfassung der Unterschiede

| Aspekt            | Swiss AI Agent Protokoll                                  | A2A Protokoll                                                  |
| :---------------- | :-------------------------------------------------------- | :------------------------------------------------------------- |
| **Primäres Ziel** | Interne Kohäsion, Beobachtbarkeit und Kontrolle           | Externe Interoperabilität zwischen unabhängigen Agents         |
| **Architektur**   | Publish-Subscribe (über Message Bus)                      | Client-Server (über HTTP/gRPC/REST)                            |
| **Zustand**       | Agenten-Code ist zustandslos; Zustand wird externalisiert | Remote-Agent ist zustandsbehaftet; verwaltet ein `Task`-Objekt |
| **Dateneinheit**  | `` Ereignis` (Control vs. Display) ``                     | \`\`Task`, `Message`, `Part`, `Artifact\`\`\`                  |
| **Granularität**  | Sehr hoch; jeder interne Schritt kann ein Ereignis sein   | Höhere Ebene; fokussiert auf Task-Zustand und Ergebnisse       |
| **Discovery**     | Dynamisch; API-Endpunkte werden zur Laufzeit generiert    | Statisch; basierend auf einer veröffentlichten `AgentCard`     |

### Interoperabilität und Koexistenz

Das Swiss AI Agent Protokoll und das A2A Protokoll schließen sich nicht gegenseitig aus; sie sind komplementär und
können zusammenarbeiten. Das Swiss AI Agent Protokoll regelt die internen Abläufe der Plattform, während A2A für die
Kommunikation mit der Außenwelt genutzt werden kann.

Eine Swiss AI Hub Instanz könnte einen **A2A Adapter Agent** exponieren. Dieser spezialisierte Agent würde als Brücke
fungieren:

1. **Extern** würde er einen Standard-A2A-Endpunkt und eine `AgentCard` präsentieren und sich der Außenwelt als
   konformer A2A-Agent zeigen.
2. **Intern** wäre er ein Teilnehmer am Swiss AI Agent Protokoll.

Wenn dieser Adapter-Agent eine A2A `message/send`-Anfrage empfängt, würde er diese Anfrage in ein internes `StartEvent`
übersetzen und an den Bus veröffentlichen, um einen anderen, internen Agenten auszulösen. Anschließend würde er den
resultierenden Strom interner `Display Events` und `StopEvent`s abonnieren und diese zurück in A2A `Task`-Updates und
`Artifacts` übersetzen, um sie an den externen A2A-Client zurückzusenden.

Dieser Ansatz ermöglicht es dem Swiss AI Hub, von seiner hochgradig beobachtbaren und skalierbaren internen Architektur
zu profitieren, während er weiterhin offen an einem breiteren, interoperablen Ökosystem von KI-Agenten teilnimmt.

## Model Context Protokoll (MCP)

Das Model Context Protokoll (MCP) ist ein Open-Source-Standard zur Verbindung von KI-Anwendungen mit externen Systemen,
wie Datenquellen, Tools und Workflows. Während sowohl das Swiss AI Agent Protokoll als auch MCP die Kommunikation in
KI-Systemen erleichtern, sind sie darauf ausgelegt, unterschiedliche Probleme zu lösen und auf unterschiedlichen
Architekturebenen zu agieren. Sie sind komplementär, nicht konkurrierend.

### Kernphilosophie und Geltungsbereich

Der primäre Unterschied liegt in ihrem beabsichtigten Geltungsbereich und Zweck.

- **MCP** ist dafür konzipiert, **einen Agenten mit seinen Tools zu verbinden**. Es standardisiert, wie eine
  KI-Anwendung (ein MCP Host) externe Fähigkeiten (die von MCP Servern exponiert werden) entdeckt und mit ihnen
  interagiert. Sein Fokus liegt darauf, Kontext bereitzustellen und Handlungen in der Außenwelt zu ermöglichen.

- **Das Swiss AI Agent Protokoll** ist dafür konzipiert, **die internen Komponenten der Plattform zu orchestrieren**. Es
  ist die private Sprache, die regelt, wie autonome Agents, APIs und andere Dienste innerhalb einer Swiss AI Hub Instanz
  zusammenarbeiten. Sein Fokus liegt auf dem Lebenszyklus, der Zustandsverwaltung und der Beobachtbarkeit interner
  Prozesse.

### Architekturmodell

Die Protokolle basieren auf unterschiedlichen Interaktionsmustern.

- **MCP** verwendet ein **Client-Server-Modell**. Ein MCP Host (die KI-Anwendung) erstellt für jeden MCP Server, mit dem
  er kommunizieren muss, einen dedizierten MCP Client. Die Interaktion ist eine direkte Punkt-zu-Punkt-Verbindung, bei
  der der Client Fähigkeiten vom Server anfordert.

- **Das Swiss AI Agent Protokoll** verwendet ein **Publish-Subscribe-Modell** über einen zentralen Message Bus.
  Teilnehmer veröffentlichen Ereignisse, ohne zu wissen, wer zuhört. Dies ermöglicht ein entkoppeltes
  Viele-zu-Viele-Kommunikationsmuster, bei dem mehrere Komponenten auf ein einzelnes Ereignis reagieren können.

### Datenmodell und Primitive

Ihre Datenmodelle sind auf ihre jeweiligen Funktionen zugeschnitten.

- **MCP** definiert eine Reihe von Primitiven, die ein Server exponieren kann: `Tools` (ausführbare Funktionen),
  `Resources` (Nur-Lese-Daten) und `Prompts` (wiederverwendbare Vorlagen). Das Protokoll konzentriert sich darauf, dass
  die KI-Anwendung diese Fähigkeiten entdeckt und dann nutzt.

- Das Kernprimitiv des **Swiss AI Agent Protokolls** ist das `Ereignis`, streng kategorisiert in `Control Events` (die
  die Logik steuern) und `Display Events` (die Beobachtbarkeit bieten). Das Protokoll konzentriert sich auf den Fluss
  dieser Ereignisse, um Zustandsübergänge zu verwalten und über Aktivitäten innerhalb eines verteilten Systems zu
  berichten.

### Zusammenfassung der Unterschiede

| Aspekt            | Swiss AI Agent Protokoll                                       | Model Context Protokoll (MCP)                              |
| :---------------- | :------------------------------------------------------------- | :--------------------------------------------------------- |
| **Primäres Ziel** | Interne Orchestrierung und Beobachtbarkeit                     | Verbindung eines Agenten mit externen Tools und Daten      |
| **Architektur**   | Publish-Subscribe (über Message Bus)                           | Client-Server (direkte Verbindungen)                       |
| **Interaktion**   | Viele-zu-viele, broadcast-basiert                              | Eins-zu-eins, Anfrage-Antwort                              |
| **Kern-Primitiv** | `` Das `Ereignis` (Control vs. Display) ``                     | \`\`Tool`, `Resource`, `Prompt\`\`\`                       |
| **Zweck**         | Den internen Zustand und Fluss autonomer Prozesse zu verwalten | Einer KI-Anwendung Fähigkeiten und Kontext bereitzustellen |

### Interoperabilität und Koexistenz

Die beiden Protokolle können effektiv koexistieren und sich gegenseitig ergänzen. Ein Swiss AI Hub Agent kann als MCP
Host agieren, um mit externen Tools zu interagieren.

Dies wird erreicht, indem ein **MCP Adapter** innerhalb des Workflows des Agenten erstellt wird. Der Adapter ist eine
Komponente, die zwischen den beiden Protokollen übersetzt.

```mermaid
sequenceDiagram
    participant InternalAgent as Agent (SAAP)
    participant EventBus as Event Bus (SAAP)
    participant McpAdapter as MCP Adapter
    participant McpServer as Externes Tool (MCP Server)

    InternalAgent->>+EventBus: Publishes ExecuteMcpToolEvent (Control Event)
    EventBus->>+McpAdapter: Delivers event
    
    Note over McpAdapter, McpServer: Der Adapter agiert nun als MCP Client.
    McpAdapter->>+McpServer: tools/call (MCP Request)
    McpServer-->>-McpAdapter: Returns tool result (MCP Response)

    McpAdapter->>+EventBus: Publishes McpToolResultEvent (Control Event)
    EventBus->>+InternalAgent: Delivers result
```

In diesem Ablauf:

1. Ein interner Agent, der mit dem Swiss AI Agent Protokoll arbeitet, entscheidet, dass er ein externes Tool verwenden
   muss. Er veröffentlicht ein `Control Event` (z.B. `ExecuteMcpToolEvent`), das den Toolnamen und die Argumente
   enthält.
2. Der `McpAdapter`, der solche Ereignisse abonniert hat, konsumiert es.
3. Der Adapter agiert dann als MCP Client und sendet eine standardmäßige `tools/call` JSON-RPC-Anfrage an den externen
   MCP Server.
4. Wenn der MCP Server antwortet, verpackt der Adapter das Ergebnis in ein neues internes `Control Event` (z.B.
   `McpToolResultEvent`) und veröffentlicht es zurück an den Event Bus.
5. Der ursprüngliche Agent oder ein anderer abonnierter Agent konsumiert das Ergebnis und setzt seinen Workflow fort.

Dieses Muster ermöglicht es Agents innerhalb des Swiss AI Hub, das reichhaltige Ökosystem externer Tools und
Datenquellen, die über MCP verfügbar sind, zu nutzen, während sie weiterhin von der robusten internen Orchestrierung,
Sicherheit und Beobachtbarkeit profitieren, die das Swiss AI Agent Protokoll bietet.

## Agent User Interaction Protokoll (AG-UI)

Das Agent User Interaction Protokoll (AG-UI) ist ein offener Standard, der speziell entwickelt wurde, um die
Kommunikation zwischen Frontend-Anwendungen und KI-Agenten zu standardisieren. Es konzentriert sich auf die
Interaktivitätsschicht zwischen Agent und Benutzer. Wie die anderen besprochenen Protokolle ist AG-UI komplementär zum
Swiss AI Agent Protokoll und adressiert einen anderen Teil der gesamten Systemarchitektur.

### Kernphilosophie und Geltungsbereich

Die Protokolle sind mit unterschiedlichen Scopes und Zielen konzipiert.

- **AG-UI** ist ein **Präsentationsschicht-Protokoll**. Sein ausschließlicher Fokus liegt darauf, einen standardisierten
  Echtzeit-Kommunikationskanal zwischen einem KI-Agenten und einer Client-Anwendung (der Benutzeroberfläche) zu
  schaffen. Es definiert ein Vokabular für das Streaming von UI-Updates, die Verwaltung des gemeinsamen Zustands für die
  UI und die Handhabung von Human-in-the-Loop-Interaktionen.

- **Das Swiss AI Agent Protokoll** ist ein **Full-Stack, internes Orchestrierungsprotokoll**. Es regelt die
  Kommunikation zwischen *allen* internen Komponenten der Plattform, nicht nur die Verbindung zur UI. Sein
  Geltungsbereich umfasst Agent-zu-Agent-Delegation, Prozess-Orchestrierung und die Verwaltung langlaufender, autonomer
  Aufgaben, die möglicherweise gar keine UI haben.

### Architekturmodell

Ihre Architekturmodelle spiegeln ihre unterschiedlichen Scopes wider.

- **AG-UI** definiert ein **Client-Server-Modell für den UI-Kanal**. Ein AG-UI-Client (im Frontend) verbindet sich mit
  einem AG-UI-kompatiblen Agenten oder Server. Das Protokoll standardisiert die Ereignisse, die über diese spezifische
  Verbindung fließen.

- **Das Swiss AI Agent Protokoll** verwendet ein **plattformweites Publish-Subscribe-Modell**. Ereignisse werden auf
  einem zentralen Message Bus ausgestrahlt und können von jedem autorisierten Teilnehmer konsumiert werden. Das API
  Gateway fungiert als Brücke zum Frontend, aber das Protokoll selbst steuert das gesamte interne Ökosystem.

### Tool- und Zustandsverwaltung

Die beiden Protokolle haben grundlegend unterschiedliche Philosophien in Bezug auf Tools und Zustand.

- **In AG-UI** sind Tools **Frontend-definiert**. Die Client-Anwendung deklariert, welche Tools verfügbar sind, und
  übergibt sie dem Agenten während eines Runs. Der Agent kann dann anfordern, diese Tools aufzurufen, aber die
  Implementierung und Ausführung erfolgen auf der Client-Seite. Die Zustandsverwaltung ist ebenfalls UI-zentriert, mit
  `STATE_SNAPSHOT`- und `STATE_DELTA`-Ereignissen, die speziell darauf ausgelegt sind, die UI eines Clients mit dem
  Agenten synchron zu halten.

- **Im Swiss AI Agent Protokoll** sind die Fähigkeiten eines Agenten **Backend-definiert** und seiner Implementierung
  inhärent. Die Tools und die Logik des Agenten sind Teil seines eigenen sicheren Backend-Dienstes. Die
  Zustandsverwaltung ist allgemeiner gehalten, wobei `RunContext` und `ThreadContext` dazu dienen, den persistenten
  Zustand langlaufender Backend-Prozesse zu verwalten, nicht nur die UI-Synchronisierung.

### Ereignismodell

Obwohl beide ereignisgesteuert sind, sind ihre Ereignis-Vokabulare für unterschiedliche Zwecke zugeschnitten.

- **AG-UI** spezifiziert einen prägnanten Satz von ungefähr 16 Ereignistypen (z.B. `TEXT_MESSAGE_CHUNK`,
  `TOOL_CALL_START`, `STATE_DELTA`), die direkt auf gängige UI-Rendering- und Interaktivitätsbedürfnisse abgebildet
  sind.

- **Das Swiss AI Agent Protokoll** verfügt über eine umfangreiche und erweiterbare Bibliothek von Ereignissen. Sein
  Hauptmerkmal ist die strikte Trennung von `Control Events` und `Display Events`, was komplexe interne Workflows
  ermöglicht, die von dem, was dem Benutzer angezeigt wird, entkoppelt sind.

### Zusammenfassung der Unterschiede

| Aspekt              | Swiss AI Agent Protokoll                                           | Agent User Interaction Protokoll (AG-UI)                      |
| :------------------ | :----------------------------------------------------------------- | :------------------------------------------------------------ |
| **Primäres Ziel**   | Full-Stack interne Orchestrierung und Kontrolle                    | Standardisierung der Agent-zu-UI-Kommunikationsverbindung     |
| **Geltungsbereich** | Gesamte interne Plattform                                          | Die Präsentationsschicht                                      |
| **Architektur**     | Publish-Subscribe (Viele-zu-viele)                                 | Client-Server (für den UI-Kanal)                              |
| **Tools**           | Backend-definiert, dem Agenten inhärent                            | Frontend-definiert, an den Agenten übergeben                  |
| **Zustand**         | Verwaltet den Backend-Prozesszustand (`Run`/`Thread`-Kontext)      | Synchronisiert den UI-Zustand (`Snapshot`/`Delta`-Ereignisse) |
| **Ereignismodell**  | Erweiterbare Bibliothek; strikte `Control`- vs. `Display`-Trennung | Fester Satz von UI-zentrierten Ereignissen                    |

### Interoperabilität und Koexistenz

Die beiden Protokolle sind sehr komplementär. Das Swiss AI Agent Protokoll kann als Backend-Engine für einen
AG-UI-kompatiblen Server dienen, wodurch mit Tools wie CopilotKit erstellte Frontends nahtlos eine Verbindung zu einer
Swiss AI Hub Instanz herstellen können.

Dies wird erreicht, indem ein **AG-UI Adapter** erstellt wird. Dieser Adapter ist ein Dienst, der zwischen den beiden
Protokollen übersetzt.

```mermaid
sequenceDiagram
    participant Frontend as Frontend (AG-UI Client)
    participant AGUIAdapter as AG-UI Adapter
    participant EventBus as Event Bus (SAAP)
    participant InternalAgent as Agent (SAAP)

    Frontend->>+AGUIAdapter: POST with AG-UI formatted request
    AGUIAdapter->>+EventBus: Publishes UserMessageEvent (SAAP Control Event)
    
    EventBus->>+InternalAgent: Delivers event
    InternalAgent->>+EventBus: Publishes ChunkEvent (SAAP Display Event)
    
    EventBus->>+AGUIAdapter: Consumes SAAP Display Event
    AGUIAdapter->>+Frontend: Streams TEXT_MESSAGE_CONTENT (AG-UI Event)

    InternalAgent->>+EventBus: Publishes StopEvent (SAAP Control & Display Event)
    EventBus->>+AGUIAdapter: Consumes SAAP StopEvent
    AGUIAdapter-->>-Frontend: Streams RUN_FINISHED (AG-UI Event) & closes connection
```

In diesem Modell ist der `AG-UI Adapter`:

1. Exponiert einen HTTP-Endpunkt, der der AG-UI-Spezifikation entspricht.
2. Empfängt AG-UI-Anfragen vom Frontend und übersetzt diese in interne Swiss AI Agent Protokoll `Control Events`.
3. Abonniert den internen `Display Event`-Stream für einen gegebenen `Display`-Kontext.
4. Übersetzt die granularen internen Ereignisse (wie `ChunkEvent` und `ThoughtEvent`) in die entsprechenden
   AG-UI-Ereignisse und streamt sie zurück an das Frontend.

Dies ermöglicht es Entwicklern, reichhaltige Benutzeroberflächen mit AG-UI-nativen Tools zu erstellen, während sie
gleichzeitig die Sicherheit, Skalierbarkeit und Beobachtbarkeit des Backend-Protokolls des Swiss AI Hub nutzen.
