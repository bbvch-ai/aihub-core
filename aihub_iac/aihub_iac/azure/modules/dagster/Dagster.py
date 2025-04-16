import base64
import pulumi

from typing import List, Optional

from pulumi_azure_native import web, dbforpostgresql, storage, network, app, managedidentity

from aihub_iac.azure.providers.NetworkProvider import NetworkProvider
from aihub_iac.azure.providers.IdentityProvider import IdentityProvider
from aihub_iac.azure.providers.RoleProvider import RoleProvider
from aihub_iac.azure.modules.dagster.DagsterConfig import DagsterConfig


class Dagster(pulumi.ComponentResource):
    """A Pulumi component resource for deploying Dagster infrastructure"""

    def __init__(self, stack: str, name: str, config: DagsterConfig, opts: Optional[pulumi.ResourceOptions] = None):
        super().__init__(f"{stack}:{name}", name, None, opts)

        self.name = name
        self.config = config

        # Initialize providers
        self.network_provider = NetworkProvider(
            self.config.resource_group, self.config.project_name, self.config.location_short
        )

        self.identity_provider = IdentityProvider(
            self.config.resource_group,
            self.config.location,
            self.config.subscription_id,
            self.config.project_name,
            self.config.location_short,
        )

        self.role_provider = RoleProvider(self.config.subscription_id)

        # Create resources
        self._create_resources()

    def _create_resources(self):
        """Create all Dagster infrastructure resources"""
        # Get existing resources
        self.existing_app_subnet = self.network_provider.get_app_subnet()
        self.existing_pg_subnet = self.network_provider.get_pg_subnet()
        self.existing_vnet = self.network_provider.get_vnet()

        # Create new resources
        self.dagster_database = self._create_postgres_database()
        self.datalake = self._create_data_lake()  # TODO: Move into vNet
        self.identity = self._create_identity()

        self.dagster_app_service = self._create_dagster_app_service()

        # Export outputs
        self._register_outputs()

    def _create_identity(self):
        """Create and configure the managed identity"""
        return self.identity_provider.create_identity(self.name)

    def _create_postgres_database(self):
        """Create the Dagster database on the Postgres server"""
        return dbforpostgresql.Database(
            resource_name=self.config.database_name,
            resource_group_name=self.config.resource_group,
            server_name=self.config.postgres_name,
            opts=pulumi.ResourceOptions(parent=self),
        )

    def _create_data_lake(self):
        """Create the data lake storage account"""
        return storage.StorageAccount(
            resource_name=self.config.dagster_datalake,
            account_name=self.config.dagster_datalake,
            resource_group_name=self.config.resource_group,
            location=self.config.location,
            kind="StorageV2",
            sku=storage.SkuArgs(name="Standard_LRS"),
            access_tier=storage.AccessTier.HOT,
            is_hns_enabled=True,
            opts=pulumi.ResourceOptions(parent=self),
        )

    def _create_dagster_app_service(self):
        """Create the Dagster Container App using an existing managed environment"""
        # Get the existing managed Container App Environment
        container_app_env = app.get_managed_environment(
            resource_group_name=self.config.resource_group,
            environment_name=self.config.container_apps_environment_name,
        )

        # Create the Container App
        return app.ContainerApp(
            container_app_name=self.config.dagster_service,
            resource_name=self.config.dagster_service,
            resource_group_name=self.config.resource_group,
            location=self.config.location,
            managed_environment_id=container_app_env.id,
            identity=app.ManagedServiceIdentityArgs(
                type=app.ManagedServiceIdentityType.USER_ASSIGNED,
                user_assigned_identities=[self.identity.user_identity],
            ),
            configuration=app.ConfigurationArgs(
                ingress=app.IngressArgs(
                    external=True,
                    target_port=8000,
                    transport="auto",
                ),
                registries=[
                    app.RegistryCredentialsArgs(
                        server=self.config.registry_url,
                        username=self.config.registry_user,
                        password_secret_ref="registry-password",
                    )
                ],
                secrets=[
                    app.SecretArgs(name="registry-password", value=self.config.registry_pat),
                    app.SecretArgs(name="postgres-password", value=self.config.postgres_password),
                    app.SecretArgs(name="oauth2-proxy-cookie-secret", value=self.config.oauth2_proxy_cookie_secret),
                    app.SecretArgs(name="oauth2-proxy-client-secret", value=self.config.oauth2_proxy_client_secret),
                ],
            ),
            template=app.TemplateArgs(
                containers=[
                    app.ContainerArgs(
                        name="dagster",
                        image=self.config.effective_docker_image,
                        resources=app.ContainerResourcesArgs(
                            cpu=self.config.container_cpu,
                            memory=self.config.container_memory,
                        ),
                        env=self._get_container_env_vars(),
                    )
                ],
                scale=app.ScaleArgs(
                    min_replicas=self.config.min_replicas,
                    max_replicas=self.config.max_replicas,
                ),
            ),
            opts=pulumi.ResourceOptions(parent=self),
        )

    def _get_container_env_vars(self) -> List[app.EnvironmentVarArgs]:
        """Get the environment variables for the container"""
        # Convert the app settings to container env vars
        env_vars = [
            app.EnvironmentVarArgs(name="WEBSITES_PORT", value="8000"),
            app.EnvironmentVarArgs(
                name="DAGSTER_SQL_DATABASE_URL",
                value=f"postgresql://{self.config.postgres_name}.postgres.database.azure.com:5432/{self.config.database_name}?user={self.config.postgres_username}&password={{{{secretref:postgres-password}}}}",
            ),
            app.EnvironmentVarArgs(
                name="DAGSTER_PG_HOST",
                value=f"postgresql://{self.config.postgres_name}.postgres.database.azure.com:5432/",
            ),
            app.EnvironmentVarArgs(name="DAGSTER_PG_DB", value=f"{self.config.database_name}"),
            app.EnvironmentVarArgs(name="AZURE_SUBSCRIPTION_NAME", value=self.config.azure_subscription_name),
            app.EnvironmentVarArgs(name="APP_NAME", value=self.config.project_name),
            app.EnvironmentVarArgs(name="OAUTH2_PROXY_CLIENT_ID", value=self.config.oauth2_proxy_client_id),
            app.EnvironmentVarArgs(name="OAUTH2_PROXY_AZURE_TENANT", value=self.config.oauth2_proxy_azure_tenant),
            app.EnvironmentVarArgs(name="OAUTH2_PROXY_PROVIDER", value=self.config.oauth2_proxy_provider),
            app.EnvironmentVarArgs(name="OAUTH2_PROXY_OIDC_ISSUER_URL", value=self.config.oauth2_proxy_oidc_issuer_url),
            app.EnvironmentVarArgs(name="OAUTH2_PROXY_COOKIE_SECRET", value="{{secretref:oauth2-proxy-cookie-secret}}"),
            app.EnvironmentVarArgs(name="OAUTH2_PROXY_CLIENT_SECRET", value="{{secretref:oauth2-proxy-client-secret}}"),
            app.EnvironmentVarArgs(name="OAUTH2_PROXY_EMAIL_DOMAINS", value=self.config.oauth2_proxy_email_domains),
            app.EnvironmentVarArgs(
                name="OAUTH2_PROXY_CUSTOM_SIGN_IN_LOGO", value=self.config.oauth2_proxy_custom_sign_in_logo
            ),
            app.EnvironmentVarArgs(name="OAUTH2_PROXY_REVERSE_PROXY", value=self.config.oauth2_proxy_reverse_proxy),
            app.EnvironmentVarArgs(
                name="OAUTH2_PROXY_REDIRECT_URL",
                value=self.config.oauth2_proxy_redirect_url
                or f"https://{self.config.dagster_service}.{self.config.location.lower()}.azurecontainerapps.io",
            ),
            app.EnvironmentVarArgs(name="DAGSTER_PG_USERNAME", value=self.config.postgres_username),
            app.EnvironmentVarArgs(name="VERSION", value=self.config.version),
        ]

        return env_vars

    def _register_outputs(self):
        """Register outputs for this component"""
        self.register_outputs(
            {
                "dagster_app_name": self.dagster_app_service.name,
                # For Container Apps, the URL format is different from App Service
                "dagster_app_url": pulumi.Output.concat(
                    "https://", self.dagster_app_service.name, ".", self.config.container_app_domain
                ),
                "postgres_database_name": self.dagster_database.name,
                "datalake_name": self.datalake.name,
            }
        )
