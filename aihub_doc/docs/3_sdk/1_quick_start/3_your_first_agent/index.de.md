````markdown
---
title: Ihr erster Agent
source_sha: "c4ef32629b42f7923c79360698b4b3efec8bbf569de98298c3f80fe9c8d28254"
---

# Ihr erster Agent

Erstellen Sie Ihren ersten Agent mit dem AI-Hub Agent (`aihub_agent`) SDK – einen einfachen Nachrichtenverarbeitungs-Agent mit einem zweistufigen Workflow.

## Was Sie lernen werden

Dieser Quickstart behandelt die wesentlichen Bausteine:

- **Agent-Struktur**: Wie Agents Nachrichten in Schritten verarbeiten
- **Event-Fluss**: Datenfluss zwischen Workflow-Schritten
- **Konfiguration**: Einstellungen, die das Verhalten des Agents steuern
- **Testen**: Ihren Agent lokal ausführen

## Voraussetzungen

Sie benötigen die laufende AI-Hub-Entwicklungsumgebung. Bevor Sie beginnen, stellen Sie sicher, dass Sie die Schritte zur [Einrichtung der Entwicklungsumgebung](../1_dev_environment_setup/) abgeschlossen haben.

## Wie Agents funktionieren

AI-Hub Agents sind **ereignisgesteuerte Workflows** mit drei wesentlichen Bestandteilen:

- **Schritte**: Funktionen, die mit `@step()` dekoriert sind und Events verarbeiten
- **Events**: Datenobjekte, die zwischen Schritten fließen
- **Konfiguration**: Typisierte Einstellungen, die das Verhalten des Agents steuern

## Einige grundlegende Konzepte für den Start!

Betrachten wir den Standard-Agent, der bei der Einrichtung der Entwicklungsumgebung erstellt wurde:

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
````

Wenn Sie die Benutzeroberfläche starten und versuchen, den Agent in der OpenWebUI zu verwenden, stellen Sie fest, dass
der Agent nicht antwortet.

![image](../../../../media/sdk/your_first_agent/pre_chunk_event.png)

### Chunk Events nutzen, um Live-Chat-Antworten anzuzeigen

Der Grund, warum Sie keine Antwort in der Chat-Oberfläche sehen, ist, dass nur spezielle Events (`DisplayEvents`) in der
UI angezeigt werden. Und für Chat-Oberflächen wird die Antwort insbesondere aus `ChunkEvent`s zusammengesetzt. Lassen
Sie uns also unseren Schritt so konfigurieren, dass er ein solches `ChunkEvent` anzeigt. Dazu müssen wir den
`EventDisplayer` in der Schritt-Funktion verwenden und die Methode `display_chunk` erwarten, wobei das erste Argument
der anzuzeigende Inhalt ist und als zweites Argument die Quelle dieses Chunks übergeben werden kann. Normalerweise ist
dies der Modellname oder das Sprachmodell, das diesen Chunk erzeugt. Da wir in unserem Fall den Chunk vorerst fest
codieren, verwenden wir einfach den ClassName des Agents als Quelle.

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

### Die Leistung des Streamings erleben

Wie Sie vielleicht von anderen KI-Tools wissen, erzeugen große Sprachmodelle ihre Antworten Stück für Stück (chunk by
chunk). Anstatt die Antwort am Ende als Ganzes anzuzeigen, können wir die endgültige Antwort schrittweise aufbauen, was
uns ermöglicht, dem Benutzer so schnell wie möglich Teile der Antwort zu präsentieren. Lassen Sie es uns demonstrieren:

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

Wir haben gerade einen zweiten Chunk hinzugefügt, der angezeigt wird. Wenn Sie den Agent nun erneut ausführen, sehen
Sie, dass er zuerst mit „Hello World!“ antworten und nach 2 Sekunden mit „You said: Hello!“ fortfahren wird.
<video controls="controls" src="../../../../media/sdk/your_first_agent/show_chunk_delay.mp4" type="video/mp4" />

### Denkschritte hinzufügen

Besonders wenn der Agent länger braucht, um sein Ergebnis zu finalisieren, ist es eine gute Praxis, den Benutzer darüber
zu informieren, was im Agent vor sich geht. Dazu können Sie `ThoughtEvent`s anzeigen lassen. Auch hier verwenden wir den
`EventDisplayer`, diesmal jedoch mit der Methode `display_thought`.

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

Nun sehen Sie, dass es einen zusätzlichen Abschnitt in der Antwort gibt, der „Thinking...“ genannt wird. Wenn Sie ihn
erweitern, können Sie unseren Gedankengang sehen, der mit dem Inhalt „Drinking coffee...“ erstellt wurde.
![image](../../../../media/sdk/your_first_agent/show_thought.png)

## Erstellen Sie Ihren ersten Multistep-Agent

### 1. Erstellen Sie ein benutzerdefiniertes Event (`events/MyCustomAgentEvent.py`):

Erstellen Sie zunächst ein Event, um Daten zwischen den Schritten zu übergeben:

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

Sie haben nun einen ersten Agent, der in zwei Schritten agiert. Im ersten Schritt tun wir alles, was wir bisher getan
haben, zählen aber auch die Anzahl der Wörter in der Benutzernachricht. Diese Information wird dann an einen zweiten
Schritt weitergeleitet, wo wir der Antwort auch „The word count is X words“ hinzufügen, wobei X die Anzahl der Wörter
ist, die wir im ersten Schritt gezählt haben. Wir haben die beiden Schritte verbunden, indem wir unser neues Event
`MyCustomAgentEvent` als Ausgabe des ersten Schritts und als Eingabe für den zweiten Schritt definiert haben.

Wenn Sie zur Agent-Übersicht navigieren, dort Ihren Agent auswählen und dann zu „Workflow“ gehen, können Sie den
Workflow und die Schritte Ihres Agents sehen. Sie können sehen, welche Schritte definiert sind und welche Eingabe- und
Ausgabe-Events diese Schritte haben.

![image](../../../../media/sdk/your_first_agent/simple_workflow.png)

### 3. Agent-Konfiguration hinzufügen (`MyCustomAgentConfig.py`):

Oft möchten Sie Ihren Agent beim Start konfigurierbar machen. Dafür können Sie die Konfigurationsklasse verwenden. Wenn
Sie Ihren Agent über die CLI einrichten, wurde bereits eine grundlegende Konfigurationsdatei für Sie erstellt, die wie
folgt aussieht:

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

Wir können auf diese Konfiguration in jedem Schritt zugreifen, wenn wir dies benötigen. Zum Beispiel können wir den
Inhalt des Feldes `config_value` im zweiten Schritt unseres Agents lesen und dessen Zeichenkettenwert ebenfalls als
Chunk posten. Normalerweise verwenden Sie die Konfiguration jedoch, um eine Logik in Ihren Schritten zu konfigurieren,
entweder mit System-Prompts oder Konfigurationen für bestimmte Methoden.

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

Sie können die Konfigurationswerte in Ihrer `trigger.py` oder beim Bau des Agents in der `main.py` setzen.

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

## Agent ausführen und debuggen

1. **Testskript ausführen**:

Um Ihren Agent schnell zu testen, können Sie ein `trigger.py`-Skript schreiben, das den Agent startet und dessen
`StartEvent` postet. Auf diese Weise können Sie den Agent ohne Benutzeroberfläche testen.

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
[Step 1] Processing message: 'Hello world this is my first agent' -> 'HELLO WORLD THIS IS MY FIRST AGENT'
[Step 2] Creating response: 'Processed: HELLO WORLD THIS IS MY FIRST AGENT (Words: 7)'
Agent completed: True
```

2. **Debuggen mit Langfuse Tracing** – Öffnen Sie `http://localhost:6006`, um Folgendes zu sehen:

   - Schritt-für-Schritt-Ausführungsfluss
   - Event-Datenfluss zwischen den Schritten
   - Timing- und Performance-Metriken
   - Details der Event-Nutzlast

3. **Logs prüfen** – Der Aufruf `enable_logging()` zeigt den Echtzeit-Event-Fluss und hilft bei der Fehlersuche.

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
- **Konfiguration**: Verwenden von typisierten Einstellungen zur Steuerung des Agent-Verhaltens
- **Testen**: Verwenden Sie den `AgentTestRunner` für isoliertes Testen
- **Debugging**: Langfuse Tracing und Logging für Observability

## Nächste Schritte

- [Ihre erste Pipeline](../4_your_first_pipeline/)
- [Agents erstellen](../../2_building_agents/)

```
```
