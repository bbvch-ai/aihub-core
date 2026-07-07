---
title: Environment Variables
description: Reference of every environment variable used by the Swiss AI Hub deployment
---

# Environment Variables

This page lists every environment variable read by the Swiss AI Hub deployment, organized by role. It is auto-generated from the Pydantic settings classes in `packages/*/swiss_ai_hub/**/*settings.py` and the docker-compose templates. Do not edit by hand — run `make generate-env-docs` to refresh.

Variables fall into three roles:

- **Compose-required** — referenced as `${VAR}` in `docker-compose.yml`. Must be set in `.env` because the project's compose templates do not provide fallback defaults.
- **App-required** — read as a required field by a Pydantic `BaseSettings` class. The application refuses to start if unset.
- **Optional** — has a default in code. Set in `.env` only to override the default.

The deployment has a base variant (`CPU`) plus pure-extension variants (`GPU`). The first section below lists every variable required by the base; subsequent sections list only the extra variables each extension introduces on top of the base.

## Variables for the base deployment (`CPU`)

### Required by docker-compose interpolation

These variables are referenced as `${VAR}` (without a `${VAR:-default}` fallback) somewhere in `docker-compose.yml`. Compose-parse will fail or render empty values if `.env` does not define them. The Consumer column shows the Pydantic settings field that reads the variable when our Python code consumes it; otherwise it points at the config file that embeds it (Keycloak realm import, identity-provider config, etc.) or — if neither — is left empty. The Service(s) column lists the compose service(s) whose `environment:` block receives the variable.

| Variable | Consumer | Service(s) | Description |
|---|---|---|---|
| `ACME_EMAIL` |  | `traefik` |  |
| `ADMIN_EMAIL` |  | `open-webui` |  |
| `ADMIN_PASSWORD_HASH` |  | `traefik` |  |
| `AIHUB_CREATE_DEFAULT_BUCKETS` | `AIHubSettings.CREATE_DEFAULT_BUCKETS` | `api`, `seaweedfs-init` | Creates default knowledge buckets and namespaces |
| `AIHUB_DEFAULT_BUCKET_NAME` | `AIHubSettings.DEFAULT_BUCKET_NAME` | `api`, `default_rag_pipeline`, `seaweedfs-init` | Name of the default knowledge bucket |
| `AIHUB_DEFAULT_NAMESPACE_NAME` | `AIHubSettings.DEFAULT_NAMESPACE_NAME` | `api` | Name of the default namespace |
| `AIHUB_SHARED_BUCKET_NAME` | `AIHubSettings.SHARED_BUCKET_NAME` | `api`, `seaweedfs-init`, `shared_rag_pipeline` | Name of the shared knowledge bucket |
| `AIHUB_SHARED_NAMESPACE_NAME` | `AIHubSettings.SHARED_NAMESPACE_NAME` | `api` | Name of the shared namespace |
| `AIHUB_STARTUP_TENANT_ACCESS_RULES` | `StartupTenantSettings.ACCESS_RULES` | `api` | Comma-separated access rules for the startup tenant. Use 'aihub.admin.>' for unrestricted access to all platform features. |
| `AIHUB_STARTUP_TENANT_DESCRIPTION` | `StartupTenantSettings.DESCRIPTION` | `api` | Description of the startup tenant. |
| `AIHUB_STARTUP_TENANT_ID` | `StartupTenantSettings.ID` | `api`, `keycloak` | Unique identifier for the startup tenant. Also used as the Keycloak group name. |
| `AIHUB_STARTUP_TENANT_NAME` | `StartupTenantSettings.NAME` | `api` | Display name of the startup tenant. |
| `AIHUB_USER_SIGNUP_FIRST_ADMIN_USER_ROLES` | `UserSignupSettings.FIRST_ADMIN_USER_ROLES` | `api` | Comma-separated list of roles assigned to the very first user. This user is typically the initial platform administrator. |
| `AIHUB_USER_SIGNUP_REGULAR_USER_ROLES` | `UserSignupSettings.REGULAR_USER_ROLES` | `api` | Comma-separated list of roles assigned to regular users (not the first user). These users typically have standard platform access. |
| `AIHUB_VERSION` | `AIHubSettings.VERSION` | `api`, `bot`, `default_rag_pipeline`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline`, `sysadmin-api` | Version of the app |
| `AUTH_OPEN_WEBUI_SIGNING_SECRET` | `AuthSettings.OPEN_WEBUI_SIGNING_SECRET` | `api`, `open-webui`, `sysadmin-api` | OpenWebUI signing secret |
| `BACKUP_MINIMUM_KEEP` | `BackupSettings.MINIMUM_KEEP` | `backup-code` |  |
| `BACKUP_POSTGRES_SUBPROCESS_TIMEOUT_SECONDS` | `BackupSettings.POSTGRES_SUBPROCESS_TIMEOUT_SECONDS` | `backup-code` |  |
| `BACKUP_RETENTION_DAYS` | `BackupSettings.RETENTION_DAYS` | `backup-code` |  |
| `BACKUP_S3_BUCKET` | `BackupSettings.S3_BUCKET` | `backup-code` |  |
| `DAGSTER_CLEANUP_BATCH_LIMIT` |  | `backup-code` |  |
| `DAGSTER_DB` |  | `backup-code` |  |
| `DAGSTER_DEBUG_LOG_RETENTION_DAYS` |  | `backup-code` |  |
| `DAGSTER_INFO_LOG_RETENTION_DAYS` |  | `backup-code` |  |
| `DAGSTER_UNIMPORTANT_EVENT_RETENTION_DAYS` |  | `backup-code` |  |
| `DAGSTER_WARNING_LOG_RETENTION_DAYS` |  | `backup-code` |  |
| `DOMAIN` | `30-clients.json`, `realm-settings.json` | `api`, `bot`, `default_rag_pipeline`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `keycloak`, `keycloak-config`, `langfuse-web`, `litellm`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `oauth2proxy-attu`, `oauth2proxy-backup`, `oauth2proxy-dagster`, `oauth2proxy-seaweed`, `open-webui`, `rag_agent`, `retrieval_agent`, `seaweedfs-s3`, `shared_rag_pipeline`, `sysadmin-api`, `sysadmin-web`, `traefik`, `web` |  |
| `ENV` |  | `api`, `open-webui`, `sysadmin-api` |  |
| `ETCD_TOKEN` |  | `etcd`, `etcd-init`, `milvus-standalone`, `seaweedfs-filer` |  |
| `EXPERT_ASKING_CHANNEL_TYPE` |  | `expert_asking_agent` |  |
| `GEMINI_API_KEY` |  | `litellm` |  |
| `HUGGINGFACE_API_KEY` |  | `litellm`, `vllm`, `vllm-bge-m3`, `vllm-bge-reranker` |  |
| `JUPYTER_TOKEN` |  | `api`, `jupyter` |  |
| `KEYCLOAK_ADMIN_PASSWORD` |  | `keycloak`, `keycloak-config` |  |
| `KEYCLOAK_ADMIN_USER` |  | `keycloak`, `keycloak-config` |  |
| `KEYCLOAK_API_SERVICE_CLIENT_SECRET` | `KeycloakSettings.API_SERVICE_CLIENT_SECRET` | `api`, `bot`, `keycloak`, `keycloak-config`, `sysadmin-api` | Client secret for the API service account |
| `KEYCLOAK_AZURE_CLIENT_ID` | `identity-providers.json` | `keycloak` |  |
| `KEYCLOAK_AZURE_CLIENT_SECRET` | `identity-providers.json` | `keycloak` |  |
| `KEYCLOAK_AZURE_TENANT_ID` | `identity-providers.json` | `keycloak` |  |
| `KEYCLOAK_OAUTH2_PROXY_ATTU_SECRET` | `30-clients.json` | `keycloak`, `keycloak-config`, `oauth2proxy-attu` |  |
| `KEYCLOAK_OAUTH2_PROXY_BACKUP_SECRET` | `30-clients.json` | `keycloak`, `keycloak-config`, `oauth2proxy-backup` |  |
| `KEYCLOAK_OAUTH2_PROXY_DAGSTER_SECRET` | `30-clients.json` | `keycloak`, `keycloak-config`, `oauth2proxy-dagster` |  |
| `KEYCLOAK_OAUTH2_PROXY_DATALAKE_SECRET` | `30-clients.json` | `keycloak`, `keycloak-config`, `oauth2proxy-seaweed` |  |
| `KEYCLOAK_OPENWEBUI_CLIENT_SECRET` | `30-clients.json` | `keycloak`, `keycloak-config`, `open-webui` |  |
| `KEYCLOAK_SHOW_KEYCLOAK_LOGIN` | `KeycloakSettings.SHOW_KEYCLOAK_LOGIN` | `api`, `sysadmin-api` | Show a direct Keycloak login button alongside federated IDPs |
| `LANGFUSE_ALLOWED_ORGANIZATION_CREATORS` |  | `langfuse-web` |  |
| `LANGFUSE_CLICKHOUSE_PASSWORD` |  | `backup-code`, `clickhouse`, `langfuse-web`, `langfuse-worker` |  |
| `LANGFUSE_ENCRYPTION_KEY` |  | `langfuse-web`, `langfuse-worker` |  |
| `LANGFUSE_INIT_USER_EMAIL` |  | `langfuse-web` |  |
| `LANGFUSE_INIT_USER_PASSWORD` |  | `langfuse-web` |  |
| `LANGFUSE_KEYCLOAK_CLIENT_SECRET` |  | `keycloak`, `keycloak-config`, `langfuse-web` |  |
| `LANGFUSE_NEXTAUTH_SECRET` |  | `langfuse-web` |  |
| `LANGFUSE_PUBLIC_KEY` | `LangfuseSettings.PUBLIC_KEY` | `api`, `langfuse-web`, `otel-collector` | Langfuse public API key |
| `LANGFUSE_SALT` |  | `langfuse-web`, `langfuse-worker` |  |
| `LANGFUSE_SECRET_KEY` | `LangfuseSettings.SECRET_KEY` | `api`, `langfuse-web`, `otel-collector` | Langfuse secret API key |
| `LITELLM_MASTER_KEY` | `litellm-config.yml` | `api`, `default_rag_pipeline`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `litellm`, `llm_wrapping_agent`, `memory_writer_agent`, `mineru-api`, `namespace_selection_agent`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline` |  |
| `LITELLM_UI_PASSWORD` |  | `litellm` |  |
| `LITELLM_UI_USERNAME` |  | `litellm` |  |
| `LOCAL_LLM_TOKEN` | `litellm-config.yml` | `litellm`, `vllm`, `vllm-bge-m3`, `vllm-bge-reranker` |  |
| `LOG_LEVEL` | `LogSettings.LEVEL` | `api`, `bot`, `dagster-daemon`, `dagster-webserver`, `default_rag_pipeline`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `open-webui`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline`, `sysadmin-api`, `traefik` | Logging level |
| `MAINTENANCE_DISABLED` |  | `backup-code` |  |
| `MEM0_EMBEDDING_MODEL_NAME` | `Mem0Settings.EMBEDDING_MODEL_NAME` | `api`, `bot`, `llm_wrapping_agent`, `memory_writer_agent`, `rag_agent`, `shared_rag_pipeline` | Name of the embedding model to use |
| `MEM0_LLM_NAME` | `Mem0Settings.LLM_NAME` | `api`, `bot`, `llm_wrapping_agent`, `memory_writer_agent`, `rag_agent`, `shared_rag_pipeline` | Name of the LLM to use |
| `MEM0_RERANKING_MODEL_NAME` | `Mem0Settings.RERANKING_MODEL_NAME` | `api`, `bot`, `llm_wrapping_agent`, `memory_writer_agent`, `rag_agent`, `shared_rag_pipeline` | Name of the embedding model to use |
| `MILVUS_DIMENSION` | `MilvusSettings.DIMENSION` | `api`, `default_rag_pipeline`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline` | Dimension of the embedding vector |
| `MILVUS_ROOT_PASSWORD` | `MilvusSettings.ROOT_PASSWORD` | `api`, `attu`, `backup-code`, `default_rag_pipeline`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `milvus-standalone`, `namespace_selection_agent`, `open-webui`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline` | Root password for Milvus authentication. If not set, no auth is used. Username is always 'root'. |
| `MINERU_API_MAX_CONCURRENT_REQUESTS` |  | `mineru-api` |  |
| `MINERU_API_TIMEOUT` | `MineruSettings.API_TIMEOUT` | `api`, `default_rag_pipeline`, `shared_rag_pipeline` | Timeout for MinerU API calls in seconds |
| `MINERU_FORMULA_ENABLE` | `MineruSettings.FORMULA_ENABLE` | `api`, `default_rag_pipeline`, `shared_rag_pipeline` | Enable formula/equation parsing |
| `MINERU_TABLE_ENABLE` | `MineruSettings.TABLE_ENABLE` | `api`, `default_rag_pipeline`, `shared_rag_pipeline` | Enable table detection and parsing |
| `MINERU_VLM_NAME` | `MineruSettings.VLM_NAME` | `api`, `default_rag_pipeline`, `mineru-api`, `shared_rag_pipeline` | LiteLLM model alias for MinerU VLM |
| `MONGO_PASSWORD` |  | `api`, `backup-code`, `bot`, `default_rag_pipeline`, `expert_asking_agent`, `expert_rag_agent`, `ferretdb`, `few_shot_agent`, `llm_wrapping_agent`, `namespace_selection_agent`, `postgres-ferretdb`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline`, `sysadmin-api` |  |
| `MONGO_USERNAME` |  | `api`, `backup-code`, `bot`, `default_rag_pipeline`, `expert_asking_agent`, `expert_rag_agent`, `ferretdb`, `few_shot_agent`, `llm_wrapping_agent`, `namespace_selection_agent`, `postgres-ferretdb`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline`, `sysadmin-api` |  |
| `NATS_TOKEN` | `NatsSettings.TOKEN` | `api`, `backup-code`, `bot`, `default_rag_pipeline`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `nats`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline`, `sysadmin-api` | Authentication token for NATS server. If not set, no auth is used. |
| `NEO4J_PASSWORD` | `Neo4jSettings.PASSWORD` | `api`, `bot`, `llm_wrapping_agent`, `memory_writer_agent`, `neo4j`, `rag_agent`, `shared_rag_pipeline` | Password for Neo4j DB Server |
| `NEO4J_USERNAME` | `Neo4jSettings.USERNAME` | `api`, `bot`, `llm_wrapping_agent`, `memory_writer_agent`, `neo4j`, `rag_agent`, `shared_rag_pipeline` | Username for Neo4j DB Server |
| `NOTIFICATION_URLS` | `NotificationSettings.URLS` | `default_rag_pipeline`, `shared_rag_pipeline` | Apprise notification URIs (comma-separated). Examples: 'slack://TokenA/TokenB/TokenC/#alerts', 'mailto://user:pw@smtp.example.com', 'discord://webhook_id/webhook_token'. See https://github.com/caronc/apprise for the full list. |
| `OAUTH_ADMIN_ROLES_OPENWEBUI` |  | `open-webui` |  |
| `OAUTH_ALLOWED_GROUPS_ATTU` |  | `oauth2proxy-attu` |  |
| `OAUTH_ALLOWED_GROUPS_BACKUP` |  | `oauth2proxy-backup` |  |
| `OAUTH_ALLOWED_GROUPS_DAGSTER` |  | `oauth2proxy-dagster` |  |
| `OAUTH_ALLOWED_GROUPS_SEAWEEDFS` |  | `oauth2proxy-seaweed` |  |
| `OAUTH_CLIENT_ID` |  | `api`, `bot`, `open-webui`, `sysadmin-api`, `sysadmin-web`, `web` |  |
| `OAUTH_CLIENT_SECRET` |  | `api`, `bot`, `open-webui`, `sysadmin-api` |  |
| `OAUTH_COOKIE_SECRET_ATTU` |  | `oauth2proxy-attu` |  |
| `OAUTH_COOKIE_SECRET_BACKUP` |  | `oauth2proxy-backup` |  |
| `OAUTH_COOKIE_SECRET_DAGSTER` |  | `oauth2proxy-dagster` |  |
| `OAUTH_COOKIE_SECRET_SEAWEEDFS` |  | `oauth2proxy-seaweed` |  |
| `OAUTH_CUSTOM_SIGN_IN_LOGO` |  | `oauth2proxy-attu`, `oauth2proxy-backup`, `oauth2proxy-dagster`, `oauth2proxy-seaweed` |  |
| `OAUTH_TENANT_ID` |  | `api`, `sysadmin-api` |  |
| `OPENWEBUI_MODEL_NAME_LOCALE` | `OpenWebuiSettings.MODEL_NAME_LOCALE` | `open-webui` | Locale used to render agent workspace-model names in OpenWebUI, which only stores a single name per model. Falls back to the platform default locale and then any available translation. |
| `OPENWEBUI_SCIM_TOKEN` | `OpenWebuiSettings.SCIM_TOKEN` | `api`, `open-webui`, `sysadmin-api` | SCIM 2.0 bearer token for group and user provisioning |
| `OPENWEBUI_SECRET_KEY` | `OpenWebuiSettings.SECRET_KEY` | `api`, `open-webui`, `sysadmin-api` | OpenWebUI WEBUI_SECRET_KEY for JWT signing |
| `OPENWEBUI_SERVICE_ACCOUNT_ID` | `OpenWebuiSettings.SERVICE_ACCOUNT_ID` | `api`, `openwebui-init`, `sysadmin-api` | UUID of the AI-Hub service account in OpenWebUI's database |
| `OPENWEBUI_WEBHOOK_SECRET` | `OpenWebuiSettings.WEBHOOK_SECRET` | `api`, `open-webui`, `sysadmin-api` | Shared secret for authenticating OpenWebUI webhook calls |
| `OPEN_TERMINAL_API_KEY` |  | `open-terminal`, `open-webui` |  |
| `OTEL_CLOUD_ENDPOINT` | `otel-config.yml` | `otel-collector` |  |
| `OTEL_CLOUD_HEADERS` | `otel-config.yml` | `otel-collector` |  |
| `OTEL_ENABLED` | `OpenTelemetrySettings.ENABLED` | `api`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `rag_agent`, `retrieval_agent`, `sysadmin-api` | Enable/disable OpenTelemetry tracing entirely |
| `POSTGRES_PASSWORD` | `openwebui-init-openwebui.sh` | `backup-code`, `dagster-daemon`, `dagster-webserver`, `default_rag_pipeline`, `keycloak`, `langfuse-web`, `langfuse-worker`, `litellm`, `open-webui`, `openwebui-init`, `pgbouncer`, `postgres`, `postgres-ferretdb`, `shared_rag_pipeline` |  |
| `POSTGRES_PORT` | `openwebui-init-openwebui.sh` | `backup-code`, `openwebui-init` |  |
| `POSTGRES_USER` | `openwebui-init-openwebui.sh` | `backup-code`, `dagster-daemon`, `dagster-webserver`, `default_rag_pipeline`, `keycloak`, `langfuse-web`, `langfuse-worker`, `litellm`, `open-webui`, `openwebui-init`, `pgbouncer`, `postgres`, `postgres-ferretdb`, `shared_rag_pipeline` |  |
| `RCLONE_RC_PASS` | `RcloneSettings.RC_PASS` | `rclone` | RC API password for authentication. |
| `RCLONE_RC_USER` | `RcloneSettings.RC_USER` | `rclone` | RC API username for authentication. |
| `REDIS_TOKEN` | `RedisSettings.TOKEN` | `api`, `backup-code`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `langfuse-web`, `langfuse-worker`, `litellm`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `open-webui`, `rag_agent`, `retrieval_agent`, `sysadmin-api`, `valkey` | Authentication token for Redis server. If not set, no auth is used. |
| `S3_STORAGE_ACCESS_KEY` | `S3StorageSettings.ACCESS_KEY` | `api`, `backup-code`, `clickhouse`, `default_rag_pipeline`, `expert_rag_agent`, `langfuse-web`, `langfuse-worker`, `milvus-standalone`, `open-webui`, `rag_agent`, `retrieval_agent`, `seaweedfs-init`, `seaweedfs-s3`, `shared_rag_pipeline` | The access key for the s3 endpoint. |
| `S3_STORAGE_SECRET_KEY` | `S3StorageSettings.SECRET_KEY` | `api`, `backup-code`, `clickhouse`, `default_rag_pipeline`, `expert_rag_agent`, `langfuse-web`, `langfuse-worker`, `milvus-standalone`, `open-webui`, `rag_agent`, `retrieval_agent`, `seaweedfs-init`, `seaweedfs-s3`, `shared_rag_pipeline` | The secret key for the s3 endpoint. |
| `SEARXNG_SECRET_KEY` |  | `searxng` |  |
| `SEAWEEDFS_TOKEN` |  | `seaweedfs-filer`, `seaweedfs-master`, `seaweedfs-s3`, `seaweedfs-volume` |  |
| `SLACK_CHANNEL_ID` |  | `expert_asking_agent` |  |
| `SLACK_SERVICE_URL` |  | `expert_asking_agent` |  |
| `SUPERUSER_EMAIL` | `SuperuserSettings.EMAIL` | `api`, `keycloak`, `sysadmin-api` | Keycloak email used to look up the superuser. |
| `SUPERUSER_FIRSTNAME` | `users-superuser.json` | `keycloak` |  |
| `SUPERUSER_LASTNAME` | `users-superuser.json` | `keycloak` |  |
| `SUPERUSER_PASSWORD` | `users-superuser.json` | `keycloak` |  |
| `SUPERUSER_ROLES_JSON` | `SuperuserSettings.ROLES_JSON` | `api`, `keycloak`, `sysadmin-api` | JSON array of realm roles assigned to the superuser, shared verbatim with the Keycloak realm import via the same environment variable. Must include AIHubSysAdmin. |
| `SUPERUSER_TOKEN` | `SuperuserSettings.TOKEN` | `api`, `open-webui`, `sysadmin-api` | Static bearer token for machine-to-machine API calls. Must start with 'sk-'. |
| `SUPERUSER_USERNAME` | `SuperuserSettings.USERNAME` | `api`, `keycloak`, `sysadmin-api` | Log-only label for the seeded superuser in API startup logs. Not persisted in Keycloak — the Keycloak username is SUPERUSER_EMAIL (registrationEmailAsUsername), so login is by email. |
| `SWISS_LLM_CLOUD_API_BASE_URL` | `litellm-config.yml` | `litellm` |  |
| `SWISS_LLM_CLOUD_API_KEY` | `litellm-config.yml` | `litellm` |  |
| `SWISS_LLM_CLOUD_EMBEDDING_API_BASE_URL` | `litellm-config.yml` | `litellm` |  |
| `SWISS_LLM_CLOUD_EMBEDDING_API_KEY` | `litellm-config.yml` | `litellm` |  |
| `SWISS_LLM_CLOUD_IMAGE_API_BASE_URL` | `litellm-config.yml` | `litellm` |  |
| `SWISS_LLM_CLOUD_IMAGE_API_KEY` | `litellm-config.yml` | `litellm` |  |
| `SWISS_LLM_CLOUD_OCR_API_BASE_URL` | `litellm-config.yml` | `litellm` |  |
| `SWISS_LLM_CLOUD_OCR_API_KEY` | `litellm-config.yml` | `litellm` |  |
| `SWISS_LLM_CLOUD_RERANKING_API_BASE_URL` | `litellm-config.yml` | `litellm` |  |
| `SWISS_LLM_CLOUD_RERANKING_API_KEY` | `litellm-config.yml` | `litellm` |  |
| `SWISS_LLM_CLOUD_WHISPER_API_BASE_URL` | `litellm-config.yml` | `litellm` |  |
| `SWISS_LLM_CLOUD_WHISPER_API_KEY` | `litellm-config.yml` | `litellm` |  |
| `TEAMS_BOT_ID` |  | `expert_asking_agent` |  |
| `TEAMS_CHANNEL_ID` |  | `expert_asking_agent` |  |
| `TEAMS_TENANT_ID` |  | `expert_asking_agent` |  |

### Required by SDK settings classes (not used by the default deployment)

These variables are declared as required fields on a Pydantic `BaseSettings` class and are **not** consumed by any service in the default docker-compose stack. The empty Service(s) column reflects this: no container in the default deployment loads the settings class. They become operationally required only when a custom agent, pipeline, or other extension is added to docker-compose that activates the corresponding SDK functionality (e.g. the SharePoint connector or Azure Document Intelligence loader). Until then, leaving the placeholders unchanged is fine — Pydantic only validates the class when something instantiates it.

| Variable | Consumer | Service(s) | Description |
|---|---|---|---|
| `AZURE_DATA_LAKE_CONNECTION_STRING` | `AzureDataLakeSettings.CONNECTION_STRING` |  | Azure Data Lake connection string for explicit authentication. Recommended over implicit authentication. |
| `AZURE_DOCUMENT_INTELLIGENCE_API_KEY` | `AzureDocumentIntelligenceSettings.API_KEY` |  | API key for Document Intelligence |
| `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT` | `AzureDocumentIntelligenceSettings.ENDPOINT` |  |  |
| `SHAREPOINT_CLIENT_ID` | `SharePointSettings.CLIENT_ID` |  | The application (client) ID. |
| `SHAREPOINT_CLIENT_SECRET` | `SharePointSettings.CLIENT_SECRET` |  | The client secret for authentication. |
| `SHAREPOINT_SITE_URL` | `SharePointSettings.SITE_URL` |  | The SharePoint site URL. |
| `SHAREPOINT_TENANT_ID` | `SharePointSettings.TENANT_ID` |  | The Azure AD tenant ID. |

### Optional: override platform defaults

These variables have sensible defaults (or are supplied to containers by docker-compose) and do not need to be set in `.env`. Add them only to override the default. Vars marked `(supplied by compose)` are required by the application but get their value injected through `docker-compose.yml`, so setting them in `.env` has no effect.

| Variable | Consumer | Default | Service(s) | Description |
|---|---|---|---|---|
| `AIHUB_API_DEBUG_MODE` | `AIHubSettings.API_DEBUG_MODE` | `False` |  | Debug mode for development |
| `AIHUB_CREATE_DEFAULT_ROLES` | `AIHubSettings.CREATE_DEFAULT_ROLES` | `True` | `api`, `sysadmin-api` | Creates default roles like AI-Hub Admin and AI-Hub User |
| `AIHUB_FRONTEND_ORIGIN` | `AIHubSettings.FRONTEND_ORIGIN` | _(supplied by compose)_ | `api`, `bot`, `default_rag_pipeline`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline`, `sysadmin-api` | Comma separated list of origins to allow CORS |
| `AIHUB_INTERNAL_API_BASE_URL` | `AIHubSettings.INTERNAL_API_BASE_URL` | `'http://api:8000'` | `sysadmin-api` | Internal base URL of the main platform API (no path), used for server-to-server calls such as the sysadmin plane proxying the access-capability catalog. Predictable per deployment: the Docker service name in compose, localhost in local dev. |
| `AIHUB_MONGO_MAIN_DB_NAME` | `AIHubSettings.MONGO_MAIN_DB_NAME` | `'aihub'` |  | Name of mongodb database that will be used to store data |
| `AIHUB_OPENAI_API_BASE_URL` | `AIHubSettings.OPENAI_API_BASE_URL` | `'http://api:8000/api/v1/active/openai'` | `api` | Base URL of AI-Hub's OpenAI-compatible endpoint, used for Langfuse LLM connection |
| `AUTH_ENABLE_API_ACCESS` | `AuthSettings.ENABLE_API_ACCESS` | `True` | `api`, `sysadmin-api` | Enable API access |
| `AZURE_DOCUMENT_INTELLIGENCE_API_VERSION` | `AzureDocumentIntelligenceSettings.API_VERSION` | `'2024-11-30'` |  |  |
| `AZURE_DOCUMENT_INTELLIGENCE_EXTENSIONS` | `AzureDocumentIntelligenceSettings.EXTENSIONS` | `['pdf', 'docx', 'xlsx', 'pptx', 'html']` |  | Supported file extensions for document processing |
| `BACKUP_AWS_ENDPOINT_URL` | `BackupSettings.AWS_ENDPOINT_URL` | `'http://seaweedfs-s3:9000'` | `backup-code` |  |
| `BACKUP_CLICKHOUSE_HOST` | `BackupSettings.CLICKHOUSE_HOST` | `'clickhouse'` | `backup-code` |  |
| `BACKUP_CLICKHOUSE_PORT` | `BackupSettings.CLICKHOUSE_PORT` | `8123` |  |  |
| `BACKUP_CLICKHOUSE_USER` | `BackupSettings.CLICKHOUSE_USER` | `'clickhouse'` | `backup-code` |  |
| `BACKUP_DAGSTER_CLEANUP_BATCH_LIMIT` | `BackupSettings.DAGSTER_CLEANUP_BATCH_LIMIT` | `1000000` | `backup-code` |  |
| `BACKUP_DAGSTER_DB` | `BackupSettings.DAGSTER_DB` | `'dagster'` | `backup-code` |  |
| `BACKUP_DAGSTER_DEBUG_LOG_RETENTION_DAYS` | `BackupSettings.DAGSTER_DEBUG_LOG_RETENTION_DAYS` | `7` | `backup-code` |  |
| `BACKUP_DAGSTER_INFO_LOG_RETENTION_DAYS` | `BackupSettings.DAGSTER_INFO_LOG_RETENTION_DAYS` | `60` | `backup-code` |  |
| `BACKUP_DAGSTER_UNIMPORTANT_EVENT_RETENTION_DAYS` | `BackupSettings.DAGSTER_UNIMPORTANT_EVENT_RETENTION_DAYS` | `30` | `backup-code` |  |
| `BACKUP_DAGSTER_WARNING_LOG_RETENTION_DAYS` | `BackupSettings.DAGSTER_WARNING_LOG_RETENTION_DAYS` | `60` | `backup-code` |  |
| `BACKUP_LANGFUSE_CLICKHOUSE_PASSWORD` | `BackupSettings.LANGFUSE_CLICKHOUSE_PASSWORD` | _(supplied by compose)_ | `backup-code` |  |
| `BACKUP_MAINTENANCE_DISABLED` | `BackupSettings.MAINTENANCE_DISABLED` | `False` | `backup-code` |  |
| `BACKUP_MILVUS_HOST` | `BackupSettings.MILVUS_HOST` | `'milvus-standalone'` | `backup-code` |  |
| `BACKUP_MILVUS_PORT` | `BackupSettings.MILVUS_PORT` | `19530` | `backup-code` |  |
| `BACKUP_MILVUS_ROOT_PASSWORD` | `BackupSettings.MILVUS_ROOT_PASSWORD` | _(supplied by compose)_ | `backup-code` |  |
| `BACKUP_MONGO_PASSWORD` | `BackupSettings.MONGO_PASSWORD` | _(supplied by compose)_ | `backup-code` |  |
| `BACKUP_MONGO_USERNAME` | `BackupSettings.MONGO_USERNAME` | `'admin'` | `backup-code` |  |
| `BACKUP_NATS_TOKEN` | `BackupSettings.NATS_TOKEN` | _(supplied by compose)_ | `backup-code` |  |
| `BACKUP_NATS_URL` | `BackupSettings.NATS_URL` | `'nats://nats:4222'` | `backup-code` |  |
| `BACKUP_NEO4J_CONTAINER` | `BackupSettings.NEO4J_CONTAINER` | `'neo4j'` | `backup-code` |  |
| `BACKUP_POSTGRES_FERRETDB_HOST` | `BackupSettings.POSTGRES_FERRETDB_HOST` | `'postgres-ferretdb'` | `backup-code` |  |
| `BACKUP_POSTGRES_HOST` | `BackupSettings.POSTGRES_HOST` | `'postgres'` | `backup-code` |  |
| `BACKUP_POSTGRES_PASSWORD` | `BackupSettings.POSTGRES_PASSWORD` | _(supplied by compose)_ | `backup-code` |  |
| `BACKUP_POSTGRES_PORT` | `BackupSettings.POSTGRES_PORT` | `5432` | `backup-code` |  |
| `BACKUP_POSTGRES_USER` | `BackupSettings.POSTGRES_USER` | `'admin'` | `backup-code` |  |
| `BACKUP_REDIS_TOKEN` | `BackupSettings.REDIS_TOKEN` | _(supplied by compose)_ | `backup-code` |  |
| `BACKUP_S3_STORAGE_ACCESS_KEY` | `BackupSettings.S3_STORAGE_ACCESS_KEY` | `'admin'` | `backup-code` |  |
| `BACKUP_S3_STORAGE_SECRET_KEY` | `BackupSettings.S3_STORAGE_SECRET_KEY` | _(supplied by compose)_ | `backup-code` |  |
| `BACKUP_VALKEY_CONTAINER` | `BackupSettings.VALKEY_CONTAINER` | `'valkey'` | `backup-code` |  |
| `BACKUP_VALKEY_HOST` | `BackupSettings.VALKEY_HOST` | `'valkey'` |  |  |
| `BACKUP_VALKEY_PORT` | `BackupSettings.VALKEY_PORT` | `6379` |  |  |
| `KEYCLOAK_API_SERVICE_CLIENT_ID` | `KeycloakSettings.API_SERVICE_CLIENT_ID` | `'aihub-api-service'` |  | Client ID for the API service account |
| `KEYCLOAK_EXTERNAL_URL` | `KeycloakSettings.EXTERNAL_URL` | `None` | `api`, `bot`, `sysadmin-api` | Keycloak external URL as seen by browsers, used for issuer validation |
| `KEYCLOAK_REALM` | `KeycloakSettings.REALM` | `'aihub'` | `api`, `bot`, `sysadmin-api` | Keycloak realm name |
| `KEYCLOAK_URL` | `KeycloakSettings.URL` | _(supplied by compose)_ | `api`, `bot`, `keycloak-config`, `sysadmin-api` | Keycloak internal URL for direct access (e.g., http://keycloak:8080) |
| `LANGFUSE_BASE_URL` | `LangfuseSettings.BASE_URL` | _(supplied by compose)_ | `api` | Langfuse server base URL |
| `LANGFUSE_PROJECT_ID` | `LangfuseSettings.PROJECT_ID` | `None` | `api` | Langfuse project ID for constructing dataset URLs |
| `LANGFUSE_PUBLIC_URL` | `LangfuseSettings.PUBLIC_URL` | `None` | `api` | Public-facing Langfuse URL for browser links (e.g. https://langfuse.example.com) |
| `LANGFUSE_TIMEOUT` | `LangfuseSettings.TIMEOUT` | `60` |  | Timeout in seconds for Langfuse API requests |
| `LITE_LLM_PROXY_API_KEY` | `LiteLLMProxySettings.API_KEY` | `None` | `api`, `default_rag_pipeline`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline` | API key for authentication. If not provided, other authentication methods will be used. |
| `LITE_LLM_PROXY_BASE_URL` | `LiteLLMProxySettings.BASE_URL` | _(supplied by compose)_ | `api`, `default_rag_pipeline`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline` | The base URL of the model. |
| `LITE_LLM_PROXY_USER_BUDGET_DURATION` | `LiteLLMProxySettings.USER_BUDGET_DURATION` | `None` |  | Budget is reset at the end of specified duration. If not set, budget is never reset. You can set duration as seconds ("30s"), minutes ("30m"), hours ("30h"), days ("30d"), months ("1mo"). |
| `LITE_LLM_PROXY_USER_MAX_BUDGET` | `LiteLLMProxySettings.USER_MAX_BUDGET` | `None` |  | Budget available to a user in one period |
| `LITE_LLM_PROXY_USER_MAX_PARALLEL_REQUESTS` | `LiteLLMProxySettings.USER_MAX_PARALLEL_REQUESTS` | `None` |  | Rate limit a user based on the number of parallel requests. Raises 429 error, if user's parallel requests > x. |
| `LITE_LLM_PROXY_USER_RPM_LIMIT` | `LiteLLMProxySettings.USER_RPM_LIMIT` | `None` |  | Specify rpm limit for a given user (Requests per minute) |
| `LITE_LLM_PROXY_USER_SOFT_BUDGET` | `LiteLLMProxySettings.USER_SOFT_BUDGET` | `None` |  | Get alerts when user crosses given budget, doesn't block requests. |
| `LITE_LLM_PROXY_USER_TPM_LIMIT` | `LiteLLMProxySettings.USER_TPM_LIMIT` | `None` |  | Specify tpm limit for a given user (Tokens per minute) |
| `MEM0_ENABLE_USER_MEMORY_GRAPH` | `Mem0Settings.ENABLE_USER_MEMORY_GRAPH` | `True` |  | Whether user-memory writes/reads use the Neo4j graph store. The graph adds ~3 sequential LLM calls per save (issue #1179). Default True preserves current behavior; set False to disable the graph for user memory. Organization memory always keeps the graph. |
| `MEM0_SUPPORT_VISION` | `Mem0Settings.SUPPORT_VISION` | `True` |  | Whether to support vision |
| `MEM0_VISION_DETAIL` | `Mem0Settings.VISION_DETAIL` | `'auto'` |  | Vision details |
| `MEMORY_DEFAULT_TENANT_ID` | `MemorySettings.DEFAULT_TENANT_ID` | `'AIHub'` |  | Default tenant ID for memory scoping |
| `MEMORY_DEFAULT_TENANT_NAMESPACE` | `MemorySettings.DEFAULT_TENANT_NAMESPACE` | `None` |  | Default tenant namespace for department-level scoping |
| `MILVUS_URL` | `MilvusSettings.URL` | _(supplied by compose)_ | `api`, `attu`, `default_rag_pipeline`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline` | Connection URL for Milvus DB Server |
| `MINERU_API_BASE_URL` | `MineruSettings.API_BASE_URL` | `'http://mineru-api:8000'` | `api`, `default_rag_pipeline`, `shared_rag_pipeline` | MinerU API endpoint URL |
| `MINERU_EXTENSIONS` | `MineruSettings.EXTENSIONS` | `['pdf', 'png', 'jpeg', 'jp2', 'webp', 'gif', 'bmp', 'jpg', 'tiff']` |  | File extensions supported by MinerU |
| `MINERU_VLM_SERVER_API_KEY` | `MineruSettings.VLM_SERVER_API_KEY` | `SecretStr('')` | `api`, `default_rag_pipeline`, `shared_rag_pipeline` | LiteLLM API key for VLM requests |
| `MINERU_VLM_SERVER_URL` | `MineruSettings.VLM_SERVER_URL` | `'http://litellm:4000'` | `api`, `default_rag_pipeline`, `shared_rag_pipeline` | LiteLLM proxy URL for VLM routing |
| `MONGO_CONNECTION_STRING` | `MongoSettings.CONNECTION_STRING` | _(supplied by compose)_ | `api`, `bot`, `default_rag_pipeline`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `llm_wrapping_agent`, `namespace_selection_agent`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline`, `sysadmin-api` | Overwrite the MongoDB connection string |
| `NATS_ENDPOINT` | `NatsSettings.ENDPOINT` | _(supplied by compose)_ | `api`, `bot`, `default_rag_pipeline`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline`, `sysadmin-api` | Connection endpoint for NATS messaging system |
| `NEO4J_URL` | `Neo4jSettings.URL` | _(supplied by compose)_ | `api`, `bot`, `llm_wrapping_agent`, `memory_writer_agent`, `rag_agent`, `shared_rag_pipeline` | Connection URL for Neo4j DB Server |
| `NOTIFICATION_DAGSTER_UI_BASE_URL` | `NotificationSettings.DAGSTER_UI_BASE_URL` | `None` | `default_rag_pipeline`, `shared_rag_pipeline` | Base URL of the Dagster UI used to build deep links in notification bodies (e.g. 'https://dagster.example.com'). |
| `NOTIFICATION_MIN_INTERVAL_SECONDS` | `NotificationSettings.MIN_INTERVAL_SECONDS` | `30` | `default_rag_pipeline`, `shared_rag_pipeline` | Minimum interval between sensor ticks in seconds. |
| `NOTIFICATION_TITLE_PREFIX` | `NotificationSettings.TITLE_PREFIX` | `'Swiss AI Hub Pipeline'` | `default_rag_pipeline`, `shared_rag_pipeline` | Prefix prepended to the notification title. |
| `OPENWEBUI_BASE_URL` | `OpenWebuiSettings.BASE_URL` | _(supplied by compose)_ | `api`, `sysadmin-api` | OpenWebUI server base URL |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `OpenTelemetrySettings.EXPORTER_OTLP_ENDPOINT` | `None` | `api`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `litellm`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `open-webui`, `rag_agent`, `retrieval_agent`, `sysadmin-api` | OTLP exporter endpoint URL |
| `OTEL_EXPORTER_OTLP_INSECURE` | `OpenTelemetrySettings.EXPORTER_OTLP_INSECURE` | `True` | `open-webui` | Use insecure connection (no TLS) for gRPC |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | `OpenTelemetrySettings.EXPORTER_OTLP_PROTOCOL` | `'grpc'` | `api`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `litellm`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `open-webui`, `rag_agent`, `retrieval_agent`, `sysadmin-api` | OTLP protocol |
| `OTEL_RESOURCE_SERVICE_NAME` | `OpenTelemetrySettings.RESOURCE_SERVICE_NAME` | `None` | `api`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `rag_agent`, `retrieval_agent`, `sysadmin-api` | Resource service name |
| `OTEL_RESOURCE_SERVICE_NAMESPACE` | `OpenTelemetrySettings.RESOURCE_SERVICE_NAMESPACE` | `None` | `api`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `rag_agent`, `retrieval_agent`, `sysadmin-api` | Resource service namespace |
| `OTEL_RESOURCE_SERVICE_VERSION` | `OpenTelemetrySettings.RESOURCE_SERVICE_VERSION` | `None` | `api`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `rag_agent`, `retrieval_agent`, `sysadmin-api` | Resource service version |
| `PARSING_PASSTHROUGH_EXTENSIONS` | `ParsingSettings.PASSTHROUGH_EXTENSIONS` | `[]` |  | File extensions that return empty content instead of 400 (e.g. for agent-only processing). Set via env as JSON array: PARSING_PASSTHROUGH_EXTENSIONS='["zip","wav"]' |
| `RCLONE_URL` | `RcloneSettings.URL` | `'http://rclone:5572'` |  | Rclone RC API URL (e.g., http://rclone:5572). |
| `REDIS_URL` | `RedisSettings.URL` | _(supplied by compose)_ | `api`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `open-webui`, `rag_agent`, `retrieval_agent`, `sysadmin-api` | Connection URL for Redis server (without token) |
| `S3_STORAGE_ENDPOINT` | `S3StorageSettings.ENDPOINT` | _(supplied by compose)_ | `api`, `default_rag_pipeline`, `expert_rag_agent`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline` | The s3 endpoint from either aws or minio. |
| `S3_STORAGE_PUBLIC_ENDPOINT` | `S3StorageSettings.PUBLIC_ENDPOINT` | `None` | `api`, `default_rag_pipeline`, `expert_rag_agent`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline` | The publicly accessible s3 endpoint for presigned URLs. If not set, falls back to ENDPOINT. Use this when internal and external endpoints differ (e.g., Docker internal vs Traefik-routed external). |
| `S3_STORAGE_REGION` | `S3StorageSettings.REGION` | `'us-east-1'` |  | The region for the s3 endpoint. For minio, value does not matter |
| `S3_STORAGE_URL_SIGNING_SECRET` | `S3StorageSettings.URL_SIGNING_SECRET` | _(supplied by compose)_ | `api`, `default_rag_pipeline`, `expert_rag_agent`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline` | A secret key used for signing and verifying temporary anonymous access URLs. |
| `USAGE_LIMIT_WARNING_THRESHOLD_PERCENT` | `UsageLimitSettings.WARNING_THRESHOLD_PERCENT` | `80` |  | Usage percentage at which warning headers are emitted |

## Additional variables for `GPU` deployments

The `GPU` variant currently does not introduce any operator-controlled variables beyond the base set above.
