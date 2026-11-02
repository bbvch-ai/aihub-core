from collections import defaultdict
from collections.abc import Callable
from typing import Annotated, Any, ClassVar, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.events.agent import ChatFeature
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.capabilities.tool_loop.tool_approval_policy import ToolApprovalPolicy


class ToolOptions(BaseModel):
    """How a tool presents itself to users and when its calls need approval; the model sees only its schema.

    Attach it to a tool function with `@ToolOptions.of(...)`, or set a capability's `tool_options`.
    """

    ATTRIBUTE: ClassVar[str] = "_aihub_tool_options"

    label: Annotated[LocaleString | None, Field(description="The tool's name as users read it.")] = None
    approval_summary: Annotated[
        LocaleString | None,
        Field(description="What a call does, for the approval prompt, with {argument} placeholders."),
    ] = None
    default_approval: Annotated[
        ToolApprovalPolicy, Field(description="When calls need approval unless the profile says otherwise.")
    ] = ToolApprovalPolicy.NEVER
    approve_every_call: Annotated[
        bool, Field(description="Whether an approval never carries over to the tool's next call.")
    ] = False
    chat_feature: Annotated[
        ChatFeature | None, Field(description="The chat toggle the tool needs switched on, if any.")
    ] = None

    @classmethod
    def of(cls, **options: Any) -> Callable[[Callable], Callable]:
        """Decorates a tool function, e.g. a method listed in a `BaseToolSpec`'s `spec_functions`."""

        def attach(function: Callable) -> Callable:
            setattr(function, cls.ATTRIBUTE, cls(**options))
            return function

        return attach

    @classmethod
    def of_function(cls, function: Callable | None) -> Self:
        return getattr(function, cls.ATTRIBUTE, None) or cls()

    def label_in(self, name: str, locale: str) -> str:
        return self.label.in_locale(locale) if self.label else name.replace("_", " ")

    def summary_in(self, arguments: dict[str, Any], locale: str) -> str:
        """The call in words for the approval prompt; its arguments one per line when the tool renders none."""
        if self.approval_summary:
            return self.approval_summary.in_locale(locale).format_map(defaultdict(str, arguments))
        return "\n".join(f"- {key}: {value}" for key, value in arguments.items())
