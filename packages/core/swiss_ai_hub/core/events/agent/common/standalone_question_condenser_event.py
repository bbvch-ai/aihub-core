from typing import Annotated, ClassVar

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class StandaloneQuestionCondenserEvent(ControlAndDisplayEvent):
    """
    Event to condense chat messages into a single standalone question as a chat message.

    A blank condensation is refused by `condense_standalone_question`, before an event of this type can be
    built. The invariant is deliberately *not* also a `field_validator` here: a validator on an event is not
    only a publish-time contract, it runs on every `model_validate`, which is how the immutable log is read
    back — JetStream replays the whole stream on each agent start, and the API rebuilds a thread's timeline
    from the persisted display copy. Blank condensations did occur before the producer-side raise existed, so
    validating on read makes that history undeserializable: replay drops the event and
    `EventService.get_events_in_thread` fails the whole thread.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.standalone_question_condenser_event.name"
    )
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.standalone_question_condenser_event.description"
    )
    condensed_chat_message: Annotated[
        ChatMessage, Field(description="Single chat message containing the condensed user question.")
    ]

    @property
    def condensed_question(self) -> str:
        """Non-blank for anything this deployment publishes; historical events may still be empty."""
        return (self.condensed_chat_message.content or "").strip()
