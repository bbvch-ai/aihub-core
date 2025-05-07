from aihub_iac.azure.resources.RessourceNamer import ResourceNamer


class ManagedEnvironmentConfig:

    def __init__(self, resource_group: str, project_name: str, location: str, location_short: str, name: str):
        self.resource_group = resource_group
        self.project_name = project_name
        self.location = location
        self.location_short = location_short
        self.name = name
        self.resource_namer = ResourceNamer(project_name=self.project_name, location_short=self.location_short)

    def log_analytics_name(self) -> str:
        return self.resource_namer.log_workspace(self.name)

    def container_env(self) -> str:
        return self.resource_namer.container_app_environment_name(self.name)
