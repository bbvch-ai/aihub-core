import json
from typing import Self

from mongoengine import EmbeddedDocument, StringField

from swiss_ai_hub.core.nats.events.discovery.agent.AgentConfigSpecs import AgentConfigSpecs


class AgentConfigSpecsEntity(EmbeddedDocument):
    """
    Stores the agent configuration validation specification in the database.

    Contains ONLY the JSON schema for validating form submissions.
    Instance-level fields (name, description, icon, agent_id) are stored
    in AgentConfigEntityDocument, not here.

    NOTE: agent_config_schema is stored as a JSON string because MongoDB
    doesn't allow dictionary keys starting with '$' (like $defs, $ref in JSON Schema).
    """

    meta = {"strict": False}  # Allow unknown fields from old schema during deserialization

    agent_class = StringField(required=True, description="The class name of the agent.")
    agent_config_schema_json = StringField(
        default="{}", description="JSON schema for validating form submissions (stored as JSON string)."
    )

    @property
    def agent_config_schema(self) -> dict:
        """Deserialize the agent config schema from JSON string to dictionary."""
        return json.loads(self.agent_config_schema_json) if self.agent_config_schema_json else {}

    @classmethod
    def from_specs(cls, specs: AgentConfigSpecs) -> Self:
        """Create an AgentConfigSpecsEntity from an AgentConfigSpecs."""
        return cls(
            agent_class=specs.agent_class,
            agent_config_schema_json=json.dumps(specs.agent_config_schema),
        )

    def to_specs(self) -> AgentConfigSpecs:
        """Convert this entity to an AgentConfigSpecs."""
        return AgentConfigSpecs(
            agent_class=self.agent_class,
            agent_config_schema=self.agent_config_schema,
        )
