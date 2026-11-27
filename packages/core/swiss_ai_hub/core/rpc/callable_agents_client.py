from typing import Annotated

from nats.aio.client import Client as NATS

from swiss_ai_hub.core.requester.nc_requester import NCRequester
from swiss_ai_hub.core.rpc.models import CallableAgent, ListCallableAgentsRequest, ListCallableAgentsResponse
from swiss_ai_hub.core.topic_managers.agents.agent_topic_manager import AgentTopicManager


class CallableAgentsClient:
    """Asks the API which agent profiles are online, for an agent that offers other agents to its model as tools.

    Agents do not read the agent registry themselves; it lives in the API's documents.
    """

    def __init__(
        self,
        nc: Annotated[NATS, "NATS client"],
        timeout_ms: Annotated[int, "Request timeout in milliseconds"] = 5000,
    ):
        self._requester: NCRequester[ListCallableAgentsRequest, ListCallableAgentsResponse] = NCRequester(
            name="CallableAgents",
            nc=nc,
            response_cls=ListCallableAgentsResponse,
            default_timeout_ms=timeout_ms,
        )
        self._subject = AgentTopicManager().get_callable_agents_rpc_subject()

    async def online_agents(self) -> list[CallableAgent]:
        response = await self._requester.request(ListCallableAgentsRequest(), subject=self._subject)
        return response.agents
