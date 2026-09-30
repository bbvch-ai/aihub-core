from typing import TYPE_CHECKING, Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.events.agent import ChatFeature, ToolDefinition

from swiss_ai_hub.agent.capabilities.tool_loop.function_tool import FunctionTool
from swiss_ai_hub.agent.capabilities.tool_loop.tool_approval_policy import ToolApprovalPolicy

if TYPE_CHECKING:
    from swiss_ai_hub.agent.capabilities.capability import Capability


class DeclaredTool(BaseModel):
    """One tool a blueprint's loop may offer: a function tool, or a capability that offers itself as a tool."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    function: Annotated[FunctionTool | None, Field(description="The tool, when it is a function.")] = None
    capability: Annotated[Any, Field(description="The capability class, when it is a capability tool.")] = None

    @classmethod
    def of(cls, tool: "FunctionTool | type[Capability]") -> "DeclaredTool":
        if isinstance(tool, FunctionTool):
            return cls(function=tool)
        if not getattr(tool, "tool_name", None):
            msg = f"{tool.__name__} offers no tool: set `tool_name` and override `tool_definition` to declare it."
            raise ValueError(msg)
        return cls(capability=tool)

    @property
    def name(self) -> str:
        return self.function.name if self.function else self.capability.tool_name

    @property
    def kind(self) -> Literal["function", "capability"]:
        return "function" if self.function else "capability"

    @property
    def chat_feature(self) -> ChatFeature | None:
        return self.function.chat_feature if self.function else self.capability.chat_feature

    @property
    def default_approval(self) -> ToolApprovalPolicy:
        return self.function.default_approval if self.function else self.capability.tool_default_approval

    @property
    def approve_every_call(self) -> bool:
        return self.function.approve_every_call if self.function else self.capability.tool_approve_every_call

    def definition(self, config: AgentConfig, locale: str) -> ToolDefinition | None:
        return self.function.definition() if self.function else self.capability.tool_definition(config, locale)
