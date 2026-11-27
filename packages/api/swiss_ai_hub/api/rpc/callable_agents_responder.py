import logging
from typing import Annotated

from nats.aio.client import Client as NATS
from swiss_ai_hub.core.persistence.agents import AgentClassEntity
from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument
from swiss_ai_hub.core.responder import NCResponder
from swiss_ai_hub.core.rpc import CallableAgent, ListCallableAgentsRequest, ListCallableAgentsResponse
from swiss_ai_hub.core.topic_managers import AgentTopicManager

logger = logging.getLogger(__name__)


class CallableAgentsResponder:
    """
    Answers an agent asking which agent profiles are online, so its model can be offered them as tools.

    Every online profile is returned; the asking agent narrows them to what its user may use, since it holds the
    user's access rules for the run already.
    """

    def __init__(self, nc: Annotated[NATS, "NATS client"]):
        self._subject = AgentTopicManager().get_callable_agents_rpc_subject()
        self._responder: NCResponder[ListCallableAgentsRequest, ListCallableAgentsResponse] = NCResponder(
            name="CallableAgents",
            nc=nc,
            subject=self._subject,
            request_cls=ListCallableAgentsRequest,
            handler=self._handle_request,
        )

    async def start(self) -> None:
        logger.info(f"CallableAgentsResponder starting on {self._subject}")
        await self._responder.start()

    async def stop(self) -> None:
        await self._responder.stop()

    @staticmethod
    async def _handle_request(request: ListCallableAgentsRequest, subject: str) -> ListCallableAgentsResponse:
        return ListCallableAgentsResponse(agents=await CallableAgentsResponder.online_agents())

    @staticmethod
    async def online_agents() -> list[CallableAgent]:
        threshold = await AgentClassEntity.online_threshold()
        agents = []
        for class_entity in await AgentClassEntity.get_all():
            if not class_entity.is_online_since(threshold):
                continue
            for config in await AgentConfigEntityDocument.find_for_name(agent_class=class_entity.agent_class):
                agents.append(
                    CallableAgent(
                        agent_class=class_entity.agent_class,
                        agent_id=config.agent_id,
                        name=config.name,
                        description=config.description,
                        is_conversational=class_entity.is_conversational,
                        start_events=[spec.to_specs() for spec in class_entity.start_events],
                    )
                )
        return agents
