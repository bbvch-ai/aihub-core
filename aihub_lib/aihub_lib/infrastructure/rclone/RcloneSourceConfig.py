from enum import Enum
from typing import Annotated, Any

from pydantic import BaseModel, Field, SecretStr, ConfigDict


class RcloneBackendType(str, Enum):
    ONEDRIVE = "onedrive"
    DRIVE = "drive"
    DROPBOX = "dropbox"
    S3 = "s3"
    LOCAL = "local"


class RcloneRegion(str, Enum):
    GLOBAL = "global"
    US = "us"
    DE = "de"
    CN = "cn"


class RcloneSourceConfig(BaseModel):
    """
    Configuration for an rclone remote source.
    """

    model_config = ConfigDict(populate_by_name=True)

    name: Annotated[str, Field(pattern=r"^[a-zA-Z0-9_-]+$", description="Remote name (alphanumeric + _ -)")]
    backend_type: Annotated[RcloneBackendType, Field(description="Rclone backend type")]

    # OAuth/Authentication
    client_id: Annotated[str | None, Field(description="OAuth2 client ID")] = None
    client_secret: Annotated[SecretStr | None, Field(description="OAuth2 client secret")] = None
    tenant: Annotated[str | None, Field(description="Tenant ID (for OneDrive/SharePoint)")] = None

    # OneDrive/SharePoint specific
    site_url: Annotated[str | None, Field(description="SharePoint site URL")] = None
    drive_type: Annotated[str | None, Field(description="Drive type")] = None
    region: Annotated[RcloneRegion, Field(description="Region")] = RcloneRegion.GLOBAL

    extra_config: Annotated[dict[str, str], Field(default_factory=dict, description="Additional config")] = dict()

    def to_rclone_params(self) -> dict[str, Any]:
        """
        Convert to the specific parameters dictionary expected by rclone config/create.
        """
        options = {}

        if self.client_id:
            options["client_id"] = self.client_id
        if self.client_secret:
            options["client_secret"] = self.client_secret.get_secret_value()
        if self.tenant:
            options["tenant"] = self.tenant
            options["client_credentials"] = "true"
        if self.site_url:
            options["config_site_url"] = self.site_url
            options["config_type"] = "url"
        if self.drive_type:
            options["drive_type"] = self.drive_type
        if self.region:
            options["region"] = self.region.value

        options.update(self.extra_config)

        return {
            "name": self.name,
            "type": self.backend_type.value,
            "parameters": options,
        }
