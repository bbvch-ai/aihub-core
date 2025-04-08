import pulumi
from typing import Optional

from pulumi_azure_native import app, operationalinsights, dbforpostgresql
from pulumi_command import local

from aihub_iac.azure.constants.resources import POSTGRES
from aihub_iac.azure.modules.webui.WebUIConfig import WebUIConfig
from aihub_iac.azure.providers.NetworkProvider import NetworkProvider
from aihub_iac.azure.resources.storage.StorageResourceFactory import StorageResourceFactory


class WebUI(pulumi.ComponentResource):
    """A Pulumi component resource for deploying container applications"""

    def __init__(
        self,
        stack: str,
        name: str,
        config: WebUIConfig,
        opts: Optional[pulumi.ResourceOptions] = None,
    ):
        super().__init__(f"{stack}:{name}", name, None, opts)

        self.config = config

        self.storage_factory = StorageResourceFactory(self.config)
        self.network_provider = NetworkProvider(
            self.config.resource_group, self.config.project_name, self.config.location_short
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

    def _create_resources(self):
        """Create all container app resources in the correct order"""
        # Step 1: Get network resources
        self.subnet = self.network_provider.get_cap_subnet()

        self.storage_account = self.storage_factory.create_storage_account(
            service_name=self.config.storage_service_name()
        )
        self.storage_account_key = self.storage_factory.get_storage_account_key(self.storage_account)

        self.webui_file_share = self.storage_factory.create_file_share("webui", self.storage_account)

        # Step 2: Create logging infrastructure
        self.log_analytics_workspace = self._create_log_analytics_workspace()
        self.log_analytics_customer_id, self.log_analytics_shared_key = self._get_log_analytics_credentials()

        # Step 3: Create managed environment
        self.managed_environment = self._create_managed_environment()

        self.env_storage = self._create_managed_environments_storage()

        # Step 6: Create container configurations
        self.containers["openwebui"] = self._create_openwebui_container()

        # Step 7: Create the container app
        self.container_app = self._create_container_app()

        self.pg_server = self._get_postgres_server()
        self.pg_db = self._create_postgres_db()
        self.pg_vector_db = self._get_postgres_server()

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
            server_name=self.config.postgres_name(),
        )

    def _create_pgvector_db(self):
        database = dbforpostgresql.Database(
            resource_name=self.config.pg_vector_db_name,
            resource_group_name=self.config.resource_group,
            server_name=self.config.postgres_name(),
        )
        local.Command(
            "enable-vector",
            create=pulumi.Output.concat(
                "PGPASSWORD='",
                self.config.postgres_password,
                "' psql -h ",
                self.pg_server.fully_qualified_domain_name,
                " -U ",
                self.config.postgres_username,
                " -d ",
                database.name,
                " -c 'CREATE EXTENSION IF NOT EXISTS vector;'",
            ),
            opts=pulumi.ResourceOptions(depends_on=[database]),
        )
        return database

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

    def _create_managed_environment(self):
        """Create the managed environment for container apps"""
        return app.ManagedEnvironment(
            resource_name=self.config.webui_container_env(),
            environment_name=self.config.webui_container_env(),
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
                infrastructure_subnet_id=self.subnet.id,
            ),
            opts=pulumi.ResourceOptions(parent=self),
        )

    def _create_managed_environments_storage(self):
        """Create managed environment storage for a volume"""
        return app.ManagedEnvironmentsStorage(
            resource_name=self.config.volume_name,
            environment_name=self.managed_environment.name,
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
            opts=pulumi.ResourceOptions(parent=self.managed_environment),
        )

    def _create_openwebui_container(self):
        """Create the OpenWebUI container configuration"""
        api_service_url = f"https://{self.config.api_service_name}.azurewebsites.net/api/v1/openai"

        default_env_vars = {
            # Tracking & Telemetry
            "SCARF_NO_ANALYTICS": "true",
            "DO_NOT_TRACK": "true",
            "ANONYMIZED_TELEMETRY": "true",
            # Websocket support
            "ENABLE_WEBSOCKET_SUPPORT": "true",
            "WEBSOCKET_MANAGER": "redis",
            "WEBSOCKET_REDIS_URL": self.config.redis_endpoint,
            "WEB_CONCURRENCY": 4,
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
            "WEBUI_NAME": self.config.openwebui.webui_name,
            "ADMIN_EMAIL": self.config.openwebui.admin_email,
            "DEFAULT_LOCALE": self.config.openwebui.default_locale,
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
            "OPENAI_API_KEY": self.config.openwebui.openai_api_key,
            "RAG_OPENAI_API_KEY": self.config.openwebui.rag_openai_api_key,
            "AUDIO_STT_OPENAI_API_KEY": self.config.openwebui.audio_stt_openai_api_key,
            "AUDIO_TTS_OPENAI_API_KEY": self.config.openwebui.audio_tts_openai_api_key,
            "IMAGES_OPENAI_API_KEY": self.config.openwebui.images_openai_api_key,
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
            "JINA_API_KEY": self.config.openwebui.jina_api_key,
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
            "OAUTH_CLIENT_ID": self.config.openwebui.oidc_client_id,
            "OAUTH_CLIENT_SECRET": self.config.openwebui.oidc_client_secret,
            "OPENID_PROVIDER_URL": self.config.openwebui.oidc_provider_url,
            "OAUTH_PROVIDER_NAME": self.config.openwebui.oidc_provider_name,
            # Postgres
            "DATABASE_URL": self.connection_string_sqlalchemy_pg,
            # User Credentials
            "ENABLE_FORWARD_USER_INFO_HEADERS": "true",
            "RAG_FULL_CONTEXT": "false",
            "RAG_WEB_SEARCH_FULL_CONTEXT": "true",
            "ENABLE_DIRECT_CONNECTIONS": "false",
        }

        # Apply any additional/override environment variables from config
        for key, value in self.config.openwebui.additional_env_vars.items():
            default_env_vars[key] = value

        # Convert the dictionary to EnvironmentVariableArgs list
        env_vars = [app.EnvironmentVariableArgs(name=key, value=value) for key, value in default_env_vars.items()]

        # Create volume mounts
        volume_mounts = [app.VolumeMountArgs(volume_name=self.config.volume_name, mount_path="/app/backend/data")]

        return app.ContainerArgs(
            name="openwebui",
            image=f"ghcr.io/open-webui/open-webui:{self.config.openwebui.image_tag}",
            env=env_vars,
            volume_mounts=volume_mounts,
            resources=app.ContainerResourcesArgs(
                cpu=self.config.openwebui.resources.cpu, memory=self.config.openwebui.resources.memory
            ),
        )

    def _create_container_app(self):
        """Create the container app with the configured containers and volumes"""
        container_list = list(self.containers.values())

        return app.ContainerApp(
            container_app_name=self.config.webui_container_app(),
            resource_name=self.config.webui_container_app(),
            resource_group_name=self.config.resource_group,
            location=self.config.location,
            managed_environment_id=self.managed_environment.id,
            configuration=app.ConfigurationArgs(
                ingress=app.IngressArgs(external=True, target_port=8080, transport="auto"),
                secrets=[
                    app.SecretArgs(
                        name="storage-account-key",
                        value=self.storage_account_key,
                    )
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
                "Stack": self.config.stack,
            },
            opts=pulumi.ResourceOptions(parent=self, depends_on=list(self.env_storages.values())),
        )

    @property
    def connection_string_sqlalchemy_pg(self):
        return (
            "postgresql://"
            f"{self.config.postgres_username}:"
            f"{self.config.postgres_password}@"
            f"{self.config.postgres_name()}.postgres.database.azure.com"
            "/"
            f"{self.config.db_name}"
        )

    @property
    def connection_string_sqlalchemy_pg_vector(self):
        return (
            "postgresql://"
            f"{self.config.postgres_username}:"
            f"{self.config.postgres_password}@"
            f"{self.config.postgres_name()}.postgres.database.azure.com"
            "/"
            f"{self.config.pg_vector_db_name}"
        )
