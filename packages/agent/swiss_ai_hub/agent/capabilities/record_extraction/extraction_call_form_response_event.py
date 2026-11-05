from swiss_ai_hub.core.events.agent import HumanInTheLoopChatResponseEvent


class ExtractionCallFormResponseEvent(HumanInTheLoopChatResponseEvent):
    """The answer to an extraction call's request form: the dialog's answers as JSON, or a typed reply."""
