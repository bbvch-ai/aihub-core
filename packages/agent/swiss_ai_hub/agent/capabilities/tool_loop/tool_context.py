from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.auth import AccessChecker, UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import KnowledgeReference, UserUploadedFile
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.topics import AgentInstanceTopic


class ToolContext(BaseModel):
    """What a tool may use: the run's config, user and display channel, and what the user sent with the message."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    agent_config: Annotated[AgentConfig, Field(description="The run's config, for values a tool binds from it.")]
    displayer: Annotated[EventDisplayer, Field(description="Shows what the tool does as it runs.")]
    t: Annotated[LocaleHandler, Field(description="The run's locale.")]
    user: Annotated[UserIdentity | None, Field(description="The asking user; none on a run without one.")] = None
    access: Annotated[AccessChecker | None, Field(description="The asking user's access rules.")] = None
    files: Annotated[list[UserUploadedFile], Field(description="The files attached to the message.")] = []
    knowledge_references: Annotated[
        list[KnowledgeReference], Field(description="The collections the user referenced on the message.")
    ] = []
    topic: Annotated[
        AgentInstanceTopic | None,
        Field(description="The run's agent and thread, for tools that keep per-thread state."),
    ] = None
