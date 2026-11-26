from typing import Annotated, Any

from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity


class HumanWorkRequestAssignment:
    """Decides who may answer a persisted human work request.

    A request names its assignees by user id, email or tenant role (``Human.Out``). Access to the process
    instance only lets a user see that a task exists; answering it is reserved for the people the process
    asked. A request naming nobody is answerable by nobody, since ``Human.Out`` rejects that configuration.
    """

    @staticmethod
    def is_assigned_to(
        work_request_data: Annotated[dict[str, Any], "The persisted HumanWorkRequestEvent's event_data"],
        user: UserIdentity,
    ) -> bool:
        if user.id in work_request_data.get("user_ids", []):
            return True
        assigned_emails = {email.casefold() for email in work_request_data.get("user_emails", [])}
        if user.email and user.email.casefold() in assigned_emails:
            return True
        return bool(set(work_request_data.get("user_roles", [])) & set(user.roles))
