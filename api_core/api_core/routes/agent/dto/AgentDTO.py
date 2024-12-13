from typing import List

from pydantic import BaseModel

from lib_core.generative_ai.agent.AgentConfig import AgentConfig
from lib_core.nats.events.discovery.AgentDiscoveryResponseEvent import StartEventSpecs


class AgentDTO(BaseModel):
    agent_class: str
    agent_id: str
    agent_config: AgentConfig

    start_events: List[StartEventSpecs]