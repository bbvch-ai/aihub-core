import time
from typing import Annotated, List, Optional, Type

from aihub_lib.auth.access.AccessChecker import AccessChecker
from aihub_lib.auth.access.AccessLevel import AccessLevel
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.dependencies.use_nats import use_nats
from aihub_lib.nats.distributor.dependencies.use_external_event_distributor import use_external_event_distributor
from aihub_lib.nats.distributor.ExternalAgentEventDistributor import ExternalAgentEventDistributor
from aihub_lib.nats.events import ExceptionEvent, StartEvent, StopEvent
from aihub_lib.routes.Controller import Controller
from bson import ObjectId
from fastapi import Body, Depends, HTTPException, Security
from fastapi.params import Query
from nats.aio.client import Client as NATS
from stringcase import snakecase

from aihub_api.events.create_input_model import create_input_model
from aihub_api.events.create_output_model import create_output_model
from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.pagination.type.PageNumber import PageNumber
from aihub_api.pagination.type.PageSize import PageSize
from aihub_api.routes.agent.AgentService import AgentService
from aihub_api.routes.agent.dto.AgentDTO import AgentDTO
from aihub_api.routes.thread.dto.PaginatedThreadsResponse import PaginatedThreadsResponse


class AgentController(Controller):
    """
    A controller managing endpoints related to agents, including discovery and retrieval.

    ### Why AgentController?
    The AgentController exposes routes for:
    - Discovering all available agents.
    - Retrieving detailed information about a specific agent.

    It leverages the `AgentService` to interact with NATS-based discovery mechanisms,
    and applies an authentication dependency to ensure that only authorized users
    can access certain agents.

    ### Endpoints
    - `GET /discover`: Returns a list of all discovered agents. Applies user access checks.
    - `GET /{agent_class}/{agent_id}`: Returns details of a specific agent, ensuring the user is authorized.

    ### Authentication
    If an `auth` dependency is provided, routes use that for authentication.
    Otherwise, it defaults to no-auth, meaning all agents are accessible.

    ### Usage
    ```python
    app = FastAPI()
    AgentController()
        .discover_agents()
        .get_agent()
        .mount(app)
    ```

    This sets up `/agent/discover` and `/agent/{agent_class}/{agent_id}` endpoints.
    """

    name = LocaleString(en="Agents")
    description = LocaleString(en="Interacts with agents")
    icon = "meteor-icons:robot"

    def __init__(
        self, *, auth: AuthHandler, route: str = "/agents", additionally_required_permission: Optional[str] = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def get_agents(self, route: str = "/") -> "AgentController":
        @self.router.get(route, tags=self.tags)
        async def get_agents(
            nc: Annotated[NATS, Depends(use_nats)],
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.agent.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> List[AgentDTO]:
            """
            Retrieve a list of all agents, both online (discoverable) and offline (not discoverable).
            """
            agents = await AgentService.get_agents(nc, t)
            return [
                agent
                for agent in agents
                if AccessChecker.from_user(user).has_access_to_agent(agent.agent_class, agent.agent_id)
            ]

        return self

    def discover_agents(self, route: str = "/discover") -> "AgentController":
        @self.router.get(route, tags=self.tags)
        async def discover_agents(
            nc: Annotated[NATS, Depends(use_nats)],
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.agent.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> List[AgentDTO]:
            """
            Retrieve a list of all online (discoverable) agents. Filters out agents the user cannot access.
            """
            agents = await AgentService.discover_agents(nc, t)
            return [
                agent
                for agent in agents
                if AccessChecker.from_user(user).has_access_to_agent(agent.agent_class, agent.agent_id)
            ]

        return self

    def get_agent(self, route: str = "/{agent_class}/{agent_id}") -> "AgentController":
        @self.router.get(route, tags=self.tags)
        async def get_agent(
            nc: Annotated[NATS, Depends(use_nats)],
            agent_class: str,
            agent_id: str,
            _: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.user.agent.{agent_class}.{agent_id}"))
            ],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> AgentDTO:
            """
            Retrieve details for a specific agent. Raises 403 if the user lacks access.
            """
            return await AgentService.get_agent(nc, agent_class, agent_id, t)

        return self

    def get_agent_threads(self, route: str = "/{agent_class}/{agent_id}/threads") -> "AgentController":
        @self.router.get(route, tags=self.tags)
        async def get_agent_threads(
            agent_class: str,
            agent_id: str,
            user: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.user.agent.{agent_class}.{agent_id}"))
            ],
            t: Annotated[LocaleHandler, Depends(use_locale)],
            page: PageNumber = 1,
            page_size: PageSize = 20,
        ) -> PaginatedThreadsResponse:
            """
            Retrieve all threads that a specific agent is part of. Raises 403 if the user lacks access.
            """
            access_level = AccessChecker.from_user(user).has_access_to_agent(agent_class, agent_id)
            total, threads = await AgentService.get_paginated_agent_threads(
                agent_class,
                agent_id,
                t=t,
                page=page,
                page_size=page_size,
                user_id=None if access_level == AccessLevel.ACCESS_ADMIN else user.id,
            )

            total_pages = (total + page_size - 1) // page_size

            return PaginatedThreadsResponse(
                threads=threads, total=total, page=page, page_size=page_size, total_pages=total_pages
            )

        return self

    def send_event_to(
        self,
        agent_class,
        agent_id,
        start_event_class: Type[StartEvent],
        stop_event_class: Type[StopEvent],
        route_postfix="/send_event",
    ) -> "AgentController":
        """
        Generates an endpoint to which an StartEvent can be send and the endpoint answers with the agents
        StopEvent.
        """
        agent_class_name = snakecase(agent_class)
        agent_id = snakecase(agent_id)
        postfix = snakecase(route_postfix.replace("/", "", 1).replace("/", "_"))
        name = f"send_event_to_{agent_class_name}_{agent_id}_{postfix}"
        start_event_input_type = create_input_model(start_event_class)
        stop_event_output_type = create_output_model(stop_event_class)

        if route_postfix.startswith("/"):
            route_postfix = route_postfix[1:]
        if route_postfix.endswith("/"):
            route_postfix = route_postfix[:-1]

        @self.router.post(f"/{agent_class_name}/{agent_id}/{route_postfix}", name=name, tags=[agent_class])
        async def send_event(
            nc: Annotated[NATS, Depends(use_nats)],
            start_event_input: Annotated[start_event_input_type, Body],
            external_event_distributor: Annotated[
                ExternalAgentEventDistributor, Depends(use_external_event_distributor)
            ],
            user: Annotated[
                UserIdentity, Security(self.user_with_permission(f"aihub.user.agent.{agent_class}.{agent_id}"))
            ],
            t: Annotated[LocaleHandler, Depends(use_locale)],
            thread_id: Annotated[str, Query(pattern="/^[a-f\d]{24}$/i")] = None,
            display_id: Annotated[str, Query(pattern="/^[a-f\d]{24}$/i")] = None,
        ) -> stop_event_output_type:
            """
            Send an event to a specific agent. Raises 403 if the user lacks access.
            """
            start_event = start_event_class(
                event_id=str(ObjectId()),
                created_at=time.time_ns(),
                user=user,
                **start_event_input.model_dump(),
                locale=t.locale,
            )
            stop_event = await AgentService.send_event(
                nc, external_event_distributor, user, start_event, agent_class, agent_id, thread_id, display_id
            )

            if isinstance(stop_event, ExceptionEvent):
                raise HTTPException(status_code=stop_event.http_status_code, detail=stop_event.message)

            return stop_event

        return self
