import pulumi

from pulumi_azure_native import web, documentdb

from aihub_iac.azure.constants.resources import APP_SERVICE, COSMOS
from aihub_iac.azure.constants.roles import ROLES
from aihub_iac.azure.modules.bot.BotConfig import BotConfig
from aihub_iac.azure.providers.EnvVariableProvider import EnvVariableProvider
from aihub_iac.azure.providers.IdentityProvider import IdentityProvider
from aihub_iac.azure.providers.NetworkProvider import NetworkProvider
from aihub_iac.azure.providers.WebAppCreator import WebAppCreator


class Bot(pulumi.ComponentResource):
    def __init__(self, stack, name, opts=None):
        super().__init__(f"{stack}:{name}", name, None, opts)
        self.stack = stack
        self.name = name
        self.project_name, self.location, self.location_short, self.resource_group, self.subscription_id = (
            EnvVariableProvider.get_environment_variables()
        )

        self.service_name = f"{self.project_name}-{APP_SERVICE}-{self.location_short}-bot"
        self.cosmos_name = f"{self.project_name}-{COSMOS}-{self.location_short}-api"

        self.network_provider = NetworkProvider(self.resource_group, self.project_name, self.location_short)
        self.identity_provider = IdentityProvider(
            self.resource_group, self.location, self.subscription_id, self.project_name, self.location_short
        )
        self.webapp_creator = WebAppCreator(
            self.service_name, self.resource_group, self.location, BotConfig().BOT_APP_SERVICE_PLAN_NAME
        )

        # API specific configuration
        self.registry_url = "https://ghcr.io"
        self.docker_image = f"DOCKER|{BotConfig().BOT_REPO_IMAGE_URL}:{BotConfig().BOT_IMAGE_TAG}"

        self.api_db_name = BotConfig().COSMOS_ACCOUNT_NAME or self.cosmos_name
        self.api_db_ressource_group = BotConfig().COSMOS_RESOURCE_GROUP_NAME or self.resource_group
        self.api_db = self._get_api_db()

        self.vnet = self.network_provider.get_vnet()
        self.subnet = self.network_provider.get_subnet()

        self.identity = self.identity_provider.create_identity(self.name)
        self.identity.assign_openai_user()
        self.identity.assign_role_to_identity(
            role=ROLES.DB_ACCOUNT_CONTRIBUTOR_ROLE_ID, scope_id=self.api_db.id, scope_name=self.api_db.name
        )

        self.identity.assign_role_to_identity(
            role=ROLES.CONTRIBUTOR_ROLE_ID, scope_id=self.api_db.id, scope_name=self.api_db.name
        )

        self._create_webapp()

    def _get_api_db(self):
        return documentdb.get_database_account(
            account_name=self.api_db_name,
            resource_group_name=self.api_db_ressource_group,
        )

    def _create_webapp(self):
        app_settings = [
            web.NameValuePairArgs(name="WEBSITES_PORT", value="8001"),
            web.NameValuePairArgs(name="DOCKER_REGISTRY_SERVER_URL", value=self.registry_url),
            web.NameValuePairArgs(name="DOCKER_REGISTRY_SERVER_USERNAME", value=BotConfig().REGISTRY_USER),
            web.NameValuePairArgs(name="DOCKER_REGISTRY_SERVER_PASSWORD", value=BotConfig().REGISTRY_PAT),
            web.NameValuePairArgs(name="AZURE_SUBSCRIPTION_ID", value=self.subscription_id),
            web.NameValuePairArgs(name="COSMOS_RESOURCE_GROUP_NAME", value=self.api_db_ressource_group),
            web.NameValuePairArgs(name="COSMOS_ACCOUNT_NAME", value=self.api_db_name),
            web.NameValuePairArgs(name="CLIENT_ID", value=BotConfig().CLIENT_ID),
            web.NameValuePairArgs(name="TENANT_ID", value=BotConfig().TENANT_ID),
            web.NameValuePairArgs(name="AUTHORITY_URL", value=BotConfig().AUTHORITY_URL),
            web.NameValuePairArgs(name="NATS_ENDPOINT", value=BotConfig().NATS_ENDPOINT),
            web.NameValuePairArgs(name="VERSION", value=BotConfig().VERSION),
            web.NameValuePairArgs(name="REGION_SHORT", value=self.location_short),
            web.NameValuePairArgs(name="APP_NAME", value=self.project_name),
            web.NameValuePairArgs(name="NAME", value=BotConfig().BOT_ANONYM_NAME),
            web.NameValuePairArgs(name="EMAIL", value=BotConfig().BOT_ANONYM_EMAIL),
            web.NameValuePairArgs(name="ROLES", value=BotConfig().BOT_ANONYM_ROLES),
            web.NameValuePairArgs(name="OID", value=BotConfig().BOT_ANONYM_OID),
            web.NameValuePairArgs(name="AZURE_CLIENT_ID", value=self.identity.client_id),
        ]

        identity = web.ManagedServiceIdentityArgs(
            type=web.ManagedServiceIdentityType.USER_ASSIGNED, user_assigned_identities=[self.identity.user_identity]
        )

        return self.webapp_creator.create_webapp(
            docker_image=self.docker_image,
            app_settings=app_settings,
            identity=identity,
            subnet_id=self.subnet.id,
        )
