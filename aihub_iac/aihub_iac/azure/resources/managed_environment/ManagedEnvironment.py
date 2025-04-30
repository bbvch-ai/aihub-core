import pulumi
from typing import Optional
from pulumi_azure_native import app, operationalinsights

from aihub_iac.azure.resources.managed_environment.ManagedEnvironmentConfig import ManagedEnvironmentConfig


class ManagedEnvironment(pulumi.ComponentResource):
    """A Pulumi component resource for creating a managed environment for container apps"""

    def __init__(
        self,
        stack: str,
        name: str,
        config: ManagedEnvironmentConfig,
        infrastructure_subnet_id: pulumi.Output[str],
        opts: Optional[pulumi.ResourceOptions] = None,
    ):
        super().__init__(f"{stack}:{name}", name, None, opts)

        self.config = config
        self.stack = stack
        self.name = name

        # Create resources
        self.log_analytics_workspace = self._create_log_analytics_workspace()
        self.log_analytics_customer_id, self.log_analytics_shared_key = self._get_log_analytics_credentials()

        self.managed_environment = self._create_managed_environment(infrastructure_subnet_id)

        # Export outputs
        self._register_outputs()

    def _create_log_analytics_workspace(self):
        """Create the Log Analytics workspace"""
        return operationalinsights.Workspace(
            workspace_name=self.config.log_analytics_name(),
            resource_name=self.config.log_analytics_name(),
            resource_group_name=self.config.resource_group,
            location=self.config.location,
            sku=operationalinsights.WorkspaceSkuArgs(name="PerGB2018"),
            retention_in_days=30,
            opts=pulumi.ResourceOptions(parent=self),
            tags={
                "Stack": self.stack,
            },
        )

    def _get_log_analytics_credentials(self):
        """Get Log Analytics credentials"""
        shared_keys = operationalinsights.get_shared_keys_output(
            resource_group_name=self.config.resource_group,
            workspace_name=self.log_analytics_workspace.name,
        )
        customer_id = self.log_analytics_workspace.customer_id
        shared_key = shared_keys.apply(lambda keys: keys.primary_shared_key)
        return customer_id, shared_key

    def _create_managed_environment(self, infrastructure_subnet_id: pulumi.Output[str]):
        """Create the managed environment for container apps"""
        return app.ManagedEnvironment(
            resource_name=self.config.container_env(),
            environment_name=self.config.container_env(),
            resource_group_name=self.config.resource_group,
            location=self.config.location,
            app_logs_configuration=app.AppLogsConfigurationArgs(
                destination="log-analytics",
                log_analytics_configuration=app.LogAnalyticsConfigurationArgs(
                    customer_id=self.log_analytics_customer_id,
                    shared_key=self.log_analytics_shared_key,
                ),
            ),
            vnet_configuration=app.VnetConfigurationArgs(
                infrastructure_subnet_id=infrastructure_subnet_id,
            ),
            opts=pulumi.ResourceOptions(parent=self),
            tags={
                "Stack": self.stack,
            },
        )

    def _register_outputs(self):
        """Register outputs for this component"""
        outputs = {
            "managed_environment_id": self.managed_environment.id,
            "managed_environment_name": self.managed_environment.name,
            "log_analytics_workspace_id": self.log_analytics_workspace.id,
            "log_analytics_workspace_name": self.log_analytics_workspace.name,
        }

        self.register_outputs(outputs)

    @property
    def id(self):
        return self.managed_environment.id
