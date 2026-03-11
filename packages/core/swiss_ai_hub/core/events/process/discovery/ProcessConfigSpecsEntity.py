import json
from typing import Self

from mongoengine import EmbeddedDocument, StringField

from swiss_ai_hub.core.events.process.discovery.ProcessConfigSpecs import ProcessConfigSpecs


class ProcessConfigSpecsEntity(EmbeddedDocument):
    """
    Stores the process configuration validation specification in the database.

    Contains ONLY the JSON schema for validating form submissions.
    Instance-level fields (name, description, icon, process_id) are stored
    in ProcessConfigEntityDocument, not here.

    NOTE: process_config_schema is stored as a JSON string because MongoDB
    doesn't allow dictionary keys starting with '$' (like $defs, $ref in JSON Schema).
    """

    meta = {"strict": False}

    process_class = StringField(required=True, description="The class name of the process.")
    process_config_schema_json = StringField(
        default="{}", description="JSON schema for validating form submissions (stored as JSON string)."
    )

    @property
    def process_config_schema(self) -> dict:
        """Deserialize the process config schema from JSON string to dictionary."""
        return json.loads(self.process_config_schema_json) if self.process_config_schema_json else {}

    @classmethod
    def from_specs(cls, specs: ProcessConfigSpecs) -> Self:
        """Create a ProcessConfigSpecsEntity from a ProcessConfigSpecs."""
        return cls(
            process_class=specs.process_class,
            process_config_schema_json=json.dumps(specs.process_config_schema),
        )

    def to_specs(self) -> ProcessConfigSpecs:
        """Convert this entity to a ProcessConfigSpecs."""
        return ProcessConfigSpecs(
            process_class=self.process_class,
            process_config_schema=self.process_config_schema,
        )
