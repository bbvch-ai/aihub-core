from typing import List

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.routes.Controller import Controller
from fastapi import Depends, HTTPException, Security

from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.routes.thread.dto.AddAgentRequest import AddAgentRequest
from aihub_api.routes.thread.dto.AddUserRequest import AddUserRequest
from aihub_api.routes.thread.dto.CreateThreadRequest import CreateThreadRequest
from aihub_api.routes.thread.dto.ThreadResponse import ThreadResponse
from aihub_api.routes.thread.ThreadService import ThreadService


class ThreadController(Controller):
    """
    A controller that manages thread-related endpoints.

    ### Why ThreadController?
    Conversations or workflows are often organized into "threads"—units that group users and agents together.
    The `ThreadController` provides endpoints to:
    - List user-specific threads.
    - Create new threads.
    - Retrieve a specific thread by ID.
    - Add or remove agents and users from threads.

    By structuring these operations in a controller, the API remains organized, and user authorization checks
    stay consistent and centralized.

    ### Endpoints
    - `GET /thread/`: Lists all threads for the authenticated user.
    - `POST /thread/{thread_id}`: Creates a thread with specified users and agents.
    - `GET /thread/{thread_id}`: Retrieves details of a specific thread, ensuring the user has access.
    - `POST /thread/{thread_id}/agents`: Adds an agent to a thread if the user is a member.
    - `DELETE /thread/{thread_id}/agents/{agent_class}/{agent_id}`: Removes an agent from a thread if authorized.
    - `POST /thread/{thread_id}/users`: Adds a user to a thread if authorized.
    - `DELETE /thread/{thread_id}/users/{remove_user_id}`: Removes a user from a thread if authorized.

    ### Authentication & Authorization
    Most operations require that the authenticated user be a member of the thread. Otherwise,
    a `403 Forbidden` is raised.

    ### Usage
    ```python
    app = FastAPI()
    ThreadController(auth=some_auth_dependency)
        .get_user_threads()
        .create_thread()
        .get_thread()
        .add_agent_to_thread()
        .remove_agent_from_thread()
        .add_user_to_thread()
        .remove_user_from_thread()
        .mount(app)
    ```
    """

    name = LocaleString(en="Thread")
    description = LocaleString(en="Get on or off threads")
    icon = "simple-icons:threads"

    not_authorized_to_view_exception = HTTPException(status_code=403, detail="Not authorized to view this thread")
    not_authorized_to_modify_exception = HTTPException(status_code=403, detail="Not authorized to modify this thread")

    def __init__(self, route: str = "/thread", auth: AuthHandler | None = None, is_admin_only=True):
        super().__init__(route, auth, is_admin_only=is_admin_only)

    def get_user_threads(self, route: str = "/") -> "ThreadController":
        @self.router.get(route, tags=self.tags)
        async def get_user_threads(
            user: AuthenticatedUser = Security(self.auth),
            t: LocaleHandler = Depends(use_locale),
        ) -> List[ThreadResponse]:
            """
            Returns all threads that the authenticated user is a member of.
            """
            return ThreadService.get_threads_for_user(user.oid, t)

        return self

    def create_thread(self, route: str = "/") -> "ThreadController":
        @self.router.post(route, tags=self.tags)
        async def create_thread(
            req: CreateThreadRequest,
            user: AuthenticatedUser = Security(self.auth),
            t: LocaleHandler = Depends(use_locale),
        ) -> ThreadResponse:
            """
            Creates a new thread with the specified name, users, and agents.
            Automatically adds the authenticated user if not already included.
            """
            if user.oid not in req.user_ids:
                req.user_ids.append(user.oid)

            # Todo: Check if all users have access to all agents in thread

            return ThreadService.create_thread(name=req.name, user_ids=req.user_ids, agent_dtos=req.agents, t=t)

        return self

    def get_thread(self, route: str = "/{thread_id}") -> "ThreadController":
        @self.router.get(route, tags=self.tags)
        async def get_thread(
            thread_id: str,
            user: AuthenticatedUser = Security(self.auth),
            t: LocaleHandler = Depends(use_locale),
        ) -> ThreadResponse:
            """
            Retrieves details of a specific thread.
            Raises 403 if the user is not a member of that thread.
            """
            thread = ThreadService.get_thread_by_id(thread_id, t)
            if user.oid not in [u.id for u in thread.users]:
                raise self.not_authorized_to_view_exception
            return thread

        return self

    def add_agent_to_thread(self, route: str = "/{thread_id}/agents") -> "ThreadController":
        @self.router.post(route, tags=self.tags)
        async def add_agent_to_thread(
            thread_id: str,
            req: AddAgentRequest,
            user: AuthenticatedUser = Security(self.auth),
            t: LocaleHandler = Depends(use_locale),
        ) -> ThreadResponse:
            """
            Adds an agent to a specified thread, if the user is a member of that thread.
            """
            thread = ThreadService.get_thread_by_id(thread_id, t)
            if user.oid not in [u.id for u in thread.users]:
                raise self.not_authorized_to_modify_exception

            # TODO: Check if all users have access to new agent

            return ThreadService.add_agent_to_thread(thread_id, req.agent_id, req.agent_class, t)

        return self

    def remove_agent_from_thread(
        self, route: str = "/{thread_id}/agents/{agent_class}/{agent_id}"
    ) -> "ThreadController":
        @self.router.delete(route, tags=self.tags)
        async def remove_agent_from_thread(
            thread_id: str,
            agent_class: str,
            agent_id: str,
            user: AuthenticatedUser = Security(self.auth),
            t: LocaleHandler = Depends(use_locale),
        ) -> ThreadResponse:
            """
            Removes an agent from the thread, if the user is part of that thread.
            """
            thread = ThreadService.get_thread_by_id(thread_id, t)
            if user.oid not in [u.id for u in thread.users]:
                raise self.not_authorized_to_modify_exception

            return ThreadService.remove_agent_from_thread(thread_id, agent_class, agent_id, t)

        return self

    def add_user_to_thread(self, route: str = "/{thread_id}/users") -> "ThreadController":
        @self.router.post(route, tags=self.tags)
        async def add_user_to_thread(
            thread_id: str,
            req: AddUserRequest,
            user: AuthenticatedUser = Security(self.auth),
            t: LocaleHandler = Depends(use_locale),
        ) -> ThreadResponse:
            """
            Adds another user to the thread, provided the current user is a member of the thread.
            """
            thread = ThreadService.get_thread_by_id(thread_id, t)
            if user.oid not in [u.id for u in thread.users]:
                raise self.not_authorized_to_modify_exception

            # TODO: Check if new users has access to all agents in thread

            return ThreadService.add_user_to_thread(thread_id, req.user_id, t)

        return self

    def remove_user_from_thread(self, route: str = "/{thread_id}/users/{remove_user_id}") -> "ThreadController":
        @self.router.delete(route, tags=self.tags)
        async def remove_user_from_thread(
            thread_id: str,
            remove_user_id: str,
            user: AuthenticatedUser = Security(self.auth),
            t: LocaleHandler = Depends(use_locale),
        ) -> ThreadResponse:
            """
            Removes a user from the thread if the authenticated user is a member of the thread.
            """
            thread = ThreadService.get_thread_by_id(thread_id, t)
            if user.oid not in [u.id for u in thread.users]:
                raise self.not_authorized_to_modify_exception

            return ThreadService.remove_user_from_thread(thread_id, remove_user_id, t)

        return self
