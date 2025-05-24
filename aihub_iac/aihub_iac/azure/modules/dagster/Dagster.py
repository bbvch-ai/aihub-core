from typing import List, Optional

import pulumi
from pulumi_azure_native import app, dbforpostgresql, network

from aihub_iac.azure.constants.resources import CONTAINER_APP, STORAGE_ACCOUNT, SUB_NET
from aihub_iac.azure.constants.roles import ROLES
from aihub_iac.azure.modules.dagster.DagsterConfig import DagsterConfig
from aihub_iac.azure.providers.IdentityProvider import IdentityProvider
from aihub_iac.azure.providers.NetworkProvider import NetworkProvider
from aihub_iac.azure.providers.RoleProvider import RoleProvider
from aihub_iac.azure.resources.managed_environment.ManagedEnvironment import ManagedEnvironment
from aihub_iac.azure.resources.managed_environment.ManagedEnvironmentConfig import ManagedEnvironmentConfig
from aihub_iac.azure.resources.storage.StorageResourceFactory import StorageResourceFactory


class Dagster(pulumi.ComponentResource):
    """A Pulumi component resource for deploying Dagster infrastructure"""

    def __init__(self, stack: str, name: str, config: DagsterConfig, opts: Optional[pulumi.ResourceOptions] = None):
        super().__init__(f"{stack}:{name}", name, None, opts)

        self.name = name
        self.stack = stack
        self.config = config

        self.storage_factory = StorageResourceFactory(self.config, self.stack)

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

        self.role_provider = RoleProvider(self.config.subscription_id)

        # Create resources
        self._create_resources()

    @property
    def dagster_subnet_name(self):
        return f"{self.config.project_name}-{SUB_NET}-{self.config.location_short}-{CONTAINER_APP}-dagster"

    @property
    def dagster_storage_subnet_name(self):
        return f"{self.config.project_name}-{SUB_NET}-{self.config.location_short}-{STORAGE_ACCOUNT}-dagster"

    def _create_dagster_subnet(self) -> network.Subnet:
        subnet = network.Subnet(
            name=self.dagster_subnet_name,
            resource_name=self.dagster_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix=self.config.DAGSTER_SUBNET_CIDR,
        )
        self.network_provider.create_subnet_nsg(
            parent=self,
            stack=self.stack,
            subnet_name=self.dagster_subnet_name,
            subnet=subnet,
            source_prefixes=[self.config.DAGSTER_SUBNET_CIDR],
        )
        return subnet

    def _create_dagster_storage_subnet(self) -> network.Subnet:
        subnet = network.Subnet(
            name=self.dagster_storage_subnet_name,
            resource_name=self.dagster_storage_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix=self.config.DAGSTER_STORAGE_SUBNET_CIDR,
        )

        public_access_rules = [
            network.SecurityRuleArgs(
                name="AllowInternetToProxy",
                priority=200,
                direction="Inbound",
                access="Allow",
                protocol="Tcp",
                source_address_prefix="Internet",
                source_port_range="*",
                destination_address_prefix="*",
                destination_port_range="4180",
            )
        ]

        self.network_provider.create_subnet_nsg(
            parent=self,
            stack=self.stack,
            subnet_name=self.network_provider.dagster_storage_subnet_name,
            subnet=subnet,
            source_prefixes=[self.config.DAGSTER_SUBNET_CIDR, self.config.DAGSTER_STORAGE_SUBNET_CIDR],
            additional_rules=public_access_rules,
        )
        return subnet

    def _create_resources(self):
        """Create all Dagster infrastructure resources"""
        # Get existing resources
        self.vnet = self.network_provider.get_vnet()
        self.existing_cap_subnet = self._create_dagster_subnet()
        self.dagster_storage_subnet = self._create_dagster_storage_subnet()

        # Create new resources
        self.dagster_database = self._create_postgres_database()
        self.blob_dns_zone = network.get_private_zone(
            private_zone_name="privatelink.blob.core.windows.net", resource_group_name=self.config.resource_group
        )

        self.datalake = pulumi.Output.all(subnet_id=self.dagster_storage_subnet.id).apply(
            lambda args: self.storage_factory.create_storage_account(
                service_name=self.config.storage_service_name,
                subnet_id=args["subnet_id"],
                vnet_id=self.vnet.id,
                blob_only=True,
                existing_blob_dns_zone=self.blob_dns_zone,
            )
        )

        self.identity = self._create_identity()
        # Assign Storage Blob Contributor Role
        self.identity.assign_role_to_identity(
            ROLES.STORAGE_BLOB_DATA_CONTRIBUTOR, self.datalake.id, self.config.storage_service_name
        )

        managed_env_config = ManagedEnvironmentConfig(
            resource_group=self.config.resource_group,
            project_name=self.config.project_name,
            location=self.config.location,
            location_short=self.config.location_short,
            name="dagster",
        )

        self.managed_environment = ManagedEnvironment(
            stack=self.stack,
            name="managed-environment",
            config=managed_env_config,
            infrastructure_subnet_id=self.existing_cap_subnet.id,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.dagster_webserver_app = self._create_dagster_webserver_app()
        self.dagster_daemon_app = self._create_dagster_daemon_app()

        # Export outputs
        self._register_outputs()

    def _create_identity(self):
        """Create and configure the managed identity"""
        return self.identity_provider.create_identity(self.name, self.stack)

    def _create_postgres_database(self):
        """Create the Dagster database on the Postgres server"""
        return dbforpostgresql.Database(
            resource_name=self.config.database_name,
            resource_group_name=self.config.resource_group,
            server_name=self.config.postgres_name,
            opts=pulumi.ResourceOptions(parent=self),
        )

    def _create_proxy_container(self):
        return app.ContainerArgs(
            name="oauth2proxy",
            image="ghcr.io/bbvch-ai/bbvch-ai/oauth2-proxy:latest",
            resources=app.ContainerResourcesArgs(
                cpu=self.config.proxy_cpu,
                memory=self.config.proxy_memory,
            ),
            env=[
                app.EnvironmentVarArgs(name="OAUTH2_PROXY_HTTP_ADDRESS", value="0.0.0.0:4180"),
                app.EnvironmentVarArgs(name="OAUTH2_PROXY_COOKIE_SECURE", value="false"),
                app.EnvironmentVarArgs(name="OAUTH2_PROXY_CODE_CHALLENGE_METHOD", value="S256"),
                app.EnvironmentVarArgs(
                    name="OAUTH2_PROXY_UPSTREAMS", value="http://localhost:8000"
                ),  # Updated for Container Apps
                app.EnvironmentVarArgs(
                    name="OAUTH2_PROXY_ALLOWED_GROUPS", value=self.config.oauth2_proxy_allowed_groups
                ),
                app.EnvironmentVarArgs(
                    name="OAUTH2_PROXY_OIDC_GROUPS_CLAIM", value=self.config.oauth2_proxy_oidc_groups_claim
                ),
                # Add the original OAuth2 proxy env vars
                app.EnvironmentVarArgs(name="OAUTH2_PROXY_CLIENT_ID", value=self.config.oauth2_proxy_client_id),
                app.EnvironmentVarArgs(name="OAUTH2_PROXY_AZURE_TENANT", value=self.config.oauth2_proxy_azure_tenant),
                app.EnvironmentVarArgs(name="OAUTH2_PROXY_PROVIDER", value=self.config.oauth2_proxy_provider),
                app.EnvironmentVarArgs(
                    name="OAUTH2_PROXY_OIDC_ISSUER_URL", value=self.config.oauth2_proxy_oidc_issuer_url
                ),
                app.EnvironmentVarArgs(name="OAUTH2_PROXY_COOKIE_SECRET", secret_ref="oauth2-proxy-cookie-secret"),
                app.EnvironmentVarArgs(name="OAUTH2_PROXY_CLIENT_SECRET", secret_ref="oauth2-proxy-client-secret"),
                app.EnvironmentVarArgs(name="OAUTH2_PROXY_EMAIL_DOMAINS", value=self.config.oauth2_proxy_email_domains),
                app.EnvironmentVarArgs(
                    name="OAUTH2_PROXY_CUSTOM_SIGN_IN_LOGO", value=self.config.oauth2_proxy_custom_sign_in_logo
                ),
                app.EnvironmentVarArgs(name="OAUTH2_PROXY_REVERSE_PROXY", value=self.config.oauth2_proxy_reverse_proxy),
                app.EnvironmentVarArgs(
                    name="OAUTH2_PROXY_REDIRECT_URL",
                    value=self.config.oauth2_proxy_redirect_url
                    or f"https://{self.config.dagster_webserver}.{self.config.container_app_domain}",
                ),
            ],
        )

    def _create_dagster_webserver_container(self):
        return app.ContainerArgs(
            name="dagster-service",
            image=self.config.effective_docker_image,
            resources=app.ContainerResourcesArgs(
                cpu=self.config.webserver_cpu,
                memory=self.config.webserver_memory,
            ),
            env=self._get_dagster_service_and_daemon_env_vars(),
        )

    def _create_dagster_daemon_container(self):
        return app.ContainerArgs(
            name="dagster-daemon",
            image=self.config.effective_docker_image,
            resources=app.ContainerResourcesArgs(
                cpu=self.config.daemon_cpu,
                memory=self.config.daemon_memory,
            ),
            command=["make", "dagster-daemon"],
            env=self._get_dagster_service_and_daemon_env_vars(),
        )

    def _get_dagster_service_and_daemon_env_vars(self) -> List[app.EnvironmentVarArgs]:
        """Get environment variables for the Dagster Service container"""
        env_vars = [
            app.EnvironmentVarArgs(name="PYTHONUNBUFFERED", value="1"),
            app.EnvironmentVarArgs(name="DAGSTER_HOME", value="/dagster_home"),
            # Add database connection info
            app.EnvironmentVarArgs(
                name="DAGSTER_PG_HOST",
                value=f"{self.config.postgres_name}.postgres.database.azure.com",
            ),
            app.EnvironmentVarArgs(name="DAGSTER_PG_DB", value=f"{self.config.database_name}"),
            app.EnvironmentVarArgs(name="DAGSTER_PG_USERNAME", value=self.config.postgres_username),
            app.EnvironmentVarArgs(name="DAGSTER_PG_PASSWORD", secret_ref="postgres-password"),
            # Add Azure-specific variables
            app.EnvironmentVarArgs(name="APP_NAME", value=self.config.project_name),
            app.EnvironmentVarArgs(name="AZURE_SUBSCRIPTION_ID", value=self.config.subscription_id),
            app.EnvironmentVarArgs(name="REGION_SHORT", value=self.config.location_short),
            app.EnvironmentVarArgs(name="VERSION", value=self.config.version),
            app.EnvironmentVarArgs(name="AZURE_CLIENT_ID", value=self.identity.client_id),
        ]

        # Add any additional environment variables from the config
        for name, value in self.config.additional_env_vars.items():
            # Check if the value is a secret reference
            if isinstance(value, dict) and "secret_ref" in value:
                env_vars.append(app.EnvironmentVarArgs(name=name, secret_ref=value["secret_ref"]))
            else:
                env_vars.append(app.EnvironmentVarArgs(name=name, value=str(value)))

        return env_vars

    def _additional_secrets_from_additional_env_vars(self) -> List[app.SecretArgs]:
        additional_secrets = []
        for name, value in self.config.additional_env_vars.items():
            if isinstance(value, dict) and "secret_ref" in value and "secret_value" in value:
                additional_secrets.append(app.SecretArgs(name=value["secret_ref"], value=value["secret_value"]))
        return additional_secrets

    def _create_dagster_webserver_app(self):
        """Create the Dagster Container App using an existing managed environment"""
        # Create the Container App

        return app.ContainerApp(
            container_app_name=self.config.dagster_webserver,
            resource_name=self.config.dagster_webserver,
            resource_group_name=self.config.resource_group,
            location=self.config.location,
            managed_environment_id=self.managed_environment.id,
            identity=app.ManagedServiceIdentityArgs(
                type=app.ManagedServiceIdentityType.USER_ASSIGNED,
                user_assigned_identities=[self.identity.user_identity],
            ),
            configuration=app.ConfigurationArgs(
                ingress=app.IngressArgs(
                    external=True,
                    target_port=4180,
                    allow_insecure=False,
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
                    *self._additional_secrets_from_additional_env_vars(),
                ],
            ),
            template=app.TemplateArgs(
                containers=[self._create_proxy_container(), self._create_dagster_webserver_container()],
                scale=app.ScaleArgs(
                    min_replicas=self.config.webserver_min_replicas,
                    max_replicas=self.config.webserver_max_replicas,
                ),
            ),
            tags={
                "Stack": self.stack,
            },
            opts=pulumi.ResourceOptions(parent=self),
        )

    def _create_dagster_daemon_app(self):
        """Create the Dagster Container App using an existing managed environment"""
        # Create the Container App
        return app.ContainerApp(
            container_app_name=self.config.dagster_daemon,
            resource_name=self.config.dagster_daemon,
            resource_group_name=self.config.resource_group,
            location=self.config.location,
            managed_environment_id=self.managed_environment.id,
            identity=app.ManagedServiceIdentityArgs(
                type=app.ManagedServiceIdentityType.USER_ASSIGNED,
                user_assigned_identities=[self.identity.user_identity],
            ),
            configuration=app.ConfigurationArgs(
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
                    *self._additional_secrets_from_additional_env_vars(),
                ],
            ),
            template=app.TemplateArgs(
                containers=[self._create_dagster_daemon_container()],
                scale=app.ScaleArgs(
                    min_replicas=1,
                    max_replicas=1,
                ),
            ),
            tags={
                "Stack": self.stack,
            },
            opts=pulumi.ResourceOptions(parent=self),
        )

    def _register_outputs(self):
        """Register outputs for this component"""
        self.register_outputs(
            {
                "postgres_database_name": self.dagster_database.name,
                "datalake_name": self.datalake.name,
            }
        )
