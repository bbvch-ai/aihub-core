from typing import Annotated, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class AgentSettings(BaseSettings):
    AGENT_REPO_IMAGE_URL: Annotated[Optional[str], Field(description="URL where the image for the agent is stored")] = (
        None
    )
    AGENT_IMAGE_TAG: Annotated[Optional[str], Field(description="image tag for the agent")] = None
    AGENT_PHOENIX_API_TOKEN: Annotated[Optional[str], Field(description="API Token for Phoenix")] = None
