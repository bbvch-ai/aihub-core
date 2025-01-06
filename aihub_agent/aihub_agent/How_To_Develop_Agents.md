# Developing New Agents - Guide

## Create a new agent
In the `aihub_agent/aihub_agent/agents` folder (or if working on customer-specific agents do it under `agents` in the customer repo) create a new python file with the name of the Agent e.g. RAGAgent.
Inherit from the `Agent` class - for more information please read the documentation in the Agent class.
```python
from aihub_agent.agents.abstract.Agent import Agent


class RAGAgent(Agent):
    pass
```

## Create an Agent Config
To configure the agents an agent needs a corresponding config. in the simplest case just inherit from the `AgentConfig` class.
For more information please read the documentation in the `AgentConfig` class.
````python
from aihub_lib.generative_ai.agent.AgentConfig import AgentConfig


class RAGAgentConfig(AgentConfig):
    pass
````

## Create a start and stop method
Your agent class has at least a step which expects a `StartEvent` and a step which outputs a `StopEvent`. Each steps needs the step decorator.
For more information read the documentation in the `step` function and the `StartEvent` and `StopEvent` classes.
```python
from aihub_agent.agents.abstract.Agent import Agent
from aihub_lib.nats.events.control.start import StartEvent
from aihub_lib.nats.events.control.stop import StopEvent
from aihub_agent.workflow.decorators.step import step
from aihub_lib.nats.events import ControlEvent


class SomeEvent(ControlEvent):
    """ This is just an example event - events should be moved to a separate file """
    pass


class RAGAgent(Agent):
    @step()
    async def start(self, event: StartEvent) -> SomeEvent:
        """ When StartEvent is received this step is executed and returns a 'SomeEvent' event """
        return SomeEvent()

    @step()
    async def stop(self, event: SomeEvent) -> StopEvent:
        """ When SomeEvent is received this step is executed and returns a 'StopEvent' """
        return StopEvent()
```

## Map out the workflow of the agent
The agent is composed of multiple steps. Each step is a method in the agent class which expects one (or more) specific event(s) and outputs one (or more) specific event(s).
Think about the steps your agent needs to take to achieve its goal. Start from the `start` method and work your way through the steps.





