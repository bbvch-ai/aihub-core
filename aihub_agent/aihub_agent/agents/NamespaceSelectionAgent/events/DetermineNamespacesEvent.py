"""Event triggering LLM namespace determination step."""

from typing import ClassVar

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.control.ControlEvent import ControlEvent


class DetermineNamespacesEvent(ControlEvent):
    """Internal event that triggers the LLM namespace determination step.

    This event is emitted to enter or re-enter the namespace determination loop.
    The conversation history and available namespaces are stored in RunContext,
    not in this event, to keep the event lightweight.
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
