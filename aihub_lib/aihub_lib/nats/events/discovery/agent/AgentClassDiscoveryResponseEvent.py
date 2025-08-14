from typing import Annotated

from pydantic import Field

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.agents.visualizers.types.WorkflowGraph import WorkflowGraph
from aihub_lib.nats.events import BaseEvent
from aihub_lib.nats.events.discovery.agent.AgentConfigSpecs import AgentConfigSpecs
from aihub_lib.nats.events.discovery.EventSpecs import EventSpecs


class AgentClassDiscoveryResponseEvent(BaseEvent):
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
    is_conversational: Annotated[
        bool, Field(description="Whether the agent can participate in a chat-based conversation")
    ]
    agent_config_specs: Annotated[
        AgentConfigSpecs,
        Field(
            description="A specification of the agent's configuration, including its name and schema. "
            "This helps consumers understand how to configure the agent.",
        ),
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
    hitl_request_events: Annotated[
        list[EventSpecs],
        Field(
            description="A list of `EventSpecs` objects, each describing a human-in-the-loop request event type and schema. "
            "These events allow the agent to request human intervention during its workflow."
        ),
    ]
    hitl_response_events: Annotated[
        list[EventSpecs],
        Field(
            description="A list of `EventSpecs` objects, each describing a human-in-the-loop response event type and schema. "
            "These events allow humans to respond to agent HITL requests."
        ),
    ]
    network_graph: Annotated[
        WorkflowGraph,
        Field(
            description="A network graph of the agent, showing how different components are connected and interact.",
        ),
    ]
    default_agent_config: Annotated[
        AgentConfig,
        Field(
            description="The default agent configuration for this agent class. "
            "This is the configuration that will be used if no specific configuration is provided.",
        ),
    ]
