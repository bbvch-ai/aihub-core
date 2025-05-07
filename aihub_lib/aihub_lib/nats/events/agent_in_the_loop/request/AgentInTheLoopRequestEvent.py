from typing import ClassVar, Optional, Type, Union

from pydantic import Field, PrivateAttr

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.agent_in_the_loop.exception.AgentInTheLoopExceptionEvent import AgentInTheLoopExceptionEvent
from aihub_lib.nats.events.agent_in_the_loop.response.AgentInTheLoopResponseEvent import AgentInTheLoopResponseEvent
from aihub_lib.nats.events.control.ControlEvent import ControlEvent
from aihub_lib.nats.events.control.start.StartEvent import StartEvent
from aihub_lib.nats.events.display.DisplayEvent import DisplayEvent
from aihub_lib.nats.events.user.UserMessageEvent import UserMessageEvent
from aihub_lib.nats.topics.agents.AgentTopic import AgentTopic
from aihub_lib.nats.topics.agents.PartialAgentTopic import PartialAgentTopic


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

    _response: Optional[Type[AgentInTheLoopResponseEvent]] = PrivateAttr(None)
    _exception: Optional[Type[AgentInTheLoopExceptionEvent]] = PrivateAttr(None)

    start_event: StartEvent | UserMessageEvent = Field(
        ..., description="The event that will be sent to the other agent to initiate its task."
    )
    other_agent_topic: Union[PartialAgentTopic, AgentTopic] = Field(
        ...,
        description="A partial or full agent topic specifying the target agent and event routing, ensuring the task is delegated to the correct agent.",
    )
    share_thread_id: bool = Field(
        True, description="Whether to share the conversation thread context with the other agent."
    )
    share_display_id: bool = Field(
        True, description="Whether to share the display context with the other agent for UI consistency."
    )
    share_run_id: bool = Field(
        False,
        description="Whether to share the run context with the other agent. Warning: In almost all cases, you will not want to share the run!",
    )

    def __init__(
        self,
        response: Optional[Type[AgentInTheLoopResponseEvent]] = None,
        exception: Optional[Type[AgentInTheLoopExceptionEvent]] = None,
        **data,
    ):
        super().__init__(**data)
        self._response = response
        self._exception = exception

    @property
    def response(self) -> Optional[Type[AgentInTheLoopResponseEvent]]:
        return self._response

    @property
    def exception(self) -> Optional[Type[AgentInTheLoopExceptionEvent]]:
        return self._exception
