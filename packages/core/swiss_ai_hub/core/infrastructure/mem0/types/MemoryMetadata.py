from typing import Annotated

from pydantic import AliasChoices, BaseModel, Field

from swiss_ai_hub.core.infrastructure.mem0.types.MemoryType import MemoryType


class MemoryMetadata(BaseModel):
    user_id: Annotated[
        str,
        Field(description="The user ID.", validation_alias=AliasChoices("user_id", "_user_id")),
    ]
    agent_id: Annotated[
        str,
        Field(description="The agent ID.", validation_alias=AliasChoices("agent_id", "_agent_id")),
    ]
    thread_id: Annotated[
        str,
        Field(description="The thread ID.", validation_alias=AliasChoices("thread_id", "_thread_id")),
    ]
    display_id: Annotated[
        str,
        Field(description="The display ID.", validation_alias=AliasChoices("display_id", "_display_id")),
    ]
    run_id: Annotated[
        str,
        Field(description="The run ID.", validation_alias=AliasChoices("run_id", "_run_id")),
    ]
    type: Annotated[
        MemoryType,
        Field(description="The type of the memory.", validation_alias=AliasChoices("type", "_type")),
    ]
    tenant_id: Annotated[
        str | None,
        Field(
            description="The tenant ID for multi-tenancy support.",
            validation_alias=AliasChoices("tenant_id", "_tenant_id", "organization_name", "_organization_name"),
        ),
    ] = None
    tenant_namespace: Annotated[
        str | None,
        Field(
            description="The tenant namespace for department-level scoping.",
            validation_alias=AliasChoices(
                "tenant_namespace", "_tenant_namespace", "organization_namespace", "_organization_namespace"
            ),
        ),
    ] = None
