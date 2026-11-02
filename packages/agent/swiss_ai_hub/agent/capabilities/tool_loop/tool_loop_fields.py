from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.form.form import Form

from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop_config import ToolLoopConfig


class ToolLoopFields(Form):
    """The tool-loop settings a blueprint's config gains by listing this mixin as a base.

    `ToolLoop` annotates its steps with this class. The defaults bound every loop, so profiles stored before the
    mixin existed keep validating. Its form needs no spreading in `as_form()`: the runner publishes it with the
    blueprint's own tools as options (`ToolLoop.published_config`).
    """

    tool_loop: Annotated[
        ToolLoopConfig,
        Field(description="How far the model may go deciding on tools, and which calls need approval.", title="Tools"),
    ] = ToolLoopConfig()
