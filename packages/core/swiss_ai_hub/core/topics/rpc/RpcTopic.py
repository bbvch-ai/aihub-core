from typing import Self

from pydantic import Field

from swiss_ai_hub.core.topic_managers.TopicManager import TopicManager
from swiss_ai_hub.core.topics.Topic import Topic


class RpcTopic(Topic):
    """
    Represents an RPC subject. Can parse subjects like:
    - aihub.rpc.config.agent.RAGAgent.default
    - aihub.rpc.config.process.Onboarding.hr

    Pattern: aihub.rpc.{service}.{entity_type}.{entity_class}.{entity_id}

    This class integrates with the Topic auto-registration mechanism, allowing
    `Topic.from_subject()` to automatically parse RPC subjects into structured objects.
    """

    service: str = Field(description="RPC service name (e.g., 'config')")
    entity_type: str = Field(description="Entity type (e.g., 'agent', 'process')")
    entity_class: str = Field(description="Entity class identifier")
    entity_id: str = Field(description="Entity instance ID")

    @property
    def execution_context_id(self) -> str:
        return f"{self.entity_class}.{self.entity_id}"

    @classmethod
    def from_subject(cls, subject: str) -> Self:
        parts = subject.split(".")
        if len(parts) != 6:
            raise ValueError(f"RPC subject must have 6 segments, got {len(parts)}: {subject}")

        prefix, rpc, service, entity_type, entity_class, entity_id = parts
        if f"{prefix}.{rpc}" != TopicManager.RPC_TOPIC:
            raise ValueError(f"Not an RPC topic: {subject}")

        return cls(
            service=service,
            entity_type=entity_type,
            entity_class=entity_class,
            entity_id=entity_id,
        )

    def to_subject(self) -> str:
        return f"{TopicManager.RPC_TOPIC}.{self.service}.{self.entity_type}.{self.entity_class}.{self.entity_id}"
