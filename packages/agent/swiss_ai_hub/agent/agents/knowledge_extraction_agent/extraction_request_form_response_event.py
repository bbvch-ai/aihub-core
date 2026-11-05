from swiss_ai_hub.core.events.agent import HumanInTheLoopChatResponseEvent


class ExtractionRequestFormResponseEvent(HumanInTheLoopChatResponseEvent):
    """The answer to the request form: the dialog's answers as JSON, or a typed reply."""
