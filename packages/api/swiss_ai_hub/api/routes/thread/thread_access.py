from fastapi import HTTPException
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import ThreadEntity

from swiss_ai_hub.api.routes.thread.dto.thread_dto import ThreadDTO


class ThreadAccess:
    """Who may read a thread and who may post into it, decided in one place for every thread and event endpoint."""

    NO_THREAD_ACCESS_DETAIL = "You do not have access to this thread. Please contact the process owner."

    @staticmethod
    def is_member(thread: ThreadDTO, user: UserIdentity) -> bool:
        return user.id in [thread_user.id for thread_user in thread.users]

    @staticmethod
    def can_view(thread: ThreadDTO, user: UserIdentity) -> bool:
        """Members and sysadmins may read any thread; a process grants access only to the threads it generated."""
        member_ids = [thread_user.id for thread_user in thread.users]
        return ThreadAccess._may_view(member_ids, thread.process_class, thread.process_id, user)

    @staticmethod
    def can_view_entity(thread: ThreadEntity, user: UserIdentity) -> bool:
        """The same rule on the stored thread, for a hot path that cannot afford building the full thread DTO."""
        member_ids = [thread_user.user_id for thread_user in thread.users]
        return ThreadAccess._may_view(member_ids, thread.process_class, thread.process_id, user)

    @staticmethod
    def _may_view(member_ids: list[str], process_class: str | None, process_id: str | None, user: UserIdentity) -> bool:
        if user.is_sys_admin or user.id in member_ids:
            return True
        if process_class is None or process_id is None:
            return False
        return AccessChecker.from_user(user).has_access_to_process(process_class, process_id)

    @staticmethod
    def ensure_can_view(thread: ThreadDTO, user: UserIdentity) -> None:
        if not ThreadAccess.can_view(thread, user):
            raise HTTPException(status_code=403, detail=ThreadAccess.NO_THREAD_ACCESS_DETAIL)

    @staticmethod
    def ensure_can_post(thread: ThreadDTO, user: UserIdentity) -> None:
        """Only members post: the event distributor refuses anyone else, so reject them before anything is sent."""
        if not ThreadAccess.is_member(thread, user):
            raise HTTPException(status_code=403, detail=ThreadAccess.NO_THREAD_ACCESS_DETAIL)
