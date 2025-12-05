import logging

from aihub_lib.nats.events import ExpertInTheLoopRequestEvent
from aihub_lib.nats.topics import AgentInstanceTopic
from aihub_lib.persistence.expert.ExpertQuestionEntity import (
    ExpertQuestionEntity,
    RequestingAgent,
    RequestingUser,
)

logger = logging.getLogger(__name__)


async def persist_expert_question(event: ExpertInTheLoopRequestEvent, topic: AgentInstanceTopic) -> None:
    """
    Persists ExpertInTheLoopRequestEvent to MongoDB.

    This handler is called by the NATS subscriber whenever an agent emits an
    ExpertInTheLoopRequestEvent. It extracts the relevant data from the event
    and topic, then persists it to the expert_questions collection.

    The agent no longer writes directly to MongoDB - this decouples agents from
    database connections and follows the pattern where the API handles all persistence.
    """
    requesting_user = RequestingUser(
        user_id=event.user.id,
        user_name=event.user.name,
        email=getattr(event.user, "email", None),
    )
    requesting_agent = RequestingAgent(
        agent_class=topic.agent_class,
        agent_id=topic.agent_id,
        thread_id=topic.thread_id,
        run_id=topic.run_id,
    )

    ExpertQuestionEntity.create_question(
        question=event.question,
        requesting_user=requesting_user,
        requesting_agent=requesting_agent,
        topic_data=event.topic.model_dump(),
        context=event.context,
        expert_group=event.expert_group,
        priority=event.priority,
        locale=event.locale,
    )

    logger.info(
        "Persisted expert question from agent %s/%s in thread %s",
        topic.agent_class,
        topic.agent_id,
        topic.thread_id,
    )
