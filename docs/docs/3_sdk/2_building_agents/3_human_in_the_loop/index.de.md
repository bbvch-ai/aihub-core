---
title: Human in the Loop
source_sha: 1829d88e85c0eca8ba68bd9a1fc64ff0c0ef96327aad0d3a04bfaaf5fe6a43fc
---

# Human in the Loop

Das **Human in the Loop (HITL)**-Muster ermöglicht es einem Agent, seine Ausführung an einem kritischen Punkt zu
pausieren und Eingaben, Genehmigungen oder Anweisungen von einem menschlichen Benutzer anzufordern, bevor er fortfährt.

## Funktionsweise

Das HITL-Muster wird durch ein Paar von Events orchestriert, die die Pause- und Fortsetzungslogik verwalten:

1. **Request**: Ein Schritt in Ihrem Agent gibt ein `HumanInTheLoop.request` Event zurück. Dies ist ein spezielles
   `ControlEvent`, das auch als `DisplayEvent` fungiert, den Workflow pausiert und dem Benutzer in der UI eine Frage
   präsentiert.
2. **Response**: Die Antwort des Benutzers wird als `HumanInTheLoop.response` Event an das System zurückgesendet.
3. **Resume**: Ein weiterer Schritt in Ihrem Agent ist so konfiguriert, dass er dieses Response-Event akzeptiert. Wenn
   das Event eintrifft, verteilt der Dispatcher es an den korrekten Schritt, und der Workflow setzt seine Ausführung
   fort.

Die `HumanInTheLoop`-Helferklasse vereinfacht diesen Prozess, indem sie eine bequeme `invoke`-Methode bereitstellt, um
das Request-Event mit den korrekten Routing-Informationen zu erstellen.

## Drei HITL-Typen

Das Framework bietet drei Interaktionstypen, jeder wird in der UI unterschiedlich dargestellt:

| Typ              | Klasse                       | UI-Verhalten                                                         | Antworttyp |
| :--------------- | :--------------------------- | :------------------------------------------------------------------- | :--------- |
| **Input**        | `HumanInTheLoopInput`        | Popup-Dialog für freie Texteingabe                                   | `str`      |
| **Confirmation** | `HumanInTheLoopConfirmation` | Ja/Nein-Schaltflächenauswahl                                         | `bool`     |
| **Chat**         | `HumanInTheLoopChat`         | Nachricht im Chat-Stream (Fallback für UIs ohne Popup-Unterstützung) | `str`      |

```python
from swiss_ai_hub.core.events.human_in_the_loop import (
    HumanInTheLoopInput,
    HumanInTheLoopConfirmation,
    HumanInTheLoopChat,
)

# Popup mit Texteingabefeld
HumanInTheLoopInput.invoke(question="What is your preferred language?")

# Ja/Nein-Schaltflächen
HumanInTheLoopConfirmation.invoke(question="Approve this transaction?")

# Chat-Nachricht (keine spezielle UI-Behandlung)
HumanInTheLoopChat.invoke(question="Please provide additional context.")
```

### Leitfaden zur Typenauswahl

| Anwendungsfall             | Typ                          | Beispiel                                          |
| :------------------------- | :--------------------------- | :------------------------------------------------ |
| Freie Benutzereingabe      | `HumanInTheLoopInput`        | "Suchanfrage eingeben:", "Problem beschreiben:"   |
| Binäre Entscheidung        | `HumanInTheLoopConfirmation` | "Diese Datei löschen?", "Mit Zahlung fortfahren?" |
| Konversationeller Fallback | `HumanInTheLoopChat`         | APIs oder UIs ohne Popup-Unterstützung            |

## Kernmuster: Einzelgenehmigung

Dieses Beispiel zeigt einen einfachen Workflow, bei dem der Agent um eine einzelne Bestätigung bittet, bevor er
fortfährt.

**Referenz**: `playground/minimal_workflow/human_in_the_loop_workflow/`

```python
from swiss_ai_hub.core.events.human_in_the_loop import HumanInTheLoopInput

class ApprovalAgent(Agent):
    @step()
    async def request_approval(self, event: StartEvent) -> HumanInTheLoopInput.request:
        return HumanInTheLoopInput.invoke(question="Please enter your feedback:")

    @step()
    async def handle_response(self, event: HumanInTheLoopInput.response) -> StopEvent:
        user_response = event.response
        return StopEvent()
```

## Mehrstufige Genehmigung mit benutzerdefinierten Event-Paaren

Für Workflows, die mehrere menschliche Interaktionen erfordern, erstellen Sie separate Unterklassen. Der Dispatcher
unterscheidet Schritte nach Event-Typ – die Verwendung desselben Basistyps für mehrere Interaktionen führt zu
Mehrdeutigkeiten.

**Referenz**: `playground/minimal_workflow/multistep_human_in_the_loop_workflow/`

### Schritt 1: Benutzerdefinierte HITL-Event-Paare definieren

Jeder HITL-Interaktionspunkt benötigt ein eigenes Request/Response-Event-Paar und eine Wrapper-Klasse:

::: code-group
```python [events/FirstStepHumanInTheLoop.py]
from swiss_ai_hub.core.events.human_in_the_loop import HumanInTheLoopInput
from swiss_ai_hub.core.events.human_in_the_loop.request import HumanInTheLoopInputRequestEvent
from swiss_ai_hub.core.events.human_in_the_loop.response import HumanInTheLoopInputResponseEvent


class FirstStepHumanInTheLoopRequestEvent(HumanInTheLoopInputRequestEvent):
    pass


class FirstStepHumanInTheLoopResponseEvent(HumanInTheLoopInputResponseEvent):
    pass


class FirstStepHumanInTheLoop(HumanInTheLoopInput):
    request = FirstStepHumanInTheLoopRequestEvent
    response = FirstStepHumanInTheLoopResponseEvent
```

```python [events/SecondStepHumanInTheLoop.py]
from swiss_ai_hub.core.events.human_in_the_loop import HumanInTheLoopInput
from swiss_ai_hub.core.events.human_in_the_loop.request import HumanInTheLoopInputRequestEvent
from swiss_ai_hub.core.events.human_in_the_loop.response import HumanInTheLoopInputResponseEvent


class SecondStepHumanInTheLoopRequestEvent(HumanInTheLoopInputRequestEvent):
    pass


class SecondStepHumanInTheLoopResponseEvent(HumanInTheLoopInputResponseEvent):
    pass


class SecondStepHumanInTheLoop(HumanInTheLoopInput):
    request = SecondStepHumanInTheLoopRequestEvent
    response = SecondStepHumanInTheLoopResponseEvent
```
:::

### Schritt 2: Verschiedene Typen im Workflow verwenden

```python
from swiss_ai_hub.core.events import StartEvent, StopEvent
from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.workflow.decorators.step import step

from .events.FirstStepHumanInTheLoop import FirstStepHumanInTheLoop
from .events.SecondStepHumanInTheLoop import SecondStepHumanInTheLoop


class MultistepHumanInTheLoopAgent(Agent):
    @step()
    async def start_step(self, event: StartEvent) -> FirstStepHumanInTheLoop.request:
        return FirstStepHumanInTheLoop.invoke(question="Shall I continue?")

    @step()
    async def second_hitl(
        self, event: FirstStepHumanInTheLoop.response
    ) -> SecondStepHumanInTheLoop.request:
        print(f"First response: {event.response}")
        return SecondStepHumanInTheLoop.invoke(question="Are you sure?")

    @step()
    async def end_step(self, event: SecondStepHumanInTheLoop.response) -> StopEvent:
        print(f"Second response: {event.response}")
        return StopEvent()
```

## Dynamische HITL-Typauswahl

Wenn der HITL-Typ von Laufzeitbedingungen abhängt, verwenden Sie Union-Rückgabetypen:

```python
from swiss_ai_hub.core.events import StopEvent, UserMessageEvent
from swiss_ai_hub.core.events.human_in_the_loop import (
    HumanInTheLoopChat,
    HumanInTheLoopConfirmation,
    HumanInTheLoopInput,
)

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.workflow.decorators.step import step


class HitlDemoAgent(Agent):
    @step()
    async def select_hitl_type(
        self, event: UserMessageEvent
    ) -> HumanInTheLoopInput.request | HumanInTheLoopConfirmation.request | HumanInTheLoopChat.request:
        choice = event.user_query.lower()

        if "confirmation" in choice:
            return HumanInTheLoopConfirmation.invoke("Do you confirm this action?")
        elif "chat" in choice:
            return HumanInTheLoopChat.invoke("This is a chat-style question. What is your response?")
        else:
            return HumanInTheLoopInput.invoke("Please enter your text input:")

    @step()
    async def handle_response(
        self,
        event: HumanInTheLoopInput.response | HumanInTheLoopConfirmation.response | HumanInTheLoopChat.response,
    ) -> StopEvent:
        if isinstance(event, HumanInTheLoopConfirmation.response):
            result = f"Confirmation: {'Yes' if event.response else 'No'}"
        else:
            result = f"Response: {event.response}"
        return StopEvent()
```

## Bot-in-the-Loop (Teams/Slack-Integration)

Bot-in-the-Loop (BITL) ermöglicht Workflows die Interaktion mit externen Messaging-Plattformen über das Azure Bot
Framework. Im Gegensatz zu HITL (das Benutzer innerhalb der Agent-UI auffordert) sendet BITL Nachrichten an Microsoft
Teams-Kanäle oder Slack-Kanäle und wartet auf Antworten von Benutzern auf diesen Plattformen.

### Kanalkonfiguration

BITL erfordert plattformspezifische Konfiguration:

::: code-group
```python [Microsoft Teams]
from swiss_ai_hub.core.events.bot_in_the_loop.request.bot_in_the_loop_request_event import TeamsConfig

teams_config = TeamsConfig(
    channel_id="19:abc123@thread.tacv2",  # Teams channel ID
    tenant_id="12345678-1234-1234-1234-123456789abc",  # Azure AD tenant ID
    bot_id="87654321-4321-4321-4321-cba987654321",  # Bot UUID
)
```

```python [Slack]
from swiss_ai_hub.core.events.bot_in_the_loop.request.bot_in_the_loop_request_event import SlackConfig

slack_config = SlackConfig(
    channel_id="C0123456789",  # Slack channel ID (starts with 'C')
    service_url="https://slack.botframework.com",
)
```
:::

### Grundlegende Verwendung

```python
from swiss_ai_hub.core.events import StopEvent
from swiss_ai_hub.core.events.bot_in_the_loop.bot_in_the_loop import BotInTheLoop

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.workflow.decorators.step import step


class BotInTheLoopAgent(Agent):
    @step()
    async def request_approval(
        self, start_event: MyStartEvent
    ) -> BotInTheLoop.request:
        return BotInTheLoop.invoke(
            user=start_event.user,
            question="Should the agent proceed with the deployment?",
            channel_config=start_event.channel_config,  # TeamsConfig or SlackConfig
        )

    @step()
    async def handle_response(self, event: BotInTheLoop.response) -> StopEvent:
        answer = event.response

        if event.responder:
            print(f"Answered by: {event.responder.user_name} ({event.responder.user_id})")
            if event.responder.aad_object_id:  # Teams-specific
                print(f"AAD Object ID: {event.responder.aad_object_id}")

        return StopEvent()
```

### Iterative Konversationen

BITL unterstützt mehrstufige Konversationen, indem ein weiteres `BotInTheLoop.request` zurückgegeben wird:

```python
@step()
async def handle_response(
    self, event: BotInTheLoop.response
) -> BotInTheLoop.request | StopEvent:
    if event.response.lower() == "yes":
        return StopEvent()
    else:
        return BotInTheLoop.invoke(
            user=event.request_event.user,
            question="What about now? Ready to proceed?",
            channel_config=event.request_event.channel_config,
        )
```

### Struktur des Response-Events

Das `BotInTheLoop.response`-Event bietet:

| Feld            | Typ                         | Beschreibung                             |
| :-------------- | :-------------------------- | :--------------------------------------- |
| `response`      | `str`                       | Der Nachrichtentext des Benutzers        |
| `request_event` | `BotInTheLoopRequestEvent`  | Ursprünglicher Request (für den Kontext) |
| `responder`     | `BotInTheLoopResponderInfo` | Wer geantwortet hat                      |

**Responder-Informationen:**

| Feld              | Typ            | Beschreibung                        |
| :---------------- | :------------- | :---------------------------------- |
| `user_id`         | `str`          | Plattform-Benutzer-ID (Slack/Teams) |
| `user_name`       | `str`          | Anzeigename                         |
| `additional_info` | `dict \| None` | Plattformspezifische Metadaten      |
| `aad_object_id`   | `str \| None`  | Azure AD Objekt-ID (nur Teams)      |

### BITL vs. HITL

| Aspekt                | HumanInTheLoop               | BotInTheLoop                                                 |
| :-------------------- | :--------------------------- | :----------------------------------------------------------- |
| **Plattform**         | Agent-UI (Web/Mobil)         | Teams / Slack                                                |
| **Benutzerkontext**   | Benutzer derselben Session   | Externe Kanalbenutzer                                        |
| **UI-Optionen**       | Input, Confirmation, Chat    | Nur Textnachricht                                            |
| **Antwortverfolgung** | Implizit (gleicher Benutzer) | Explizit (`responder`-Feld)                                  |
| **Anwendungsfall**    | In-App-Genehmigungen         | Plattformübergreifende Benachrichtigungen, Team-Eskalationen |
