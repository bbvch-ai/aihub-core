from typing import Annotated, Any, Callable, List

from fastapi import Depends, HTTPException
from nats.aio.client import Client as NATS

from aihub_api.routes.thread.ThreadService import ThreadService
from aihub_api.routes.thread.dto.AddAgentRequest import AddAgentRequest
from aihub_api.routes.thread.dto.AddUserRequest import AddUserRequest
from aihub_api.routes.thread.dto.CreateThreadRequest import CreateThreadRequest
from aihub_api.routes.thread.dto.ThreadResponse import ThreadResponse
from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.nats.dependencies.use_nats import use_nats
from aihub_lib.routes.Controller import Controller


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

    not_authorized_to_view_exception = HTTPException(status_code=403, detail="Not authorized to view this thread")
    not_authorized_to_modify_exception = HTTPException(status_code=403, detail="Not authorized to modify this thread")

    def __init__(self, route: str = "/thread", auth: Callable[..., Any] = None):
        super().__init__(route, auth)

    def get_user_threads(self, route: str = "/") -> "ThreadController":
        @self.router.get(route)
        async def list_user_threads(
            nc: Annotated[NATS, Depends(use_nats)],
            user: AuthenticatedUser = Depends(self.auth),
        ) -> List[ThreadResponse]:
            """
            Returns all threads that the authenticated user is a member of.
            """
            return await ThreadService.get_threads_for_user(nc, user.oid)

        return self

    def create_thread(self, route: str = "/{thread_id}") -> "ThreadController":
        @self.router.post(route)
        async def create_thread(
            req: CreateThreadRequest,
            nc: Annotated[NATS, Depends(use_nats)],
            user: AuthenticatedUser = Depends(self.auth),
        ) -> ThreadResponse:
            """
            Creates a new thread with the specified name, users, and agents.
            Automatically adds the authenticated user if not already included.
            """
            if user.oid not in req.user_ids:
                req.user_ids.append(user.oid)

            return await ThreadService.create_thread(nc, name=req.name, user_ids=req.user_ids, agent_dtos=req.agents)

        return self

    def get_thread(self, route: str = "/{thread_id}") -> "ThreadController":
        @self.router.get(route)
        async def get_thread(
            thread_id: str,
            nc: Annotated[NATS, Depends(use_nats)],
            user: AuthenticatedUser = Depends(self.auth),
        ) -> ThreadResponse:
            """
            Retrieves details of a specific thread.
            Raises 403 if the user is not a member of that thread.
            """
            thread = await ThreadService.get_thread_by_id(nc, thread_id)
            if user.oid not in [u.user_id for u in thread.users]:
                raise self.not_authorized_to_view_exception
            return thread

        return self

    def add_agent_to_thread(self, route: str = "/{thread_id}/agents") -> "ThreadController":
        @self.router.post(route)
        async def add_agent_to_thread(
            thread_id: str,
            req: AddAgentRequest,
            nc: Annotated[NATS, Depends(use_nats)],
            user: AuthenticatedUser = Depends(self.auth),
        ) -> ThreadResponse:
            """
            Adds an agent to a specified thread, if the user is a member of that thread.
            """
            thread = await ThreadService.get_thread_by_id(nc, thread_id)
            if user.oid not in [u.user_id for u in thread.users]:
                raise self.not_authorized_to_modify_exception

            return await ThreadService.add_agent_to_thread(nc, thread_id, req.agent_id, req.agent_class)

        return self

    def remove_agent_from_thread(
        self, route: str = "/{thread_id}/agents/{agent_class}/{agent_id}"
    ) -> "ThreadController":
        @self.router.delete(route)
        async def remove_agent_from_thread(
            thread_id: str,
            agent_class: str,
            agent_id: str,
            nc: Annotated[NATS, Depends(use_nats)],
            user: AuthenticatedUser = Depends(self.auth),
        ) -> ThreadResponse:
            """
            Removes an agent from the thread, if the user is part of that thread.
            """
            thread = await ThreadService.get_thread_by_id(nc, thread_id)
            if user.oid not in [u.user_id for u in thread.users]:
                raise self.not_authorized_to_modify_exception

            return await ThreadService.remove_agent_from_thread(nc, thread_id, agent_class, agent_id)

        return self

    def add_user_to_thread(self, route: str = "/{thread_id}/users") -> "ThreadController":
        @self.router.post(route)
        async def add_user_to_thread(
            thread_id: str,
            req: AddUserRequest,
            nc: Annotated[NATS, Depends(use_nats)],
            user: AuthenticatedUser = Depends(self.auth),
        ) -> ThreadResponse:
            """
            Adds another user to the thread, provided the current user is a member of the thread.
            """
            thread = await ThreadService.get_thread_by_id(nc, thread_id)
            if user.oid not in [u.user_id for u in thread.users]:
                raise self.not_authorized_to_modify_exception

            return await ThreadService.add_user_to_thread(nc, thread_id, req.user_id)

        return self

    def remove_user_from_thread(self, route: str = "/{thread_id}/users/{remove_user_id}") -> "ThreadController":
        @self.router.delete(route)
        async def remove_user_from_thread(
            thread_id: str,
            remove_user_id: str,
            nc: Annotated[NATS, Depends(use_nats)],
            user: AuthenticatedUser = Depends(self.auth),
        ) -> ThreadResponse:
            """
            Removes a user from the thread if the authenticated user is a member of the thread.
            """
            thread = await ThreadService.get_thread_by_id(nc, thread_id)
            if user.oid not in [u.user_id for u in thread.users]:
                raise self.not_authorized_to_modify_exception

            return await ThreadService.remove_user_from_thread(nc, thread_id, remove_user_id)

        return self
