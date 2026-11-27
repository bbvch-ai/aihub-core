from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.display.display_event import DisplayEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class DelegatedProgressEvent(DisplayEvent):
    """
    A step a delegated agent started, shown in the delegating run.

    A delegation a model chose as a tool runs on a thread and display of its own, so its answer reaches the model
    and not the user. This is what the user sees of it instead: each step as it starts, under the tool call.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.delegated_progress_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.delegated_progress_event.description"
    )

    request_event_id: Annotated[str, Field(description="`event_id` of the delegating `AgentInTheLoopRequestEvent`.")]
    tool_call_id: Annotated[str | None, Field(description="The tool call the delegation answers, if any.")] = None
    agent_class: Annotated[str, Field(description="The delegated agent's class.")]
    agent_id: Annotated[str, Field(description="The delegated agent's profile.")]
    step: Annotated[str, Field(description="The step that started, in the run's locale.")]
