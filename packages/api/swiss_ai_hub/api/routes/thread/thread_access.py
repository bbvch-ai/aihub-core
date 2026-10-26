from fastapi import HTTPException
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity

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
        if user.is_sys_admin or ThreadAccess.is_member(thread, user):
            return True
        if thread.process_class is None or thread.process_id is None:
            return False
        return AccessChecker.from_user(user).has_access_to_process(thread.process_class, thread.process_id)

    @staticmethod
    def ensure_can_view(thread: ThreadDTO, user: UserIdentity) -> None:
        if not ThreadAccess.can_view(thread, user):
            raise HTTPException(status_code=403, detail=ThreadAccess.NO_THREAD_ACCESS_DETAIL)

    @staticmethod
    def ensure_can_post(thread: ThreadDTO, user: UserIdentity) -> None:
        """Only members post: the event distributor refuses anyone else, so reject them before anything is sent."""
        if not ThreadAccess.is_member(thread, user):
            raise HTTPException(status_code=403, detail=ThreadAccess.NO_THREAD_ACCESS_DETAIL)
