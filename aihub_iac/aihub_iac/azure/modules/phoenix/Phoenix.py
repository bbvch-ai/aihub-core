import pulumi

from typing import List, Optional

from pulumi_azure_native import web, dbforpostgresql

from aihub_iac.azure.modules.phoenix.PhoenixConfig import PhoenixConfig
from aihub_iac.azure.providers.NetworkProvider import NetworkProvider
from aihub_iac.azure.providers.IdentityProvider import IdentityProvider
from aihub_iac.azure.providers.WebAppCreator import WebAppCreator


class Phoenix(pulumi.ComponentResource):
    """A Pulumi component resource for deploying Phoenix infrastructure"""

    def __init__(self, stack: str, name: str, config: PhoenixConfig, opts: Optional[pulumi.ResourceOptions] = None):
        super().__init__(f"{stack}:{name}", name, None, opts)

        self.name = name
        self.stack = stack
        # Create configuration from environment or use provided config
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

        self.webapp_creator = WebAppCreator(
            service_name=self.config.service_name,
            resource_group=self.config.resource_group,
            location=self.config.location,
            app_service_plan_name=self.config.app_service_plan_name,
        )

        # Create resources
        self._create_resources()

    def _create_resources(self):
        """Create all Phoenix infrastructure resources"""
        self.vnet = self.network_provider.get_vnet()
        self.subnet = self.network_provider.get_phoenix_subnet()

        # Step 2: Create postgres database on existing server
        self.phoenix_database = self._create_postgres_database()

        self.identity = self._create_identity()

        # Step 3: Create app service
        self.phoenix_app_service = self._create_phoenix_app_service()

        # Export outputs
        self._register_outputs()

    def _create_postgres_database(self):
        """Create the Phoenix database on the existing PostgreSQL server"""
        return dbforpostgresql.Database(
            resource_name=self.config.database_name,
            resource_group_name=self.config.resource_group,
            server_name=self.config.postgres_name,
            opts=pulumi.ResourceOptions(parent=self),
        )

    def _create_identity(self):
        """Create and configure the managed identity"""
        identity = self.identity_provider.create_identity(self.name, self.stack)
        return identity

    def _create_phoenix_app_service(self):
        """Create the Phoenix App Service"""
        server_name = self.config.postgres_name

        connection_string = self.phoenix_database.name.apply(
            lambda db_name: f"postgresql://{server_name}.postgres.database.azure.com:5432/{db_name}?user={self.config.postgres_username}&password={self.config.postgres_password}"
        )

        # Create the base app settings
        app_settings = [
            *self._get_oauth_env(),
            *self._get_registry_env(),
            web.NameValuePairArgs(name="WEBSITES_PORT", value="6006"),
            web.NameValuePairArgs(name="PHOENIX_SQL_DATABASE_URL", value=connection_string),
            web.NameValuePairArgs(name="PHOENIX_ENABLE_AUTH", value="True"),
            web.NameValuePairArgs(name="PHOENIX_SECRET", value=self.config.phoenix_secret),
            web.NameValuePairArgs(name="VERSION", value=self.config.version),
            web.NameValuePairArgs(name="AZURE_CLIENT_ID", value=self.identity.client_id),
        ]

        identity = web.ManagedServiceIdentityArgs(
            type=web.ManagedServiceIdentityType.USER_ASSIGNED, user_assigned_identities=[self.identity.user_identity]
        )

        # Create the web app
        return self.webapp_creator.create_webapp(
            docker_image=self.config.effective_docker_image,
            app_settings=app_settings,
            identity=identity,
            subnet_id=self.subnet.id,
            stack=self.stack,
        )

    def _get_oauth_env(self) -> List[web.NameValuePairArgs]:
        """Get environment variables for the oAuth"""
        return [
            web.NameValuePairArgs(name="PHOENIX_OAUTH2_MICROSOFT_ENTRA_ID_CLIENT_ID", value=self.config.client_id),
            web.NameValuePairArgs(
                name="PHOENIX_OAUTH2_MICROSOFT_ENTRA_ID_CLIENT_SECRET", value=self.config.client_secret
            ),
            web.NameValuePairArgs(
                name="PHOENIX_OAUTH2_MICROSOFT_ENTRA_ID_OIDC_CONFIG_URL", value=self.config.oidc_config_url
            ),
        ]

    def _get_registry_env(self) -> List[web.NameValuePairArgs]:
        """Get environment variables for the docker registry"""
        return [
            web.NameValuePairArgs(name="DOCKER_REGISTRY_SERVER_URL", value=self.config.registry_url),
            web.NameValuePairArgs(name="DOCKER_REGISTRY_SERVER_USERNAME", value=self.config.registry_user),
            web.NameValuePairArgs(name="DOCKER_REGISTRY_SERVER_PASSWORD", value=self.config.registry_pat),
        ]

    def _register_outputs(self):
        """Register outputs for this component"""
        # Get the server name (either from config or using the resource namer)
        self.register_outputs(
            {
                "phoenix_app_name": self.phoenix_app_service.name,
                "phoenix_app_url": self.phoenix_app_service.default_host_name.apply(
                    lambda host_name: f"https://{host_name}"
                ),
                "postgres_server_name": self.config.postgres_name,
                "postgres_database_name": self.phoenix_database.name,
            }
        )
