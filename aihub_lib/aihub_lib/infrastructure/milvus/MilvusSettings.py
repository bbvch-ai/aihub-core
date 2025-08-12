from typing import Annotated

from pydantic import Field

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class MilvusSettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("MILVUS_")

    URL: Annotated[str, Field(description="Connection URL for Milvus DB Server")]
