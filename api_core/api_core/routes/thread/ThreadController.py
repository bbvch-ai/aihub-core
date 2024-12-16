from typing import Callable, Any
from fastapi import APIRouter, Depends, HTTPException

from api_core.auth.AuthenticatedUser import AuthenticatedUser
from api_core.routes.Controller import Controller
from api_core.routes.thread.dto.AddAgentRequest import AddAgentRequest
from api_core.routes.thread.dto.AddUserRequest import AddUserRequest
from api_core.routes.thread.dto.CreateThreadRequest import CreateThreadRequest
from api_core.routes.thread.dto.ThreadListResponse import ThreadListResponse
from api_core.routes.thread.dto.ThreadResponse import ThreadResponse
from api_core.routes.thread.ThreadService import ThreadService


class ThreadController(Controller):
    
    def __init__(self, route: str = "/thread", user_auth_strategy: Callable[..., Any] = None):
        super().__init__(route, user_auth_strategy)


    def get_user_threads(self, route: str = "/") -> "ThreadController":
        @self.router.get(route)
        async def list_user_threads(user: AuthenticatedUser = Depends(self.user_auth_strategy)) -> ThreadListResponse:
            threads = ThreadService.get_threads_for_user(user.oid)
            return ThreadListResponse(
                threads=[ThreadResponse.from_thread_entity(t) for t in threads]
            )
        return self


    def create_thread(self, route: str = "/{thread_id}") -> "ThreadController":
        @self.router.post(route)
        async def create_thread(
                req: CreateThreadRequest,
                user: AuthenticatedUser = Depends(self.user_auth_strategy),
        ) -> ThreadResponse:
            if user.oid not in req.user_ids:
                req.user_ids.append(user.oid)

            thread = ThreadService.create_thread(name=req.name, user_ids=req.user_ids, agent_dtos=req.agents)
            return ThreadResponse.from_thread_entity(thread)
        return self

    def get_thread(self, route: str = "/{thread_id}") -> "ThreadController":

        @self.router.get("/{thread_id}")
        async def get_thread(thread_id: str, user: AuthenticatedUser = Depends(self.user_auth_strategy)) -> ThreadResponse:
            thread = ThreadService.get_thread_by_id(thread_id)
            if user.oid not in [u.user_id for u in thread.users]:
                raise HTTPException(status_code=403, detail="Not authorized to view this thread")
            return ThreadResponse.from_thread_entity(thread)

        return self

    def add_agent_to_thread(self, route: str = "/{thread_id}/agents") -> "ThreadController":
        @self.router.post(route)
        async def add_agent_to_thread(thread_id: str, req: AddAgentRequest,
                                      user: AuthenticatedUser = Depends(self.user_auth_strategy)) -> ThreadResponse:
            thread = ThreadService.get_thread_by_id(thread_id)
            if user.oid not in [u.user_id for u in thread.users]:
                raise HTTPException(status_code=403, detail="Not authorized to modify this thread")

            thread = ThreadService.add_agent_to_thread(thread_id, req.agent_id, req.agent_class)
            return ThreadResponse.from_thread_entity(thread)
        return self

    def remove_agent_from_thread(self, route: str = "/{thread_id}/agents/{agent_id}") -> "ThreadController":
        @self.router.delete(route)
        async def remove_agent_from_thread(thread_id: str, agent_id: str, user: AuthenticatedUser = Depends(
            self.user_auth_strategy)) -> ThreadResponse:
            thread = ThreadService.get_thread_by_id(thread_id)
            if user.oid not in [u.user_id for u in thread.users]:
                raise HTTPException(status_code=403, detail="Not authorized to modify this thread")

            thread = ThreadService.remove_agent_from_thread(thread_id, agent_id)
            return ThreadResponse.from_thread_entity(thread)
        return self

    def add_user_to_thread(self, route: str = "/{thread_id}/users") -> "ThreadController":
        @self.router.post(route)
        async def add_user_to_thread(thread_id: str, req: AddUserRequest,
                                     user: AuthenticatedUser = Depends(self.user_auth_strategy)) -> ThreadResponse:
            thread = ThreadService.get_thread_by_id(thread_id)
            if user.oid not in [u.user_id for u in thread.users]:
                raise HTTPException(status_code=403, detail="Not authorized to modify this thread")

            thread = ThreadService.add_user_to_thread(thread_id, req.user_id)
            return ThreadResponse.from_thread_entity(thread)
        return self

    def remove_user_from_thread(self, route: str = "/{thread_id}/users/{remove_user_id}") -> "ThreadController":

        @self.router.delete(route)
        async def remove_user_from_thread(thread_id: str, remove_user_id: str, user: AuthenticatedUser = Depends(self.user_auth_strategy)) -> ThreadResponse:
            thread = ThreadService.get_thread_by_id(thread_id)
            if user.oid not in [u.user_id for u in thread.users]:
                raise HTTPException(status_code=403, detail="Not authorized to modify this thread")

            thread = ThreadService.remove_user_from_thread(thread_id, remove_user_id)
            return ThreadResponse.from_thread_entity(thread)

        return self



