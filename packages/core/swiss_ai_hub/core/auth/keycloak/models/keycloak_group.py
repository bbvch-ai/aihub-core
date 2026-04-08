from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class KeycloakGroup(BaseModel):
    """Pydantic model for a Keycloak GroupRepresentation."""

    model_config = ConfigDict(populate_by_name=True)

    id: Annotated[str, Field(description="Unique Keycloak group ID (UUID).")]
    name: Annotated[str, Field(description="Group name.")]
    path: Annotated[str | None, Field(description="Full group path (e.g. /tenants/default).")] = None
    parent_id: Annotated[str | None, Field(alias="parentId", description="Parent group ID.")] = None
    sub_group_count: Annotated[int | None, Field(alias="subGroupCount", description="Number of sub-groups.")] = None
    sub_groups: Annotated[list[KeycloakGroup], Field(alias="subGroups", description="Child groups.")] = []
    attributes: Annotated[dict[str, list[str]], Field(description="Custom group attributes as key-value pairs.")] = {}
