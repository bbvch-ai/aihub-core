from typing import Annotated, Any

from pydantic import Field
from swiss_ai_hub.core.form.form import Form

from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop_config import ToolLoopConfig


class ToolLoopFields(Form):
    """The tool-loop settings a blueprint's config gains by listing this mixin as a base.

    `ToolLoop` annotates its steps with this class. The defaults bound every loop, so profiles stored before the
    mixin existed keep validating.
    """

    tool_loop: Annotated[
        ToolLoopConfig,
        Field(description="How far the model may go deciding on tools, and which calls need approval.", title="Tools"),
    ] = ToolLoopConfig()

    @classmethod
    def tool_loop_form_elements(cls, tool_names: list[str]) -> dict[str, Any]:
        """The form elements for this class's own fields, for a subclass's `as_form()` to spread; `tool_names` are
        the tools the blueprint declares, e.g. `ToolLoop.names(MyAgent.tools)`."""
        return {"tool_loop": ToolLoopConfig.as_form(tool_names)}
