from datetime import UTC, datetime

from bson import ObjectId
from bson.errors import InvalidId
from llama_index.core.base.llms.types import MessageRole
from mongoengine import (
    DateTimeField,
    Document,
    DoesNotExist,
    EmbeddedDocument,
    EmbeddedDocumentField,
    EnumField,
    ListField,
    StringField,
)

from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.i18n.LocaleHandler import LocaleHandler
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

    Namespaces use compound format "bucket_name/namespace_name" to identify
    which knowledge domains the insight belongs to.
    """

    meta = {
        "collection": "insights",
        "strict": False,
        "indexes": [
            {"fields": ["namespaces"]},
            {"fields": ["created_at"]},
            {"fields": ["source.thread_id"]},
            {"fields": ["namespaces", "creator.agent_class", "creator.agent_id", "-created_at"]},
        ],
    }

    # Content fields - raw data, no LLM processing
    question = StringField(required=True)
    expert_answer = StringField(required=True)
    conversation = ListField(EmbeddedDocumentField(InsightMessage), required=True)

    # Organization - multiple namespaces in compound format "bucket_name/namespace_name"
    namespaces = ListField(StringField(), required=True)

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
        namespaces: list[str],
        source: InsightSource,
        creator: InsightCreator,
    ) -> "InsightEntity":
        """Create a new insight from expert conversation data.

        Args:
            namespaces: List of compound namespace strings in format "bucket_name/namespace_name".
        """
        entity = cls(
            id=ObjectId(),
            question=question,
            expert_answer=expert_answer,
            conversation=conversation,
            namespaces=namespaces,
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
        Uses ObjectId.is_valid() to avoid unnecessary MongoDB queries for non-ObjectId strings.
        """
        if not ObjectId.is_valid(insight_id):
            return None
        try:
            return cls.objects.get(id=ObjectId(insight_id))
        except (InvalidId, DoesNotExist):
            return None

    def to_ingested_node(self, t: LocaleHandler) -> IngestedNode:
        """Convert this insight to an IngestedNode for retrieval and display."""
        conversation_lines = [f"{t(f'lib.insight.role.{msg.role.value}')}: {msg.content}" for msg in self.conversation]
        content_parts: list[str] = [
            f"{t('lib.insight.label.question')}: {self.question}",
            f"{t('lib.insight.label.answer')}: {self.expert_answer}",
            f"{t('lib.insight.label.conversation')}:",
            *conversation_lines,
        ]

        content: str = "\n".join(content_parts)
        created_at: str = self.created_at.isoformat().replace("+00:00", "Z")
        updated_at: str = self.updated_at.isoformat().replace("+00:00", "Z")

        # Use first namespace for IngestedNode (single namespace field)
        # Full namespace list is available in metadata
        primary_namespace = self.namespaces[0] if self.namespaces else "default"

        return IngestedNode(
            id=str(self.id),
            content=content,
            document_id=str(self.id),
            source=f"insight:{self.id}",
            source_origin=self.source.thread_id,
            namespace=primary_namespace,
            document_title=self.question,
            created_at=created_at,
            updated_at=updated_at,
            inserted_at=created_at,
            metadata={
                "insight_type": "expert_conversation",
                "expert_user_id": self.source.expert_user_id,
                "expert_name": self.source.expert_name,
                "agent_class": self.creator.agent_class,
                "agent_id": self.creator.agent_id,
                "namespaces": self.namespaces,
            },
        )

    @classmethod
    @trace_fn
    def get_by_namespaces_and_agent(
        cls,
        namespaces: list[str],
        agent_class: str,
        agent_id: str,
        limit: int = 100,
    ) -> list["InsightEntity"]:
        """
        Get insights matching any of the given namespaces, filtered by agent class and id.

        Args:
            namespaces: List of compound namespace strings in format "bucket_name/namespace_name".
        """
        return list(
            cls.objects(
                namespaces__in=namespaces,
                creator__agent_class=agent_class,
                creator__agent_id=agent_id,
            )
            .order_by("-created_at")
            .limit(limit)
        )

    @classmethod
    @trace_fn
    def get_all_by_agent(
        cls,
        agent_class: str,
        agent_id: str,
        limit: int = 100,
    ) -> list["InsightEntity"]:
        """
        Get all insights for an agent without namespace filtering.
        """
        return list(
            cls.objects(
                creator__agent_class=agent_class,
                creator__agent_id=agent_id,
            )
            .order_by("-created_at")
            .limit(limit)
        )
