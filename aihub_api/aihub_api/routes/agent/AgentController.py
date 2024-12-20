from typing import Callable, Any, List, Annotated

from fastapi import Depends, HTTPException
from nats.aio.client import Client as NATS

from aihub_api.auth.AuthenticatedUser import AuthenticatedUser
from aihub_api.nats.dependencies.use_nats import use_nats
from aihub_api.routes.Controller import Controller
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

    def __init__(self, route: str = "/agent", auth: Callable[..., Any] = None):
        super().__init__(route, auth)

    def discover_agents(self, route: str = "/discover") -> "AgentController":
        @self.router.get(route)
        async def discover_agents(
                nc: Annotated[NATS, Depends(use_nats)],
                user: AuthenticatedUser = Depends(self.auth),
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
                user: AuthenticatedUser = Depends(self.auth),
        ) -> AgentDTO:
            """
            Retrieve details for a specific agent. Raises 403 if the user lacks access.
            """
            if not user.has_access_to_agent(agent_class, agent_id):
                raise HTTPException(status_code=403, detail="User does not have access to this agent.")
            return await AgentService.get_agent(nc, agent_class, agent_id)
        return self
