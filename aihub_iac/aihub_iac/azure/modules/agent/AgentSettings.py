from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class AgentSettings(BaseSettings):
    AGENT_REPO_IMAGE_URL: Optional[str] = Field(default=None, description="URL where the image for the agent is stored")
    AGENT_IMAGE_TAG: Optional[str] = Field(default=None, description="image tag for the agent")
    AGENT_PHOENIX_API_TOKEN: Optional[str] = Field(default=None, description="API Token for Phoenix")
