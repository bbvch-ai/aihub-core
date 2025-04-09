from typing import Any, Dict

from aihub_lib.nats.events.control.ControlEvent import ControlEvent


class StartEvent(ControlEvent):
    """
    An event signaling the start of a new run within a thread, providing initial context such as
    user messages, assistant responses, and locale settings.

    ### Why StartEvent?
    The start event - and all events inheriting from it - trigger a new workflow run. By inheriting
    from the StartEvent, initial context for the workflow can be set.

    By extending `ControlEvent`, `StartEvent` influences workflow steps—only `ControlEvent` types
    drive the flow. Other event types may provide data or UI updates but do not start or control runs.
    """

    def to_context_dict(self) -> Dict[str, Any]:
        """
        Returns a dictionary suitable for context injection, excluding internal event fields like
        event_id and created_at. This helps workflows pass only essential context to downstream steps.
        """
        non_private = {k: v for k, v in self.model_dump().items() if not k.startswith("_")}
        # Remove internal fields not needed by downstream steps
        del non_private["event_id"]
        del non_private["created_at"]
        return non_private
