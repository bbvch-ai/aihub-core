# Developing New Agents - Guide

## Create a new agent
In the `aihub_agent/aihub_agent/agents` folder create a new python file with the name of the Agent e.g. RAGAgent.
Inherit from the `Agent` class.
```python
from aihub_agent.agents.abstract.Agent import Agent

class RAGAgent(Agent):
    pass
```

## Create a start and stop method
Your agent class has at least a step which expects a `StartEvent` and a step which outputs a `StopEvent`. Each steps needs the step decorator.

```python
from aihub_agent.agents.abstract.Agent import Agent
from aihub_lib.nats.events.control.start import StartEvent
from aihub_lib.nats.events.control.stop import StopEvent
from aihub_agent.workflow.decorators.step import step

class RAGAgent(Agent):
    @step()
    def start(self, event: StartEvent):
        pass

    @step()
    def stop(self) -> StopEvent:
        pass
```

## Create an Agent Config
To configure the agents an agent needs a corresponding config. in the simplest case just inherit from the `AgentConfig` class.
````python
from aihub_lib.generative_ai.agent.AgentConfig import AgentConfig

class RAGAgentConfig(AgentConfig):
    pass
````

## Map out the workflow of the agent
The agent is composed of multiple steps. Each step is a method in the agent class which expects a specific event and outputs a specific event.
Think about the steps your agent needs to take to achieve its goal. Start from the `start` method and work your way through the steps.

## Implement the steps
Implement the steps of the agent. Each step should be a method in the agent class which expects a specific event and outputs a specific event.




