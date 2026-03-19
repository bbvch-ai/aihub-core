---
title: Human-in-the-Loop
source_sha: "074ec20f7a61c1c4eae62e9beff09f7ae3d3b411ab0ce06e0e39980474d2570c"
---

# Human-in-the-Loop

Das **Human-in-the-Loop (HITL)**-Muster ermöglicht es einem Agenten, seine Ausführung an einem kritischen Punkt anzuhalten und Eingaben, Genehmigungen oder Anweisungen von einem menschlichen Benutzer anzufordern, bevor er fortfährt.

## Funktionsweise

Das HITL-Muster wird durch ein Ereignispaar orchestriert, das die Logik zum Anhalten und Fortsetzen steuert:

1.  **Request**: Ein Schritt in Ihrem Agenten gibt ein `HumanInTheLoop.request`-Ereignis zurück. Dies ist ein spezielles `ControlEvent`, das auch als `DisplayEvent` fungiert, den Workflow anhält und dem Benutzer in der UI eine Frage präsentiert.
2.  **Response**: Die Antwort des Benutzers wird als `HumanInTheLoop.response`-Ereignis an das System zurückgesendet.
3.  **Resume**: Ein weiterer Schritt in Ihrem Agenten ist so konfiguriert, dass er dieses Antwort-Ereignis akzeptiert. Wenn das Ereignis eintrifft, leitet der Dispatcher es an den richtigen Schritt weiter, und der Workflow setzt seine Ausführung fort.

Die `HumanInTheLoop`-Hilfsklasse vereinfacht diesen Prozess, indem sie eine bequeme `invoke`-Methode bereitstellt, um das Anfrage-Ereignis mit den korrekten Routing-Informationen zu erstellen.

## Drei HITL-Typen

Das Framework bietet drei Interaktionstypen, die jeweils in der UI unterschiedlich dargestellt werden:

| Typ              | Klasse                       | UI-Verhalten                                                    | Antworttyp    |
| :--------------- | :--------------------------- | :-------------------------------------------------------------- | :------------ |
| **Input**        | `HumanInTheLoopInput`        | Popup-Dialog für Freitext-Eingabe                              | `str`         |
| **Confirmation** | `HumanInTheLoopConfirmation` | Ja/Nein-Schaltflächenauswahl                                    | `bool`        |
| **Chat**         | `HumanInTheLoopChat`         | Nachricht im Chat-Stream (Fallback für UIs ohne Popup-Unterstützung) | `str`         |

```python
from swiss_ai_hub.core.events.agent.hitl.human_in_the_loop_input import HumanInTheLoopInput
from swiss_ai_hub.core.events.agent.hitl.human_in_the_loop_confirmation import HumanInTheLoopConfirmation
from swiss_ai_hub.core.events.agent.hitl.human_in_the_loop_chat import HumanInTheLoopChat

# Popup with text input field
HumanInTheLoopInput.invoke(question="What is your preferred language?")

# Yes/No buttons
HumanInTheLoopConfirmation.invoke(question="Approve this transaction?")

# Chat message (no special UI treatment)
HumanInTheLoopChat.invoke(question="Please provide additional context.")
```

### Leitfaden zur Typauswahl

| Anwendungsfall             | Typ                          | Beispiel                                     |
| :------------------------- | :--------------------------- | :------------------------------------------- |
| Freiform-Benutzereingabe   | `HumanInTheLoopInput`        | „Suchanfrage eingeben:", „Problem beschreiben:" |
| Binäre Entscheidung        | `HumanInTheLoopConfirmation` | „Diese Datei löschen?", „Mit der Zahlung fortfahren?" |
| Konversationeller Fallback | `HumanInTheLoopChat`         | APIs oder UIs ohne Popup-Unterstützung       |

## Kernmuster: Einzelgenehmigung

Dieses Beispiel zeigt einen einfachen Workflow, bei dem der Agent eine einzelne Bestätigung anfordert, bevor er fortfährt.

**Referenz**: `playground/minimal_workflow/human_in_the_loop_workflow/`

```python
from swiss_ai_hub.core.events.agent.hitl.human_in_the_loop_input import HumanInTheLoopInput

class ApprovalAgent(Agent):
    @step()
    async def request_approval(self, event: StartEvent) -> HumanInTheLoopInput.request:
        return HumanInTheLoopInput.invoke(question="Please enter your feedback:")

    @step()
    async def handle_response(self, event: HumanInTheLoopInput.response) -> StopEvent:
        user_response = event.response
        return StopEvent()
```

## Mehrstufige Genehmigung mit benutzerdefinierten Ereignispaaren

Für Workflows, die mehrere menschliche Interaktionen erfordern, erstellen Sie separate Unterklassen. Der Dispatcher unterscheidet Schritte nach Ereignistyp – die Verwendung desselben Basistyps für mehrere Interaktionen führt zu Mehrdeutigkeiten.

**Referenz**: `playground/minimal_workflow/multistep_human_in_the_loop_workflow/`

### Schritt 1: Benutzerdefinierte HITL-Ereignispaare definieren

Jeder HITL-Interaktionspunkt benötigt ein eigenes Anfrage-/Antwort-Ereignispaar und eine Wrapper-Klasse:

::: code-group
```python [events/FirstStepHumanInTheLoop.py]
from swiss_ai_hub.core.events.agent.hitl.human_in_the_loop_input import HumanInTheLoopInput
from swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_input_request_event import HumanInTheLoopInputRequestEvent
from swiss_ai_hub.core.events.agent.hitl.response.human_in_the_loop_input_response_event import HumanInTheLoopInputResponseEvent


class FirstStepHumanInTheLoopRequestEvent(HumanInTheLoopInputRequestEvent):
    pass


class FirstStepHumanInTheLoopResponseEvent(HumanInTheLoopInputResponseEvent):
    pass


class FirstStepHumanInTheLoop(HumanInTheLoopInput):
    request = FirstStepHumanInTheLoopRequestEvent
    response = FirstStepHumanInTheLoopResponseEvent
```

```python [events/SecondStepHumanInTheLoop.py]
from swiss_ai_hub.core.events.agent.hitl.human_in_the_loop_input import HumanInTheLoopInput
from swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_input_request_event import HumanInTheLoopInputRequestEvent
from swiss_ai_hub.core.events.agent.hitl.response.human_in_the_loop_input_response_event import HumanInTheLoopInputResponseEvent


class SecondStepHumanInTheLoopRequestEvent(HumanInTheLoopInputRequestEvent):
    pass


class SecondStepHumanInTheLoopResponseEvent(HumanInTheLoopInputResponseEvent):
    pass


class SecondStepHumanInTheLoop(HumanInTheLoopInput):
    request = SecondStepHumanInTheLoopRequestEvent
    response = SecondStepHumanInTheLoopResponseEvent
```
:::

### Schritt 2: Verwendung unterschiedlicher Typen im Workflow

```python
from swiss_ai_hub.core.events.agent.control.start.start_event import StartEvent
from swiss_ai_hub.core.events.agent.control.stop.stop_event import StopEvent
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
from swiss_ai_hub.core.events.agent.control.stop.stop_event import StopEvent
from swiss_ai_hub.core.events.agent.user.user_message_event import UserMessageEvent
from swiss_ai_hub.core.events.agent.hitl.human_in_the_loop_chat import HumanInTheLoopChat
from swiss_ai_hub.core.events.agent.hitl.human_in_the_loop_confirmation import HumanInTheLoopConfirmation
from swiss_ai_hub.core.events.agent.hitl.human_in_the_loop_input import HumanInTheLoopInput

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

Bot-in-the-Loop (BITL) ermöglicht Workflows die Interaktion mit externen Messaging-Plattformen über das Azure Bot Framework. Im Gegensatz zu HITL (das Benutzer innerhalb der Agent-UI auffordert), sendet BITL Nachrichten an Microsoft Teams-Kanäle oder Slack-Kanäle und erwartet Antworten von Benutzern auf diesen Plattformen.

### Kanal-Konfiguration

BITL erfordert plattformspezifische Konfiguration:

::: code-group
```python [Microsoft Teams]
from swiss_ai_hub.core.events.agent.bitl.request.bot_in_the_loop_request_event import TeamsConfig

teams_config = TeamsConfig(
    channel_id="19:abc123@thread.tacv2",  # Teams channel ID
    tenant_id="12345678-1234-1234-1234-123456789abc",  # Azure AD tenant ID
    bot_id="87654321-4321-4321-4321-cba987654321",  # Bot UUID
)
```

```python [Slack]
from swiss_ai_hub.core.events.agent.bitl.request.bot_in_the_loop_request_event import SlackConfig

slack_config = SlackConfig(
    channel_id="C0123456789",  # Slack channel ID (starts with 'C')
    service_url="https://slack.botframework.com",
)
```
:::

### Grundlegende Verwendung

```python
from swiss_ai_hub.core.events.agent.control.stop.stop_event import StopEvent
from swiss_ai_hub.core.events.agent.bitl.bot_in_the_loop import BotInTheLoop

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

BITL unterstützt mehrstufige Konversationen, indem es ein weiteres `BotInTheLoop.request` zurückgibt:

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

### Struktur des Antwort-Ereignisses

Das `BotInTheLoop.response`-Ereignis bietet:

| Feld            | Typ                         | Beschreibung                          |
| :-------------- | :-------------------------- | :------------------------------------ |
| `response`      | `str`                       | Der Nachrichtentext des Benutzers      |
| `request_event` | `BotInTheLoopRequestEvent`  | Ursprüngliche Anfrage (für den Kontext) |
| `responder`     | `BotInTheLoopResponderInfo` | Wer geantwortet hat                   |

**Responder-Informationen:**

| Feld              | Typ            | Beschreibung                        |
| :---------------- | :------------- | :---------------------------------- |
| `user_id`         | `str`          | Plattform-Benutzer-ID (Slack/Teams) |
| `user_name`       | `str`          | Anzeigename                         |
| `additional_info` | `dict \| None` | Plattformspezifische Metadaten      |
| `aad_object_id`   | `str \| None`  | Azure AD Objekt-ID (nur Teams)      |

### BITL vs. HITL

| Aspekt               | HumanInTheLoop            | BotInTheLoop                                      |
| :------------------- | :------------------------ | :------------------------------------------------ |
| **Plattform**        | Agent-UI (Web/Mobil)      | Teams / Slack                                     |
| **Benutzerkontext**  | Benutzer der gleichen Session | Externe Kanalbenutzer                             |
| **UI-Optionen**      | Input, Confirmation, Chat | Nur Textnachricht                                 |
| **Antwortverfolgung** | Implizit (gleicher Benutzer) | Explizit (`responder`-Feld)                      |
| **Anwendungsfall**   | In-App-Genehmigungen      | Plattformübergreifende Benachrichtigungen, Team-Eskalationen |
