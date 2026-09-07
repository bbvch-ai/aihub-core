---
title: Umgebungsvariablen
source_sha: "248e9d46ec4cf3f80bf3a32efeafabe38ebf0bbc03847e648f40881985d1b0b4"
description: Referenz aller Umgebungsvariablen, die vom Swiss AI Hub Deployment verwendet werden
---

# Umgebungsvariablen

Diese Seite listet alle Umgebungsvariablen auf, die vom Swiss AI Hub Deployment gelesen werden, organisiert nach ihrer Rolle. Sie wird automatisch aus den Pydantic-Settings-Klassen in `packages/*/swiss_ai_hub/**/*settings.py` und den docker-compose-Templates generiert. Bearbeiten Sie diese nicht manuell – führen Sie `make generate-env-docs` aus, um sie zu aktualisieren.

Variablen fallen in drei Kategorien:

- **Compose-erforderlich** — referenziert als `${VAR}` in `docker-compose.yml`. Muss in `.env` gesetzt werden, da die Compose-Templates des Projekts keine Fallback-Standardwerte bereitstellen.
- **App-erforderlich** — wird als Pflichtfeld von einer Pydantic `BaseSettings`-Klasse gelesen. Die Anwendung verweigert den Start, wenn nicht gesetzt.
- **Optional** — hat einen Standardwert im Code. Nur in `.env` setzen, um den Standardwert zu überschreiben.

Das Deployment verfügt über eine Basisvariante (`CPU`) sowie reine Erweiterungsvarianten (`GPU`). Der erste Abschnitt unten listet alle für die Basis erforderlichen Variablen auf; nachfolgende Abschnitte listen nur die zusätzlichen Variablen auf, die jede Erweiterung über die Basis hinaus einführt.

## Variablen für das Basis-Deployment (`CPU`)

### Erforderlich für docker-compose-Interpolation

Diese Variablen werden als `${VAR}` (ohne einen `${VAR:-default}` Fallback) irgendwo in `docker-compose.yml` referenziert. Die Compose-Analyse schlägt fehl oder rendert leere Werte, wenn `.env` sie nicht definiert. Die Spalte „Consumer“ zeigt das Pydantic-Settings-Feld, das die Variable liest, wenn unser Python-Code sie konsumiert; andernfalls verweist sie auf die Konfigurationsdatei, die sie einbettet (Keycloak Realm-Import, Identity-Provider-Konfiguration usw.), oder – falls beides nicht zutrifft – bleibt sie leer. Die Spalte „Service(s)“ listet die Compose-Service(s) auf, deren `environment:`-Block die Variable erhält.

| Variable | Consumer | Service(s) | Beschreibung |
|---|---|---|---|
| `ACME_EMAIL` |  | `traefik` | |
| `ADMIN_EMAIL` |  | `open-webui` | |
| `ADMIN_PASSWORD_HASH` |  | `traefik` | |
| `AIHUB_CREATE_DEFAULT_BUCKETS` | `AIHubSettings.CREATE_DEFAULT_BUCKETS` | `api`, `seaweedfs-init` | Erstellt standardmässige Wissens-Buckets und Namespaces |
| `AIHUB_DEFAULT_BUCKET_NAME` | `AIHubSettings.DEFAULT_BUCKET_NAME` | `api`, `default_rag_pipeline`, `seaweedfs-init` | Name des Standard-Wissens-Buckets |
| `AIHUB_DEFAULT_NAMESPACE_NAME` | `AIHubSettings.DEFAULT_NAMESPACE_NAME` | `api` | Name des Standard-Namespaces |
| `AIHUB_SHARED_BUCKET_NAME` | `AIHubSettings.SHARED_BUCKET_NAME` | `api`, `seaweedfs-init`, `shared_rag_pipeline` | Name des geteilten Wissens-Buckets |
| `AIHUB_SHARED_NAMESPACE_NAME` | `AIHubSettings.SHARED_NAMESPACE_NAME` | `api` | Name des geteilten Namespaces |
| `AIHUB_SHOW_LEGACY_KNOWLEDGE` | `AIHubSettings.SHOW_LEGACY_KNOWLEDGE` | `api` | Ob die veralteten, an das Deployment gebundenen Wissensdatenbanken (default_rag / shared_rag) in der UI gelistet werden. Standardmässig deaktiviert: Ihre Pipelines sind in jeder Phase deaktiviert, sodass die Datenbanken obsolet sind, es sei denn, ein Deployment betreibt noch eine ältere Pipeline – setzen Sie dies dort auf „true“, um sie weiterhin zu verwalten. |
| `AIHUB_STARTUP_TENANT_ACCESS_RULES` | `StartupTenantSettings.ACCESS_RULES` | `api` | Kommagetrennte Zugriffsregeln für den Startup-Mandanten. Verwenden Sie 'aihub.admin.>' für uneingeschränkten Zugriff auf alle Plattformfunktionen. |
| `AIHUB_STARTUP_TENANT_DESCRIPTION` | `StartupTenantSettings.DESCRIPTION` | `api` | Beschreibung des Startup-Mandanten. |
| `AIHUB_STARTUP_TENANT_ID` | `StartupTenantSettings.ID` | `api`, `keycloak` | Eindeutiger Bezeichner für den Startup-Mandanten. Wird auch als Keycloak-Gruppenname verwendet. |
| `AIHUB_STARTUP_TENANT_NAME` | `StartupTenantSettings.NAME` | `api` | Anzeigename des Startup-Mandanten. |
| `AIHUB_USER_SIGNUP_FIRST_ADMIN_USER_ROLES` | `UserSignupSettings.FIRST_ADMIN_USER_ROLES` | `api` | Kommagetrennte Liste der Rollen, die dem allerersten Benutzer zugewiesen werden. Dieser Benutzer ist typischerweise der anfängliche Plattformadministrator. |
| `AIHUB_USER_SIGNUP_REGULAR_USER_ROLES` | `UserSignupSettings.REGULAR_USER_ROLES` | `api` | Kommagetrennte Liste der Rollen, die regulären Benutzern (nicht dem ersten Benutzer) zugewiesen werden. Diese Benutzer haben typischerweise Standardzugriff auf die Plattform. |
| `AIHUB_VERSION` | `AIHubSettings.VERSION` | `api`, `bot`, `default_rag_pipeline`, `document_ingestion_pipeline`, `email_classification_agent`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `imap_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline`, `sysadmin-api` | Version der App |
| `AUTH_OPEN_WEBUI_SIGNING_SECRET` | `AuthSettings.OPEN_WEBUI_SIGNING_SECRET` | `api`, `open-webui`, `sysadmin-api` | OpenWebUI Signing Secret |
| `BACKUP_MINIMUM_KEEP` | `BackupSettings.MINIMUM_KEEP` | `backup-code` | |
| `BACKUP_POSTGRES_SUBPROCESS_TIMEOUT_SECONDS` | `BackupSettings.POSTGRES_SUBPROCESS_TIMEOUT_SECONDS` | `backup-code` | |
| `BACKUP_RETENTION_DAYS` | `BackupSettings.RETENTION_DAYS` | `backup-code` | |
| `BACKUP_S3_BUCKET` | `BackupSettings.S3_BUCKET` | `backup-code` | |
| `DAGSTER_CLEANUP_BATCH_LIMIT` | | `backup-code` | |
| `DAGSTER_DB` | | `backup-code` | |
| `DAGSTER_DEBUG_LOG_RETENTION_DAYS` | | `backup-code` | |
| `DAGSTER_INFO_LOG_RETENTION_DAYS` | | `backup-code` | |
| `DAGSTER_MAX_CONCURRENT_RUNS` | | `dagster-daemon`, `dagster-webserver`, `default_rag_pipeline`, `shared_rag_pipeline` | |
| `DAGSTER_UNIMPORTANT_EVENT_RETENTION_DAYS` | | `backup-code` | |
| `DAGSTER_WARNING_LOG_RETENTION_DAYS` | | `backup-code` | |
| `DOCUMENT_INGESTION_EMBEDDING_MODEL` | `DocumentIngestionPipelineSettings.EMBEDDING_MODEL` | `document_ingestion_pipeline` | LiteLLM-Modellname, der zum Einbetten von Chunks verwendet wird. |
| `DOCUMENT_INGESTION_LLM_MODEL` | `DocumentIngestionPipelineSettings.LLM_MODEL` | `document_ingestion_pipeline` | LiteLLM-Modellname, der für Zusammenfassungen, Tabellenverfeinerung und Abbildungsbeschreibungen verwendet wird. |
| `DOCUMENT_INGESTION_OBSERVE_JOB_HOUR` | `DocumentIngestionPipelineSettings.OBSERVE_JOB_HOUR` | `document_ingestion_pipeline` | Stunde des täglichen Beobachtungsplans pro Bucket. |
| `DOCUMENT_INGESTION_OBSERVE_JOB_MINUTE` | `DocumentIngestionPipelineSettings.OBSERVE_JOB_MINUTE` | `document_ingestion_pipeline` | Minute des täglichen Beobachtungsplans pro Bucket. |
| `DOCUMENT_INGESTION_WITH_FIGURE_DESCRIPTIONS` | `DocumentIngestionPipelineSettings.WITH_FIGURE_DESCRIPTIONS` | `document_ingestion_pipeline` | Generiert Abbildungsbeschreibungen mit einem Vision LLM. |
| `DOCUMENT_INGESTION_WITH_SUMMARY_NODES` | `DocumentIngestionPipelineSettings.WITH_SUMMARY_NODES` | `document_ingestion_pipeline` | Generiert rekursive Zusammenfassungen für hierarchisches RAG. |
| `DOCUMENT_INGESTION_WITH_TABLE_REFINEMENT` | `DocumentIngestionPipelineSettings.WITH_TABLE_REFINEMENT` | `document_ingestion_pipeline` | Verfeinert Tabellen mit dem LLM, um Struktur zu erkennen und sie aufzuteilen. |
| `DOMAIN` | `30-clients.json`, `realm-settings.json` | `api`, `bot`, `default_rag_pipeline`, `document_ingestion_pipeline`, `email_classification_agent`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `imap_agent`, `keycloak`, `keycloak-config`, `langfuse-web`, `litellm`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `oauth2proxy-attu`, `oauth2proxy-backup`, `oauth2proxy-dagster`, `oauth2proxy-seaweed`, `open-webui`, `rag_agent`, `retrieval_agent`, `seaweedfs-s3`, `shared_rag_pipeline`, `sysadmin-api`, `sysadmin-web`, `traefik`, `web` | |
| `ENABLE_OTEL_METRICS` | | `open-webui` | |
| `ENV` | | `api`, `open-webui`, `sysadmin-api` | |
| `ETCD_TOKEN` | | `etcd`, `etcd-init`, `milvus-standalone`, `seaweedfs-filer` | |
| `EXPERT_ASKING_CHANNEL_TYPE` | | `expert_asking_agent` | |
| `GEMINI_API_KEY` | | `litellm` | |
| `HUGGINGFACE_API_KEY` | | `litellm`, `vllm`, `vllm-bge-m3`, `vllm-bge-reranker` | |
| `JUPYTER_TOKEN` | | `api`, `jupyter` | |
| `KEYCLOAK_ADMIN_PASSWORD` | | `keycloak`, `keycloak-config` | |
| `KEYCLOAK_ADMIN_USER` | | `keycloak`, `keycloak-config` | |
| `KEYCLOAK_API_SERVICE_CLIENT_SECRET` | `KeycloakSettings.API_SERVICE_CLIENT_SECRET` | `api`, `bot`, `keycloak`, `keycloak-config`, `sysadmin-api` | Client Secret für das API-Service-Konto |
| `KEYCLOAK_AZURE_CLIENT_ID` | `identity-providers.json` | `keycloak` | |
| `KEYCLOAK_AZURE_CLIENT_SECRET` | `identity-providers.json` | `keycloak` | |
| `KEYCLOAK_AZURE_TENANT_ID` | `identity-providers.json` | `keycloak` | |
| `KEYCLOAK_OAUTH2_PROXY_ATTU_SECRET` | `30-clients.json` | `keycloak`, `keycloak-config`, `oauth2proxy-attu` | |
| `KEYCLOAK_OAUTH2_PROXY_BACKUP_SECRET` | `30-clients.json` | `keycloak`, `keycloak-config`, `oauth2proxy-backup` | |
| `KEYCLOAK_OAUTH2_PROXY_DAGSTER_SECRET` | `30-clients.json` | `keycloak`, `keycloak-config`, `oauth2proxy-dagster` | |
| `KEYCLOAK_OAUTH2_PROXY_DATALAKE_SECRET` | `30-clients.json` | `keycloak`, `keycloak-config`, `oauth2proxy-seaweed` | |
| `KEYCLOAK_OPENWEBUI_CLIENT_SECRET` | `30-clients.json` | `keycloak`, `keycloak-config`, `open-webui` | |
| `KEYCLOAK_SHOW_KEYCLOAK_LOGIN` | `KeycloakSettings.SHOW_KEYCLOAK_LOGIN` | `api`, `sysadmin-api` | Zeigt einen direkten Keycloak-Login-Button neben föderierten IDPs |
| `LANGFUSE_ALLOWED_ORGANIZATION_CREATORS` | | `langfuse-web` | |
| `LANGFUSE_CLICKHOUSE_PASSWORD` | | `backup-code`, `clickhouse`, `langfuse-web`, `langfuse-worker` | |
| `LANGFUSE_ENCRYPTION_KEY` | | `langfuse-web`, `langfuse-worker` | |
| `LANGFUSE_INIT_USER_EMAIL` | | `langfuse-web` | |
| `LANGFUSE_INIT_USER_PASSWORD` | | `langfuse-web` | |
| `LANGFUSE_KEYCLOAK_CLIENT_SECRET` | | `keycloak`, `keycloak-config`, `langfuse-web` | |
| `LANGFUSE_NEXTAUTH_SECRET` | | `langfuse-web` | |
| `LANGFUSE_PUBLIC_KEY` | `LangfuseSettings.PUBLIC_KEY` | `api`, `langfuse-web`, `otel-collector` | Langfuse Public API Key |
| `LANGFUSE_SALT` | | `langfuse-web`, `langfuse-worker` | |
| `LANGFUSE_SECRET_KEY` | `LangfuseSettings.SECRET_KEY` | `api`, `langfuse-web`, `otel-collector` | Langfuse Secret API Key |
| `LITELLM_MASTER_KEY` | `litellm-config.yml` | `api`, `default_rag_pipeline`, `document_ingestion_pipeline`, `email_classification_agent`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `imap_agent`, `litellm`, `llm_wrapping_agent`, `memory_writer_agent`, `mineru-api`, `namespace_selection_agent`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline` | |
| `LITELLM_UI_PASSWORD` | | `litellm` | |
| `LITELLM_UI_USERNAME` | | `litellm` | |
| `LOCAL_LLM_TOKEN` | `litellm-config.yml` | `litellm`, `vllm`, `vllm-bge-m3`, `vllm-bge-reranker` | |
| `LOG_LEVEL` | `LogSettings.LEVEL` | `api`, `bot`, `dagster-daemon`, `dagster-webserver`, `default_rag_pipeline`, `document_ingestion_pipeline`, `email_classification_agent`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `imap_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `open-webui`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline`, `sysadmin-api`, `traefik` | Logging-Level |
| `MAINTENANCE_DISABLED` | | `backup-code` | |
| `MEM0_EMBEDDING_MODEL_NAME` | `Mem0Settings.EMBEDDING_MODEL_NAME` | `api`, `bot`, `expert_asking_agent`, `expert_rag_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `rag_agent`, `shared_rag_pipeline` | Name des zu verwendenden Embedding-Modells |
| `MEM0_LLM_NAME` | `Mem0Settings.LLM_NAME` | `api`, `bot`, `expert_asking_agent`, `expert_rag_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `rag_agent`, `shared_rag_pipeline` | Name des zu verwendenden LLM |
| `MEM0_RERANKING_MODEL_NAME` | `Mem0Settings.RERANKING_MODEL_NAME` | `api`, `bot`, `expert_asking_agent`, `expert_rag_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `rag_agent`, `shared_rag_pipeline` | Name des zu verwendenden Embedding-Modells |
| `MEM0_TELEMETRY` | | `api`, `bot`, `email_classification_agent`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `imap_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline` | |
| `MILVUS_DIMENSION` | `MilvusSettings.DIMENSION` | `api`, `default_rag_pipeline`, `document_ingestion_pipeline`, `email_classification_agent`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `imap_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline` | Dimension des Embedding-Vektors |
| `MILVUS_ROOT_PASSWORD` | `MilvusSettings.ROOT_PASSWORD` | `api`, `attu`, `backup-code`, `default_rag_pipeline`, `document_ingestion_pipeline`, `email_classification_agent`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `imap_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `milvus-standalone`, `namespace_selection_agent`, `open-webui`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline` | Root-Passwort für die Milvus-Authentifizierung. Wenn nicht gesetzt, wird keine Authentifizierung verwendet. Der Benutzername ist immer 'root'. |
| `MINERU_API_MAX_CONCURRENT_REQUESTS` | | `mineru-api` | |
| `MINERU_API_TIMEOUT` | `MineruSettings.API_TIMEOUT` | `api`, `default_rag_pipeline`, `document_ingestion_pipeline`, `email_classification_agent`, `shared_rag_pipeline` | Timeout für MinerU API-Aufrufe in Sekunden |
| `MINERU_FORMULA_ENABLE` | `MineruSettings.FORMULA_ENABLE` | `api`, `default_rag_pipeline`, `document_ingestion_pipeline`, `email_classification_agent`, `shared_rag_pipeline` | Aktiviert das Parsen von Formeln/Gleichungen |
| `MINERU_MAX_CONCURRENT_BATCH_REQUESTS` | `MineruSettings.MAX_CONCURRENT_BATCH_REQUESTS` | `api`, `default_rag_pipeline`, `email_classification_agent`, `shared_rag_pipeline` | Client-seitige gleichzeitige Seiten-Batch-Anfragen pro Dokument |
| `MINERU_PAGE_BATCH_SIZE` | `MineruSettings.PAGE_BATCH_SIZE` | `api`, `default_rag_pipeline`, `email_classification_agent`, `shared_rag_pipeline` | Seiten pro MinerU-Anfrage für PDFs; hält den Serverspeicher konstant. 0 deaktiviert das Batching |
| `MINERU_TABLE_ENABLE` | `MineruSettings.TABLE_ENABLE` | `api`, `default_rag_pipeline`, `document_ingestion_pipeline`, `email_classification_agent`, `shared_rag_pipeline` | Aktiviert die Tabellenerkennung und -analyse |
| `MINERU_VLM_NAME` | `MineruSettings.VLM_NAME` | `api`, `default_rag_pipeline`, `document_ingestion_pipeline`, `email_classification_agent`, `mineru-api`, `shared_rag_pipeline` | LiteLLM-Modellalias für MinerU VLM |
| `MONGO_PASSWORD` | | `api`, `backup-code`, `bot`, `default_rag_pipeline`, `document_ingestion_pipeline`, `email_classification_agent`, `expert_asking_agent`, `expert_rag_agent`, `ferretdb`, `few_shot_agent`, `imap_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `postgres-ferretdb`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline`, `sysadmin-api` | |
| `MONGO_USERNAME` | | `api`, `backup-code`, `bot`, `default_rag_pipeline`, `document_ingestion_pipeline`, `email_classification_agent`, `expert_asking_agent`, `expert_rag_agent`, `ferretdb`, `few_shot_agent`, `imap_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `postgres-ferretdb`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline`, `sysadmin-api` | |
| `NATS_TOKEN` | `NatsSettings.TOKEN` | `api`, `backup-code`, `bot`, `default_rag_pipeline`, `document_ingestion_pipeline`, `email_classification_agent`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `imap_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `nats`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline`, `sysadmin-api` | Authentifizierungstoken für den NATS-Server. Wenn nicht gesetzt, wird keine Authentifizierung verwendet. |
| `NEO4J_PASSWORD` | `Neo4jSettings.PASSWORD` | `api`, `bot`, `expert_asking_agent`, `expert_rag_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `neo4j`, `rag_agent`, `shared_rag_pipeline` | Passwort für den Neo4j DB-Server |
| `NEO4J_USERNAME` | `Neo4jSettings.USERNAME` | `api`, `bot`, `expert_asking_agent`, `expert_rag_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `neo4j`, `rag_agent`, `shared_rag_pipeline` | Benutzername für den Neo4j DB-Server |
| `NOTIFICATION_URLS` | `NotificationSettings.URLS` | `default_rag_pipeline`, `document_ingestion_pipeline`, `shared_rag_pipeline` | Apprise Benachrichtigungs-URIs (kommagetrennt). Beispiele: 'slack://TokenA/TokenB/TokenC/#alerts', 'mailto://user:pw@smtp.example.com', 'discord://webhook_id/webhook_token'. Siehe https://github.com/caronc/apprise für die vollständige Liste. |
| `OAUTH_ADMIN_ROLES_OPENWEBUI` | | `open-webui` | |
| `OAUTH_ALLOWED_GROUPS_ATTU` | | `oauth2proxy-attu` | |
| `OAUTH_ALLOWED_GROUPS_BACKUP` | | `oauth2proxy-backup` | |
| `OAUTH_ALLOWED_GROUPS_DAGSTER` | | `oauth2proxy-dagster` | |
| `OAUTH_ALLOWED_GROUPS_SEAWEEDFS` | | `oauth2proxy-seaweed` | |
| `OAUTH_CLIENT_ID` | | `api`, `bot`, `open-webui`, `sysadmin-api`, `sysadmin-web`, `web` | |
| `OAUTH_CLIENT_SECRET` | | `api`, `bot`, `open-webui`, `sysadmin-api` | |
| `OAUTH_COOKIE_SECRET_ATTU` | | `oauth2proxy-attu` | |
| `OAUTH_COOKIE_SECRET_BACKUP` | | `oauth2proxy-backup` | |
| `OAUTH_COOKIE_SECRET_DAGSTER` | | `oauth2proxy-dagster` | |
| `OAUTH_COOKIE_SECRET_SEAWEEDFS` | | `oauth2proxy-seaweed` | |
| `OAUTH_CUSTOM_SIGN_IN_LOGO` | | `oauth2proxy-attu`, `oauth2proxy-backup`, `oauth2proxy-dagster`, `oauth2proxy-seaweed` | |
| `OAUTH_TENANT_ID` | | `api`, `sysadmin-api` | |
| `OPENWEBUI_BYPASS_ADMIN_ACCESS_CONTROL` | | `open-webui` | |
| `OPENWEBUI_ENABLE_ADMIN_EXPORT` | | `open-webui` | |
| `OPENWEBUI_MODEL_NAME_LOCALE` | `OpenWebuiSettings.MODEL_NAME_LOCALE` | `open-webui` | Gebietsschema, das zum Rendern von Agent-Workspace-Modellnamen in OpenWebUI verwendet wird, welches nur einen einzigen Namen pro Modell speichert. Fällt zurück auf das Plattform-Standardgebietsschema und dann auf jede verfügbare Übersetzung. |
| `OPENWEBUI_SCIM_TOKEN` | `OpenWebuiSettings.SCIM_TOKEN` | `api`, `open-webui`, `sysadmin-api` | SCIM 2.0 Bearer-Token für Gruppen- und Benutzerbereitstellung |
| `OPENWEBUI_SECRET_KEY` | `OpenWebuiSettings.SECRET_KEY` | `api`, `open-webui`, `sysadmin-api` | OpenWebUI WEBUI_SECRET_KEY für JWT-Signierung |
| `OPENWEBUI_SERVICE_ACCOUNT_ID` | `OpenWebuiSettings.SERVICE_ACCOUNT_ID` | `api`, `openwebui-init`, `sysadmin-api` | UUID des AI-Hub Service Accounts in der OpenWebUI-Datenbank |
| `OPENWEBUI_WEBHOOK_SECRET` | `OpenWebuiSettings.WEBHOOK_SECRET` | `api`, `open-webui`, `sysadmin-api` | Geteiltes Secret zur Authentifizierung von OpenWebUI-Webhook-Aufrufen |
| `OPEN_TERMINAL_API_KEY` | | `open-terminal`, `open-webui` | |
| `OTEL_CLOUD_ENDPOINT` | `otel-config.yml` | `otel-collector` | |
| `OTEL_CLOUD_HEADERS` | `otel-config.yml` | `otel-collector` | |
| `OTEL_ENABLED` | `OpenTelemetrySettings.ENABLED` | `api`, `email_classification_agent`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `imap_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `rag_agent`, `retrieval_agent`, `sysadmin-api` | OpenTelemetry-Tracing vollständig aktivieren/deaktivieren |
| `OTEL_METRICS_ENABLED` | `OpenTelemetrySettings.METRICS_ENABLED` | `api` | OpenTelemetry-Anforderungsmetriken aktivieren/deaktivieren (getrennt vom Tracing) |
| `POSTGRES_PASSWORD` | `openwebui-init-openwebui.sh` | `backup-code`, `dagster-daemon`, `dagster-webserver`, `default_rag_pipeline`, `document_ingestion_pipeline`, `keycloak`, `langfuse-web`, `langfuse-worker`, `litellm`, `open-webui`, `openwebui-init`, `pgbouncer`, `postgres`, `postgres-ferretdb`, `shared_rag_pipeline` | |
| `POSTGRES_PORT` | `openwebui-init-openwebui.sh` | `backup-code`, `openwebui-init` | |
| `POSTGRES_USER` | `openwebui-init-openwebui.sh` | `backup-code`, `dagster-daemon`, `dagster-webserver`, `default_rag_pipeline`, `document_ingestion_pipeline`, `keycloak`, `langfuse-web`, `langfuse-worker`, `litellm`, `open-webui`, `openwebui-init`, `pgbouncer`, `postgres`, `postgres-ferretdb`, `shared_rag_pipeline` | |
| `RAG_IMAGE_INLINE_ENABLED` | `RagImageInlineSettings.ENABLED` | `expert_rag_agent`, `litellm`, `rag_agent`, `retrieval_agent` | Ob RAG-Abbildungen als Base64 am LiteLLM-Gateway inline eingebettet werden. |
| `RAG_IMAGE_INLINE_MAX_BYTES` | | `litellm` | |
| `RCLONE_RC_PASS` | `RcloneSettings.RC_PASS` | `rclone` | RC API-Passwort für die Authentifizierung. |
| `RCLONE_RC_USER` | `RcloneSettings.RC_USER` | `rclone` | RC API-Benutzername für die Authentifizierung. |
| `REDIS_TOKEN` | `RedisSettings.TOKEN` | `api`, `backup-code`, `email_classification_agent`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `imap_agent`, `langfuse-web`, `langfuse-worker`, `litellm`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `open-webui`, `rag_agent`, `retrieval_agent`, `sysadmin-api`, `valkey` | Authentifizierungstoken für den Redis-Server. Wenn nicht gesetzt, wird keine Authentifizierung verwendet. |
| `S3_STORAGE_ACCESS_KEY` | `S3StorageSettings.ACCESS_KEY` | `api`, `backup-code`, `clickhouse`, `default_rag_pipeline`, `document_ingestion_pipeline`, `email_classification_agent`, `expert_rag_agent`, `imap_agent`, `langfuse-web`, `langfuse-worker`, `milvus-standalone`, `open-webui`, `rag_agent`, `retrieval_agent`, `seaweedfs-init`, `seaweedfs-s3`, `shared_rag_pipeline` | Der Access Key für den S3-Endpunkt. |
| `S3_STORAGE_SECRET_KEY` | `S3StorageSettings.SECRET_KEY` | `api`, `backup-code`, `clickhouse`, `default_rag_pipeline`, `document_ingestion_pipeline`, `email_classification_agent`, `expert_rag_agent`, `imap_agent`, `langfuse-web`, `langfuse-worker`, `milvus-standalone`, `open-webui`, `rag_agent`, `retrieval_agent`, `seaweedfs-init`, `seaweedfs-s3`, `shared_rag_pipeline` | Der Secret Key für den S3-Endpunkt. |
| `SCHEDULER_EVENT_RETENTION_DAYS` | `SchedulerSettings.EVENT_RETENTION_DAYS` | `api` | Alter, nach dem Ereignisse in einem geplanten Thread bereinigt werden. Null deaktiviert die Bereinigung vollständig, was der Standard ist: Das Löschen der Historie eines Mandanten muss eine Handlung des Operators sein, niemals etwas, das ein Deployment von selbst beginnt. |
| `SCHEDULER_LEASE_TTL_SECONDS` | `SchedulerSettings.LEASE_TTL_SECONDS` | `api` | Lebensdauer des Leader-Lease. Muss die Worst-Case-Tick-Laufzeit überschreiten, da sonst das Lease mitten im Tick abläuft und eine zweite Replika gleichzeitig eine startet. |
| `SCHEDULER_MAX_CATCHUP_MINUTES` | `SchedulerSettings.MAX_CATCHUP_MINUTES` | `api` | Wie weit ein Tick nach Ausfallzeiten zurückgespielt wird. Ereignisse, die älter sind als diese, werden protokolliert und verworfen, anstatt als eine Flut veralteter Läufe ausgelöst zu werden. |
| `SCHEDULER_MAX_RUNS_PER_PROFILE_PER_MONTH` | `SchedulerSettings.MAX_RUNS_PER_PROFILE_PER_MONTH` | `api` | Die meisten Läufe, die ein einzelner Zeitplan in 30 Tagen produzieren darf, werden beim Speichern des Profils abgelehnt. Standardmässig auf den engsten Zeitplan eingestellt, den Cron ausdrücken kann (jede Minute), sodass standardmässig nichts ausdrückbares abgelehnt wird und dies für ein Deployment existiert, das weniger zulassen möchte. |
| `SCHEDULER_MAX_TOTAL_RUNS_PER_MONTH` | `SchedulerSettings.MAX_TOTAL_RUNS_PER_MONTH` | `api` | Die meisten Läufe, die alle Zeitpläne zusammen in 30 Tagen produzieren dürfen, wird beim Speichern eines Profils geprüft. Null deaktiviert die Prüfung, was der Standard ist – die richtige Obergrenze hängt davon ab, wie viele Agents ein Deployment betreibt und was sie kosten, und keine plattformweite Konstante weiss das. |
| `SCHEDULER_REDIS_KEY_PREFIX` | `SchedulerSettings.REDIS_KEY_PREFIX` | `api` | Namespace für alle Scheduler-Schlüssel in Redis. Ändern Sie ihn, um einen isolierten Scheduler auszuführen. |
| `SCHEDULER_RETENTION_INTERVAL_SECONDS` | `SchedulerSettings.RETENTION_INTERVAL_SECONDS` | `api` | Mindestsekunden zwischen Bereinigungen, clusterweit erzwungen. Hält Massenlöschungen vom Tick fern. |
| `SCHEDULER_TICK_INTERVAL_SECONDS` | `SchedulerSettings.TICK_INTERVAL_SECONDS` | `api` | Sekunden zwischen Scheduler-Ticks. Begrenzt, wie spät ein Ereignis ausgelöst werden kann. |
| `SEARXNG_SECRET_KEY` | | `searxng` | |
| `SEAWEEDFS_TOKEN` | | `seaweedfs-filer`, `seaweedfs-master`, `seaweedfs-s3`, `seaweedfs-volume` | |
| `SLACK_CHANNEL_ID` | | `expert_asking_agent` | |
| `SLACK_SERVICE_URL` | | `expert_asking_agent` | |
| `SUPERUSER_EMAIL` | `SuperuserSettings.EMAIL` | `api`, `keycloak`, `sysadmin-api` | Keycloak E-Mail, die zur Suche des Superusers verwendet wird. |
| `SUPERUSER_FIRSTNAME` | `users-superuser.json` | `keycloak` | |
| `SUPERUSER_LASTNAME` | `users-superuser.json` | `keycloak` | |
| `SUPERUSER_PASSWORD` | `users-superuser.json` | `keycloak` | |
| `SUPERUSER_ROLES_JSON` | `SuperuserSettings.ROLES_JSON` | `api`, `keycloak`, `sysadmin-api` | JSON-Array der Realm-Rollen, die dem Superuser zugewiesen sind und über dieselbe Umgebungsvariable wortgetreu mit dem Keycloak-Realm-Import geteilt werden. Muss AIHubSysAdmin enthalten. |
| `SUPERUSER_TOKEN` | `SuperuserSettings.TOKEN` | `api`, `open-webui`, `sysadmin-api` | Statiisches Bearer-Token für Machine-to-Machine-API-Aufrufe. Muss mit 'sk-' beginnen. |
| `SUPERUSER_USERNAME` | `SuperuserSettings.USERNAME` | `api`, `keycloak`, `sysadmin-api` | Nur-Log-Bezeichnung für den initialisierten Superuser in den API-Startprotokollen. Wird nicht in Keycloak gespeichert – der Keycloak-Benutzername ist SUPERUSER_EMAIL (registrationEmailAsUsername), die Anmeldung erfolgt also per E-Mail. |
| `SWISS_LLM_CLOUD_API_BASE_URL` | `litellm-config.yml` | `litellm` | |
| `SWISS_LLM_CLOUD_API_KEY` | `litellm-config.yml` | `litellm` | |
| `SWISS_LLM_CLOUD_EMBEDDING_API_BASE_URL` | `litellm-config.yml` | `litellm` | |
| `SWISS_LLM_CLOUD_EMBEDDING_API_KEY` | `litellm-config.yml` | `litellm` | |
| `SWISS_LLM_CLOUD_IMAGE_API_BASE_URL` | `litellm-config.yml` | `litellm` | |
| `SWISS_LLM_CLOUD_IMAGE_API_KEY` | `litellm-config.yml` | `litellm` | |
| `SWISS_LLM_CLOUD_OCR_API_BASE_URL` | `litellm-config.yml` | `litellm` | |
| `SWISS_LLM_CLOUD_OCR_API_KEY` | `litellm-config.yml` | `litellm` | |
| `SWISS_LLM_CLOUD_RERANKING_API_BASE_URL` | `litellm-config.yml` | `litellm` | |
| `SWISS_LLM_CLOUD_RERANKING_API_KEY` | `litellm-config.yml` | `litellm` | |
| `SWISS_LLM_CLOUD_WHISPER_API_BASE_URL` | `litellm-config.yml` | `litellm` | |
| `SWISS_LLM_CLOUD_WHISPER_API_KEY` | `litellm-config.yml` | `litellm` | |
| `SWISS_LLM_CLOUD_WHISPER_MODEL` | `litellm-config.yml` | `litellm` | |
| `TEAMS_BOT_ID` | | `expert_asking_agent` | |
| `TEAMS_CHANNEL_ID` | | `expert_asking_agent` | |
| `TEAMS_TENANT_ID` | | `expert_asking_agent` | |

### Erforderlich durch SDK-Settings-Klassen (nicht im Standard-Deployment verwendet)

Diese Variablen sind als Pflichtfelder einer Pydantic `BaseSettings`-Klasse deklariert und werden **nicht** von einem Service im Standard-Docker-Compose-Stack konsumiert. Die leere Spalte „Service(s)“ spiegelt dies wider: Kein Container im Standard-Deployment lädt die Settings-Klasse. Sie werden erst dann operativ erforderlich, wenn ein benutzerdefinierter Agent, eine Pipeline oder eine andere Erweiterung zu Docker-Compose hinzugefügt wird, die die entsprechende SDK-Funktionalität aktiviert (z. B. der SharePoint-Konnektor oder der Azure Document Intelligence Loader). Bis dahin ist es in Ordnung, die Platzhalter unverändert zu lassen – Pydantic validiert die Klasse nur, wenn etwas sie instanziiert.

| Variable | Consumer | Service(s) | Beschreibung |
|---|---|---|---|
| `AZURE_DATA_LAKE_CONNECTION_STRING` | `AzureDataLakeSettings.CONNECTION_STRING` | | Azure Data Lake Verbindungszeichenfolge für explizite Authentifizierung. Empfohlen gegenüber impliziter Authentifizierung. |
| `AZURE_DOCUMENT_INTELLIGENCE_API_KEY` | `AzureDocumentIntelligenceSettings.API_KEY` | | API-Schlüssel für Document Intelligence |
| `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT` | `AzureDocumentIntelligenceSettings.ENDPOINT` | | |
| `SHAREPOINT_CLIENT_ID` | `SharePointSettings.CLIENT_ID` | | Die Anwendungs- (Client-)ID. |
| `SHAREPOINT_CLIENT_SECRET` | `SharePointSettings.CLIENT_SECRET` | | Das Client Secret für die Authentifizierung. |
| `SHAREPOINT_SITE_URL` | `SharePointSettings.SITE_URL` | | Die SharePoint-Site-URL. |
| `SHAREPOINT_TENANT_ID` | `SharePointSettings.TENANT_ID` | | Die Azure AD Tenant ID. |

### Optional: Plattform-Standardwerte überschreiben

Diese Variablen haben sinnvolle Standardwerte (oder werden Containern von Docker-Compose bereitgestellt) und müssen nicht in `.env` gesetzt werden. Fügen Sie sie nur hinzu, um den Standardwert zu überschreiben. Variablen, die mit `(von Compose bereitgestellt)` gekennzeichnet sind, werden von der Anwendung benötigt, erhalten ihren Wert jedoch über `docker-compose.yml` injiziert, sodass das Setzen in `.env` keine Auswirkung hat.

| Variable | Consumer | Default | Service(s) | Beschreibung |
|---|---|---|---|---|
| `AIHUB_API_DEBUG_MODE` | `AIHubSettings.API_DEBUG_MODE` | `Falsch` | | Debug-Modus für die Entwicklung |
| `AIHUB_CREATE_DEFAULT_ROLES` | `AIHubSettings.CREATE_DEFAULT_ROLES` | `Wahr` | `api`, `sysadmin-api` | Erstellt Standardrollen wie AI-Hub Admin und AI-Hub User |
| `AIHUB_FRONTEND_ORIGIN` | `AIHubSettings.FRONTEND_ORIGIN` | _(von Compose bereitgestellt)_ | `api`, `bot`, `default_rag_pipeline`, `document_ingestion_pipeline`, `email_classification_agent`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `imap_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline`, `sysadmin-api` | Kommagetrennte Liste der Ursprünge, die CORS erlaubt sind |
| `AIHUB_INTERNAL_API_BASE_URL` | `AIHubSettings.INTERNAL_API_BASE_URL` | `'http://api:8000'` | `sysadmin-api` | Interne Basis-URL der Hauptplattform-API (ohne Pfad), verwendet für Server-zu-Server-Aufrufe, wie z. B. die Proxy-Funktion der SysAdmin-Ebene für den Zugriffs-Fähigkeitskatalog. Vorhersehbar pro Deployment: der Docker-Service-Name in Compose, localhost in der lokalen Entwicklung. |
| `AIHUB_MONGO_MAIN_DB_NAME` | `AIHubSettings.MONGO_MAIN_DB_NAME` | `'aihub'` | | Name der MongoDB-Datenbank, die zum Speichern von Daten verwendet wird |
| `AIHUB_OPENAI_API_BASE_URL` | `AIHubSettings.OPENAI_API_BASE_URL` | `'http://api:8000/api/v1/active/openai'` | `api` | Basis-URL des OpenAI-kompatiblen Endpunkts von AI-Hub, verwendet für die Langfuse LLM-Verbindung |
| `AUTH_ENABLE_API_ACCESS` | `AuthSettings.ENABLE_API_ACCESS` | `Wahr` | `api`, `sysadmin-api` | API-Zugriff aktivieren |
| `AZURE_DOCUMENT_INTELLIGENCE_API_VERSION` | `AzureDocumentIntelligenceSettings.API_VERSION` | `'2024-11-30'` | | |
| `AZURE_DOCUMENT_INTELLIGENCE_EXTENSIONS` | `AzureDocumentIntelligenceSettings.EXTENSIONS` | `['pdf', 'docx', 'xlsx', 'pptx', 'html']` | | Unterstützte Dateierweiterungen für die Dokumentenverarbeitung |
| `BACKUP_AWS_ENDPOINT_URL` | `BackupSettings.AWS_ENDPOINT_URL` | `'http://seaweedfs-s3:9000'` | `backup-code` | |
| `BACKUP_CLICKHOUSE_HOST` | `BackupSettings.CLICKHOUSE_HOST` | `'clickhouse'` | `backup-code` | |
| `BACKUP_CLICKHOUSE_PORT` | `BackupSettings.CLICKHOUSE_PORT` | `8123` | | |
| `BACKUP_CLICKHOUSE_USER` | `BackupSettings.CLICKHOUSE_USER` | `'clickhouse'` | `backup-code` | |
| `BACKUP_DAGSTER_CLEANUP_BATCH_LIMIT` | `BackupSettings.DAGSTER_CLEANUP_BATCH_LIMIT` | `1000000` | `backup-code` | |
| `BACKUP_DAGSTER_DB` | `BackupSettings.DAGSTER_DB` | `'dagster'` | `backup-code` | |
| `BACKUP_DAGSTER_DEBUG_LOG_RETENTION_DAYS` | `BackupSettings.DAGSTER_DEBUG_LOG_RETENTION_DAYS` | `7` | `backup-code` | |
| `BACKUP_DAGSTER_INFO_LOG_RETENTION_DAYS` | `BackupSettings.DAGSTER_INFO_LOG_RETENTION_DAYS` | `60` | `backup-code` | |
| `BACKUP_DAGSTER_UNIMPORTANT_EVENT_RETENTION_DAYS` | `BackupSettings.DAGSTER_UNIMPORTANT_EVENT_RETENTION_DAYS` | `30` | `backup-code` | |
| `BACKUP_DAGSTER_WARNING_LOG_RETENTION_DAYS` | `BackupSettings.DAGSTER_WARNING_LOG_RETENTION_DAYS` | `60` | `backup-code` | |
| `BACKUP_LANGFUSE_CLICKHOUSE_PASSWORD` | `BackupSettings.LANGFUSE_CLICKHOUSE_PASSWORD` | _(von Compose bereitgestellt)_ | `backup-code` | |
| `BACKUP_MAINTENANCE_DISABLED` | `BackupSettings.MAINTENANCE_DISABLED` | `Falsch` | `backup-code` | |
| `BACKUP_MILVUS_HOST` | `BackupSettings.MILVUS_HOST` | `'milvus-standalone'` | `backup-code` | |
| `BACKUP_MILVUS_PORT` | `BackupSettings.MILVUS_PORT` | `19530` | `backup-code` | |
| `BACKUP_MILVUS_ROOT_PASSWORD` | `BackupSettings.MILVUS_ROOT_PASSWORD` | _(von Compose bereitgestellt)_ | `backup-code` | |
| `BACKUP_MONGO_PASSWORD` | `BackupSettings.MONGO_PASSWORD` | _(von Compose bereitgestellt)_ | `backup-code` | |
| `BACKUP_MONGO_USERNAME` | `BackupSettings.MONGO_USERNAME` | `'admin'` | `backup-code` | |
| `BACKUP_NATS_TOKEN` | `BackupSettings.NATS_TOKEN` | _(von Compose bereitgestellt)_ | `backup-code` | |
| `BACKUP_NATS_URL` | `BackupSettings.NATS_URL` | `'nats://nats:4222'` | `backup-code` | |
| `BACKUP_NEO4J_CONTAINER` | `BackupSettings.NEO4J_CONTAINER` | `'neo4j'` | `backup-code` | |
| `BACKUP_POSTGRES_FERRETDB_HOST` | `BackupSettings.POSTGRES_FERRETDB_HOST` | `'postgres-ferretdb'` | `backup-code` | |
| `BACKUP_POSTGRES_HOST` | `BackupSettings.POSTGRES_HOST` | `'postgres'` | `backup-code` | |
| `BACKUP_POSTGRES_PASSWORD` | `BackupSettings.POSTGRES_PASSWORD` | _(von Compose bereitgestellt)_ | `backup-code` | |
| `BACKUP_POSTGRES_PORT` | `BackupSettings.POSTGRES_PORT` | `5432` | `backup-code` | |
| `BACKUP_POSTGRES_USER` | `BackupSettings.POSTGRES_USER` | `'admin'` | `backup-code` | |
| `BACKUP_REDIS_TOKEN` | `BackupSettings.REDIS_TOKEN` | _(von Compose bereitgestellt)_ | `backup-code` | |
| `BACKUP_S3_STORAGE_ACCESS_KEY` | `BackupSettings.S3_STORAGE_ACCESS_KEY` | `'admin'` | `backup-code` | |
| `BACKUP_S3_STORAGE_SECRET_KEY` | `BackupSettings.S3_STORAGE_SECRET_KEY` | _(von Compose bereitgestellt)_ | `backup-code` | |
| `BACKUP_VALKEY_CONTAINER` | `BackupSettings.VALKEY_CONTAINER` | `'valkey'` | `backup-code` | |
| `BACKUP_VALKEY_HOST` | `BackupSettings.VALKEY_HOST` | `'valkey'` | | |
| `BACKUP_VALKEY_PORT` | `BackupSettings.VALKEY_PORT` | `6379` | | |
| `KEYCLOAK_API_SERVICE_CLIENT_ID` | `KeycloakSettings.API_SERVICE_CLIENT_ID` | `'aihub-api-service'` | | Client ID für das API-Service-Konto |
| `KEYCLOAK_EXTERNAL_URL` | `KeycloakSettings.EXTERNAL_URL` | `Keine` | `api`, `bot`, `sysadmin-api` | Externe Keycloak-URL, wie sie von Browsern gesehen wird, verwendet für die Aussteller-Validierung |
| `KEYCLOAK_REALM` | `KeycloakSettings.REALM` | `'aihub'` | `api`, `bot`, `sysadmin-api` | Keycloak Realm-Name |
| `KEYCLOAK_URL` | `KeycloakSettings.URL` | _(von Compose bereitgestellt)_ | `api`, `bot`, `keycloak-config`, `sysadmin-api` | Interne Keycloak-URL für direkten Zugriff (z. B. http://keycloak:8080) |
| `LANGFUSE_BASE_URL` | `LangfuseSettings.BASE_URL` | _(von Compose bereitgestellt)_ | `api` | Langfuse Server-Basis-URL |
| `LANGFUSE_PROJECT_ID` | `LangfuseSettings.PROJECT_ID` | `Keine` | `api` | Langfuse Projekt-ID zum Erstellen von Datensatz-URLs |
| `LANGFUSE_PUBLIC_URL` | `LangfuseSettings.PUBLIC_URL` | `Keine` | `api` | Öffentlich zugängliche Langfuse-URL für Browser-Links (z. B. https://langfuse.example.com) |
| `LANGFUSE_TIMEOUT` | `LangfuseSettings.TIMEOUT` | `60` | | Timeout in Sekunden für Langfuse API-Anfragen |
| `LITE_LLM_PROXY_API_KEY` | `LiteLLMProxySettings.API_KEY` | `Keine` | `api`, `default_rag_pipeline`, `document_ingestion_pipeline`, `email_classification_agent`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `imap_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline` | API-Schlüssel für die Authentifizierung. Wenn nicht angegeben, werden andere Authentifizierungsmethoden verwendet. |
| `LITE_LLM_PROXY_BASE_URL` | `LiteLLMProxySettings.BASE_URL` | _(von Compose bereitgestellt)_ | `api`, `default_rag_pipeline`, `document_ingestion_pipeline`, `email_classification_agent`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `imap_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline` | Die Basis-URL des Modells. |
| `LITE_LLM_PROXY_USER_BUDGET_DURATION` | `LiteLLMProxySettings.USER_BUDGET_DURATION` | `Keine` | | Das Budget wird am Ende der angegebenen Dauer zurückgesetzt. Wenn nicht gesetzt, wird das Budget nie zurückgesetzt. Sie können die Dauer in Sekunden ("30s"), Minuten ("30m"), Stunden ("30h"), Tagen ("30d"), Monaten ("1mo") angeben. |
| `LITE_LLM_PROXY_USER_MAX_BUDGET` | `LiteLLMProxySettings.USER_MAX_BUDGET` | `Keine` | | Budget, das einem Benutzer in einem Zeitraum zur Verfügung steht |
| `LITE_LLM_PROXY_USER_MAX_PARALLEL_REQUESTS` | `LiteLLMProxySettings.USER_MAX_PARALLEL_REQUESTS` | `Keine` | | Begrenzt die Rate eines Benutzers basierend auf der Anzahl paralleler Anfragen. Löst einen 429-Fehler aus, wenn die parallelen Anfragen des Benutzers > x sind. |
| `LITE_LLM_PROXY_USER_RPM_LIMIT` | `LiteLLMProxySettings.USER_RPM_LIMIT` | `Keine` | | RPM-Limit für einen bestimmten Benutzer festlegen (Anfragen pro Minute) |
| `LITE_LLM_PROXY_USER_SOFT_BUDGET` | `LiteLLMProxySettings.USER_SOFT_BUDGET` | `Keine` | | Erhält Benachrichtigungen, wenn der Benutzer das angegebene Budget überschreitet, blockiert aber keine Anfragen. |
| `LITE_LLM_PROXY_USER_TPM_LIMIT` | `LiteLLMProxySettings.USER_TPM_LIMIT` | `Keine` | | TPM-Limit für einen bestimmten Benutzer festlegen (Tokens pro Minute) |
| `MEM0_SUPPORT_VISION` | `Mem0Settings.SUPPORT_VISION` | `Wahr` | | Ob Vision unterstützt werden soll |
| `MEM0_VISION_DETAIL` | `Mem0Settings.VISION_DETAIL` | `'auto'` | | Visionsdetails |
| `MEMORY_DEFAULT_TENANT_ID` | `MemorySettings.DEFAULT_TENANT_ID` | `'AIHub'` | | Standard-Mandanten-ID für die Speicherskoping |
| `MEMORY_DEFAULT_TENANT_NAMESPACE` | `MemorySettings.DEFAULT_TENANT_NAMESPACE` | `Keine` | | Standard-Mandanten-Namespace für die Skoping auf Abteilungsebene |
| `MILVUS_URL` | `MilvusSettings.URL` | _(von Compose bereitgestellt)_ | `api`, `attu`, `default_rag_pipeline`, `document_ingestion_pipeline`, `email_classification_agent`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `imap_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline` | Verbindungs-URL für Milvus DB-Server |
| `MINERU_API_BASE_URL` | `MineruSettings.API_BASE_URL` | `'http://mineru-api:8000'` | `api`, `default_rag_pipeline`, `document_ingestion_pipeline`, `email_classification_agent`, `shared_rag_pipeline` | MinerU API-Endpunkt-URL |
| `MINERU_EXTENSIONS` | `MineruSettings.EXTENSIONS` | `['pdf', 'png', 'jpeg', 'jp2', 'webp', 'gif', 'bmp', 'jpg', 'tiff']` | | Vom MinerU unterstützte Dateierweiterungen |
| `MINERU_VLM_SERVER_API_KEY` | `MineruSettings.VLM_SERVER_API_KEY` | `SecretStr('')` | `api`, `default_rag_pipeline`, `document_ingestion_pipeline`, `email_classification_agent`, `shared_rag_pipeline` | LiteLLM API-Schlüssel für VLM-Anfragen |
| `MINERU_VLM_SERVER_URL` | `MineruSettings.VLM_SERVER_URL` | `'http://litellm:4000'` | `api`, `default_rag_pipeline`, `document_ingestion_pipeline`, `email_classification_agent`, `shared_rag_pipeline` | LiteLLM Proxy-URL für VLM-Routing |
| `MONGO_CONNECTION_STRING` | `MongoSettings.CONNECTION_STRING` | _(von Compose bereitgestellt)_ | `api`, `bot`, `default_rag_pipeline`, `document_ingestion_pipeline`, `email_classification_agent`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `imap_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline`, `sysadmin-api` | Überschreibt die MongoDB-Verbindungszeichenfolge |
| `NATS_ENDPOINT` | `NatsSettings.ENDPOINT` | _(von Compose bereitgestellt)_ | `api`, `bot`, `default_rag_pipeline`, `document_ingestion_pipeline`, `email_classification_agent`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `imap_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline`, `sysadmin-api` | Verbindungs-Endpunkt für das NATS-Messaging-System |
| `NEO4J_URL` | `Neo4jSettings.URL` | _(von Compose bereitgestellt)_ | `api`, `bot`, `expert_asking_agent`, `expert_rag_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `rag_agent`, `shared_rag_pipeline` | Verbindungs-URL für Neo4j DB-Server |
| `NOTIFICATION_DAGSTER_UI_BASE_URL` | `NotificationSettings.DAGSTER_UI_BASE_URL` | `Keine` | `default_rag_pipeline`, `document_ingestion_pipeline`, `shared_rag_pipeline` | Basis-URL der Dagster UI, die zum Erstellen von Deep Links in Benachrichtigungstexten verwendet wird (z. B. 'https://dagster.example.com'). |
| `NOTIFICATION_MIN_INTERVAL_SECONDS` | `NotificationSettings.MIN_INTERVAL_SECONDS` | `30` | `default_rag_pipeline`, `document_ingestion_pipeline`, `shared_rag_pipeline` | Mindestintervall zwischen Sensor-Ticks in Sekunden. |
| `NOTIFICATION_TITLE_PREFIX` | `NotificationSettings.TITLE_PREFIX` | `'Swiss AI Hub Pipeline'` | `default_rag_pipeline`, `document_ingestion_pipeline`, `shared_rag_pipeline` | Präfix, das dem Benachrichtigungstitel vorangestellt wird. |
| `OPENWEBUI_BASE_URL` | `OpenWebuiSettings.BASE_URL` | _(von Compose bereitgestellt)_ | `api`, `sysadmin-api` | OpenWebUI Server-Basis-URL |
| `OPENWEBUI_CONVERSATION_METADATA_MODEL` | `OpenWebuiSettings.CONVERSATION_METADATA_MODEL` | `'text-generation/gemma-4-31B-it'` | `api` | LiteLLM-Name (``capability/name``) des Modells, das Konversationsmetadaten – Chat-Titel und Folgefragen – für Chats generiert, die keinen Agenten im Hintergrund haben. OpenWebUI führt es unter der Identität des Endbenutzers aus, sodass eine Rolle ohne Zugriff auf dieses Modell beide Funktionen stillschweigend verliert; der Zugriffskatalog kennzeichnet das Modell aus diesem Grund. Dasselbe Modell wie die OpenWebUI ``TASK_MODEL``-Umgebungsvariable, jedoch in LiteLLM-Form, da diese den Workspace-Modell benennt, das es umhüllt. |
| `OTEL_BLRP_MAX_EXPORT_BATCH_SIZE` | `OpenTelemetrySettings.BLRP_MAX_EXPORT_BATCH_SIZE` | `2048` | | Log-Records pro OTLP-Export |
| `OTEL_BLRP_MAX_QUEUE_SIZE` | `OpenTelemetrySettings.BLRP_MAX_QUEUE_SIZE` | `16384` | | Gepufferte Log-Records, bevor neue verworfen werden |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `OpenTelemetrySettings.EXPORTER_OTLP_ENDPOINT` | `Keine` | `api`, `email_classification_agent`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `imap_agent`, `litellm`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `open-webui`, `rag_agent`, `retrieval_agent`, `sysadmin-api` | OTLP-Exporter-Endpunkt-URL |
| `OTEL_EXPORTER_OTLP_INSECURE` | `OpenTelemetrySettings.EXPORTER_OTLP_INSECURE` | `Wahr` | `open-webui` | Unsichere Verbindung verwenden (kein TLS) für gRPC |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | `OpenTelemetrySettings.EXPORTER_OTLP_PROTOCOL` | `'grpc'` | `api`, `email_classification_agent`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `imap_agent`, `litellm`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `open-webui`, `rag_agent`, `retrieval_agent`, `sysadmin-api` | OTLP-Protokoll |
| `OTEL_EXPORTER_OTLP_TIMEOUT` | `OpenTelemetrySettings.EXPORTER_OTLP_TIMEOUT` | `60` | | Sekunden, die ein OTLP-Export für Wiederholungsversuche aufwenden darf |
| `OTEL_RESOURCE_SERVICE_NAME` | `OpenTelemetrySettings.RESOURCE_SERVICE_NAME` | `Keine` | `api`, `email_classification_agent`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `imap_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `rag_agent`, `retrieval_agent`, `sysadmin-api` | Ressourcendienstname |
| `OTEL_RESOURCE_SERVICE_NAMESPACE` | `OpenTelemetrySettings.RESOURCE_SERVICE_NAMESPACE` | `Keine` | `api`, `email_classification_agent`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `imap_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `rag_agent`, `retrieval_agent`, `sysadmin-api` | Ressourcendienst-Namespace |
| `OTEL_RESOURCE_SERVICE_VERSION` | `OpenTelemetrySettings.RESOURCE_SERVICE_VERSION` | `Keine` | `api`, `email_classification_agent`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `imap_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `rag_agent`, `retrieval_agent`, `sysadmin-api` | Ressourcendienstversion |
| `PARSING_PASSTHROUGH_EXTENSIONS` | `ParsingSettings.PASSTHROUGH_EXTENSIONS` | `[]` | | Dateierweiterungen, die leeren Inhalt anstelle von 400 zurückgeben (z. B. für die Nur-Agenten-Verarbeitung). Über Umgebungsvariable als JSON-Array festlegen: PARSING_PASSTHROUGH_EXTENSIONS='["zip","wav"]' |
| `RCLONE_URL` | `RcloneSettings.URL` | `'http://rclone:5572'` | | Rclone RC API-URL (z. B. http://rclone:5572). |
| `REDIS_URL` | `RedisSettings.URL` | _(von Compose bereitgestellt)_ | `api`, `email_classification_agent`, `expert_asking_agent`, `expert_rag_agent`, `few_shot_agent`, `imap_agent`, `llm_wrapping_agent`, `memory_writer_agent`, `namespace_selection_agent`, `open-webui`, `rag_agent`, `retrieval_agent`, `sysadmin-api` | Verbindungs-URL für den Redis-Server (ohne Token) |
| `S3_STORAGE_ENDPOINT` | `S3StorageSettings.ENDPOINT` | _(von Compose bereitgestellt)_ | `api`, `default_rag_pipeline`, `document_ingestion_pipeline`, `email_classification_agent`, `expert_rag_agent`, `imap_agent`, `litellm`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline` | Der S3-Endpunkt von AWS oder MinIO. |
| `S3_STORAGE_INTERNAL_ENDPOINT` | `S3StorageSettings.INTERNAL_ENDPOINT` | `Keine` | | Der S3-Endpunkt im Cluster (Docker DNS) für vorab signierte URLs, die von anderen Services im Cluster abgerufen werden (z. B. das LiteLLM-Gateway, das RAG-Abbildungen inline einbettet). Wird nur zum Signieren verwendet, nie direkt verbunden, sodass es vom Host ohne DNS-Auflösung funktioniert. Wenn nicht gesetzt, fällt es auf ENDPOINT zurück. |
| `S3_STORAGE_PUBLIC_ENDPOINT` | `S3StorageSettings.PUBLIC_ENDPOINT` | `Keine` | `api`, `default_rag_pipeline`, `document_ingestion_pipeline`, `email_classification_agent`, `expert_rag_agent`, `imap_agent`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline` | Der öffentlich zugängliche S3-Endpunkt für vorab signierte URLs. Wenn nicht gesetzt, fällt es auf ENDPOINT zurück. Verwenden Sie dies, wenn interne und externe Endpunkte unterschiedlich sind (z. B. Docker intern vs. Traefik-geroutet extern). |
| `S3_STORAGE_REGION` | `S3StorageSettings.REGION` | `'us-east-1'` | | Die Region für den S3-Endpunkt. Für MinIO ist der Wert irrelevant |
| `S3_STORAGE_URL_SIGNING_SECRET` | `S3StorageSettings.URL_SIGNING_SECRET` | _(von Compose bereitgestellt)_ | `api`, `default_rag_pipeline`, `document_ingestion_pipeline`, `email_classification_agent`, `expert_rag_agent`, `imap_agent`, `rag_agent`, `retrieval_agent`, `shared_rag_pipeline` | Ein geheimen Schlüssel, der zum Signieren und Überprüfen temporärer anonymer Zugriffs-URLs verwendet wird. |
| `USAGE_LIMIT_WARNING_THRESHOLD_PERCENT` | `UsageLimitSettings.WARNING_THRESHOLD_PERCENT` | `80` | | Nutzungsprozentsatz, bei dem Warn-Header ausgegeben werden |

## Zusätzliche Variablen für GPU-Deployments

Die `GPU`-Variante führt derzeit keine vom Operator gesteuerten Variablen über den oben genannten Basissatz hinaus ein.
