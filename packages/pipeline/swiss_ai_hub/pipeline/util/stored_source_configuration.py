from typing import Annotated, Any, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.persistence import BucketEntity
from swiss_ai_hub.core.secrets import SecretEncryptionService
from swiss_ai_hub.core.source_pipelines import SourcePipelineConfig

from swiss_ai_hub.pipeline.util.bucket_utils import ensure_main_db_connection


class StoredSourceConfiguration[TConfig: SourcePipelineConfig](BaseModel):
    """A database's source configuration from one read of its row: validated with secrets decrypted, and as stored.

    Both come from the same read, so a caller writing a secret back compares against exactly the value its run
    was configured with, never against a second read that a concurrent edit could already have changed.
    """

    config: Annotated[TConfig, Field(description="Validated configuration, secrets decrypted.", repr=False)]
    stored: Annotated[
        dict[str, Any], Field(description="source_configuration as stored, secrets encrypted.", repr=False)
    ]

    @classmethod
    def read(
        cls,
        bucket: Annotated[str, "Bucket name of the knowledge database"],
        source: Annotated[str, "Source pipeline id this code location runs as"],
        config_type: Annotated[type[TConfig], "The pipeline's config class to validate into"],
    ) -> Self:
        ensure_main_db_connection()
        entity = BucketEntity.get_bucket_by_bucket_name(bucket)
        if entity.deleting:
            raise ValueError(f"Knowledge database '{bucket}' is being deleted and must not be synced.")
        if entity.source != source:
            raise ValueError(f"Knowledge database '{bucket}' is filled by source '{entity.source}', not '{source}'.")
        stored = dict(entity.source_configuration)
        decrypted = SecretEncryptionService.from_settings().decrypt_paths(stored, config_type.secret_field_paths())
        return cls(config=config_type.model_validate(decrypted), stored=stored)
