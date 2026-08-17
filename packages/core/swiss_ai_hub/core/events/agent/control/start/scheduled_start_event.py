from datetime import datetime
from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.events.agent.control.start.start_event import StartEvent
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class ScheduledStartEvent(StartEvent):
    """Start event fired by the cron scheduler — handling it is what makes an agent schedulable.

    Mirrors how accepting a `UserMessageEvent` makes an agent conversational: `AgentRunner` derives
    `is_schedulable` from the start events an agent declares, so a blueprint opts in by adding a step
    that consumes this event, with no separate registration.

    Scheduled runs are system runs, so `user` is always None and the agent must not depend on an
    initiating identity. Whatever tenant context the agent needs comes from its own profile
    configuration (as `OrgMemoryWriteConfig.tenant_id` already does), never from the run.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.scheduled_start_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.scheduled_start_event.description"
    )

    locale: Annotated[
        str,
        Field(description="The locale the scheduled run reports its display output in."),
    ] = LocaleHandler.DEFAULT_LOCALE
    user: Annotated[
        UserIdentity | None,
        Field(description="Always None — scheduled runs are system-initiated and carry no execution identity."),
    ] = None
    scheduled_for: Annotated[
        datetime,
        Field(
            description="The cron occurrence this run fires for, in UTC. Distinct from `created_at`, which records "
            "when the scheduler published the event — the two differ by the scheduler's tick latency."
        ),
    ]
