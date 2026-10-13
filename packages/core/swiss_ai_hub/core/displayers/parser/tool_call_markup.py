import re
from typing import ClassVar


class ToolCallMarkup:
    """A tool call a model rendered into its answer instead of returning it in ``tool_calls``.

    Two sources, one symptom. A serving stack with no parser for a model's native tool-call tokens
    passes them through as text; and a model imitates a tool-calling transcript it saw in training
    when a prompt reads like one, even with no tool on offer. Nothing executes either, so there is
    no intent to recover: it is only text, and it belongs anywhere except the answer.
    """

    SPANS: ClassVar[tuple[tuple[str, str], ...]] = (
        ("<|tool_calls_section_begin|>", "<|tool_calls_section_end|>"),
        ("<tool_call>", "</tool_call>"),
    )

    _REACT_OPENING: ClassVar[str] = '{"action":'

    @staticmethod
    def _compact(text: str) -> str:
        return "".join(text.split())

    @staticmethod
    def opens_react_object(text: str) -> bool:
        """Whether the message *starts* as a ReAct tool-call object.

        Anchored at the start so prose discussing ``action_input`` survives, and matched on the
        opening alone so a response cut short is suppressed just the same. The trailing colon keeps
        a legitimate ``{"actionType": ...}`` out.
        """
        return ToolCallMarkup._compact(text).startswith(ToolCallMarkup._REACT_OPENING)

    @staticmethod
    def may_open_react_object(text: str) -> bool:
        """Whether ``text`` is still a viable prefix, so a streaming caller keeps withholding it."""
        return ToolCallMarkup._REACT_OPENING.startswith(ToolCallMarkup._compact(text))

    @staticmethod
    def strip(text: str) -> str:
        """Remove markup that must never reach the answer, leaving surrounding prose intact.

        An unterminated span runs to the end of the text: the closing token is what the models at
        issue drop most often, and half a tool call is no more presentable than a whole one.
        """
        if ToolCallMarkup.opens_react_object(text):
            return ""

        for opening, closing in ToolCallMarkup.SPANS:
            text = re.sub(
                f"{re.escape(opening)}.*?(?:{re.escape(closing)}|$)",
                "",
                text,
                flags=re.DOTALL,
            )
        return text
