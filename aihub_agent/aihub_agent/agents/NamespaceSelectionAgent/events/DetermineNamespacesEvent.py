"""Event triggering LLM namespace determination step."""

from typing import Annotated, ClassVar

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.control.ControlEvent import ControlEvent
from pydantic import Field


class DetermineNamespacesEvent(ControlEvent):
    """Internal event that triggers the LLM namespace determination step.

    This event carries available namespaces through the determination loop,
    eliminating the need for RunContext storage of this data.
    """

    _display_name: ClassVar[LocaleString] = LocaleString(
        en="Determine Namespaces Event",
        de="Namespaces-Bestimmungs-Event",
        fr="Événement de détermination des namespaces",
        it="Evento di determinazione dei namespace",
    )
    _display_description: ClassVar[LocaleString] = LocaleString(
        en="Triggers the LLM to determine namespaces from conversation context.",
        de="Löst das LLM aus, um Namespaces aus dem Gesprächskontext zu bestimmen.",
        fr="Déclenche le LLM pour déterminer les namespaces à partir du contexte de conversation.",
        it="Attiva l'LLM per determinare i namespace dal contesto della conversazione.",
    )

    available_namespaces: Annotated[
        dict[str, list[str]],
        Field(
            default_factory=dict,
            description="Map of bucket names to their available namespace names.",
        ),
    ]
