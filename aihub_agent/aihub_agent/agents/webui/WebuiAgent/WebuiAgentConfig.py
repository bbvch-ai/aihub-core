from pydantic import BaseModel

from aihub_lib.agents.AgentConfig import AgentConfig

class WebuiFeatures(BaseModel):
    web_search: bool = False

class WebuiAgentConfig(AgentConfig):
    webui_base_url: str
    webui_bearer_token: str
    assistant_name: str
    features: WebuiFeatures