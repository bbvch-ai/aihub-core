import json
from typing import Self

from pydantic import BaseModel, ConfigDict, Field

from swiss_ai_hub.core.form.config_specs import ConfigSpecs


class StoredConfigSpecs(BaseModel):
    """An announced configuration schema, embedded in the Beanie entities.

    The Pydantic counterpart of `ConfigSpecsEntity`, which stays for the MongoEngine entities. The schema is stored
    as a JSON string because MongoDB rejects dictionary keys starting with '$' (``$defs``, ``$ref``).
    """

    model_config = ConfigDict(extra="allow")

    config_class: str = Field(default="", description="The class name of the configuration.")
    config_schema_json: str = Field(default="{}", description="JSON schema for validating form submissions.")

    @property
    def config_schema(self) -> dict:
        return json.loads(self.config_schema_json) if self.config_schema_json else {}

    @classmethod
    def from_specs(cls, specs: ConfigSpecs) -> Self:
        return cls(config_class=specs.config_class, config_schema_json=json.dumps(specs.config_schema))

    def to_specs(self) -> ConfigSpecs:
        return ConfigSpecs(config_class=self.config_class, config_schema=self.config_schema)
