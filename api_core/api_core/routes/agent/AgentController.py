from typing import Callable, Any, List, Annotated

from fastapi import Depends, HTTPException
from nats.aio.client import Client as NATS

from api_core.auth.AuthenticatedUser import AuthenticatedUser
from api_core.nats.dependencies.use_nats import use_nats
from api_core.routes.Controller import Controller
from api_core.routes.agent.AgentService import AgentService
from api_core.routes.agent.dto.AgentDTO import AgentDTO


class AgentController(Controller):

    def __init__(self, route: str = "/agent", auth: Callable[..., Any] = None):
        super().__init__(route, auth)

    def discover_agents(self, route: str = "/discover") -> "AgentController":
        @self.router.get(route)
        async def discover_agents(
                nc: Annotated[NATS, Depends(use_nats)],
                user: AuthenticatedUser = Depends(self.auth),
        ) -> List[AgentDTO]:
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
            if not user.has_access_to_agent(agent_class, agent_id):
                raise HTTPException(status_code=403, detail="User does not have access to agent.")
            return await AgentService.get_agent(nc, agent_class, agent_id)
        return self