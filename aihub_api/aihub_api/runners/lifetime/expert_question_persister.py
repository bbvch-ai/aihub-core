import logging

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import ExpertInTheLoopRequestEvent
from aihub_lib.nats.topics import AgentInstanceTopic
from aihub_lib.persistence.expert.ExpertGroupEntity import ExpertGroupEntity
from aihub_lib.persistence.expert.ExpertQuestionEntity import (
    ExpertQuestionEntity,
    RequestingAgent,
    RequestingUser,
)
from aihub_lib.persistence.notification.NotificationEntity import NotificationEntity

logger = logging.getLogger(__name__)


async def persist_expert_question(event: ExpertInTheLoopRequestEvent, topic: AgentInstanceTopic) -> None:
    """
    Persists ExpertInTheLoopRequestEvent to MongoDB and notifies relevant experts.

    This handler is called by the NATS subscriber whenever an agent emits an
    ExpertInTheLoopRequestEvent. It:
    1. Persists the question to the expert_questions collection
    2. Looks up the expert group (if specified) and notifies all members

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

    question_entity = ExpertQuestionEntity.create_question(
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

    _notify_experts(question_entity, event)


def _notify_experts(question_entity: ExpertQuestionEntity, event: ExpertInTheLoopRequestEvent) -> None:
    """Creates notifications for all experts in the specified group."""
    expert_group = event.expert_group
    if not expert_group:
        logger.debug("No expert_group specified, skipping expert notifications")
        return

    member_user_ids = ExpertGroupEntity.get_member_user_ids(expert_group)
    if not member_user_ids:
        logger.warning(
            "Expert group '%s' not found or has no members, skipping notifications",
            expert_group,
        )
        return

    user_name = event.user.name or event.user.username or "A user"
    question_preview = event.question[:100] + "..." if len(event.question) > 100 else event.question

    severity = "medium"
    if event.priority in ("high", "urgent"):
        severity = "high"
    elif event.priority == "low":
        severity = "low"

    try:
        NotificationEntity.create_notifications_for_users(
            user_ids=member_user_ids,
            title=LocaleString(
                en="New Expert Question",
                de="Neue Expertenfrage",
                fr="Nouvelle question d'expert",
                it="Nuova domanda dell'esperto",
            ),
            message=LocaleString(
                en=f'{user_name} needs expert help: "{question_preview}"',
                de=f'{user_name} braucht Expertenhilfe: "{question_preview}"',
                fr=f"{user_name} a besoin d'aide d'expert: \"{question_preview}\"",
                it=f'{user_name} ha bisogno di aiuto esperto: "{question_preview}"',
            ),
            notification_type="info",
            severity=severity,
            link=f"/expert/questions/{question_entity.id}",
            notification_group_id=f"expert_question_{question_entity.id}",
        )
        logger.info(
            "Created notifications for %d experts in group '%s' for question %s",
            len(member_user_ids),
            expert_group,
            question_entity.id,
        )
    except Exception as e:
        logger.warning(
            "Failed to create notifications for expert group '%s': %s",
            expert_group,
            e,
        )
