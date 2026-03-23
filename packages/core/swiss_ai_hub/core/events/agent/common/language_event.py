from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NODE_LANGUAGE_ENGLISH, LanguageValue


class LanguageEvent(ControlEvent):
    """
    Event indicating the language from the (user's) request. This event can be used to identify the language of the
    request and set the language for subsequent processing.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.request_language_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.request_language_event.description"
    )

    language_short_name: Annotated[LanguageValue, Field(description="The language of the user.")] = (
        NODE_LANGUAGE_ENGLISH
    )
