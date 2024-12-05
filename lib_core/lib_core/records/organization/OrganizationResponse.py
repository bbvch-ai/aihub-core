from typing import Optional

from pydantic import BaseModel, Field

from lib_core.records.organization.FeaturesResponse import FeaturesResponse


class OrganizationResponse(BaseModel):
    name: str = Field(
        ...,
        description="Display name of organization.",
        example="bbv Software Services AG",
    )
    shortname: str = Field(
        ...,
        description="Unique short name under which the organization will be accessible online.",
        example="bbv",
    )
    msal_client_id: str = Field(
        ...,
        description="The MSAL client ID for the organization.",
        example="12345678-abcd-1234-ef00-123456abcdef",
    )
    msal_tenant_id: str = Field(
        ...,
        description="The MSAL tenant ID for the organization.",
        example="12345678-abcd-1234-ef00-123456abcdef",
    )
    logo_url: str = Field(
        ...,
        description="The URL to the organization's logo.",
        example="https://aiagentsstpublicblobs.blob.core.windows.net/logos/logo.png",
    )
    dark_logo_url: str = Field(
        ...,
        description="The URL to the organization's logo for dark backgrounds.",
        example="https://aiagentsstpublicblobs.blob.core.windows.net/logos/logo.png",
    )
    features: Optional[FeaturesResponse] = Field(
        None, description="The features available to the organization."
    )
