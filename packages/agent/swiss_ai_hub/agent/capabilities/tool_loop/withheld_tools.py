from typing import Annotated

from pydantic import BaseModel, Field
from swiss_ai_hub.core.events.agent import ChatFeature, Message, TextContent
from swiss_ai_hub.core.i18n import LocaleHandler


class WithheldTools(BaseModel):
    """The tools that would serve this message but are not offered, and why.

    A model never told about them concludes that what the user refers to does not exist: with file reading turned
    off it answers that no file was attached. Told which tool is missing and who can turn it on, it says that instead.
    """

    by_profile: Annotated[
        list[str], Field(description="Labels of the tools the profile disables; only an administrator enables them.")
    ] = []
    by_toggle: Annotated[
        list[ChatFeature], Field(description="Chat toggles the user left off, each withholding the tools it gates.")
    ] = []

    def add_by_profile(self, label: str) -> None:
        if label not in self.by_profile:
            self.by_profile.append(label)

    def add_by_toggle(self, feature: ChatFeature) -> None:
        if feature not in self.by_toggle:
            self.by_toggle.append(feature)

    def note(self, t: LocaleHandler) -> str | None:
        if not self.by_profile and not self.by_toggle:
            return None
        lines = [
            t("agent.tool_loop.prompt.withheld.intro"),
            *(t("agent.tool_loop.prompt.withheld.by_profile", tool=label) for label in self.by_profile),
            *(
                t(
                    "agent.tool_loop.prompt.withheld.by_toggle",
                    toggle=t(f"agent.tool_loop.prompt.withheld.toggles.{feature.value}"),
                )
                for feature in self.by_toggle
            ),
        ]
        return "\n".join(lines)

    def into(self, messages: list[Message], t: LocaleHandler) -> list[Message]:
        """The note joins the leading system message, which condensing never touches; chat templates such as Qwen's
        reject a system message after the first."""
        note = self.note(t)
        if note is None:
            return messages
        if messages and messages[0].role == "system":
            contents = [*(messages[0].contents or []), TextContent(text=f"\n\n{note}")]
            return [messages[0].model_copy(update={"contents": contents}), *messages[1:]]
        return [Message.from_string(role="system", content=note), *messages]
