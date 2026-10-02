from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.auth import AccessChecker, UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.i18n import LocaleHandler


class ToolContext(BaseModel):
    """What a function tool may use while it runs: the run's config and user, and the run's display channel."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    agent_config: Annotated[AgentConfig, Field(description="The run's config, for values a tool binds from it.")]
    displayer: Annotated[EventDisplayer, Field(description="Shows what the tool does as it runs.")]
    t: Annotated[LocaleHandler, Field(description="The run's locale.")]
    user: Annotated[UserIdentity | None, Field(description="The asking user; none on a run without one.")] = None
    access: Annotated[AccessChecker | None, Field(description="The asking user's access rules.")] = None
