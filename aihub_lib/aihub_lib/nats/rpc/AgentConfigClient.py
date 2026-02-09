from typing import Annotated, Any

from nats.aio.client import Client as NATS

from aihub_lib.nats.requester.NCRequester import NCRequester
from aihub_lib.nats.rpc.models import FetchAgentConfigRequest, FetchAgentConfigResponse
from aihub_lib.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager


class AgentConfigClient:
    """
    High-level client for fetching agent configurations via NATS RPC.

    This client provides a simple interface for agents to fetch their configurations
    from the API service at runtime, decoupling config management from event payloads.

    ### Example Usage:
    ```python
    client = AgentConfigClient(nc)
    config = await client.fetch_config("RAGAgent", "default")
    ```

    ### Subject Pattern:
    Requests are sent to: `aihub.rpc.config.agent.{agent_class}.{agent_id}`
    (managed by AgentTopicManager.get_agent_config_rpc_subject)
    """

    def __init__(
        self,
        nc: Annotated[NATS, "NATS client"],
        timeout_ms: Annotated[int, "Request timeout in milliseconds"] = 5000,
    ):
        self._requester: NCRequester[FetchAgentConfigRequest, FetchAgentConfigResponse] = NCRequester(
            name="AgentConfig",
            nc=nc,
            response_cls=FetchAgentConfigResponse,
            default_timeout_ms=timeout_ms,
        )
        self._topic_manager = AgentTopicManager()

    async def fetch_config(
        self,
        agent_class: str,
        agent_id: str,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """
        Fetch configuration for an agent instance.
        """
        subject = self._topic_manager.get_agent_config_rpc_subject(agent_class, agent_id)

        response = await self._requester.request(
            FetchAgentConfigRequest(agent_class=agent_class, agent_id=agent_id),
            subject=subject,
            timeout_ms=timeout_ms,
        )

        if not response.found:
            raise ValueError(f"Config not found for {agent_class}/{agent_id}: {response.error}")

        return response.config
