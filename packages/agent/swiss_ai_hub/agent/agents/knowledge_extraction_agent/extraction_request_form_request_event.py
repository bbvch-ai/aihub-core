from swiss_ai_hub.core.events.agent import HumanInTheLoopQuestionsRequestEvent


class ExtractionRequestFormRequestEvent(HumanInTheLoopQuestionsRequestEvent):
    """Asks the user to confirm or correct where, which rows and which columns the table is extracted from."""
