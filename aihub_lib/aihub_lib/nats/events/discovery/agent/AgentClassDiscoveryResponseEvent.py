from typing import Annotated, Any

from pydantic import BaseModel, Field

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.agents.visualizers.types.WorkflowGraph import WorkflowGraph
from aihub_lib.nats.events import BaseEvent


class EventSpecs(BaseModel):
    """
    Defines a specification for a start event that an agent can handle.
    """

    event_name: Annotated[
        str,
        Field(
            description="The name of event (e.g., a particular ControlEvent subclass name) "
            "that the agent can consume as a start event.",
        ),
    ]
    event_schema: Annotated[
        dict[str, Any],
        Field(
            description="A dictionary describing the schema of this start event, providing details about "
            "expected fields and their types. This helps external consumers understand how to "
            "construct and validate events for initiating the agent's workflow.",
        ),
    ]
    event_parents: Annotated[
        list[str],
        Field(
            description="A list of parent event names that this event is derived from, "
            "allowing for hierarchical event structures."
        ),
    ]

    @classmethod
    def from_event_class(cls, event_class: type[BaseEvent]):
        return cls(
            event_name=event_class.event_name_from_class(),
            event_schema=event_class.model_json_schema(),
            event_parents=event_class.parent_event_names_from_class(),
        )


class AgentConfigSpecs(BaseModel):
    """
    Defines a specification for an agent's configuration.
    """

    agent_config_name: Annotated[
        str,
        Field(description="The name of the agent configuration (e.g., 'LLMWrappingAgentConfig'). "),
    ]
    agent_config_schema: Annotated[
        dict[str, Any],
        Field(
            description="A dictionary describing the schema of the agent configuration, providing details about "
            "expected fields and their types. This helps external consumers understand how to "
            "construct and validate agent configurations.",
        ),
    ]

    @classmethod
    def from_agent_config_class(cls, agent_config_class: type[AgentConfig]):
        return cls(
            agent_config_name=agent_config_class.config_name_from_class(),
            agent_config_schema=agent_config_class.model_json_schema(),
        )


class AgentClassDiscoveryResponseEvent(BaseEvent):
    """
    A response event sent after an agent discovery request, detailing an agent's class, ID, configuration,
    and the set of start events it can handle.

    ### Why AgentDiscoveryResponseEvent?
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
    network_graph: Annotated[
        WorkflowGraph,
        Field(
            description="A network graph of the agent, showing how different components are connected and interact.",
        ),
    ]
