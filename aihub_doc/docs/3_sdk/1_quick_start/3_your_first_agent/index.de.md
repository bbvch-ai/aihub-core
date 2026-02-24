---
title: Ihr erster Agent
source_sha: 7563f7e98c72f7c7442d54623acd4cd891842c6eae45712b4abf5ef52ec665c1
---

# Ihr erster Agent

Erstellen Sie Ihren ersten Agenten mithilfe des AI-Hub Agent (`aihub_agent`) SDK – einen einfachen Nachrichten
verarbeitenden Agenten mit einem 2-Schritt-Workflow.

## Was Sie lernen werden

Dieser Schnellstart behandelt die wesentlichen Bausteine:

- **Agent-Struktur**: Wie Agents Nachrichten in Schritten verarbeiten
- **Event-Fluss**: Daten, die zwischen Workflow-Schritten fließen
- **Konfiguration**: Einstellungen, die das Verhalten des Agenten steuern
- **Testen**: Ihren Agenten lokal ausführen

## Voraussetzungen

Sie benötigen die laufende AI-Hub Entwicklungsumgebung. Bevor Sie beginnen, stellen Sie sicher, dass Sie die Schritte
zur [Einrichtung der Entwicklungsumgebung](../1_dev_environment_setup/) abgeschlossen haben.

## Wie Agents funktionieren

AI-Hub Agents sind **ereignisgesteuerte Workflows** mit drei wesentlichen Teilen:

- **Schritte**: Funktionen, die mit `@step()` dekoriert sind und Events verarbeiten
- **Events**: Datenobjekte, die zwischen Schritten fließen
- **Konfiguration**: Typisierte Einstellungen, die das Verhalten des Agenten steuern

## Einige grundlegende Konzepte zum Start!

Schauen wir uns den Standard-Agenten an, der bei der Einrichtung der Entwicklungsumgebung erstellt wurde:

```python
import logging

from aihub_agent.agents.Agent import Agent
from aihub_lib.nats.events.user import UserMessageEvent
from aihub_lib.nats.events import StopEvent
from aihub_agent.workflow.decorators.step import step

logger = logging.getLogger(__name__)


class MyCustomAgent(Agent):

    @step()
    async def start_step(
        self,
        event: UserMessageEvent,
    ) -> StopEvent:
        content = event.messages[-1].content
        print(f"[Step 1]: UserMessageEvent: {content}")
        hello_world_message = "Hello World!\n"
        return StopEvent(final_message=hello_world_message)
```

Wenn Sie die UI starten und versuchen, den Agenten in der OpenWebUI zu verwenden, werden Sie feststellen, dass der Agent
nicht antwortet.

![image](../../../../media/sdk/your_first_agent/pre_chunk_event.png)

### Chunk Events verwenden, um Live-Chat-Antworten anzuzeigen

Der Grund, warum Sie im Chat-Interface keine Antwort sehen, ist, dass in der UI nur spezielle Events (`DisplayEvents`)
angezeigt werden. Und für Chat-Interfaces wird die Antwort speziell aus `ChunkEvent`s zusammengesetzt. Lassen Sie uns
also unseren Schritt befähigen, ein solches `ChunkEvent` anzuzeigen. Dafür müssen wir den `EventDisplayer` in der
Schritt-Funktion verwenden und die Methode `display_chunk` erwarten, mit einem ersten Argument des anzuzeigenden
Inhalts, und als zweites Argument können wir die Quelle dieses Chunks übergeben. Normalerweise ist dies der Modellname
oder das Sprachmodell, das diesen Chunk produziert. Da wir in unserem Fall den Chunk vorerst fest codieren, verwenden
wir einfach den Klassennamen des Agenten als Quelle.

```python
import logging

from aihub_agent.agents.Agent import Agent
from aihub_lib.nats.events.user import UserMessageEvent
from aihub_lib.nats.events import StopEvent
from aihub_agent.workflow.decorators.step import step
from aihub_lib.displayers.EventDisplayer import EventDisplayer # [!code ++]

logger = logging.getLogger(__name__)


class MyCustomAgent(Agent):

    @step()
    async def start_step(
        self,
        event: UserMessageEvent,
        displayer: EventDisplayer, # [!code ++]
    ) -> StopEvent:
        content = event.messages[-1].content
        print(f"[Step 1]: UserMessageEvent: {content}")
        hello_world_message = "Hello World!\n"
        await displayer.display_chunk(hello_world_message, "MyCustomAgent") # [!code ++]
        return StopEvent(final_message=hello_world_message)
```

So sehen wir, dass der Agent mit einer tatsächlichen Nachricht antwortet.

![image](../../../../media/sdk/your_first_agent/post_chunk_event.png)

### Die Macht des Streamings sehen

Wie Sie vielleicht von anderen KI-Tools wissen, produzieren große Sprachmodelle ihre Antworten Stück für Stück. Anstatt
die Antwort am Ende nur als Ganzes anzuzeigen, können wir die endgültige Antwort Stück für Stück aufbauen, was es uns
ermöglicht, dem Benutzer so schnell wie möglich einen Teil der Antwort zu zeigen. Lassen Sie uns dies demonstrieren:

```python
import logging
import asyncio # [!code ++]

from aihub_agent.agents.Agent import Agent
from aihub_lib.nats.events.user import UserMessageEvent
from aihub_lib.nats.events import StopEvent
from aihub_agent.workflow.decorators.step import step
from aihub_lib.displayers.EventDisplayer import EventDisplayer

logger = logging.getLogger(__name__)


class MyCustomAgent(Agent):

    @step()
    async def start_step(
        self,
        event: UserMessageEvent,
        displayer: EventDisplayer,
    ) -> StopEvent:
        content = event.messages[-1].content
        print(f"[Step 1]: UserMessageEvent: {content}")
        hello_world_message = "Hello World!\n"
        await displayer.display_chunk(hello_world_message, "MyCustomAgent")
        await asyncio.sleep(2) # [!code ++]
        repeat_message = f"You said: {content}!\n" # [!code ++]
        await displayer.display_chunk(repeat_message, "MyCustomAgent") # [!code ++]
        return StopEvent(final_message=hello_world_message)
```

Wir haben gerade einen zweiten Chunk hinzugefügt, der angezeigt wird. Wenn Sie den Agenten jetzt erneut ausführen, sehen
Sie, dass er zuerst mit `Hello World!` und nach 2 Sekunden mit `You said: Hello!` antworten wird.
<video controls="controls" src="../../../../media/sdk/your_first_agent/show_chunk_delay.mp4" type="video/mp4" />

### Einige Denk-Schritte hinzufügen

Besonders wenn der Agent länger braucht, um sein Ergebnis zu finalisieren, ist es eine gute Praxis, den Benutzer darüber
zu informieren, was im Agenten vor sich geht. Um dies zu ermöglichen, können Sie `ThoughtEvent`s anzeigen. Auch hier
verwenden wir den `EventDisplayer`, diesmal jedoch mit der Methode `display_thought`.

```python
import logging
import asyncio

from aihub_agent.agents.Agent import Agent
from aihub_lib.nats.events.user import UserMessageEvent
from aihub_lib.nats.events import StopEvent
from aihub_agent.workflow.decorators.step import step
from aihub_lib.displayers.EventDisplayer import EventDisplayer

logger = logging.getLogger(__name__)


class MyCustomAgent(Agent):

    @step()
    async def start_step(
        self,
        event: UserMessageEvent,
        displayer: EventDisplayer,
    ) -> StopEvent:
        content = event.messages[-1].content
        print(f"[Step 1]: UserMessageEvent: {content}")
        await displayer.display_thought("Drinking coffee...")  # [!code ++]
        hello_world_message = "Hello World!\n"
        await displayer.display_chunk(hello_world_message, "MyCustomAgent")
        await asyncio.sleep(2)
        repeat_message = f"You said: {content}!\n"
        await displayer.display_chunk(repeat_message, "MyCustomAgent")
        return StopEvent(final_message=hello_world_message)
```

Jetzt sehen Sie, dass es einen zusätzlichen Abschnitt in der Antwort namens `Thinking...` gibt. Wenn Sie ihn erweitern,
können Sie unseren Gedanken mit dem Inhalt `Drinking coffee...` sehen.
![image](../../../../media/sdk/your_first_agent/show_thought.png)

## Erstellen Sie Ihren ersten Multistep-Agenten

### 1. Ein benutzerdefiniertes Event erstellen (`events/MyCustomAgentEvent.py`):

Erstellen Sie zuerst ein Event, um Daten zwischen den Schritten zu übergeben:

```python
from typing import Annotated

from aihub_lib.nats.events import ControlEvent
from pydantic import Field


class MyCustomAgentEvent(ControlEvent):
    word_count: Annotated[int, Field(description="The word count of the processed content")]

```

### 2. Agent-Implementierung anpassen (`MyCustomAgent.py`):

```python
import logging
import asyncio

from aihub_agent.agents.Agent import Agent
from aihub_lib.nats.events.user import UserMessageEvent
from aihub_lib.nats.events import StopEvent
from aihub_agent.workflow.decorators.step import step
from aihub_lib.displayers.EventDisplayer import EventDisplayer

from .events.MyCustomAgentEvent import MyCustomAgentEvent # [!code ++]

logger = logging.getLogger(__name__)


class MyCustomAgent(Agent):

    @step()
    async def start_step(
        self,
        event: UserMessageEvent,
        displayer: EventDisplayer,
    ) -> MyCustomAgentEvent:
        content = event.messages[-1].content
        print(f"[Step 1]: UserMessageEvent: {content}")
        await displayer.display_thought("Drinking coffee...")
        hello_world_message = "Hello World!\n"
        await displayer.display_chunk(hello_world_message, "MyCustomAgent")
        await asyncio.sleep(2)
        repeat_message = f"You said: {content}!\n"
        await displayer.display_chunk(repeat_message, "MyCustomAgent")
        word_count = len(content.split()) # [!code ++]
        return MyCustomAgentEvent(word_count=word_count) # [!code ++]
        return StopEvent(final_message=hello_world_message) # [!code --]

    @step() # [!code ++]
    async def stop_step( # [!code ++]
        self, # [!code ++]
        event: MyCustomAgentEvent, # [!code ++]
        displayer: EventDisplayer, # [!code ++]
    ) -> StopEvent: # [!code ++]
        await displayer.display_chunk(f"The word count is {event.word_count} words\n", "MyCustomAgent") # [!code ++]
        return StopEvent() # [!code ++]
```

Jetzt haben Sie einen ersten Agenten, der in zwei Schritten agiert. Im ersten Schritt tun wir alles, was wir zuvor getan
haben, aber wir zählen auch die Anzahl der Wörter in der Benutzernachricht. Diese Information wird dann an einen zweiten
Schritt übergeben, wo wir der Antwort auch `The word count is X words` hinzufügen, wobei X die Anzahl der Wörter ist,
die wir im ersten Schritt gezählt haben. Wir haben die beiden Schritte verbunden, indem wir unser neues Event
`MyCustomAgentEvent` als Ausgabe des ersten Schritts und als Eingabe für den zweiten Schritt definiert haben.

Wenn Sie zur Agent-Übersicht navigieren, dort Ihren Agenten auswählen und dann zu `Workflow` gehen, können Sie den
Workflow und die Schritte Ihres Agenten sehen. Sie können sehen, welche Schritte definiert sind und welche Eingabe- und
Ausgabe-Events diese Schritte haben.

![image](../../../../media/sdk/your_first_agent/simple_workflow.png)

### 3. Agent-Konfiguration hinzufügen (`MyCustomAgentConfig.py`):

Oft möchten Sie Ihren Agenten beim Start konfigurieren können. Dafür können Sie die Konfigurationsklasse verwenden. Wenn
Sie Ihren Agenten über die CLI eingerichtet haben, wurde bereits eine grundlegende Konfigurationsdatei für Sie erstellt,
die wie folgt aussieht:

```python
from typing import Annotated

from pydantic import Field
from aihub_lib.agents.AgentConfig import AgentConfig


class MyCustomAgentConfig(AgentConfig):
    """Configuration class for My First Agent Agent."""

    config_value: Annotated[str, Field(
        default="Default Config Value",
        description="Some configuration value for the agent"
    )]
```

Wir können auf diese Konfiguration in jedem Schritt zugreifen, wenn wir sie benötigen. Zum Beispiel können wir den
Inhalt des Feldes `config_value` im zweiten Schritt unseres Agenten lesen und seinen String-Wert auch als Chunk
veröffentlichen. Normalerweise verwenden Sie die Konfiguration jedoch, um eine Logik in Ihren Schritten zu
konfigurieren, entweder mit System-Prompts oder Konfigurationen für einige Methoden.

```python
import logging
import asyncio

from aihub_agent.agents.Agent import Agent
from aihub_lib.nats.events.user import UserMessageEvent
from aihub_lib.nats.events import StopEvent
from aihub_agent.workflow.decorators.step import step
from aihub_lib.displayers.EventDisplayer import EventDisplayer

from .events.MyCustomAgentEvent import MyCustomAgentEvent
from .MyCustomAgentConfig import MyCustomAgentConfig  # [!code ++]

logger = logging.getLogger(__name__)


class MyCustomAgent(Agent):

    @step()
    async def start_step(
        self,
        event: UserMessageEvent,
        displayer: EventDisplayer,
    ) -> MyCustomAgentEvent:
        content = event.messages[-1].content
        print(f"[Step 1]: UserMessageEvent: {content}")
        await displayer.display_thought("Drinking coffee...")
        hello_world_message = "Hello World!\n"
        await displayer.display_chunk(hello_world_message, "MyCustomAgent")
        await asyncio.sleep(2)
        repeat_message = f"You said: {content}!\n"
        await displayer.display_chunk(repeat_message, "MyCustomAgent")
        word_count = len(content.split())
        return MyCustomAgentEvent(word_count=word_count)

    @step()
    async def stop_step(
        self,
        event: MyCustomAgentEvent,
        config: MyCustomAgentConfig,  # [!code ++]
        displayer: EventDisplayer,
    ) -> StopEvent:
        await displayer.display_chunk(f"The word count is {event.word_count} words\n", "MyCustomAgent")
        await displayer.display_chunk(f"My config sais: {config.config_value}", "MyCustomAgent")
        return StopEvent()
```

Sie können die Konfigurationswerte in Ihrer `trigger.py` oder beim Bau des Agenten in der `main.py` festlegen.

```python{10}
async def main():
    runner = AgentRunner(
        agent_type=MyCustomAgent,
        agent_config=MyCustomAgentConfig(
            agent_class=MyCustomAgent.__name__,
            agent_id="my_custom_agent",
            name=LocaleString(en="My Custom Agent"),
            description=LocaleString(en="This is a simple agent created from a template."),
            config_value="My first Config Value"
        ),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
```

### 4. Testskript (`trigger.py`):

## Agenten ausführen und debuggen

1. **Testskript ausführen**:

Um Ihren Agenten schnell zu testen, können Sie ein `trigger.py`-Skript schreiben, das den Agenten startet und sein
StartEvent postet. Auf diese Weise können Sie den Agenten ohne UI testen.

::: code-group

```python [trigger.py]
import asyncio
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import UserMessageEvent
from aihub_lib.testing.auth_utils.fake_user import fake_user
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from MyAgent import MyAgent
from MyAgentConfig import MyAgentConfig

# Enable detailed logging to see event flow
enable_logging()

async def main():
    # Configure the agent
    config = MyAgentConfig(
        agent_class=MyCustomAgent.__name__,
        agent_id="my_custom_agent",
        name=LocaleString(en="My Custom Agent"),
        description=LocaleString(en="This is a simple agent created from a template."),
        config_value="My first Config Value"
    )
    
    # Create test runner
    runner = AgentTestRunner(agent_type=MyAgent, agent_config=config)
    
    # Run the agent with a test message
    async with runner.test_run() as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(
                    content="Hello world this is my first agent",
                    role=MessageRole.USER
                )],
                user=fake_user()
            )
        )
    
    print(f"Agent completed: {runner.has_stop_event}")

if __name__ == "__main__":
    asyncio.run(main())
```

```bash
python trigger.py
```

Erwartete Ausgabe:

```
[Schritt 1] Verarbeite Nachricht: 'Hello world this is my first agent' -> 'HELLO WORLD THIS IS MY FIRST AGENT'
[Schritt 2] Erstelle Antwort: 'Processed: HELLO WORLD THIS IS MY FIRST AGENT (Words: 7)'
Agent abgeschlossen: True
```

2. **Mit Langfuse Tracing debuggen** – Öffnen Sie `http://localhost:6006`, um Folgendes zu sehen:

   - Schritt-für-Schritt-Ausführungsfluss
   - Event-Daten, die zwischen den Schritten fließen
   - Timing- und Performance-Metriken
   - Details zur Event-Payload

3. **Logs prüfen** – Der Aufruf `enable_logging()` zeigt den Event-Fluss in Echtzeit und hilft bei der Fehlersuche.

## Den Workflow verstehen

Ihr Agent folgt diesem Event-Fluss:

1. **UserMessageEvent** → `process_message()` → **MessageEvent**
2. **MessageEvent** → `create_response()` → **StopEvent**

Jeder Schritt:

- Empfängt ein Event als Eingabe
- Verarbeitet die Daten
- Gibt ein neues Event zurück
- Die Workflow-Engine leitet Events an den nächsten Schritt weiter

## Was Sie gelernt haben

- **Ereignisgesteuerte Workflows**: Schritte verarbeiten Events und produzieren neue Events
- **Benutzerdefinierte Events**: Erstellen typisierter Datenobjekte zur Übergabe zwischen Schritten
- **Konfiguration**: Verwenden typisierter Einstellungen zur Steuerung des Agentenverhaltens
- **Testen**: `AgentTestRunner` für isolierte Tests verwenden
- **Debuggen**: Langfuse Tracing und Logging für Observability

## Nächste Schritte

- [Ihre erste Pipeline](../4_your_first_pipeline/) -
- [Agents erstellen](../../2_building_agents/) - Erfahren Sie mehr über fortgeschrittene Agent-Muster
