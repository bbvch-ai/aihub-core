from functools import cached_property
from typing import ClassVar

from pydantic import BaseModel, Field

from aihub_iac.azure.resources.RessourceNamer import ResourceNamer
from aihub_iac.azure.settings.ProjectSettings import ProjectSettings


class BaseConfig(BaseModel):

    _project_settings: ClassVar[ProjectSettings] = ProjectSettings()

    # Project and environment settings
    project_name: str = Field(
        default_factory=lambda: BaseConfig._project_settings.APP_NAME, description="Name of the project"
    )
    location: str = Field(
        default_factory=lambda: BaseConfig._project_settings.LOCATION, description="Location of the resources"
    )
    location_short: str = Field(
        default_factory=lambda: BaseConfig._project_settings.LOCATION_SHORT, description="Short location code"
    )
    resource_group: str = Field(
        default_factory=lambda: BaseConfig._project_settings.RESOURCE_GROUP, description="Resource group name"
    )
    subscription_id: str = Field(
        default_factory=lambda: BaseConfig._project_settings.ARM_SUBSCRIPTION_ID, description="Subscription ID"
    )

    @cached_property
    def resource_namer(self) -> ResourceNamer:
        return ResourceNamer(project_name=self.project_name, location_short=self.location_short)
