from typing import Annotated

from aihub_lib.auth.access.AccessChecker import AccessChecker
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.persistence.access.entities.RoleEntity import RoleEntity
from aihub_lib.persistence.user.UserEntity import UserEntity
from aihub_lib.routes.Controller import Controller
from fastapi import Depends, HTTPException, Path, Security

from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.pagination.type.PageNumber import PageNumber
from aihub_api.pagination.type.PageSize import PageSize
from aihub_api.routes.openai.dto.HistoryResponse import HistoryResponse
from aihub_api.routes.thread.dto.AddAgentRequest import AddAgentRequest
from aihub_api.routes.thread.dto.AddUserRequest import AddUserRequest
from aihub_api.routes.thread.dto.CreateThreadRequest import CreateThreadRequest
from aihub_api.routes.thread.dto.PaginatedThreadsResponse import PaginatedThreadsResponse
from aihub_api.routes.thread.dto.ThreadDTO import ThreadDTO
from aihub_api.routes.thread.ThreadService import ThreadService


class ThreadController(Controller):
    """
    A controller that manages thread-related endpoints.

    Conversations or workflows are often organized into "threads"—units that group users and agents together.
    The `ThreadController` provides endpoints to:
    - List user-specific threads.
    - Create new threads.
    - Retrieve a specific thread by ID.
    - Add or remove agents and users from threads.

    By structuring these operations in a controller, the API remains organized, and user authorization checks
    stay consistent and centralized.
    """

    name = LocaleString(en="Conversations", de="Unterhaltungen", fr="Conversations", it="Conversazioni")
    description = LocaleString(
        en="Manage your conversation history",
        de="Gesprächsverlauf verwalten",
        fr="Gérez votre historique de conversations",
        it="Gestisci la cronologia delle conversazioni",
    )
    icon = "simple-icons:threads"

    not_authorized_to_view_exception = HTTPException(status_code=403, detail="Not authorized to view this thread")
    not_authorized_to_modify_exception = HTTPException(status_code=403, detail="Not authorized to modify this thread")

    def __init__(
        self, *, auth: AuthHandler, route: str = "/threads", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def get_user_threads(self, route: str = "/") -> "ThreadController":
        @self.router.get(route, tags=self.tags)
        async def get_user_threads(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
            page: PageNumber = 1,
            page_size: PageSize = 20,
        ) -> PaginatedThreadsResponse:
            """
            Returns all threads that the authenticated user is a member of.
            """
            total, threads = await ThreadService.get_paginated_threads_for_user(
                user.id, t=t, page=page, page_size=page_size
            )

            total_pages = (total + page_size - 1) // page_size

            return PaginatedThreadsResponse(
                threads=threads, total=total, page=page, page_size=page_size, total_pages=total_pages
            )

        return self

    def create_thread(self, route: str = "/") -> "ThreadController":
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

            for user_id in create_request_dto.user_ids:
                thread_user = UserEntity.by_oid(user_id)
                access_rules = RoleEntity.get_access_rules_for_roles(thread_user.roles)
                access = AccessChecker(list(access_rules))
                for agent in create_request_dto.agents:
                    if not access.has_access_to_agent(agent.agent_class, agent.agent_id):
                        raise HTTPException(
                            status_code=403,
                            detail=f"User {user_id} does not have access to agent {agent.agent_class}:{agent.agent_id}",
                        )

            return await ThreadService.create_thread(
                name=create_request_dto.name,
                user_ids=create_request_dto.user_ids,
                agent_dtos=create_request_dto.agents,
                t=t,
            )

        return self

    def get_thread(self, route: str = "/{thread_id}") -> "ThreadController":
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
            thread = await ThreadService.get_thread_by_id(thread_id, t=t)

            user_in_thread = user.id in [u.id for u in thread.users]
            thread_belongs_to_users_process = AccessChecker.from_user(user).has_access_to_process(
                thread.process_class, thread.process_id
            )
            if not (user_in_thread or thread_belongs_to_users_process):
                raise self.not_authorized_to_view_exception

            return thread

        return self

    def add_agent_to_thread(self, route: str = "/{thread_id}/agents") -> "ThreadController":
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
            thread = await ThreadService.get_thread_by_id(thread_id, t=t)

            if thread.process_class or thread.process_id:
                raise HTTPException(status_code=403, detail="Cannot add agent to process thread")

            if user.id not in [u.id for u in thread.users]:
                raise self.not_authorized_to_modify_exception

            for thread_user in thread.users:
                user_entity = UserEntity.by_oid(thread_user.id)
                access_rules = RoleEntity.get_access_rules_for_roles(user_entity.roles)
                access = AccessChecker(list(access_rules))
                if not access.has_access_to_agent(req.agent_class, req.agent_id):
                    raise HTTPException(
                        status_code=403,
                        detail=f"User {thread_user.id} does not have access to agent {req.agent_class}:{req.agent_id}",
                    )

            return await ThreadService.add_agent_to_thread(thread_id, req.agent_id, req.agent_class, t=t)

        return self

    def thread_as_message_history(self, route: str = "/{thread_id}/history") -> "ThreadController":
        @self.router.get(route, tags=self.tags)
        async def thread_as_message_history(
            thread_id: Annotated[str, Path(title="Thread ID", pattern=r"^[a-f0-9]{24}$")],
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> HistoryResponse:
            thread = await ThreadService.get_thread_by_id(thread_id, t=t)

            user_in_thread = user.id in [u.id for u in thread.users]
            thread_belongs_to_users_process = AccessChecker.from_user(user).has_access_to_process(
                thread.process_class, thread.process_id
            )
            if not (user_in_thread or thread_belongs_to_users_process):
                raise self.not_authorized_to_view_exception

            return await ThreadService.thread_as_message_history(thread_id)

    def remove_agent_from_thread(
        self, route: str = "/{thread_id}/agents/{agent_class}/{agent_id}"
    ) -> "ThreadController":
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
            thread = await ThreadService.get_thread_by_id(thread_id, t=t)

            if thread.process_class or thread.process_id:
                raise HTTPException(status_code=403, detail="Cannot remove agent from process thread")

            if user.id not in [u.id for u in thread.users]:
                raise self.not_authorized_to_modify_exception

            return await ThreadService.remove_agent_from_thread(thread_id, agent_class, agent_id, t=t)

        return self

    def add_user_to_thread(self, route: str = "/{thread_id}/users") -> "ThreadController":
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
            thread = await ThreadService.get_thread_by_id(thread_id, t=t)

            if thread.process_class or thread.process_id:
                raise HTTPException(status_code=403, detail="Cannot remove agent from process thread")

            if user.id not in [u.id for u in thread.users]:
                raise self.not_authorized_to_modify_exception

            user_to_add = UserEntity.by_oid(add_user_dto.user_id)
            access_rules = RoleEntity.get_access_rules_for_roles(user_to_add.roles)
            for agent in thread.agents:
                if not AccessChecker(list(access_rules)).has_access_to_agent(agent.agent_class, agent.agent_id):
                    raise HTTPException(
                        status_code=403,
                        detail=f"User {add_user_dto.user_id} does not have access "
                        f"to agent {agent.agent_class}:{agent.agent_id}",
                    )

            return await ThreadService.add_user_to_thread(thread_id, add_user_dto.user_id, t=t)

        return self

    def remove_user_from_thread(self, route: str = "/{thread_id}/users/{remove_user_id}") -> "ThreadController":
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
            thread = await ThreadService.get_thread_by_id(thread_id, t=t)

            if thread.process_class or thread.process_id:
                raise HTTPException(status_code=403, detail="Cannot remove agent from process thread")

            if user.id not in [u.id for u in thread.users]:
                raise self.not_authorized_to_modify_exception

            return await ThreadService.remove_user_from_thread(thread_id, remove_user_id, t=t)

        return self
