import time
from typing import Annotated, Any

from bson import ObjectId
from pydantic import Field

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events.ControlAndDisplayEvent import ControlAndDisplayEvent


class StartEvent(ControlAndDisplayEvent):
    """
    An event signaling the start of a new run within a thread, providing initial context such as
    user messages, assistant responses, and locale settings.

    ### Why StartEvent?
    The start event - and all events inheriting from it - trigger a new workflow run. By inheriting
    from the StartEvent, initial context for the workflow can be set.

    By extending `ControlEvent`, `StartEvent` influences workflow steps—only `ControlEvent` types
    drive the flow. Other event types may provide data or UI updates but do not start or control runs.
    """

    agent_config: Annotated["dict[str, Any] | None", Field(description="Agent configuration")] = None

    def to_context_dict(self) -> dict[str, Any]:
        """
        Returns a dictionary suitable for context injection, excluding internal event fields like
        event_id and created_at. This helps workflows pass only essential context to downstream steps.
        """
        non_private = {k: v for k, v in self.model_dump().items() if not k.startswith("_")}
        # Remove internal fields not needed by downstream steps
        del non_private["event_id"]
        del non_private["created_at"]
        return non_private

    @classmethod
    def from_raw_data(
        cls,
        raw_event_data: dict[str, Any],
        user: UserIdentity,
        start_event_name: str,
        start_event_parents: list[str],
        agent_config: AgentConfig,
        t: LocaleHandler,
        **args,
    ) -> "StartEvent":
        json_data: dict[str, Any] = {
            "event_id": str(ObjectId()),
            "created_at": time.time_ns(),
            "user": user,
            **raw_event_data,
            "locale": t.locale,
            "_parent_event_names": start_event_parents,
            "_event_name": start_event_name,
            "agent_config": agent_config.model_dump(),
        }
        return cls.deserialize_event(json_data)
