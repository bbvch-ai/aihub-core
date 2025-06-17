from aihub_lib.i18n.LocaleString import LocaleString
from pydantic import BaseModel, Field


class ProcessConfig(BaseModel):
    process_id: str = Field(..., description="The id of the process.")
    name: LocaleString = Field(..., description="The name of the process.")
    description: LocaleString = Field(..., description="The description of the process.")
