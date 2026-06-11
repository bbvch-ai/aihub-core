from datetime import datetime
from typing import Annotated, Self

from fastapi import Depends, HTTPException, Path, Query, Security
from mongoengine import DoesNotExist
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.routes import TenantScopedController

from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString
from swiss_ai_hub.api.i18n.dependencies.use_locale import use_locale
from swiss_ai_hub.api.pagination.type.page_number import PageNumber
from swiss_ai_hub.api.pagination.type.page_size import PageSize
from swiss_ai_hub.api.routes.openai.dto.history_response import HistoryResponse
from swiss_ai_hub.api.routes.thread.dto.add_agent_request import AddAgentRequest
from swiss_ai_hub.api.routes.thread.dto.add_user_request import AddUserRequest
from swiss_ai_hub.api.routes.thread.dto.create_thread_request import CreateThreadRequest
from swiss_ai_hub.api.routes.thread.dto.open_chat_hitl_response import OpenChatHitlResponse
from swiss_ai_hub.api.routes.thread.dto.paginated_threads_response import PaginatedThreadsResponse
from swiss_ai_hub.api.routes.thread.dto.thread_dto import ThreadDTO
from swiss_ai_hub.core.persistence.messaging.entities.types.thread_sort import SortOrder
from swiss_ai_hub.api.routes.thread.thread_service import ThreadService


class ThreadController(TenantScopedController):
    """
    A controller that manages thread-related endpoints.

    Conversations or workflows are often organized into "threads" - units that group users and agents together.
    The `ThreadController` provides endpoints to:
    - List user-specific threads.
    - Create new threads.
    - Retrieve a specific thread by ID.
    - Add or remove agents and users from threads.

    By structuring these operations in a controller, the API remains organized, and user authorization checks
    stay consistent and centralized.
    """

    name = ApiLocaleString.from_i18n_path("api.controllers.thread.name")
    description = ApiLocaleString.from_i18n_path("api.controllers.thread.description")
    icon = "mage:message-information"

    not_authorized_to_view_exception = HTTPException(status_code=403, detail="Not authorized to view this thread")
    not_authorized_to_modify_exception = HTTPException(status_code=403, detail="Not authorized to modify this thread")
    thread_not_found_exception = HTTPException(status_code=404, detail="Thread not found")

    @staticmethod
    async def _get_thread_or_404(thread_id: str, t: LocaleHandler) -> ThreadDTO:
        try:
            return await ThreadService.get_thread_by_id(thread_id, t=t)
        except DoesNotExist:
            raise ThreadController.thread_not_found_exception

    @staticmethod
    def _check_view_access(thread: ThreadDTO, user: UserIdentity) -> None:
        """Raise 403 if user is not a member of the thread and has no process access."""
        user_in_thread = user.id in [u.id for u in thread.users]
        has_process_access = AccessChecker.from_user(user).has_access_to_process(
            thread.process_class, thread.process_id
        )
        if not (user_in_thread or has_process_access):
            raise ThreadController.not_authorized_to_view_exception

    def __init__(
        self, *, auth: AuthHandler, route: str = "/threads", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def get_user_threads(self, route: str = "/") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_user_threads(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
            search: Annotated[str | None, Query(description="Search by thread name")] = None,
            agent_id: Annotated[str | None, Query(description="Filter by agent id")] = None,
            user_id: Annotated[str | None, Query(description="Filter by user id")] = None,
            status: Annotated[
                str | None,
                Query(description="Filter by status: active, completed, failed", pattern="^(active|completed|failed)$"),
            ] = None,
            from_date: Annotated[
                datetime | None, Query(alias="from", description="Filter threads created from this date")
            ] = None,
            to_date: Annotated[
                datetime | None, Query(alias="to", description="Filter threads created up to this date")
            ] = None,
            page: PageNumber = 1,
            page_size: PageSize = 20,
            sort_field: Annotated[
                str,
                Query(
                    description="Field to sort by: name, created_at",
                    pattern="^(name|created_at)$",
                ),
            ] = "created_at",
            sort_order: Annotated[
                SortOrder, Query(description="Sort order: 1 for ascending, -1 for descending")
            ] = SortOrder.DESCENDING,
        ) -> PaginatedThreadsResponse:
            """
            Returns all threads that the authenticated user is a member of.
            """
            total, threads = await ThreadService.get_paginated_threads_for_user(
                user.id,
                t=t,
                page=page,
                page_size=page_size,
                sort_by=sort_field,
                sort_order=sort_order,
                search=search,
                agent_id=agent_id,
                user_search_id=user_id,
                status=status,
                from_date=from_date,
                to_date=to_date,
            )

            total_pages = (total + page_size - 1) // page_size

            return PaginatedThreadsResponse(
                threads=threads, total=total, page=page, page_size=page_size, total_pages=total_pages
            )

        return self

    def create_thread(self, route: str = "/") -> Self:
        @self.router.post(route, tags=self.tags)
        async def create_thread(
            create_request_dto: CreateThreadRequest,
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> ThreadDTO:
            """
            Creates a new thread with the specified name, users, and agents.
            Automatically adds the authenticated user if not already included.
            """
            if user.id not in create_request_dto.user_ids:
                create_request_dto.user_ids.append(user.id)

            agents = [(agent.agent_class, agent.agent_id) for agent in create_request_dto.agents]
            await ThreadService.validate_users_have_agent_access(
                user_ids=create_request_dto.user_ids,
                agents=agents,
                tenant=user.acting_within_tenant,
            )

            return await ThreadService.create_thread(
                name=create_request_dto.name,
                user_ids=create_request_dto.user_ids,
                agent_dtos=create_request_dto.agents,
                t=t,
            )

        return self

    def get_thread(self, route: str = "/{thread_id}") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_thread(
            thread_id: Annotated[str, Path(title="Thread ID", pattern=r"^[a-f0-9]{24}$")],
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> ThreadDTO:
            """
            Retrieves details of a specific thread.
            Raises 403 if the user is not a member of that thread.
            """
            thread = await ThreadController._get_thread_or_404(thread_id, t)
            ThreadController._check_view_access(thread, user)
            return thread

        return self

    def add_agent_to_thread(self, route: str = "/{thread_id}/agents") -> Self:
        @self.router.post(route, tags=self.tags)
        async def add_agent_to_thread(
            thread_id: Annotated[str, Path(title="Thread ID", pattern=r"^[a-f0-9]{24}$")],
            req: AddAgentRequest,
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> ThreadDTO:
            """
            Adds an agent to a specified thread, if the user is a member of that thread.
            """
            thread = await ThreadController._get_thread_or_404(thread_id, t)

            if thread.process_class or thread.process_id:
                raise HTTPException(status_code=403, detail="Cannot add agent to process thread")

            if user.id not in [u.id for u in thread.users]:
                raise self.not_authorized_to_modify_exception

            user_ids = [u.id for u in thread.users]
            await ThreadService.validate_users_have_agent_access(
                user_ids=user_ids,
                agents=[(req.agent_class, req.agent_id)],
                tenant=user.acting_within_tenant,
            )

            return await ThreadService.add_agent_to_thread(thread_id, req.agent_id, req.agent_class, t=t)

        return self

    def thread_as_message_history(self, route: str = "/{thread_id}/history") -> Self:
        @self.router.get(route, tags=self.tags)
        async def thread_as_message_history(
            thread_id: Annotated[str, Path(title="Thread ID", pattern=r"^[a-f0-9]{24}$")],
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> HistoryResponse:
            thread = await ThreadController._get_thread_or_404(thread_id, t)
            ThreadController._check_view_access(thread, user)
            return await ThreadService.thread_as_message_history(thread_id)

    def remove_agent_from_thread(self, route: str = "/{thread_id}/agents/{agent_class}/{agent_id}") -> Self:
        @self.router.delete(route, tags=self.tags)
        async def remove_agent_from_thread(
            thread_id: Annotated[str, Path(title="Thread ID", pattern=r"^[a-f0-9]{24}$")],
            agent_class: Annotated[str, Path(title="Agent Class")],
            agent_id: Annotated[str, Path(title="Agent ID")],
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> ThreadDTO:
            """
            Removes an agent from the thread, if the user is part of that thread.
            """
            thread = await ThreadController._get_thread_or_404(thread_id, t)

            if thread.process_class or thread.process_id:
                raise HTTPException(status_code=403, detail="Cannot remove agent from process thread")

            if user.id not in [u.id for u in thread.users]:
                raise self.not_authorized_to_modify_exception

            return await ThreadService.remove_agent_from_thread(thread_id, agent_class, agent_id, t=t)

        return self

    def add_user_to_thread(self, route: str = "/{thread_id}/users") -> Self:
        @self.router.post(route, tags=self.tags)
        async def add_user_to_thread(
            thread_id: Annotated[str, Path(title="Thread ID", pattern=r"^[a-f0-9]{24}$")],
            add_user_dto: AddUserRequest,
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> ThreadDTO:
            """
            Adds another user to the thread, provided the current user is a member of the thread.
            """
            thread = await ThreadController._get_thread_or_404(thread_id, t)

            if thread.process_class or thread.process_id:
                raise HTTPException(status_code=403, detail="Cannot add user to process thread")

            if user.id not in [u.id for u in thread.users]:
                raise self.not_authorized_to_modify_exception

            agents = [(agent.agent_class, agent.agent_id) for agent in thread.agents]
            await ThreadService.validate_users_have_agent_access(
                user_ids=[add_user_dto.user_id],
                agents=agents,
                tenant=user.acting_within_tenant,
            )

            return await ThreadService.add_user_to_thread(thread_id, add_user_dto.user_id, t=t)

        return self

    def remove_user_from_thread(self, route: str = "/{thread_id}/users/{remove_user_id}") -> Self:
        @self.router.delete(route, tags=self.tags)
        async def remove_user_from_thread(
            thread_id: Annotated[str, Path(title="Thread ID", pattern=r"^[a-f0-9]{24}$")],
            remove_user_id: Annotated[str, Path(title="User ID")],
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> ThreadDTO:
            """
            Removes a user from the thread if the authenticated user is a member of the thread.
            """
            thread = await ThreadController._get_thread_or_404(thread_id, t)

            if thread.process_class or thread.process_id:
                raise HTTPException(status_code=403, detail="Cannot remove agent from process thread")

            if user.id not in [u.id for u in thread.users]:
                raise self.not_authorized_to_modify_exception

            return await ThreadService.remove_user_from_thread(thread_id, remove_user_id, t=t)

        return self

    def get_open_chat_hitl(self, route: str = "/{thread_id}/open-chat-hitl") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_open_chat_hitl(
            thread_id: Annotated[str, Path(title="Thread ID", pattern=r"^[a-f0-9]{24}$")],
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> OpenChatHitlResponse:
            """
            Returns the open chat HITL request for a thread, if any.

            Chat HITLs are HITL requests where the question appears as a regular chat message
            and the user responds by typing a normal chat message (not via popup dialog).
            """
            thread = await ThreadController._get_thread_or_404(thread_id, t)
            ThreadController._check_view_access(thread, user)
            return ThreadService.get_open_chat_hitl(thread_id)

        return self
