from typing import Annotated, ClassVar

from pydantic import Field, PrivateAttr

from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.nats.events.agent_in_the_loop.exception.AgentInTheLoopExceptionEvent import (
    AgentInTheLoopExceptionEvent,
)
from swiss_ai_hub.core.nats.events.agent_in_the_loop.response.AgentInTheLoopResponseEvent import (
    AgentInTheLoopResponseEvent,
)
from swiss_ai_hub.core.nats.events.control.ControlEvent import ControlEvent
from swiss_ai_hub.core.nats.events.control.start.StartEvent import StartEvent
from swiss_ai_hub.core.nats.events.display.DisplayEvent import DisplayEvent
from swiss_ai_hub.core.nats.events.user.UserMessageEvent import UserMessageEvent
from swiss_ai_hub.core.nats.topics.agents.AgentInstanceTopic import AgentInstanceTopic
from swiss_ai_hub.core.nats.topics.agents.PartialAgentTopic import PartialAgentTopic


class AgentInTheLoopRequestEvent(DisplayEvent, ControlEvent):
    """
    An event delegating a task to another agent at a specific point in a workflow.

    ### Why AgentInTheLoopRequestEvent?
    In automated workflows, certain tasks may require specialized capabilities from other agents. This event:
    - Is a `DisplayEvent`, so the delegation can be monitored in user interfaces
    - Carries a start event that initiates the other agent's task
    - Manages context sharing between agents (thread, display, run IDs)
    - Handles both successful responses and exceptions from the delegated agent
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.aitl_request_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.aitl_request_event.description"
    )

    _response: type[AgentInTheLoopResponseEvent] | None = PrivateAttr(None)
    _exception: type[AgentInTheLoopExceptionEvent] | None = PrivateAttr(None)

    start_event: Annotated[
        StartEvent | UserMessageEvent,
        Field(description="The event that will be sent to the other agent to initiate its task."),
    ]
    other_agent_topic: Annotated[
        PartialAgentTopic | AgentInstanceTopic,
        Field(
            description="A partial or full agent topic specifying the target agent and event routing, "
            "ensuring the task is delegated to the correct agent.",
        ),
    ]
    share_thread_id: Annotated[
        bool, Field(description="Whether to share the conversation thread context with the other agent.")
    ] = True
    share_display_id: Annotated[
        bool, Field(description="Whether to share the display context with the other agent for UI consistency.")
    ] = True
    share_run_id: Annotated[
        bool,
        Field(
            description="Whether to share the run context with the other agent. "
            "Warning: In almost all cases, you will not want to share the run!",
        ),
    ] = False

    def __init__(
        self,
        response: type[AgentInTheLoopResponseEvent] | None = None,
        exception: type[AgentInTheLoopExceptionEvent] | None = None,
        **data,
    ):
        super().__init__(**data)
        self._response = response
        self._exception = exception

    @property
    def response(self) -> type[AgentInTheLoopResponseEvent] | None:
        return self._response

    @property
    def exception(self) -> type[AgentInTheLoopExceptionEvent] | None:
        return self._exception
