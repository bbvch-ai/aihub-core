from datetime import UTC, datetime
from typing import Literal

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

    question_id = StringField()
    thread_id = StringField()
    expert_name = StringField()
    expert_email = StringField()


class InsightCreator(EmbeddedDocument):
    """Information about the agent/user who created the insight."""

    agent_class = StringField()
    agent_id = StringField()
    user_id = StringField()
    user_name = StringField()


InsightStatus = Literal["active", "archived", "deleted"]


class InsightEntity(Document):
    """
    Represents an insight extracted from expert conversations.

    Insights are structured knowledge pieces that can be used by RAG agents
    to provide grounded answers to user questions.
    """

    meta = {
        "collection": "insights",
        "strict": False,
        "indexes": [
            {"fields": ["status"]},
            {"fields": ["namespace"]},
            {"fields": ["created_at"]},
            {"fields": ["tags"]},
            {"fields": ["status", "namespace"]},
            {"fields": ["source.thread_id"]},
            {"fields": ["source.question_id"]},
            {"fields": ["$title", "$content"]},  # Text search index
        ],
    }

    # Content fields
    title = StringField(required=True)
    content = StringField(required=True)
    question = StringField(required=True)
    expert_answer = StringField()

    # Organization
    namespace = StringField(default="default")
    tags = ListField(StringField())

    # Status
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
        title: str,
        content: str,
        question: str,
        expert_answer: str | None = None,
        namespace: str = "default",
        tags: list[str] | None = None,
        source: InsightSource | None = None,
        creator: InsightCreator | None = None,
    ) -> "InsightEntity":
        """Create a new insight."""
        entity = cls(
            id=ObjectId(),
            title=title,
            content=content,
            question=question,
            expert_answer=expert_answer,
            namespace=namespace,
            tags=tags or [],
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

    @classmethod
    @trace_fn
    def get_insights_by_tags(
        cls,
        tags: list[str],
        namespace: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list["InsightEntity"], int]:
        """Get insights by tags."""
        query = cls.objects(status="active", tags__in=tags)

        if namespace:
            query = query.filter(namespace=namespace)

        offset = (page - 1) * page_size
        insights = list(query.order_by("-created_at").skip(offset).limit(page_size))
        total = query.count()
        return insights, total

    @classmethod
    @trace_fn
    def search_insights(
        cls,
        search_text: str,
        namespace: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list["InsightEntity"], int]:
        """Search insights by text content."""
        query = cls.objects(status="active").search_text(search_text)

        if namespace:
            query = query.filter(namespace=namespace)

        offset = (page - 1) * page_size
        insights = list(query.order_by("$text_score").skip(offset).limit(page_size))
        total = query.count()
        return insights, total

    @classmethod
    @trace_fn
    def count_active_by_namespace(cls, namespace: str | None = None) -> int:
        """Count active insights, optionally filtered by namespace."""
        query = cls.objects(status="active")
        if namespace:
            query = query.filter(namespace=namespace)
        return query.count()

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

    @trace_fn
    def update_content(self, title: str | None = None, content: str | None = None) -> "InsightEntity":
        """Update the insight content."""
        if title:
            self.title = title
        if content:
            self.content = content
        self.updated_at = datetime.now(UTC)
        self.save()
        return self

    @trace_fn
    def add_tags(self, tags: list[str]) -> "InsightEntity":
        """Add tags to this insight."""
        for tag in tags:
            if tag not in self.tags:
                self.tags.append(tag)
        self.updated_at = datetime.now(UTC)
        self.save()
        return self
