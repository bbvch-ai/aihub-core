from typing import Annotated

from pydantic import BaseModel, Field


class ConfigAuthorizationViolation(BaseModel):
    """A single authorization violation found during config validation."""

    field: Annotated[str, Field(description="Dot-path to the form field, e.g. 'rag_config.knowledge_databases'.")]
    resource_type: Annotated[
        str, Field(description="Type of the unauthorized resource: 'knowledge_database' or 'agent'.")
    ]
    resource: Annotated[str, Field(description="Identifier of the unauthorized resource.")]
    message: Annotated[str, Field(description="Human-readable explanation of the violation.")]
