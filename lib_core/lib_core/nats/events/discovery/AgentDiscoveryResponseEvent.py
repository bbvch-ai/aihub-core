from typing import List, Dict, Any

from pydantic import BaseModel

from lib_core.generative_ai.agent.AgentConfig import AgentConfig
from lib_core.nats.events import BaseEvent


class StartEventSpecs(BaseModel):
    event_type: str
    event_schema: Dict[str, Any]

class AgentDiscoveryResponseEvent(BaseEvent):
    agent_class: str
    agent_id: str
    agent_config: AgentConfig

    start_events: List[StartEventSpecs]