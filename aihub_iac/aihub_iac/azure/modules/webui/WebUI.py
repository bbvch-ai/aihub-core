from typing import List, Optional

import pulumi
from pulumi_azure_native import app, containerinstance, dbforpostgresql, network

from aihub_iac.azure.constants.resources import (
    CONTAINER_APP,
    CONTAINER_APP_ENVIRONMENT,
    CONTAINER_INSTANCE,
    POSTGRES,
    STORAGE_ACCOUNT,
    SUB_NET,
)
from aihub_iac.azure.modules.nats.NatsConfig import NatsConfig
from aihub_iac.azure.modules.webui.WebUIConfig import WebUIConfig
from aihub_iac.azure.providers.NetworkProvider import NetworkProvider
from aihub_iac.azure.resources.managed_environment.ManagedEnvironment import ManagedEnvironment
from aihub_iac.azure.resources.managed_environment.ManagedEnvironmentConfig import ManagedEnvironmentConfig
from aihub_iac.azure.resources.storage.StorageResourceFactory import StorageResourceFactory


class WebUI(pulumi.ComponentResource):
    def __init__(
        self,
        stack: str,
        name: str,
        config: WebUIConfig,
        opts: Optional[pulumi.ResourceOptions] = None,
    ):
        super().__init__(f"{stack}:{name}", name, None, opts)

        self.name = name
        self.stack = stack
        self.config = config

        self.storage_factory = StorageResourceFactory(self.config, self.stack)
        self.network_provider = NetworkProvider(
            self.config.resource_group, self.config.project_name, self.config.location, self.config.location_short
        )

        # Initialize resources
        self.log_analytics_workspace = None
        self.log_analytics_customer_id = None
        self.log_analytics_shared_key = None
        self.managed_environment = None
        self.storage_account = None
        self.storage_account_key = None
        self.file_shares = {}
        self.env_storages = {}
        self.containers = {}
        self.app_volumes = []
        self.container_app = None

        # Create resources
        self._create_resources()

    @property
    def webui_subnet_name(self):
        return f"{self.config.project_name}-{SUB_NET}-{self.config.location_short}-{CONTAINER_APP}-webui"

    @property
    def webui_storage_subnet_name(self):
        return f"{self.config.project_name}-{SUB_NET}-{self.config.location_short}-{STORAGE_ACCOUNT}-webui"

    def _create_webui_subnet(self) -> network.Subnet:
        subnet = network.Subnet(
            name=self.webui_subnet_name,
            resource_name=self.webui_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix=self.config.WEBUI_SUBNET_CIDR,
        )
        self.network_provider.create_subnet_nsg(
            parent=self,
            stack=self.stack,
            subnet_name=self.webui_subnet_name,
            subnet=subnet,
            source_prefixes=[self.config.WEBUI_SUBNET_CIDR],
        )
        return subnet

    def _create_webui_storage_subnet(self) -> network.Subnet:
        subnet = network.Subnet(
            name=self.webui_storage_subnet_name,
            resource_name=self.webui_storage_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix=self.config.WEBUI_STORAGE_SUBNET_CIDR,
        )
        self.network_provider.create_subnet_nsg(
            parent=self,
            stack=self.stack,
            subnet_name=self.webui_storage_subnet_name,
            subnet=subnet,
            source_prefixes=[NatsConfig.NATS_SUBNET_CIDR, self.config.WEBUI_STORAGE_SUBNET_CIDR],
        )
        return subnet

    def _create_resources(self):
        """Create all container app resources in the correct order"""
        # Step 1: Get network resources
        self.vnet = self.network_provider.get_vnet()
        self.webui_subnet = self._create_webui_subnet()
        self.webui_storage_subnet = self._create_webui_storage_subnet()

        self.blob_dns_zone = network.get_private_zone(
            private_zone_name="privatelink.blob.core.windows.net", resource_group_name=self.config.resource_group
        )
        self.file_dns_zone = network.get_private_zone(
            private_zone_name="privatelink.file.core.windows.net", resource_group_name=self.config.resource_group
        )

        self.storage_account = pulumi.Output.all(subnet_id=self.webui_storage_subnet.id).apply(
            lambda args: self.storage_factory.create_storage_account(
                service_name=self.config.storage_service_name,
                subnet_id=args["subnet_id"],
                vnet_id=self.vnet.id,
                existing_blob_dns_zone=self.blob_dns_zone,
                existing_file_dns_zone=self.file_dns_zone,
            )
        )

        self.storage_account_key = self.storage_factory.get_storage_account_key(self.storage_account)

        self.webui_file_share = self.storage_factory.create_file_share("webui", self.storage_account)

        managed_env_config = ManagedEnvironmentConfig(
            resource_group=self.config.resource_group,
            project_name=self.config.project_name,
            location=self.config.location,
            location_short=self.config.location_short,
            name="webui",
        )

        self.managed_environment = ManagedEnvironment(
            stack=self.stack,
            name="managed-environment",
            config=managed_env_config,
            infrastructure_subnet_id=self.webui_subnet.id,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.env_storage = self._create_managed_environments_storage()

        self.app_volumes = [
            app.VolumeArgs(
                name=self.config.volume_name,
                storage_name=self.config.volume_name,
            )
        ]

        # Step 6: Create container configurations
        self.containers["openwebui"] = self._create_openwebui_container()

        # Step 7: Create the container app
        self.container_app = self._create_container_app()

        self.pg_server = self._get_postgres_server()
        self.pg_db = self._create_postgres_db()
        self.pg_vector_db = self._create_pgvector_db()

        # Export outputs
        self.register_outputs(
            {
                "container_app_name": self.container_app.name,
                "container_app_url": self.container_app.latest_revision_fqdn.apply(
                    lambda fqdn: f"https://{fqdn}" if fqdn else None
                ),
            }
        )

    def _get_postgres_server(self):
        return dbforpostgresql.get_server(
            resource_group_name=self.config.resource_group,
            server_name=f"{self.config.project_name}-{POSTGRES}-{self.config.location_short}",
        )

    def _create_postgres_db(self):
        return dbforpostgresql.Database(
            resource_name=self.config.db_name,
            resource_group_name=self.config.resource_group,
            server_name=self.config.postgres_name,
            opts=pulumi.ResourceOptions(parent=self),
        )

    def _create_pgvector_db(self):
        database = dbforpostgresql.Database(
            resource_name=self.config.pg_vector_db_name,
            resource_group_name=self.config.resource_group,
            server_name=self.config.postgres_name,
            opts=pulumi.ResourceOptions(parent=self),
        )
        return database

    def _create_managed_environments_storage(self):
        """Create managed environment storage for a volume"""
        return app.ManagedEnvironmentsStorage(
            resource_name=self.config.volume_name,
            environment_name=f"{self.config.project_name}-{CONTAINER_APP_ENVIRONMENT}-{self.config.location_short}-webui",
            properties=app.ManagedEnvironmentStoragePropertiesArgs(
                azure_file=app.AzureFilePropertiesArgs(
                    access_mode=app.AccessMode.READ_WRITE,
                    account_key=self.storage_account_key,
                    account_name=self.storage_account.name,
                    share_name=self.webui_file_share.name,
                )
            ),
            resource_group_name=self.config.resource_group,
            storage_name=self.config.volume_name,
            opts=pulumi.ResourceOptions(parent=self, depends_on=[self.managed_environment]),
        )

    def _create_openwebui_container(self):
        """Create the OpenWebUI container configuration"""
        api_service_url = f"https://{self.config.api_service_name}.azurewebsites.net/api/v1/openai"

        nats_ip = self._get_nats_private_ip()

        default_env_vars = {
            # Tracking & Telemetry
            "SCARF_NO_ANALYTICS": "true",
            "DO_NOT_TRACK": "true",
            "ANONYMIZED_TELEMETRY": "true",
            # Websocket support
            "ENABLE_WEBSOCKET_SUPPORT": "true",
            "WEBSOCKET_MANAGER": "redis",
            "WEBSOCKET_REDIS_URL": f"redis://{nats_ip}:6379/1",
            "WEB_CONCURRENCY": "4",
            # UI and Security
            "CORS_ALLOW_ORIGIN": "http://localhost:3000",
            "RESET_CONFIG_ON_START": "true",
            "ENABLE_SIGNUP": "false",
            "ENABLE_LOGIN_FORM": "false",
            "ENABLE_ADMIN_EXPORT": "true",
            "ENABLE_ADMIN_CHAT_ACCESS": "true",
            "ENABLE_CHANNELS": "false",
            "SHOW_ADMIN_DETAILS": "true",
            "DEFAULT_USER_ROLE": "user",
            "WEBUI_NAME": self.config.openwebui_config.webui_name,
            "ADMIN_EMAIL": self.config.openwebui_config.admin_email,
            "DEFAULT_LOCALE": self.config.openwebui_config.default_locale,
            # API settings
            "ENABLE_OLLAMA_API": "false",
            "ENABLE_OPENAI_API": "true",
            "PRESERVE_METADATA_IN_OPENAI_API_CALLS": "true",
            "OPENAI_API_BASE_URL": api_service_url,
            "RAG_OPENAI_API_BASE_URL": api_service_url,
            "AUDIO_STT_OPENAI_API_BASE_URL": api_service_url,
            "AUDIO_TTS_OPENAI_API_BASE_URL": api_service_url,
            "IMAGES_OPENAI_API_BASE_URL": api_service_url,
            # API Keys
            "OPENAI_API_KEY": self.config.openwebui_config.openai_api_key,
            "RAG_OPENAI_API_KEY": self.config.openwebui_config.rag_openai_api_key,
            "AUDIO_STT_OPENAI_API_KEY": self.config.openwebui_config.audio_stt_openai_api_key,
            "AUDIO_TTS_OPENAI_API_KEY": self.config.openwebui_config.audio_tts_openai_api_key,
            "IMAGES_OPENAI_API_KEY": self.config.openwebui_config.images_openai_api_key,
            # Image Generation
            "ENABLE_IMAGE_GENERATION": "true",
            "IMAGE_GENERATION_ENGINE": "openai",
            "IMAGE_SIZE": "1792x1024",
            "IMAGE_GENERATION_MODEL": "dall-e-3",
            # Task / Model settings
            "TASK_MODEL_EXTERNAL": "unsloth/Llama-3.2-1B-Instruct",
            # Autocomplete Generation
            "ENABLE_AUTOCOMPLETE_GENERATION": "true",
            "AUTOCOMPLETE_GENERATION_INPUT_MAX_LENGTH": "60",
            # Retrieval Augmented Generation (RAG) settings
            "VECTOR_DB": "pgvector",
            "RAG_EMBEDDING_ENGINE": "openai",
            "RAG_EMBEDDING_MODEL": "text-embedding-3-large",
            "RAG_EMBEDDING_OPENAI_BATCH_SIZE": "8",
            "RAG_TOP_K": "3",
            "RAG_RELEVANCE_THRESHOLD": "0.5",
            "CHUNK_SIZE": "1024",
            "CHUNK_OVERLAP": "256",
            "PDF_EXTRACT_IMAGES": "true",
            "RAG_FILE_MAX_SIZE": "1024",
            "RAG_FILE_MAX_COUNT": "10",
            "ENABLE_RETRIEVAL_QUERY_GENERATION": "true",
            # PGvec connection
            "PGVECTOR_DB_URL": self.connection_string_sqlalchemy_pg_vector,
            # Web Search & Query Generation
            "ENABLE_RAG_WEB_SEARCH": "true",
            "ENABLE_SEARCH_QUERY_GENERATION": "true",
            "RAG_WEB_SEARCH_RESULT_COUNT": "3",
            "RAG_WEB_SEARCH_ENGINE": "jina",
            "JINA_API_KEY": self.config.openwebui_config.jina_api_key,
            # Audio settings
            "AUDIO_STT_ENGINE": "openai",
            "AUDIO_STT_MODEL": "whisper-1",
            "AUDIO_TTS_ENGINE": "openai",
            "AUDIO_TTS_MODEL": "tts-1-hd",
            "AUDIO_TTS_VOICE": "alloy",
            # API Key enforcement
            "ENABLE_API_KEY": "false",
            "WEBUI_URL": "http://localhost:3000",
            # OAuth Settings
            "ENABLE_OAUTH_SIGNUP": "true",
            "OAUTH_CLIENT_ID": self.config.openwebui_config.oidc_client_id,
            "OAUTH_CLIENT_SECRET": self.config.openwebui_config.oidc_client_secret,
            "OPENID_PROVIDER_URL": self.config.openwebui_config.oidc_provider_url,
            "OAUTH_PROVIDER_NAME": self.config.openwebui_config.oidc_provider_name,
            # Postgres
            "DATABASE_URL": self.connection_string_sqlalchemy_pg,
            # User Credentials
            "ENABLE_FORWARD_USER_INFO_HEADERS": "true",
            "RAG_FULL_CONTEXT": "false",
            "RAG_WEB_SEARCH_FULL_CONTEXT": "true",
            "ENABLE_DIRECT_CONNECTIONS": "false",
        }

        # Apply any additional/override environment variables from config
        for key, value in self.config.openwebui_config.additional_env_vars.items():
            default_env_vars[key] = value

        # Convert the dictionary to EnvironmentVariableArgs list
        env_vars = [app.EnvironmentVariableArgs(name=key, value=value) for key, value in default_env_vars.items()]

        # Create volume mounts
        volume_mounts = [app.VolumeMountArgs(volume_name=self.config.volume_name, mount_path="/app/backend/data")]

        return app.ContainerArgs(
            name="openwebui",
            image=self.config.effective_docker_image,
            env=env_vars,
            volume_mounts=volume_mounts,
            resources=app.ContainerResourcesArgs(cpu=self.config.cpu, memory=self.config.memory),
        )

    def _get_nats_private_ip(self) -> str:
        container_group = containerinstance.get_container_group(
            container_group_name=f"{self.config.project_name}-{CONTAINER_INSTANCE}-{self.config.location_short}-nats",
            resource_group_name=self.config.resource_group,
        )
        if container_group.ip_address is not None and container_group.ip_address.ip is not None:
            return container_group.ip_address.ip
        else:
            raise ValueError(f"No private IP found for container group {container_group.name}")

    def _additional_secrets_from_additional_env_vars(self) -> List[app.SecretArgs]:
        additional_secrets = []
        for name, value in self.config.openwebui_config.additional_env_vars.items():
            if isinstance(value, dict) and "secret_ref" in value and "secret_value" in value:
                additional_secrets.append(app.SecretArgs(name=value["secret_ref"], value=value["secret_value"]))
        return additional_secrets

    def _create_container_app(self):
        """Create the container app with the configured containers and volumes"""
        container_list = list(self.containers.values())

        return app.ContainerApp(
            container_app_name=self.config.webui_container_app,
            resource_name=self.config.webui_container_app,
            resource_group_name=self.config.resource_group,
            location=self.config.location,
            managed_environment_id=self.managed_environment.id,
            configuration=app.ConfigurationArgs(
                ingress=app.IngressArgs(external=True, target_port=8080, transport="auto"),
                registries=[
                    app.RegistryCredentialsArgs(
                        server=self.config.registry_url,
                        username=self.config.registry_user,
                        password_secret_ref="registry-password",
                    )
                ],
                secrets=[
                    app.SecretArgs(
                        name="storage-account-key",
                        value=self.storage_account_key,
                    ),
                    app.SecretArgs(name="registry-password", value=self.config.registry_pat),
                    app.SecretArgs(name="postgres-password", value=self.config.postgres_password),
                    *self._additional_secrets_from_additional_env_vars(),
                ],
            ),
            template=app.TemplateArgs(
                containers=container_list,
                volumes=self.app_volumes,
                scale=app.ScaleArgs(
                    min_replicas=1,
                ),
            ),
            tags={
                "Stack": self.stack,
            },
            opts=pulumi.ResourceOptions(parent=self, depends_on=list(self.env_storages.values())),
        )

    @property
    def connection_string_sqlalchemy_pg(self):
        return (
            "postgresql://"
            f"{self.config.postgres_username}:"
            f"{self.config.postgres_password}@"
            f"{self.config.postgres_name}.postgres.database.azure.com"
            "/"
            f"{self.config.db_name}"
        )

    @property
    def connection_string_sqlalchemy_pg_vector(self):
        return (
            "postgresql://"
            f"{self.config.postgres_username}:"
            f"{self.config.postgres_password}@"
            f"{self.config.postgres_name}.postgres.database.azure.com"
            "/"
            f"{self.config.pg_vector_db_name}"
        )
