from typing import Annotated, List

from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.dependencies.use_nats import use_nats
from aihub_lib.routes.Controller import Controller
from fastapi import Depends, HTTPException, Security
from nats.aio.client import Client as NATS

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
    name = LocaleString(en="Agents")
    description = LocaleString(en="Interacts with agents")
    icon = "meteor-icons:robot"

    def __init__(self, route: str = "/agent", auth: AuthHandler | None = None, is_admin_only=True):
        super().__init__(route, auth, is_admin_only=is_admin_only)

    def discover_agents(self, route: str = "/discover") -> "AgentController":
        @self.router.get(route, tags=self.tags)
        async def discover_agents(
            nc: Annotated[NATS, Depends(use_nats)],
            user: AuthenticatedUser = Security(self.auth),
                t: LocaleHandler = Depends(use_locale),
        ) -> List[AgentDTO]:
            """
            Retrieve a list of all discovered agents. Filters out agents the user cannot access.
            """
            agents = await AgentService.discover_agents(nc, t)
            return [agent for agent in agents if user.has_access_to_agent(agent.agent_class, agent.agent_id)]

        return self

    def get_agent(self, route: str = "/{agent_class}/{agent_id}") -> "AgentController":
        @self.router.get(route, tags=self.tags)
        async def get_agent(
            nc: Annotated[NATS, Depends(use_nats)],
            agent_class: str,
            agent_id: str,
            user: AuthenticatedUser = Security(self.auth),
            t: LocaleHandler = Depends(use_locale),
        ) -> AgentDTO:
            """
            Retrieve details for a specific agent. Raises 403 if the user lacks access.
            """
            if not user.has_access_to_agent(agent_class, agent_id):
                raise HTTPException(status_code=403, detail="User does not have access to this agent.")
            return await AgentService.get_agent(nc, agent_class, agent_id, t)

        return self
