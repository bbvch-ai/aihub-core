import pulumi
from typing import Optional
from pulumi_azure_native import app, operationalinsights


class ManagedEnvironmentConfig:
    """Configuration for the Managed Environment"""

    def __init__(self, resource_group: str, project_name: str, location: str, location_short: str, name: str):
        self.resource_group = resource_group
        self.project_name = project_name
        self.location = location
        self.location_short = location_short
        self.name = name

    def log_analytics_name(self) -> str:
        """Get the Log Analytics workspace name"""
        return f"{self.project_name}-logs-{self.location_short}-{self.name}"

    def container_env(self) -> str:
        """Get the container app environment name"""
        return f"{self.project_name}-capp-{self.location_short}-{self.name}"
