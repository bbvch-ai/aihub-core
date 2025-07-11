from typing import Annotated

from pydantic import Field

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.nats.events.form.Form import Form
from aihub_lib.nats.events.work.WorkEvent import WorkEvent


class HumanWorkEvent(WorkEvent, Form):
    """
    A work event that can be initiated by a human and may contain FormKit UI elements.
    """

    submitted_by: Annotated[UserIdentity | None, Field(description="The user who submitted the form.")] = None


