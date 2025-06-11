from aihub_lib.nats.events.work_request.program.ProgramWorkRequestEvent import ProgramWorkRequestEvent


class SaveDecisionRequest(ProgramWorkRequestEvent):
    decision: str