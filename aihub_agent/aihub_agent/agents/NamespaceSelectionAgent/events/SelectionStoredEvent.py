from typing import Annotated, ClassVar

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.control.ControlEvent import ControlEvent
from pydantic import Field


class SelectionStoredEvent(ControlEvent):
    """Internal event indicating namespace selection has been stored.

    This event is emitted after the user's namespace selection has been
    validated and persisted to ThreadContext. It carries the selection
    so subsequent steps can use it for confirmation messaging.
    """

    _display_name: ClassVar[LocaleString] = LocaleString(
        en="Selection Stored Event",
        de="Auswahl-gespeichert-Event",
        fr="Événement de sélection stockée",
        it="Evento di selezione memorizzata",
    )
    _display_description: ClassVar[LocaleString] = LocaleString(
        en="Indicates that the namespace selection has been stored.",
        de="Zeigt an, dass die Namespace-Auswahl gespeichert wurde.",
        fr="Indique que la sélection du namespace a été stockée.",
        it="Indica che la selezione del namespace è stata memorizzata.",
    )

    selected_namespaces: Annotated[
        dict[str, str],
        Field(description="Map of bucket_name to selected namespace_name."),
    ]
