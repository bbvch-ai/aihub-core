---
title: Ihr erster Agent
source_sha: fe8b130f7da34f80a71bda26e4bdc377aff03e8c0ff9d12c028a12a465f1751b
---

# Ihr erster Agent

Erstellen Sie Ihren ersten Agenten mit dem Swiss AI Hub Agent (`swiss_ai_hub.agent`) SDK – einen einfachen
Nachrichtenverarbeitungs-Agenten mit einem 2-Schritte-Workflow.

## Was Sie lernen werden

Dieses Quickstart behandelt die wesentlichen Bausteine:

- **Agent-Struktur**: Wie Agents Nachrichten in Schritten verarbeiten
- **Event-Fluss**: Datenfluss zwischen Workflow-Schritten
- **Konfiguration**: Einstellungen, die das Verhalten des Agenten steuern
- **Testen**: Ihren Agenten lokal ausführen

## Voraussetzungen

Sie benötigen die Swiss AI Hub Entwicklungsumgebung. Bevor Sie beginnen, stellen Sie sicher, dass Sie die Schritte zum
[Einrichten der Entwicklungsumgebung](../1_dev_environment_setup/) abgeschlossen haben.

## Wie Agents funktionieren

Swiss AI Hub Agents sind **ereignisgesteuerte Workflows** mit drei wesentlichen Bestandteilen:

- **Schritte**: Funktionen, die mit `@step()` dekoriert sind und Events verarbeiten
- **Events**: Datenobjekte, die zwischen den Schritten fliessen
- **Konfiguration**: Typisierte Einstellungen, die das Verhalten des Agenten steuern

## Einige Grundkonzepte zum Einstieg!

Werfen wir einen Blick auf den Standard-Agenten, der bei der Einrichtung der Entwicklungsumgebung erstellt wurde:

```python
import logging

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.core.events.agent.user import UserMessageEvent
from swiss_ai_hub.core.events.agent.control import StopEvent
from swiss_ai_hub.agent.workflow.decorators.step import step

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

Der Grund, warum Sie keine Antwort in der Chat-Oberfläche sehen, ist, dass nur spezielle Events (`DisplayEvents`) in der
UI angezeigt werden. Und bei Chat-Oberflächen setzt sich die Antwort insbesondere aus `ChunkEvent`s zusammen.
Ermöglichen wir unserem Schritt also, ein solches `ChunkEvent` anzuzeigen. Dazu müssen wir den `EventDisplayer` in der
Step-Funktion verwenden und die `display_chunk`-Methode mit einem ersten Argument für den anzuzeigenden Inhalt und als
zweites Argument die Quelle dieses Chunks übergeben. Normalerweise ist dies der Modellname oder das Sprachmodell, das
diesen Chunk erzeugt. Da wir in unserem Fall den Chunk vorerst fest codieren, verwenden wir einfach den Klassennamen des
Agenten als Quelle.

```python
import logging

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.core.events.agent.user import UserMessageEvent
from swiss_ai_hub.core.events.agent.control import StopEvent
from swiss_ai_hub.agent.workflow.decorators.step import step
from swiss_ai_hub.core.displayers.event_displayer import EventDisplayer # [!code ++]

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

### Die Macht des Streamings erleben

Wie Sie vielleicht von anderen KI-Tools wissen, erzeugen grosse Sprachmodelle ihre Antworten Stück für Stück. Anstatt
die Antwort am Ende als Ganzes anzuzeigen, können wir die endgültige Antwort schrittweise aufbauen, was es uns
ermöglicht, dem Benutzer so schnell wie möglich einen Teil der Antwort zu zeigen. Lassen Sie es uns demonstrieren:

```python
import logging
import asyncio # [!code ++]

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.core.events.agent.user import UserMessageEvent
from swiss_ai_hub.core.events.agent.control import StopEvent
from swiss_ai_hub.agent.workflow.decorators.step import step
from swiss_ai_hub.core.displayers.event_displayer import EventDisplayer

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
Sie, dass er zuerst mit `Hello World!` antworten und nach 2 Sekunden mit `You said: Hello!` reagieren wird.
<video controls="controls" src="../../../../media/sdk/your_first_agent/show_chunk_delay.mp4" type="video/mp4" />

### Denk-Schritte hinzufügen

Besonders wenn der Agent länger braucht, um sein Ergebnis zu finalisieren, ist es eine gute Praxis, den Benutzer darüber
zu informieren, was im Agenten vor sich geht. Um dies zu ermöglichen, können Sie `ThoughtEvent`s anzeigen. Auch hier
verwenden wir den `EventDisplayer`, aber diesmal mit der `display_thought`-Methode.

```python
import logging
import asyncio

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.core.events.agent.user import UserMessageEvent
from swiss_ai_hub.core.events.agent.control import StopEvent
from swiss_ai_hub.agent.workflow.decorators.step import step
from swiss_ai_hub.core.displayers.event_displayer import EventDisplayer

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

Nun sehen Sie, dass es einen zusätzlichen Abschnitt in der Antwort namens `Thinking...` gibt. Wenn Sie diesen erweitern,
können Sie unseren Gedanken sehen, der mit dem Inhalt `Drinking coffee...` erstellt wurde.
![image](../../../../media/sdk/your_first_agent/show_thought.png)

## Ihren ersten Multi-Schritt-Agenten erstellen

### 1. Ein benutzerdefiniertes Event erstellen (`events/MyCustomAgentEvent.py`):

Zuerst erstellen Sie ein Event, um Daten zwischen den Schritten zu übergeben:

```python
from typing import Annotated

from swiss_ai_hub.core.events.agent.control import ControlEvent
from pydantic import Field


class MyCustomAgentEvent(ControlEvent):
    word_count: Annotated[int, Field(description="The word count of the processed content")]

```

### 2. Agent-Implementierung anpassen (`MyCustomAgent.py`):

```python
import logging
import asyncio

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.core.events.agent.user import UserMessageEvent
from swiss_ai_hub.core.events.agent.control import StopEvent
from swiss_ai_hub.agent.workflow.decorators.step import step
from swiss_ai_hub.core.displayers.event_displayer import EventDisplayer

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

Nun haben Sie einen ersten Agenten, der in zwei Schritten agiert. Im ersten Schritt tun wir alles, was wir zuvor getan
haben, aber wir zählen auch die Anzahl der Wörter in der Benutzernachricht. Diese Information wird dann an einen zweiten
Schritt weitergegeben, wo wir der Antwort auch `The word count is X words` hinzufügen, wobei X die Anzahl der Wörter
ist, die wir im ersten Schritt gezählt haben. Wir haben die beiden Schritte verbunden, indem wir unser neues Event
`MyCustomAgentEvent` als Ausgabe des ersten Schritts und als Eingabe für den zweiten Schritt definiert haben.

Wenn Sie zur Agent-Übersicht navigieren, dort Ihren Agenten auswählen und dann zu `Workflow` gehen, können Sie den
Workflow und die Schritte Ihres Agenten sehen. Sie können sehen, welche Schritte definiert sind und welche Eingabe- und
Ausgabe-Events diese Schritte haben.

![image](../../../../media/sdk/your_first_agent/simple_workflow.png)

### 3. Agent-Konfiguration hinzufügen (`MyCustomAgentConfig.py`):

Oftmals möchten Sie, dass Ihr Agent beim Start konfigurierbar ist. Dafür können Sie die Konfigurationsklasse verwenden.
Wenn Sie Ihren Agenten über die CLI eingerichtet haben, wurde bereits eine grundlegende Konfigurationsdatei für Sie
erstellt, die so aussieht:

```python
from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.agents.agent_config import AgentConfig


class MyCustomAgentConfig(AgentConfig):
    """Configuration class for My First Agent Agent."""

    config_value: Annotated[str, Field(
        default="Default Config Value",
        description="Some configuration value for the agent"
    )]
```

Wir können auf diese Konfiguration in jedem Schritt zugreifen, wenn wir es benötigen. Zum Beispiel können wir den Inhalt
des Feldes `config_value` im zweiten Schritt unseres Agenten lesen und seinen String-Wert ebenfalls als Chunk posten.
Normalerweise verwenden Sie die Konfiguration jedoch, um eine Logik in Ihren Schritten zu konfigurieren, entweder mit
System-Prompts oder Konfigurationen für bestimmte Methoden.

```python
import logging
import asyncio

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.core.events.agent.user import UserMessageEvent
from swiss_ai_hub.core.events.agent.control import StopEvent
from swiss_ai_hub.agent.workflow.decorators.step import step
from swiss_ai_hub.core.displayers.event_displayer import EventDisplayer

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

Sie können die Konfigurationswerte in Ihrer `trigger.py` oder beim Erstellen des Agenten in der `main.py` festlegen.

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

## Ihren Agenten ausführen und debuggen

1. **Testskript ausführen**:

Um Ihren Agenten schnell zu testen, können Sie ein `trigger.py`-Skript schreiben, das den Agenten startet und dessen
StartEvent postet. Auf diese Weise können Sie den Agenten ohne UI testen.

::: code-group

```python [trigger.py]
import asyncio
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.events.agent.user import UserMessageEvent
from swiss_ai_hub.core.testing.auth_utils import fake_user
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner
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
[Step 1] Processing message: 'Hello world this is my first agent' -> 'HELLO WORLD THIS IS MY FIRST AGENT'
[Step 2] Creating response: 'Processed: HELLO WORLD THIS IS MY FIRST AGENT (Words: 7)'
Agent completed: True
```

2. **Debuggen mit Langfuse Tracing** – Öffnen Sie `http://localhost:6006`, um Folgendes zu sehen:

   - Schrittweiser Ausführungsfluss
   - Event-Datenfluss zwischen den Schritten
   - Zeit- und Leistungsmetriken
   - Details der Event-Payload

3. **Protokolle überprüfen** – Der Aufruf `enable_logging()` zeigt den Event-Fluss in Echtzeit und hilft bei der
   Fehlersuche.

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

- **Ereignisgesteuerte Workflows**: Schritte verarbeiten Events und erzeugen neue Events
- **Benutzerdefinierte Events**: Erstellen von typisierten Datenobjekten zur Übergabe zwischen Schritten
- **Konfiguration**: Verwendung von typisierten Einstellungen zur Steuerung des Agentenverhaltens
- **Testen**: `AgentTestRunner` für isolierte Tests verwenden
- **Debugging**: Langfuse Tracing und Logging für die Beobachtbarkeit

## Nächste Schritte

- [Ihre erste Pipeline](../4_your_first_pipeline/) -
- [Agenten erstellen](../../2_building_agents/) - Erfahren Sie mehr über fortgeschrittene Agent-Muster
