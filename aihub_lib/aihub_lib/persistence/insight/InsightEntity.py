from datetime import UTC, datetime

from bson import ObjectId
from mongoengine import (
    DateTimeField,
    Document,
    EmbeddedDocument,
    EmbeddedDocumentField,
    ListField,
    StringField,
)

from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn


class InsightSource(EmbeddedDocument):
    """Information about the source of the insight (expert conversation)."""

    thread_id = StringField()
    expert_user_id = StringField()
    expert_name = StringField()


class InsightCreator(EmbeddedDocument):
    """Information about the agent/user who created the insight."""

    agent_class = StringField()
    agent_id = StringField()
    user_id = StringField()
    user_name = StringField()


class InsightEntity(Document):
    """
    Represents an insight extracted from expert conversations.

    Insights are knowledge pieces created when an expert successfully answers
    a question. They store the raw question/answer data for future reference.
    """

    meta = {
        "collection": "insights",
        "strict": False,
        "indexes": [
            {"fields": ["status"]},
            {"fields": ["namespace"]},
            {"fields": ["created_at"]},
            {"fields": ["status", "namespace"]},
            {"fields": ["source.thread_id"]},
        ],
    }

    # Content fields - raw data, no LLM processing
    question = StringField(required=True)
    expert_answer = StringField(required=True)
    conversation = ListField(StringField())

    # Organization
    namespace = StringField(default="default")
    status = StringField(choices=("active", "archived", "deleted"), default="active")

    # Provenance
    source = EmbeddedDocumentField(InsightSource)
    creator = EmbeddedDocumentField(InsightCreator)

    # Timestamps
    created_at = DateTimeField(default=lambda: datetime.now(UTC))
    updated_at = DateTimeField(default=lambda: datetime.now(UTC))

    @classmethod
    @trace_fn
    def create_insight(
        cls,
        question: str,
        expert_answer: str,
        conversation: list[str] | None = None,
        namespace: str = "default",
        source: InsightSource | None = None,
        creator: InsightCreator | None = None,
    ) -> "InsightEntity":
        """Create a new insight from expert conversation data."""
        entity = cls(
            id=ObjectId(),
            question=question,
            expert_answer=expert_answer,
            conversation=conversation or [],
            namespace=namespace,
            source=source,
            creator=creator,
        )
        entity.save()
        return entity

    @classmethod
    @trace_fn
    def get_by_id(cls, insight_id: str) -> "InsightEntity":
        """Get an insight by its ID."""
        return cls.objects().get(id=ObjectId(insight_id))

    @classmethod
    @trace_fn
    def get_active_insights(
        cls,
        namespace: str | None = None,
        page: int = 1,
        page_size: int = 20,
        order_by: str = "-created_at",
    ) -> tuple[list["InsightEntity"], int]:
        """Get active insights, optionally filtered by namespace."""
        query = cls.objects(status="active")

        if namespace:
            query = query.filter(namespace=namespace)

        offset = (page - 1) * page_size
        insights = list(query.order_by(order_by).skip(offset).limit(page_size))
        total = query.count()
        return insights, total

    @classmethod
    @trace_fn
    def get_insights_for_thread(cls, thread_id: str) -> list["InsightEntity"]:
        """Get all insights for a specific thread."""
        return list(cls.objects(source__thread_id=thread_id).order_by("-created_at"))

    @trace_fn
    def archive(self) -> "InsightEntity":
        """Archive this insight."""
        self.status = "archived"
        self.updated_at = datetime.now(UTC)
        self.save()
        return self

    @trace_fn
    def delete_insight(self) -> "InsightEntity":
        """Soft delete this insight."""
        self.status = "deleted"
        self.updated_at = datetime.now(UTC)
        self.save()
        return self
