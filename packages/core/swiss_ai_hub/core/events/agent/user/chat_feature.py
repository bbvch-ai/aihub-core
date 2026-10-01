from enum import StrEnum


class ChatFeature(StrEnum):
    """
    A capability a user can request per message in a chat client, which the agent then decides how to serve.

    Web search, code interpreter and image generation map onto OpenWebUI's native toggles. A feature OpenWebUI
    has no toggle for is surfaced as one of our toggle filters instead (`openwebui_toggle_filter_id`), so adding
    a member here is all a new feature needs on the contract side.
    """

    WEB_SEARCH = "web_search"
    CODE_INTERPRETER = "code_interpreter"
    IMAGE_GENERATION = "image_generation"

    @property
    def openwebui_capability(self) -> str | None:
        """The OpenWebUI model capability that shows this feature's native toggle, or None if there is none."""
        return self.value if self in _OPENWEBUI_NATIVE_TOGGLES else None

    @property
    def openwebui_toggle_filter_id(self) -> str:
        """The id our toggle filter for this feature is registered under, for features without a native toggle."""
        return f"aihub-feature-{self.value.replace('_', '-')}"


_OPENWEBUI_NATIVE_TOGGLES = frozenset(
    {ChatFeature.WEB_SEARCH, ChatFeature.CODE_INTERPRETER, ChatFeature.IMAGE_GENERATION}
)
