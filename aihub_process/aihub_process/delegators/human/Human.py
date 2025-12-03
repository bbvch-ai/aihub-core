from typing import Annotated, Literal

from aihub_lib.nats.events.form.Form import Form
from pydantic import Field, model_validator

from aihub_process.delegators.AbstractProcessEntity import BaseProcessEntity


class Human(BaseProcessEntity):
    """
    The human process entity defines a human that participates in a process. To know from which users
    to reqeust work, you can provide either a list of user IDs, user emails or a list of roles
    that the users must have to be qualified for submitting this request. You can also specify
    whether to notify the users using a notification or not.
    For a piece of work submitted by the user, we specify the API route and method at which we
    expect the work to be submitted.
    Note that there is one special case: When a human input marks the start of a process, we must also
    have an instance of a HumanWorkEvent that defines the form that the user can submit.
    """

    class In(BaseProcessEntity.In):
        """Receive human work as an input on the specified api route, submitted via defined http-method"""

        route: Annotated[str, Field(description="The API route to submit work to.")]
        method: Annotated[
            Literal["POST", "PUT", "DELETE"], Field(description="HTTP method by API endpoint for submission")
        ] = "POST"
        start_form: Annotated[
            Form | None,
            Field(
                description="If human input marks start of process, "
                "use this form instance to generate user form in frontend"
            ),
        ] = None

    class Out(BaseProcessEntity.Out):
        user_ids: Annotated[list[str], Field(description="The list of user IDs that can submit work.")] = []
        user_emails: Annotated[list[str], Field(description="The list of user E-Mails that can submit work.")] = []
        user_roles: Annotated[list[str], Field(description="The list of roles that can submit work.")] = []
        notify: Annotated[bool, Field(description="Whether to notify the users or not.")] = True

        @model_validator(mode="after")
        def ensure_some_users(self):
            """Ensures at least one user_id, user_email oder user_role is given"""
            if not any([self.user_ids, self.user_emails, self.user_roles]):
                raise ValueError("At least one user_id, user_email or user_role must be given.")
            return self
