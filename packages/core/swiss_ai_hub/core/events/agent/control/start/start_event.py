import time
from typing import Any, Self

from bson import ObjectId

from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler


class StartEvent(ControlAndDisplayEvent):
    """
    An event signaling the start of a new run within a thread, providing initial context such as
    user messages, assistant responses, and locale settings.

    ### Why StartEvent?
    The start event - and all events inheriting from it - trigger a new workflow run. By inheriting
    from the StartEvent, initial context for the workflow can be set.

    By extending `ControlEvent`, `StartEvent` influences workflow steps - only `ControlEvent` types
    drive the flow. Other event types may provide data or UI updates but do not start or control runs.

    ### Agent Configuration
    The agent_id is NOT on the event - it comes from the NATS subject/topic. When events are
    published to `agent.<class>.<id>.<thread>...`, the AgentDispatcher extracts the agent_id
    from the topic and uses it to fetch configuration via NATS request-reply. This keeps
    StartEvent lightweight and decouples config management from event payloads.
    """

    def to_context_dict(self) -> dict[str, Any]:
        """
        Returns a dictionary suitable for context injection, excluding internal event fields like
        event_id and created_at. This helps workflows pass only essential context to downstream steps.

        Dumped in JSON mode because the dispatcher writes every value here into `RunContext`, which
        serializes with `json.dumps` and reads back with `json.loads`. Python mode left the two halves
        inconsistent: a field of any type JSON cannot represent — a `datetime`, say — dumped fine here
        and then raised `TypeError` inside the store, killing the run before a single step executed.
        JSON mode is what the read path already returns, so it aligns them.
        """
        non_private = {k: v for k, v in self.model_dump(mode="json").items() if not k.startswith("_")}
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
        t: LocaleHandler,
    ) -> Self:
        """
        Creates a StartEvent from raw data.

        Note: agent_id is NOT included in the event. It comes from the NATS subject/topic
        that the event is published to. The AgentDispatcher extracts it from the topic
        and uses it to fetch configuration via RPC.
        """
        json_data: dict[str, Any] = {
            "event_id": str(ObjectId()),
            "created_at": time.time_ns(),
            "user": user,
            **raw_event_data,
            "locale": t.locale,
            "_parent_event_names": start_event_parents,
            "_event_name": start_event_name,
        }
        return cls.deserialize_event(json_data)
