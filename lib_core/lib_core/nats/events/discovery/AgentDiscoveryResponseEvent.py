from typing import List, Dict, Any

from pydantic import BaseModel, Field

from lib_core.generative_ai.agent.AgentConfig import AgentConfig
from lib_core.nats.events import BaseEvent


class StartEventSpecs(BaseModel):
    """
    Defines a specification for a start event that an agent can handle.
    """
    event_type: str = Field(..., description="The type of event (e.g., a particular ControlEvent subclass name) that the agent can consume as a start event.")
    event_schema: Dict[str, Any] = Field(..., description="A dictionary describing the schema of this start event, providing details about expected fields and their types. This helps external consumers understand how to construct and validate events for initiating the agent's workflow.")


class AgentDiscoveryResponseEvent(BaseEvent):
    """
    A response event sent after an agent discovery request, detailing an agent's class, ID, configuration,
    and the set of start events it can handle.

    ### Why AgentDiscoveryResponseEvent?
    After a discovery request, consumers need to know:
    - Which agent instance is available (identified by `agent_class` and `agent_id`).
    - What configuration that agent operates under (e.g., model parameters, runtime settings).
    - Which start events the agent can process to begin its workflow.

    By providing this structured information, the discovery response helps orchestrators and clients
    dynamically integrate with newly discovered agents without manual configuration or guesswork.

    """

    agent_class: str = Field(..., description="The class or category of the agent (e.g., a specific type of AI assistant).")
    agent_id: str = Field(..., description="A unique identifier for the agent instance.")
    agent_config: AgentConfig = Field(..., description="The agent's configuration object, containing details like the model used, temperature settings, or other domain-specific parameters.")
    start_events: List[StartEventSpecs] = Field(..., description="A list of `StartEventSpecs` objects, each describing a start event type and schema. This lets consumers understand exactly how to initiate the agent's workflow.")
