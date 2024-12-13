from typing import Callable, Any, List

from fastapi import Depends, Request, HTTPException

from api_core.auth.AuthenticatedUser import AuthenticatedUser
from api_core.routes.Controller import Controller
from api_core.routes.agent.AgentService import AgentService
from api_core.routes.agent.dto.AgentDTO import AgentDTO


class AgentController(Controller):

    def __init__(self, route: str = "/agent", user_auth_strategy: Callable[..., Any] = None):
        super().__init__(route, user_auth_strategy)

    def discover_agents(self, route: str = "/discover") -> "AgentController":
        @self.router.get(route)
        async def discover_agents(
                request: Request,
                user: AuthenticatedUser = Depends(self.user_auth_strategy),
        ) -> List[AgentDTO]:
            agents = await AgentService.discover_agents(request.app.state.nc)
            return [agent for agent in agents if user.has_access_to_agent(agent.agent_class, agent.agent_id)]
        return self

    def get_agent(self, route: str = "/{agent_class}/{agent_id}") -> "AgentController":
        @self.router.get(route)
        async def get_agent(
                request: Request,
                agent_class: str,
                agent_id: str,
                user: AuthenticatedUser = Depends(self.user_auth_strategy),
        ) -> AgentDTO:
            if not user.has_access_to_agent(agent_class, agent_id):
                raise HTTPException(status_code=403, detail="User does not have access to agent.")
            return await AgentService.get_agent(request.app.state.nc, agent_class, agent_id)
        return self