from typing import Annotated

from pydantic import BaseModel, Field, computed_field

from aihub_lib.i18n.LocaleString import LocaleString


class BaseConfig(BaseModel):
    name: Annotated[LocaleString, Field(description="The name of the process or agent.")]
    description: Annotated[LocaleString, Field(description="The description of the process or agent.")]
    icon: Annotated[str, Field(description="The icon representing the process or agent.")] = "meteor-icons:robot"

    @computed_field
    @property
    def _config_name(self) -> str:
        return self.__class__.__name__
