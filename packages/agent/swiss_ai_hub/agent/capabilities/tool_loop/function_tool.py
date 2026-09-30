from collections.abc import Awaitable, Callable
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field
from swiss_ai_hub.core.events.agent import ChatFeature, ToolDefinition

from swiss_ai_hub.agent.capabilities.tool_loop.tool_approval_policy import ToolApprovalPolicy
from swiss_ai_hub.agent.capabilities.tool_loop.tool_context import ToolContext


class FunctionTool(BaseModel):
    """A tool that is just an async function: no sub-workflow of its own, run inside the loop.

    For small tools. A tool whose work deserves its own events and steps (retrieval, web search, code execution) is
    a capability instead, so a model-chosen call looks exactly like an explicit one.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: Annotated[str, Field(description="The name the model calls the tool by.", pattern=r"^[a-zA-Z0-9_-]{1,64}$")]
    description: Annotated[str, Field(description="What the tool does and when to use it, for the model.")]
    arguments: Annotated[type[BaseModel], Field(description="The tool's arguments; their JSON schema is offered.")]
    run: Annotated[
        Callable[[BaseModel, ToolContext], Awaitable[str]],
        Field(description="Runs the call with validated arguments and returns what the model reads."),
    ]
    chat_feature: Annotated[
        ChatFeature | None, Field(description="The chat toggle the tool needs switched on, if any.")
    ] = None
    default_approval: Annotated[
        ToolApprovalPolicy, Field(description="When calls need approval unless the profile says otherwise.")
    ] = ToolApprovalPolicy.NEVER
    approve_every_call: Annotated[
        bool, Field(description="Whether an approval never carries over to the tool's next call.")
    ] = False

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name, description=self.description, parameters=self.arguments.model_json_schema()
        )
