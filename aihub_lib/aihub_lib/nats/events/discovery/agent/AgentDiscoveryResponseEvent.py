from typing import Annotated

from pydantic import Field

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.agents.visualizers.types.WorkflowGraph import WorkflowGraph
from aihub_lib.nats.events import BaseEvent
from aihub_lib.nats.events.discovery.EventSpecs import EventSpecs


class AgentDiscoveryResponseEvent(BaseEvent):
    """
    A response event sent after an agent discovery request, detailing an agent's class, ID, configuration,
    and the set of start events it can handle.

    After a discovery request, consumers need to know:
    - Which agent instance is available (identified by `agent_class` and `agent_id`).
    - What configuration that agent operates under (e.g., model parameters, runtime settings).
    - Which start events the agent can process to begin its workflow.
    - Which stop events the agent might respond with.

    By providing this structured information, the discovery response helps orchestrators and clients
    dynamically integrate with newly discovered agents without manual configuration or guesswork.
    """

    agent_class: Annotated[
        str, Field(description="The class or category of the agent (e.g., a specific type of AI assistant).")
    ]
    agent_id: Annotated[str, Field(description="A unique identifier for the agent instance.")]
    agent_config: Annotated[
        AgentConfig,
        Field(
            description="The agent's configuration object, containing details like the model used, "
            "temperature settings, or other domain-specific parameters.",
        ),
    ]
    is_conversational: Annotated[
        bool, Field(description="Whether the agent can participate in a chat-based conversation")
    ]
    start_events: Annotated[
        list[EventSpecs],
        Field(
            description="A list of `EventSpecs` objects, each describing a start event type and schema. "
            "This lets consumers understand exactly how to initiate the agent's workflow.",
        ),
    ]
    stop_events: Annotated[
        list[EventSpecs],
        Field(
            description="A list of `EventSpecs` objects, each describing a stop event type and schema. "
            "This lets consumers understand exactly how to initiate the agent's workflow.",
        ),
    ]
    network_graph: Annotated[
        WorkflowGraph,
        Field(
            description="A network graph of the agent, showing how different components are connected and interact.",
        ),
    ]
