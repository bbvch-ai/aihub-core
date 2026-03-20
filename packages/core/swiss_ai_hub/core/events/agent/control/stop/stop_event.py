from typing import ClassVar

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class StopEvent(ControlAndDisplayEvent):
    """
    An event signaling the conclusion of a run within a thread, acting both as a control signal
    and a user-facing message.

    ### Why StopEvent?
    In many workflows, reaching a terminal state (e.g., producing a final result or hitting an
    end-of-workflow condition) must:
    - Influence the system’s control flow, ensuring no further steps are executed.
    - Provide a visible indicator to the end-user or UI that the process has completed.

    By inheriting from both `ControlEvent` and `DisplayEvent`:
    - As a `ControlEvent`, it instructs the workflow engine to stop processing subsequent steps.
    - As a `DisplayEvent`, it can be shown to users or captured by dashboards, indicating that
      the run is over and providing any final output or status messages.

    ### Use Cases
    - Signaling that a response is ready, and no more actions are needed.
    - Informing the user interface that the conversation or task has concluded.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.stop_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.stop_event.description")
