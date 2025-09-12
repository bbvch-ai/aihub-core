from typing import Annotated

from pydantic import Field, SecretStr

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class S3StorageSettings(EnvironmentSettings):
    """
    Configuration settings for S3-compatible storage services.

    This configuration class manages connection parameters for S3-compatible
    storage backends including AWS S3 and MinIO. It uses Pydantic BaseSettings
    to load configuration from environment variables with fallback defaults.
    """

    model_config = EnvironmentSettings.create_settings_config("S3_STORAGE_")

    ENDPOINT: Annotated[str, Field(description="The s3 endpoint from either aws or minio.")]
    ACCESS_KEY: Annotated[str, Field(description="The access key for the s3 endpoint.")]
    SECRET_KEY: Annotated[SecretStr, Field(description="The secret key for the s3 endpoint.")]
    REGION: Annotated[str, Field(description="The region for the s3 endpoint. For minio, value does not matter")] = (
        "us-east-1"
    )

    # This secret key is used to sign our own internal URLs, not for Azure.
    URL_SIGNING_SECRET: Annotated[
        SecretStr,
        Field(
            description="A secret key used for signing and verifying temporary anonymous access URLs.",
        ),
    ]
