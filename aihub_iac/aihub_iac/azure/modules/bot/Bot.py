from typing import Optional, List

import pulumi

from pulumi_azure_native import web, documentdb

from aihub_iac.azure.constants.roles import ROLES
from aihub_iac.azure.modules.bot.BotConfig import BotConfig
from aihub_iac.azure.providers.IdentityProvider import IdentityProvider
from aihub_iac.azure.providers.NetworkProvider import NetworkProvider
from aihub_iac.azure.providers.WebAppCreator import WebAppCreator


class Bot(pulumi.ComponentResource):
    """A Pulumi component resource for deploying Bot services"""

    def __init__(self, stack: str, name: str, config: BotConfig, opts: Optional[pulumi.ResourceOptions] = None):
        super().__init__(f"{stack}:{name}", name, None, opts)

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
            self.config.service_name,
            self.config.resource_group,
            self.config.location,
            self.config.app_service_plan_name,
        )

        self._create_resources()

    def _create_resources(self):
        """Create all required resources with proper dependency management"""
        self.vnet = self.network_provider.get_vnet()
        self.subnet = self.network_provider.app_subnet

        self.api_db = self._get_api_db()

        self.identity = self._create_identity()

        self.webapp = self._create_webapp()

        # Export important outputs
        self.register_outputs(
            {
                "webapp_id": self.webapp.id,
                "webapp_name": self.webapp.name,
                "webapp_url": self.webapp.default_host_name.apply(lambda host_name: f"https://{host_name}"),
                "identity_id": self.identity.principal_id,
            }
        )

    def _get_api_db(self) -> documentdb.GetDatabaseAccountResult:
        """Get the Cosmos DB account"""
        return documentdb.get_database_account(
            account_name=self.config.effective_cosmos_account_name(),
            resource_group_name=self.config.effective_cosmos_resource_group(),
        )

    def _create_identity(self):
        """Create and configure the managed identity"""
        identity = self.identity_provider.create_identity(self.config.name)

        # Assign required roles
        identity.assign_openai_user()
        identity.assign_role_to_identity(
            role=ROLES.DB_ACCOUNT_CONTRIBUTOR_ROLE_ID, scope_id=self.api_db.id, scope_name=self.api_db.name
        )

        identity.assign_role_to_identity(
            role=ROLES.CONTRIBUTOR_ROLE_ID, scope_id=self.api_db.id, scope_name=self.api_db.name
        )

        return identity

    def _create_webapp(self):
        """Create the web app with all required configuration"""
        app_settings = [
            *self._get_base_env(),
            *self._get_registry_env(),
            *self._get_oauth_env(),
            web.NameValuePairArgs(name="WEBSITES_PORT", value="8001"),
            web.NameValuePairArgs(
                name="COSMOS_RESOURCE_GROUP_NAME", value=self.config.effective_cosmos_resource_group()
            ),
            web.NameValuePairArgs(name="COSMOS_ACCOUNT_NAME", value=self.config.effective_cosmos_account_name()),
            web.NameValuePairArgs(name="NATS_ENDPOINT", value=self.config.nats_endpoint),
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
        )

    def _get_base_env(self) -> List[web.NameValuePairArgs]:
        """Get base environment variables for subscription, app name and region"""
        return [
            web.NameValuePairArgs(name="AZURE_SUBSCRIPTION_ID", value=self.config.subscription_id),
            web.NameValuePairArgs(name="REGION_SHORT", value=self.config.location_short),
            web.NameValuePairArgs(name="APP_NAME", value=self.config.project_name),
        ]

    def _get_registry_env(self) -> List[web.NameValuePairArgs]:
        """Get environment variables for the docker registry"""
        return [
            web.NameValuePairArgs(name="DOCKER_REGISTRY_SERVER_URL", value=self.config.registry_url),
            web.NameValuePairArgs(name="DOCKER_REGISTRY_SERVER_USERNAME", value=self.config.registry_user),
            web.NameValuePairArgs(name="DOCKER_REGISTRY_SERVER_PASSWORD", value=self.config.registry_pat),
        ]

    def _get_oauth_env(self) -> List[web.NameValuePairArgs]:
        """Get environment variables for the oAuth"""
        return [
            web.NameValuePairArgs(name="CLIENT_ID", value=self.config.client_id),
            web.NameValuePairArgs(name="TENANT_ID", value=self.config.tenant_id),
            web.NameValuePairArgs(name="AUTHORITY_URL", value=self.config.authority_url),
        ]
