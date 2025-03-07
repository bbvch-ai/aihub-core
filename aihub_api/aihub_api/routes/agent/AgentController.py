import time
from typing import Annotated, List, Type

from fastapi.params import Query

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.dependencies.use_nats import use_nats
from aihub_lib.nats.events import StartEvent, StopEvent
from aihub_lib.routes.Controller import Controller
from aihub_lib.sockets.receiver.dependencies.use_ws_receiver import use_ws_receiver
from aihub_lib.sockets.receiver.WebSocketReceiver import WebSocketReceiver
from bson import ObjectId
from fastapi import Body, Depends, HTTPException, Security
from nats.aio.client import Client as NATS
from stringcase import snakecase

from aihub_api.events.create_input_model import create_input_model
from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.routes.agent.AgentService import AgentService
from aihub_api.routes.agent.dto.AgentDTO import AgentDTO


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

    def __init__(self, route: str = "/agent", auth: AuthHandler | None = None):
        super().__init__(route, auth)

    def discover_agents(self, route: str = "/discover") -> "AgentController":
        @self.router.get(route)
        async def discover_agents(
            nc: Annotated[NATS, Depends(use_nats)],
            user: AuthenticatedUser = Security(self.auth),
        ) -> List[AgentDTO]:
            """
            Retrieve a list of all discovered agents. Filters out agents the user cannot access.
            """
            agents = await AgentService.discover_agents(nc)
            return [agent for agent in agents if user.has_access_to_agent(agent.agent_class, agent.agent_id)]

        return self

    def get_agent(self, route: str = "/{agent_class}/{agent_id}") -> "AgentController":
        @self.router.get(route)
        async def get_agent(
            nc: Annotated[NATS, Depends(use_nats)],
            agent_class: str,
            agent_id: str,
            user: AuthenticatedUser = Security(self.auth),
        ) -> AgentDTO:
            """
            Retrieve details for a specific agent. Raises 403 if the user lacks access.
            """
            if not user.has_access_to_agent(agent_class, agent_id):
                raise HTTPException(status_code=403, detail="User does not have access to this agent.")
            return await AgentService.get_agent(nc, agent_class, agent_id)

        return self

    def send_event_to(
        self, agent_class, agent_id, start_event_type: Type[StartEvent], stop_event_type: Type[StopEvent]
    ) -> "AgentController":
        """
        Generates an endpoint to which an StartEvent can be send and the endpoint answers with the agents
        StopEvent.
        """
        agent_class_name = snakecase(agent_class)
        agent_class_id = snakecase(agent_id)
        name = f"send_event_to_{agent_class_name}_{agent_class_id}"
        start_event_input_type = create_input_model(start_event_type)

        @self.router.post(f"/{agent_class_name}/{agent_class_id}/send_event", name=name)
        async def send_event(
            nc: Annotated[NATS, Depends(use_nats)],
            start_event_input: Annotated[start_event_input_type, Body],
            ws_receiver: Annotated[WebSocketReceiver, Depends(use_ws_receiver)],
            user: AuthenticatedUser = Security(self.auth),
            thread_id: Annotated[str, Query(pattern="/^[a-f\d]{24}$/i")] = None,
            display_id: Annotated[str, Query(pattern="/^[a-f\d]{24}$/i")] = None,
            t: LocaleHandler = Depends(use_locale),
        ) -> stop_event_type:
            """
            Send an event to a specific agent. Raises 403 if the user lacks access.
            """
            if not user.has_access_to_agent(agent_class, agent_id):
                raise HTTPException(status_code=403, detail="User does not have access to this agent.")
            start_event = start_event_type(
                event_id=str(ObjectId()),
                created_at=time.time_ns(),
                **start_event_input.model_dump(),
                user=user,
                locale=t.locale,
            )
            return await AgentService.send_event(nc, ws_receiver, user, start_event, agent_class, agent_id, thread_id, display_id)

        return self
