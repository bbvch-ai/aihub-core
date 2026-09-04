from typing import Annotated, ClassVar

from pydantic import Field, PrivateAttr

from swiss_ai_hub.core.events.agent.aitl.exception.agent_in_the_loop_exception_event import (
    AgentInTheLoopExceptionEvent,
)
from swiss_ai_hub.core.events.agent.aitl.response.agent_in_the_loop_response_event import (
    AgentInTheLoopResponseEvent,
)
from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent
from swiss_ai_hub.core.events.agent.control.start.start_event import StartEvent
from swiss_ai_hub.core.events.agent.display.display_event import DisplayEvent
from swiss_ai_hub.core.events.agent.user.user_message_event import UserMessageEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.topics.agents.agent_instance_topic import AgentInstanceTopic
from swiss_ai_hub.core.topics.agents.partial_agent_topic import PartialAgentTopic


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
            "Warning: In almost all cases, you will not want to share the run! The response subscription is scoped "
            "to the delegated run id, so sharing it makes every subscriber of a fan-out fire on every delegate.",
        ),
    ] = False
    timeout_seconds: Annotated[
        float | None,
        Field(
            description="How long to wait for the delegated agent before synthesizing a failure. `None` (the "
            "default) waits forever, which is what a delegate that never starts — an offline agent, a mistyped "
            "agent_id — costs the caller: no stop event is ever published, so the caller's run never resumes. Set "
            "it when the caller cannot tolerate that, and note it only covers a delegate that does not answer: the "
            "timer lives in the caller's dispatcher process, so it dies with the response subscription it guards.",
        ),
    ] = None

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
