from typing import Callable, Any, List, Annotated
from fastapi import Depends, HTTPException
from nats.aio.client import Client as NATS

from api_core.auth.AuthenticatedUser import AuthenticatedUser
from api_core.nats.dependencies.use_nats import use_nats
from api_core.routes.Controller import Controller
from api_core.routes.thread.dto.AddAgentRequest import AddAgentRequest
from api_core.routes.thread.dto.AddUserRequest import AddUserRequest
from api_core.routes.thread.dto.CreateThreadRequest import CreateThreadRequest
from api_core.routes.thread.dto.ThreadResponse import ThreadResponse
from api_core.routes.thread.ThreadService import ThreadService


class ThreadController(Controller):

    def __init__(self, route: str = "/thread", auth: Callable[..., Any] = None):
        super().__init__(route, auth)

    def get_user_threads(self, route: str = "/") -> "ThreadController":
        @self.router.get(route)
        async def list_user_threads(
                nc: Annotated[NATS, Depends(use_nats)],
                user: AuthenticatedUser = Depends(self.auth),
        ) -> List[ThreadResponse]:
            return await ThreadService.get_threads_for_user(nc, user.oid)

        return self

    def create_thread(self, route: str = "/{thread_id}") -> "ThreadController":
        @self.router.post(route)
        async def create_thread(
                req: CreateThreadRequest,
                nc: Annotated[NATS, Depends(use_nats)],
                user: AuthenticatedUser = Depends(self.auth),
        ) -> ThreadResponse:
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
            thread = await ThreadService.get_thread_by_id(nc, thread_id)
            if user.oid not in [u.user_id for u in thread.users]:
                raise HTTPException(status_code=403, detail="Not authorized to view this thread")
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
            thread = await ThreadService.get_thread_by_id(nc, thread_id)
            if user.oid not in [u.user_id for u in thread.users]:
                raise HTTPException(status_code=403, detail="Not authorized to modify this thread")

            return await ThreadService.add_agent_to_thread(nc, thread_id, req.agent_id, req.agent_class)

        return self

    def remove_agent_from_thread(self, route: str = "/{thread_id}/agents/{agent_class}/{agent_id}") -> "ThreadController":
        @self.router.delete(route)
        async def remove_agent_from_thread(
                thread_id: str,
                agent_class: str,
                agent_id: str,
                nc: Annotated[NATS, Depends(use_nats)],
                user: AuthenticatedUser = Depends(self.auth),
        ) -> ThreadResponse:
            thread = await ThreadService.get_thread_by_id(nc, thread_id)
            if user.oid not in [u.user_id for u in thread.users]:
                raise HTTPException(status_code=403, detail="Not authorized to modify this thread")

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
            thread = await ThreadService.get_thread_by_id(nc, thread_id)
            if user.oid not in [u.user_id for u in thread.users]:
                raise HTTPException(status_code=403, detail="Not authorized to modify this thread")

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
            thread = await ThreadService.get_thread_by_id(nc, thread_id)
            if user.oid not in [u.user_id for u in thread.users]:
                raise HTTPException(status_code=403, detail="Not authorized to modify this thread")

            return await ThreadService.remove_user_from_thread(nc, thread_id, remove_user_id)

        return self
