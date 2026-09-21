import json
from typing import Self

from mongoengine import EmbeddedDocument, StringField

from swiss_ai_hub.core.form.config_specs import ConfigSpecs


class ConfigSpecsEntity(EmbeddedDocument):
    """
    Stores an announced configuration schema.

    The schema is stored as a JSON string because MongoDB rejects dictionary keys starting with '$'
    (``$defs``, ``$ref``), which every non-trivial JSON schema contains.
    """

    meta = {"strict": False}

    config_class = StringField(default="", description="The class name of the configuration.")
    config_schema_json = StringField(default="{}", description="JSON schema for validating form submissions.")

    @property
    def config_schema(self) -> dict:
        return json.loads(self.config_schema_json) if self.config_schema_json else {}

    @classmethod
    def from_specs(cls, specs: ConfigSpecs) -> Self:
        return cls(config_class=specs.config_class, config_schema_json=json.dumps(specs.config_schema))

    def to_specs(self) -> ConfigSpecs:
        return ConfigSpecs(config_class=self.config_class, config_schema=self.config_schema)
