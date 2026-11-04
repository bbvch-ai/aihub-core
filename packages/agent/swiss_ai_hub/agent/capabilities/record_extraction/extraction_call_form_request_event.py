from swiss_ai_hub.core.events.agent import HumanInTheLoopQuestionsRequestEvent


class ExtractionCallFormRequestEvent(HumanInTheLoopQuestionsRequestEvent):
    """Asks the user to confirm or correct an extraction the model wants to run, before any document is read."""
