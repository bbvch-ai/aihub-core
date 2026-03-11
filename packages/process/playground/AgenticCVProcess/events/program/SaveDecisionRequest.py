from swiss_ai_hub.core.events.process.work_request.program.ProgramWorkRequestEvent import ProgramWorkRequestEvent


class SaveDecisionRequest(ProgramWorkRequestEvent):
    decision: str
