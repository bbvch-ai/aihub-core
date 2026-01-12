from datetime import UTC, datetime

from bson import ObjectId
from llama_index.core.base.llms.types import MessageRole
from mongoengine import (
    DateTimeField,
    Document,
    EmbeddedDocument,
    EmbeddedDocumentField,
    EnumField,
    ListField,
    StringField,
)

from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn


class InsightMessage(EmbeddedDocument):
    """A single message in an insight conversation."""

    role = EnumField(MessageRole, required=True)
    content = StringField(required=True)


class InsightSource(EmbeddedDocument):
    """Information about the source of the insight (expert conversation)."""

    thread_id = StringField(required=True)
    expert_user_id = StringField(required=True)
    expert_name = StringField(required=True)


class InsightCreator(EmbeddedDocument):
    """Information about the agent/user who created the insight."""

    agent_class = StringField(required=True)
    agent_id = StringField(required=True)
    user_id = StringField(required=True)
    user_name = StringField(required=True)


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
            {"fields": ["namespace"]},
            {"fields": ["created_at"]},
            {"fields": ["source.thread_id"]},
            {"fields": ["namespace", "creator.agent_class", "creator.agent_id", "-created_at"]},
        ],
    }

    # Content fields - raw data, no LLM processing
    question = StringField(required=True)
    expert_answer = StringField(required=True)
    conversation = ListField(EmbeddedDocumentField(InsightMessage), required=True)

    # Organization
    namespace = StringField(required=True)

    # Provenance
    source = EmbeddedDocumentField(InsightSource, required=True)
    creator = EmbeddedDocumentField(InsightCreator, required=True)

    # Timestamps
    created_at = DateTimeField(default=lambda: datetime.now(UTC))
    updated_at = DateTimeField(default=lambda: datetime.now(UTC))

    @classmethod
    @trace_fn
    def create_insight(
        cls,
        question: str,
        expert_answer: str,
        conversation: list[InsightMessage],
        namespace: str,
        source: InsightSource,
        creator: InsightCreator,
    ) -> "InsightEntity":
        """Create a new insight from expert conversation data."""
        entity = cls(
            id=ObjectId(),
            question=question,
            expert_answer=expert_answer,
            conversation=conversation,
            namespace=namespace,
            source=source,
            creator=creator,
        )
        entity.save()
        return entity

    @classmethod
    @trace_fn
    def get_by_id(cls, insight_id: str) -> "InsightEntity | None":
        """
        Get an insight by its ID.

        Returns None if the ID is not a valid ObjectId or the insight doesn't exist.
        """
        try:
            return cls.objects.get(id=ObjectId(insight_id))
        except Exception:
            return None

    @classmethod
    @trace_fn
    def get_by_namespace_and_agent(
        cls,
        namespace: str,
        agent_class: str,
        agent_id: str,
        limit: int = 100,
    ) -> list["InsightEntity"]:
        """
        Get insights for a namespace filtered by agent class and id.
        """
        return list(
            cls.objects(
                namespace=namespace,
                creator__agent_class=agent_class,
                creator__agent_id=agent_id,
            )
            .order_by("-created_at")
            .limit(limit)
        )
