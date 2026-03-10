"""
NATS RPC responder for agent configuration requests.

This module provides a responder that allows agents to fetch their configurations
at runtime via NATS request-reply, decoupling config management from event payloads.
"""

import logging
from typing import Annotated

from nats.aio.client import Client as NATS
from swiss_ai_hub.core.nats.responder.NCResponder import NCResponder
from swiss_ai_hub.core.nats.rpc.models import FetchAgentConfigRequest, FetchAgentConfigResponse
from swiss_ai_hub.core.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager

from swiss_ai_hub.api.routes.agent.AgentService import AgentService

logger = logging.getLogger(__name__)


class AgentConfigResponder:
    """
    NATS RPC responder for agent configuration requests.

    Listens on `aihub.rpc.config.agent.*.*` and responds with agent configurations
    fetched from the database.

    Subject pattern is managed by AgentTopicManager.get_agent_config_rpc_subject().

    ### Example Usage:
    ```python
    responder = AgentConfigResponder(nc)
    await responder.start()
    # ... on shutdown
    await responder.stop()
    ```
    """

    def __init__(
        self,
        nc: Annotated[NATS, "NATS client"],
    ):
        self._topic_manager = AgentTopicManager()
        self._subject = self._topic_manager.get_agent_config_rpc_subject("*", "*")
        self._responder: NCResponder[FetchAgentConfigRequest, FetchAgentConfigResponse] = NCResponder(
            name="AgentConfig",
            nc=nc,
            subject=self._subject,
            request_cls=FetchAgentConfigRequest,
            handler=self._handle_request,
        )

    async def start(self) -> None:
        """Start listening for agent config requests."""
        logger.info(f"AgentConfigResponder starting on {self._subject}")
        await self._responder.start()

    async def stop(self) -> None:
        """Stop listening for requests."""
        logger.info("AgentConfigResponder stopping")
        await self._responder.stop()

    async def _handle_request(
        self,
        request: FetchAgentConfigRequest,
        subject: str,
    ) -> FetchAgentConfigResponse:
        """
        Handle a config fetch request by looking up the agent's configuration.
        """
        logger.debug(f"Handling config request for {request.agent_class}/{request.agent_id}")

        try:
            config = await AgentService.get_agent_configuration(
                agent_class=request.agent_class,
                agent_id=request.agent_id,
            )

            return FetchAgentConfigResponse(
                agent_class=request.agent_class,
                agent_id=request.agent_id,
                config=config,
                found=True,
            )

        except Exception as e:
            logger.exception(f"Error fetching config for {request.agent_class}/{request.agent_id}: {e}")
            return FetchAgentConfigResponse(
                agent_class=request.agent_class,
                agent_id=request.agent_id,
                config={},
                found=False,
                error=str(e),
            )
