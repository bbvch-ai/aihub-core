from datetime import UTC, datetime
from typing import Literal

from bson import ObjectId
from mongoengine import (
    DateTimeField,
    DictField,
    Document,
    EmbeddedDocument,
    EmbeddedDocumentField,
    StringField,
)

from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn


class RequestingUser(EmbeddedDocument):
    """Information about the user who triggered the question."""

    user_id = StringField(required=True)
    user_name = StringField()
    email = StringField()


class RequestingAgent(EmbeddedDocument):
    """Information about the agent requesting expert input."""

    agent_class = StringField(required=True)
    agent_id = StringField(required=True)
    thread_id = StringField(required=True)
    run_id = StringField(required=True)


class ExpertResponder(EmbeddedDocument):
    """Information about the expert who answered the question."""

    user_id = StringField(required=True)
    user_name = StringField()
    email = StringField()
    expert_group = StringField()


QuestionStatus = Literal["pending", "answered", "expired", "cancelled"]


class ExpertQuestionEntity(Document):
    """
    Represents an expert question submitted via the Expert-in-the-Loop pattern.

    This entity persists questions from agents that need expert guidance through
    the platform's built-in GUI interface.
    """

    meta = {
        "collection": "expert_questions",
        "strict": False,
        "indexes": [
            {"fields": ["status"]},
            {"fields": ["expert_group"]},
            {"fields": ["priority"]},
            {"fields": ["created_at"]},
            {"fields": ["status", "expert_group"]},
            {"fields": ["requesting_agent.thread_id"]},
            {"fields": ["requesting_user.user_id"]},
        ],
    }

    question = StringField(required=True)
    context = StringField()
    expert_group = StringField()
    priority = StringField(choices=("low", "normal", "high", "urgent"), default="normal")
    locale = StringField(choices=("de", "en", "fr", "it"), default="en")

    status = StringField(choices=("pending", "answered", "expired", "cancelled"), default="pending")

    requesting_user = EmbeddedDocumentField(RequestingUser, required=True)
    requesting_agent = EmbeddedDocumentField(RequestingAgent, required=True)

    response = StringField()
    responder = EmbeddedDocumentField(ExpertResponder)
    responded_at = DateTimeField()

    topic_data = DictField(required=True)

    created_at = DateTimeField(default=lambda: datetime.now(UTC))
    updated_at = DateTimeField(default=lambda: datetime.now(UTC))

    @classmethod
    @trace_fn
    def create_question(
        cls,
        question: str,
        requesting_user: RequestingUser,
        requesting_agent: RequestingAgent,
        topic_data: dict,
        context: str | None = None,
        expert_group: str | None = None,
        priority: str = "normal",
        locale: str = "en",
    ) -> "ExpertQuestionEntity":
        """Create a new expert question."""
        entity = cls(
            id=ObjectId(),
            question=question,
            context=context,
            expert_group=expert_group,
            priority=priority,
            locale=locale,
            requesting_user=requesting_user,
            requesting_agent=requesting_agent,
            topic_data=topic_data,
        )
        entity.save()
        return entity

    @classmethod
    @trace_fn
    def get_by_id(cls, question_id: str) -> "ExpertQuestionEntity":
        """Get a question by its ID."""
        return cls.objects().get(id=ObjectId(question_id))

    @classmethod
    @trace_fn
    def get_pending_questions(
        cls,
        expert_group: str | None = None,
        page: int = 1,
        page_size: int = 20,
        order_by: str = "-created_at",
    ) -> tuple[list["ExpertQuestionEntity"], int]:
        """Get pending questions, optionally filtered by expert group."""
        query = cls.objects(status="pending")

        if expert_group:
            query = query.filter(expert_group=expert_group)

        offset = (page - 1) * page_size
        questions = list(query.order_by(order_by).skip(offset).limit(page_size))
        total = query.count()
        return questions, total

    @classmethod
    @trace_fn
    def get_questions_for_thread(cls, thread_id: str) -> list["ExpertQuestionEntity"]:
        """Get all questions for a specific thread."""
        return list(cls.objects(requesting_agent__thread_id=thread_id).order_by("-created_at"))

    @classmethod
    @trace_fn
    def get_questions_by_status(
        cls,
        status: QuestionStatus,
        expert_group: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list["ExpertQuestionEntity"], int]:
        """Get questions by status, optionally filtered by expert group."""
        query = cls.objects(status=status)

        if expert_group:
            query = query.filter(expert_group=expert_group)

        offset = (page - 1) * page_size
        questions = list(query.order_by("-created_at").skip(offset).limit(page_size))
        total = query.count()
        return questions, total

    @classmethod
    @trace_fn
    def count_pending_by_group(cls, expert_group: str | None = None) -> int:
        """Count pending questions, optionally filtered by expert group."""
        query = cls.objects(status="pending")
        if expert_group:
            query = query.filter(expert_group=expert_group)
        return query.count()

    @trace_fn
    def submit_answer(self, response: str, responder: ExpertResponder) -> "ExpertQuestionEntity":
        """Submit an answer to this question."""
        self.response = response
        self.responder = responder
        self.status = "answered"
        self.responded_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)
        self.save()
        return self

    @trace_fn
    def mark_as_expired(self) -> "ExpertQuestionEntity":
        """Mark this question as expired."""
        self.status = "expired"
        self.updated_at = datetime.now(UTC)
        self.save()
        return self

    @trace_fn
    def mark_as_cancelled(self) -> "ExpertQuestionEntity":
        """Mark this question as cancelled."""
        self.status = "cancelled"
        self.updated_at = datetime.now(UTC)
        self.save()
        return self
