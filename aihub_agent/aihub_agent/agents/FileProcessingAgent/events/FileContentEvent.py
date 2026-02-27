from aihub_lib.nats.events.control.ControlEvent import ControlEvent


class FileContentEvent(ControlEvent):
    """Carries extracted file text from the extract step to the prepare step."""

    file_context: str = ""
