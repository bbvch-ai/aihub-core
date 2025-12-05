import logging
import math

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.nats.events.expert_in_the_loop.request.ExpertInTheLoopRequestEvent import ExpertInTheLoopRequestEvent
from aihub_lib.nats.events.expert_in_the_loop.response.ExpertInTheLoopResponseEvent import (
    ExpertInTheLoopResponderInfo,
    ExpertInTheLoopResponseEvent,
)
from aihub_lib.nats.publishers.JSPublisher import JSPublisher
from aihub_lib.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager
from aihub_lib.nats.topics.agents.AgentInstanceTopic import AgentInstanceTopic
from aihub_lib.nats.topics.agents.PartialAgentTopic import PartialAgentTopic
from aihub_lib.persistence.expert.ExpertQuestionEntity import (
    ExpertQuestionEntity,
    ExpertResponder,
)
from aihub_lib.persistence.notification.NotificationEntity import NotificationEntity
from bson import ObjectId
from mongoengine import DoesNotExist
from nats.js import JetStreamContext

from aihub_api.routes.expert.dto.ExpertQuestionDTO import ExpertQuestionDTO
from aihub_api.routes.expert.dto.PaginatedExpertQuestionsResponse import PaginatedExpertQuestionsResponse

logger = logging.getLogger(__name__)


class ExpertQuestionService:
    """Service layer for handling expert question business logic."""

    @staticmethod
    @trace_fn
    def get_pending_questions(
        expert_group: str | None,
        page: int,
        page_size: int,
    ) -> PaginatedExpertQuestionsResponse:
        """Retrieves a paginated list of pending questions."""
        entities, total = ExpertQuestionEntity.get_pending_questions(
            expert_group=expert_group,
            page=page,
            page_size=page_size,
        )
        dtos = [ExpertQuestionDTO.from_entity(entity) for entity in entities]
        return PaginatedExpertQuestionsResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if page_size > 0 else 0,
            questions=dtos,
        )

    @staticmethod
    @trace_fn
    def get_question_by_id(question_id: str) -> ExpertQuestionDTO:
        """Retrieves a single question by ID."""
        entity = ExpertQuestionEntity.get_by_id(question_id)
        return ExpertQuestionDTO.from_entity(entity)

    @staticmethod
    @trace_fn
    def get_questions_by_status(
        status: str,
        expert_group: str | None,
        page: int,
        page_size: int,
    ) -> PaginatedExpertQuestionsResponse:
        """Retrieves a paginated list of questions by status."""
        entities, total = ExpertQuestionEntity.get_questions_by_status(
            status=status,
            expert_group=expert_group,
            page=page,
            page_size=page_size,
        )
        dtos = [ExpertQuestionDTO.from_entity(entity) for entity in entities]
        return PaginatedExpertQuestionsResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if page_size > 0 else 0,
            questions=dtos,
        )

    @staticmethod
    @trace_fn
    def count_pending(expert_group: str | None = None) -> int:
        """Counts pending questions, optionally filtered by expert group."""
        return ExpertQuestionEntity.count_pending_by_group(expert_group)

    @staticmethod
    @trace_fn
    async def submit_answer(
        question_id: str,
        response: str,
        user: UserIdentity,
        js: JetStreamContext,
        expert_group: str | None = None,
    ) -> ExpertQuestionDTO:
        """
        Submits an answer to a pending question and publishes the response event.

        This method:
        1. Updates the question entity with the answer
        2. Reconstructs the original request event
        3. Creates a response event
        4. Publishes the response to the correct NATS topic
        """
        try:
            entity = ExpertQuestionEntity.get_by_id(question_id)
        except DoesNotExist:
            raise ValueError(f"Question {question_id} not found")

        if entity.status != "pending":
            raise ValueError(f"Question {question_id} is not pending (status: {entity.status})")

        responder = ExpertResponder(
            user_id=user.id,
            user_name=user.name or user.username,
            email=user.email,
            expert_group=expert_group,
        )

        entity.submit_answer(response=response, responder=responder)

        await ExpertQuestionService._publish_response_event(entity, js)

        # Notify the requesting user that their question has been answered
        ExpertQuestionService._notify_user_of_answer(entity)

        return ExpertQuestionDTO.from_entity(entity)

    @staticmethod
    async def _publish_response_event(entity: ExpertQuestionEntity, js: JetStreamContext):
        """Publishes the ExpertInTheLoopResponseEvent to NATS."""
        topic_data = entity.topic_data

        if "agent_class" in topic_data and "agent_id" in topic_data:
            topic = AgentInstanceTopic(**topic_data)
        else:
            topic = PartialAgentTopic(**topic_data)

        request_event = ExpertInTheLoopRequestEvent(
            user={"id": entity.requesting_user.user_id, "name": entity.requesting_user.user_name},
            question=entity.question,
            context=entity.context,
            expert_group=entity.expert_group,
            priority=entity.priority,
            locale=entity.locale,
            topic=topic,
        )

        responder_info = None
        if entity.responder:
            responder_info = ExpertInTheLoopResponderInfo(
                user_id=entity.responder.user_id,
                user_name=entity.responder.user_name,
                email=entity.responder.email,
                expert_group=entity.responder.expert_group,
            )

        response_event = ExpertInTheLoopResponseEvent(
            response=entity.response,
            request_event=request_event,
            responder=responder_info,
        )

        agent_topic = entity.requesting_agent
        topic_manager = AgentThreadTopicManager(
            agent_class=agent_topic.agent_class,
            agent_id=agent_topic.agent_id,
            thread_id=agent_topic.thread_id,
            display_id=str(ObjectId()),
            run_id=agent_topic.run_id,
        )

        subject = topic_manager.get_subject_for_control_event_in_thread(
            event_name=response_event.event_name,
            event_id=response_event.event_id,
        )

        publisher = JSPublisher("ExpertQuestionService", js)
        await publisher.publish_event(response_event, subject)

        logger.info(f"Published ExpertInTheLoopResponseEvent for question {entity.id} to {subject}")

    @staticmethod
    @trace_fn
    def cancel_question(question_id: str) -> ExpertQuestionDTO:
        """Cancels a pending question."""
        try:
            entity = ExpertQuestionEntity.get_by_id(question_id)
        except DoesNotExist:
            raise ValueError(f"Question {question_id} not found")

        if entity.status != "pending":
            raise ValueError(f"Question {question_id} is not pending (status: {entity.status})")

        entity.mark_as_cancelled()
        return ExpertQuestionDTO.from_entity(entity)

    @staticmethod
    def _notify_user_of_answer(entity: ExpertQuestionEntity) -> None:
        """Creates a notification for the requesting user when their question is answered."""
        requesting_user_id = entity.requesting_user.user_id
        expert_name = entity.responder.user_name if entity.responder else "An expert"
        question_preview = entity.question[:50] + "..." if len(entity.question) > 50 else entity.question

        try:
            NotificationEntity.create_notification(
                user_id=requesting_user_id,
                title=LocaleString(
                    en="Expert Question Answered",
                    de="Expertenfrage beantwortet",
                    fr="Question d'expert répondue",
                    it="Domanda dell'esperto risposta",
                ),
                message=LocaleString(
                    en=f'{expert_name} has answered your question: "{question_preview}"',
                    de=f'{expert_name} hat Ihre Frage beantwortet: "{question_preview}"',
                    fr=f'{expert_name} a répondu à votre question: "{question_preview}"',
                    it=f'{expert_name} ha risposto alla tua domanda: "{question_preview}"',
                ),
                notification_type="success",
                severity="medium",
                link=f"/expert/questions/{entity.id}",
                notification_group_id=f"expert_question_{entity.id}",
            )
            logger.info(f"Created notification for user {requesting_user_id} about answered question {entity.id}")
        except Exception as e:
            # Log but don't fail the answer submission if notification fails
            logger.warning(f"Failed to create notification for answered question {entity.id}: {e}")
