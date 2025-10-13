from typing import Annotated, ClassVar

from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.control.ControlEvent import ControlEvent
from aihub_lib.persistence.rag.vectors.node_metadata import NODE_LANGUAGE_ENGLISH, LanguageValue


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
