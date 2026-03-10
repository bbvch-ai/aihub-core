from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class RcloneBackendType(StrEnum):
    ONEDRIVE = "onedrive"
    DRIVE = "drive"
    S3 = "s3"
    LOCAL = "local"
    AZUREBLOB = "azureblob"
    SFTP = "sftp"


class RcloneSourceConfig(BaseModel):
    """
    Domain model for an Rclone remote configuration.

    Only contains common fields. All backend-specific options go in `options`.
    """

    model_config = ConfigDict(populate_by_name=True)

    name: Annotated[str, Field(pattern=r"^[a-zA-Z0-9_-]+$", description="Remote name (alphanumeric + _ -)")]
    backend_type: Annotated[RcloneBackendType, Field(description="Rclone backend type")]
    options: Annotated[dict[str, Any], Field(default_factory=dict, description="Backend-specific options")]

    def to_rclone_params(self) -> dict[str, Any]:
        """Convert to JSON payload for Rclone's 'config/create' API."""
        params = {}
        for key, value in self.options.items():
            if isinstance(value, SecretStr):
                params[key] = value.get_secret_value()
            else:
                params[key] = value

        return {
            "name": self.name,
            "type": self.backend_type.value,
            "parameters": params,
        }
