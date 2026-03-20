from swiss_ai_hub.core.events.process import ProgramWorkRequestEvent


class SaveDecisionRequest(ProgramWorkRequestEvent):
    decision: str
