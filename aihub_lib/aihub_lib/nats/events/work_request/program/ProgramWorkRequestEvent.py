from aihub_lib.nats.events.work_request.WorkRequestEvent import WorkRequestEvent


class ProgramWorkRequestEvent(WorkRequestEvent):
    """
    WIP
    """

    endpoint: str | None = None
    method: str | None = None
