from swiss_ai_hub.core.nats.events.work_request.program.ProgramWorkRequestEvent import ProgramWorkRequestEvent


class SaveDecisionRequest(ProgramWorkRequestEvent):
    decision: str
