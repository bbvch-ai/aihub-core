import pulumi
from pulumi_azure_native import containerinstance, cosmosdb, web

from aihub_iac.azure.constants.roles import ROLES
from aihub_iac.azure.modules.api.ApiConfig import ApiConfig
from aihub_iac.azure.providers.IdentityProvider import IdentityProvider
from aihub_iac.azure.providers.NetworkProvider import NetworkProvider
from aihub_iac.azure.providers.WebAppCreator import WebAppCreator


class Api(pulumi.ComponentResource):
    """A Pulumi component resource for deploying API services"""

    def __init__(
        self,
        stack: str,
        name: str,
        config: ApiConfig,
        opts: pulumi.ResourceOptions | None = None,
    ):
        super().__init__(f"{stack}:{name}", name, None, opts)

        self.name = name
        self.stack = stack
        # Create configuration from environment or use provided config
        self.config = config

        # Initialize providers
        self.network_provider = NetworkProvider(
            self.config.resource_group, self.config.project_name, self.config.location, self.config.location_short
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

        # Create resources in the right order with proper dependencies
        self._create_resources()

    def _create_resources(self):
        """Create all required resources with proper dependency management"""
        # Step 1: Get networking resources
        self.vnet = self.network_provider.get_vnet()
        self.subnet = self.network_provider.get_app_subnet()

        # Step 2: Get the Cosmos DB resource
        self.api_db = self._get_api_db()

        # Step 3: Set up identity and assign roles
        self.identity = self._create_identity()

        # Step 4: Create the web app
        self.webapp = self._create_webapp()

        # Export important outputs
        self.register_outputs(
            {
                "webapp_id": self.webapp.id,
                "webapp_name": self.webapp.name,
                "webapp_url": self.webapp.default_host_name.apply(lambda host_name: f"https://{host_name}"),
            }
        )

    def _get_nats_container_group_private_ip(self) -> str:
        container_group = containerinstance.get_container_group(
            container_group_name=self.config.nats_container_group_name,
            resource_group_name=self.config.resource_group,
        )
        if container_group.ip_address is not None and container_group.ip_address.ip is not None:
            return container_group.ip_address.ip
        else:
            raise ValueError(f"No private IP found for container group {container_group.name}")

    def _get_api_db(self) -> cosmosdb.GetDatabaseAccountResult:
        """Get the Cosmos DB account"""
        return cosmosdb.get_database_account(
            account_name=self.config.effective_cosmos_account_name,
            resource_group_name=self.config.effective_cosmos_resource_group,
        )

    def _create_identity(self):
        """Create and configure the managed identity"""
        identity = self.identity_provider.create_identity(self.name, self.stack)

        # Assign required roles
        identity.assign_role_to_identity(
            role=ROLES.DB_ACCOUNT_CONTRIBUTOR_ROLE_ID,
            scope_id=self.api_db.id,
            scope_name=self.api_db.name,
        )

        identity.assign_role_to_identity(
            role=ROLES.CONTRIBUTOR_ROLE_ID, scope_id=self.api_db.id, scope_name=self.api_db.name
        )

        return identity

    def _create_webapp(self):
        """Create the web app with all required configuration"""
        nats_ip = self._get_nats_container_group_private_ip()
        app_settings = [
            *self._get_base_env(),
            *self._get_registry_env(),
            *self._get_oauth_env(),
            web.NameValuePairArgs(name="WEBSITES_PORT", value="8000"),
            web.NameValuePairArgs(name="COSMOS_RESOURCE_GROUP_NAME", value=self.config.effective_cosmos_resource_group),
            web.NameValuePairArgs(name="COSMOS_ACCOUNT_NAME", value=self.config.effective_cosmos_account_name),
            web.NameValuePairArgs(name="NATS_ENDPOINT", value=f"nats://{nats_ip}:4222"),
            web.NameValuePairArgs(name="VERSION", value=self.config.version),
            web.NameValuePairArgs(name="NAME", value=self.config.anonym_name),
            web.NameValuePairArgs(name="EMAIL", value=self.config.anonym_email),
            web.NameValuePairArgs(name="ROLES", value=self.config.anonym_roles),
            web.NameValuePairArgs(name="OID", value=self.config.anonym_oid),
            web.NameValuePairArgs(name="AZURE_CLIENT_ID", value=self.identity.client_id),
        ]

        identity = web.ManagedServiceIdentityArgs(
            type=web.ManagedServiceIdentityType.USER_ASSIGNED, user_assigned_identities=[self.identity.user_identity]
        )

        return self.webapp_creator.create_webapp(
            docker_image=self.config.effective_docker_image,
            app_settings=app_settings,
            identity=identity,
            subnet_id=self.subnet.id,
            stack=self.stack,
        )

    def _get_base_env(self) -> list[web.NameValuePairArgs]:
        """Get base environment variables for subscription, app name and region"""
        return [
            web.NameValuePairArgs(name="AZURE_SUBSCRIPTION_ID", value=self.config.subscription_id),
            web.NameValuePairArgs(name="REGION_SHORT", value=self.config.location_short),
            web.NameValuePairArgs(name="APP_NAME", value=self.config.project_name),
        ]

    def _get_registry_env(self) -> list[web.NameValuePairArgs]:
        """Get environment variables for the docker registry"""
        return [
            web.NameValuePairArgs(name="DOCKER_REGISTRY_SERVER_URL", value=self.config.registry_url),
            web.NameValuePairArgs(name="DOCKER_REGISTRY_SERVER_USERNAME", value=self.config.registry_user),
            web.NameValuePairArgs(name="DOCKER_REGISTRY_SERVER_PASSWORD", value=self.config.registry_pat),
        ]

    def _get_oauth_env(self) -> list[web.NameValuePairArgs]:
        """Get environment variables for the oAuth"""
        return [
            web.NameValuePairArgs(name="CLIENT_ID", value=self.config.client_id),
            web.NameValuePairArgs(name="TENANT_ID", value=self.config.tenant_id),
            web.NameValuePairArgs(name="AUTHORITY_URL", value=self.config.authority_url),
        ]
