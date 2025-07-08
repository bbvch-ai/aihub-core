from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings


class AgentSettings(BaseSettings):
    AGENT_REPO_IMAGE_URL: Annotated[str | None, Field(description="URL where the image for the agent is stored")] = None
    AGENT_IMAGE_TAG: Annotated[str | None, Field(description="image tag for the agent")] = None
    AGENT_PHOENIX_API_TOKEN: Annotated[str | None, Field(description="API Token for Phoenix")] = None
