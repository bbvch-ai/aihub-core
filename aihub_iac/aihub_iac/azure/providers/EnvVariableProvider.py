
from aihub_iac.azure.settings.ProjectSettings import ProjectSettings


class EnvVariableProvider:
    @staticmethod
    def get_environment_variables():
        project_name = ProjectSettings().APP_NAME
        location = ProjectSettings().LOCATION
        location_short = ProjectSettings().LOCATION_SHORT
        resource_group = ProjectSettings().RESOURCE_GROUP
        subscription_id = ProjectSettings().ARM_SUBSCRIPTION_ID
        return project_name, location, location_short, resource_group, subscription_id
