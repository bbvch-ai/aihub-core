---
title: Ein-Befehl-Deployment
source_sha: 1dcb3cd3912994e5d3cada4e949b7f1b88384ba2784454c3bb0277d92e6ac679
---

# Ein-Befehl-Deployment: Starten Sie Ihre KI-Plattform

Die Swiss AI Hub Plattform wird mit einem einzigen Docker Compose Befehl deployed. Dieser optimierte Prozess bringt Ihre
vollständige KI-Infrastruktur in Minuten, nicht in Stunden, zum Laufen.

## Deployment-Übersicht

::: tip Zwei Deployment-Optionen
Der Swiss AI Hub unterstützt zwei Deployment-Modi. Befolgen Sie für beide die gleichen Schritte und verwenden Sie die
entsprechenden Befehle für Ihren Deployment-Typ:

- **Produktions-Deployment**: Deployment auf einem Server mit einem echten Domainnamen (z.B. `aihub.yourcompany.com`)

  - Verwendet `docker-compose.latest.yml`
  - Verwendet Let's Encrypt für automatische SSL-Zertifikate
  - Erfordert eine DNS-Konfiguration, die auf Ihren Server zeigt

- **Lokales Deployment**: Ausführung auf Ihrer lokalen Maschine für Entwicklung/Tests

  - Verwendet `docker-compose.local.yml`
  - Verwendet selbstsignierte SSL-Zertifikate (mkcert)
  - Verwendet die Domain `127.0.0.1.nip.io` (löst automatisch zu localhost auf)

Jeder der folgenden Schritte zeigt Befehle für beide Deployment-Typen. Befolgen Sie einfach die Befehle, die Ihrem
gewählten Deployment-Modus entsprechen.
:::

______________________________________________________________________

## Schritt 1: Deployment-Dateien herunterladen

**Für die Produktion:**

```bash
# Create deployment directory
mkdir swiss-ai-hub-deployment
cd swiss-ai-hub-deployment

# Download the production deployment configuration
curl -O https://raw.githubusercontent.com/bbvch-ai/aihub-core/main/docker-compose.latest.yml

# Download the configs directory
curl -L https://github.com/bbvch-ai/aihub-core/tarball/main | tar -xz --strip=2 "*/configs"
```

**Für lokales Deployment:**

```bash
# Create deployment directory
mkdir swiss-ai-hub-deployment
cd swiss-ai-hub-deployment

# Download the local deployment configuration
curl -O https://raw.githubusercontent.com/bbvch-ai/aihub-core/main/docker-compose.local.yml

# Download the configs directory
curl -L https://github.com/bbvch-ai/aihub-core/tarball/main | tar -xz --strip=2 "*/configs"

# Generate SSL certificates with mkcert
mkcert -install  # Install local CA (only needed once)
mkcert -key-file configs/traefik/certs/dev-key.pem -cert-file configs/traefik/certs/dev-cert.pem \
  "localhost" "*.localhost" \
  "127.0.0.1.nip.io" "*.127.0.0.1.nip.io"
```

::: tip Was ist nip.io?
Die Domain `*.127.0.0.1.nip.io` löst automatisch zu Ihrem Localhost (127.0.0.1) auf und bietet eine
Wildcard-DNS-Auflösung, ohne dass Sie Ihre Hosts-Datei ändern müssen. Dies ermöglicht ein Subdomain-basiertes Routing in
der lokalen Entwicklung.
:::

______________________________________________________________________

## Schritt 2: Umgebungsvariablen konfigurieren

### Umgebungskonfiguration erstellen

Erstellen Sie eine `.env`-Datei mit Ihren Konfigurationseinstellungen:

```bash
touch .env
```

### Wesentliche Konfigurationsvorlage

Kopieren Sie diese Vorlage in Ihre `.env`-Datei und ersetzen Sie die Platzhalterwerte:

```env
# =============================================================================
# AI-Hub Production Environment Configuration
# =============================================================================
# This file contains ONLY the environment variables that must be configured.
# All internal Docker network endpoints are hardcoded in the compose files.
# =============================================================================

# -----------------------------------------------------------------------------
# General Settings
# -----------------------------------------------------------------------------
LOG_LEVEL="INFO"
ENV="prod"
DOMAIN="REPLACE_WITH_YOUR_DOMAIN"

# Let's Encrypt / Traefik
ACME_EMAIL="admin@your-company.com"
ADMIN_PASSWORD_HASH=""

# -----------------------------------------------------------------------------
# API Keys (External Services) - Configure at least one LLM provider
# -----------------------------------------------------------------------------
AZURE_OPENAI_KEY="REPLACE_WITH_AZURE_OPENAI_KEY"
AZURE_OPENAI_BASE_URL="REPLACE_WITH_AZURE_OPENAI_BASE_URL"
GEMINI_API_KEY=""
JINA_API_KEY=""
HUGGINGFACE_API_KEY=""

# Optional providers
SWISS_LLM_CLOUD_API_BASE_URL=""
SWISS_LLM_CLOUD_API_KEY=""
COHERE_API_BASE=""
COHERE_API_KEY=""

# -----------------------------------------------------------------------------
# OAuth2 / OIDC Configuration (REQUIRED)
# -----------------------------------------------------------------------------
OAUTH_PROVIDER_NAME="Azure AD"
OAUTH_CLIENT_ID="REPLACE_WITH_YOUR_CLIENT_ID"
OAUTH_CLIENT_SECRET="REPLACE_WITH_YOUR_CLIENT_SECRET"
OAUTH_AUTHORITY_URL="https://login.microsoftonline.com/REPLACE_WITH_YOUR_TENANT_ID"
OAUTH_TENANT_ID="REPLACE_WITH_YOUR_TENANT_ID"
OAUTH_COOKIE_SECRET_DAGSTER="REPLACE_WITH_16_HEX_CHARS"
OAUTH_COOKIE_SECRET_SEAWEEDFS="REPLACE_WITH_16_HEX_CHARS"
OAUTH_COOKIE_SECRET_ATTU="REPLACE_WITH_16_HEX_CHARS"

# Azure-specific OAuth (same values as above)
AZURE_CLIENT_ID="REPLACE_WITH_YOUR_CLIENT_ID"
AZURE_TENANT_ID="REPLACE_WITH_YOUR_TENANT_ID"
AZURE_CLIENT_SECRET="REPLACE_WITH_YOUR_CLIENT_SECRET"

# OAuth Custom Branding (optional)
OAUTH_CUSTOM_SIGN_IN_LOGO=""

# -----------------------------------------------------------------------------
# Authentication & Security (REQUIRED - Generate new secrets!)
# -----------------------------------------------------------------------------
AUTH_OPEN_WEBUI_SIGNING_SECRET="REPLACE_WITH_RANDOM_STRING"

# Superuser Configuration
SUPERUSER_NAME="AI-Hub Superuser"
SUPERUSER_EMAIL="admin@your-company.com"
SUPERUSER_OID="REPLACE_WITH_RANDOM_STRING"
SUPERUSER_ROLE="AIHubSuperuser"
SUPERUSER_TOKEN="REPLACE_WITH_RANDOM_STRING"

# -----------------------------------------------------------------------------
# Database Credentials (REQUIRED - Use strong passwords!)
# -----------------------------------------------------------------------------
# PostgreSQL 
POSTGRES_USER="admin"
POSTGRES_PASSWORD="REPLACE_WITH_RANDOM_STRING"

# MongoDB (FerretDB) 
MONGO_USERNAME="admin"
MONGO_PASSWORD="REPLACE_WITH_RANDOM_STRING"

# S3 Storage (SeaweedFS) 
S3_STORAGE_ACCESS_KEY="admin"
S3_STORAGE_SECRET_KEY="REPLACE_WITH_RANDOM_STRING"
# Public endpoint for presigned URLs (auto-configured as https://s3.${DOMAIN} in docker-compose)
# S3_STORAGE_PUBLIC_ENDPOINT is set automatically - only override if using a custom S3 domain

# -----------------------------------------------------------------------------
# LiteLLM Configuration (REQUIRED)
# -----------------------------------------------------------------------------
LITELLM_UI_USERNAME="admin"
LITELLM_UI_PASSWORD="REPLACE_WITH_RANDOM_STRING"
LITELLM_MASTER_KEY="REPLACE_WITH_RANDOM_STRING"

# -----------------------------------------------------------------------------
# Service Configuration
# -----------------------------------------------------------------------------
JUPYTER_TOKEN="REPLACE_WITH_RANDOM_STRING"
# Langfuse Configuration (LLM observability and evaluation)
LANGFUSE_SALT="REPLACE_WITH_RANDOM_STRING"
LANGFUSE_NEXTAUTH_SECRET="REPLACE_WITH_RANDOM_STRING"
LANGFUSE_ENCRYPTION_KEY="REPLACE_WITH_64_HEX_CHARS"
LANGFUSE_NEXTAUTH_URL="https://langfuse.${DOMAIN}"
LANGFUSE_PUBLIC_KEY="pk-lf-REPLACE_WITH_LANGFUSE_PUBLIC_KEY"
LANGFUSE_SECRET_KEY="sk-lf-REPLACE_WITH_LANGFUSE_SECRET_KEY"
LANGFUSE_INIT_USER_EMAIL="admin@your-company.com"
LANGFUSE_INIT_USER_PASSWORD="REPLACE_WITH_RANDOM_STRING"
LANGFUSE_CLICKHOUSE_PASSWORD="REPLACE_WITH_RANDOM_STRING"

# MinerU Configuration
MINERU_API_TIMEOUT="600"
MINERU_VLM_NAME="text-generation/ocr"

# Milvus Configuration (must match your embedding model dimensions)
MILVUS_DIMENSION="3072"

# -----------------------------------------------------------------------------
# AI-Hub Application Settings
# -----------------------------------------------------------------------------
AIHUB_API_VERSION="latest"
AIHUB_CREATE_DEFAULT_ROLES="True"

# Admin Settings
ADMIN_EMAIL="admin@your-company.com"

# OAuth Group Restrictions (Azure AD group names)
OAUTH_ALLOWED_GROUPS_DAGSTER="AIHubAdmin"
OAUTH_ALLOWED_GROUPS_SEAWEEDFS="AIHubAdmin"
OAUTH_ALLOWED_GROUPS_ATTU="AIHubAdmin"

# -----------------------------------------------------------------------------
# Expert Asking Agent Configuration (Optional - for expert escalation)
# -----------------------------------------------------------------------------
# Channel type: "teams" or "slack"
EXPERT_ASKING_CHANNEL_TYPE="teams"

# Teams Configuration (required if EXPERT_ASKING_CHANNEL_TYPE="teams")
TEAMS_CHANNEL_ID="REPLACE_WITH_TEAMS_CHANNEL_ID"
TEAMS_TENANT_ID="REPLACE_WITH_TEAMS_TENANT_ID"
TEAMS_BOT_ID="REPLACE_WITH_TEAMS_BOT_ID"

# Slack Configuration (required if EXPERT_ASKING_CHANNEL_TYPE="slack")
SLACK_CHANNEL_ID=""
SLACK_SERVICE_URL="https://slack.botframework.com"

# -----------------------------------------------------------------------------
# OpenTelemetry Configuration (Optional)
# -----------------------------------------------------------------------------
OTEL_ENABLED="true"
OTEL_EXPORTER_OTLP_PROTOCOL="grpc"
OTEL_RESOURCE_SERVICE_VERSION="1.0.0"
OTEL_RESOURCE_SERVICE_NAMESPACE="swiss-ai-hub"

# Cloud OTEL (optional - for external observability platforms)
OTEL_CLOUD_ENDPOINT="placeholder:1234"
OTEL_CLOUD_HEADERS=""
```

### Konfigurationsrichtlinien

**Kritische Werte, die ersetzt werden müssen:**

1. **Domain** – Setzen Sie `DOMAIN` auf Ihre Produktionsdomain (z.B. `aihub.yourcompany.com`) oder `127.0.0.1.nip.io`
   für lokale Tests

2. **Authentifizierungswerte** (aus den Voraussetzungen):

   - `REPLACE_WITH_YOUR_CLIENT_ID` → Ihre Azure App Registration Client ID
   - `REPLACE_WITH_YOUR_CLIENT_SECRET` → Ihr Azure App Registration Client Secret
   - `REPLACE_WITH_YOUR_TENANT_ID` → Ihre Azure Tenant ID

3. **KI-Modellzugriff** (konfigurieren Sie mindestens einen):

   - `REPLACE_WITH_AZURE_OPENAI_BASE_URL` → Ihre Azure OpenAI Endpunkt-URL
   - `REPLACE_WITH_AZURE_OPENAI_KEY` → Ihr Azure OpenAI API-Schlüssel

4. **Geheimnisse** (generieren Sie für jeden einzigartige Werte):

   - Ersetzen Sie alle `REPLACE_WITH_RANDOM_STRING` durch: `openssl rand -hex 32`
   - Ersetzen Sie `REPLACE_WITH_16_HEX_CHARS` durch: `openssl rand -hex 16`

5. **Experten-Eskalation** (optional – für Expert-in-the-Loop-Funktionen):

   - `REPLACE_WITH_TEAMS_CHANNEL_ID` → Ihre Teams-Kanal-ID (Format: `19:xxx@thread.tacv2`)
   - `REPLACE_WITH_TEAMS_TENANT_ID` → Ihre Azure AD Tenant ID
   - `REPLACE_WITH_TEAMS_BOT_ID` → Ihre Azure Bot Service Anwendungs-ID

::: info Vereinfachte Konfiguration
Interne Service-Endpunkte (wie Datenbank-URLs, Nachrichten-Warteschlangen usw.) sind nun in den Docker Compose Dateien
fest codiert. Sie müssen nur Anmeldeinformationen und externe Service-Verbindungen konfigurieren.
:::

::: tip Zufällige Strings generieren
Verwenden Sie diese Befehle, um sichere, zufällige Strings zu generieren:

```bash
# For most secrets (64 characters)
openssl rand -hex 32

# For OAuth cookie secrets (32 characters each - generate separately for each service)
openssl rand -hex 16  # For OAUTH_COOKIE_SECRET_DAGSTER, OAUTH_COOKIE_SECRET_ATTU, ...
```

Führen Sie den entsprechenden Befehl für jeden Platzhalter aus.
:::

### Umgebung validieren

Vor dem Deployment überprüfen Sie Ihre Konfiguration:

```bash
# Check for placeholder values that need replacement
grep -n "REPLACE_WITH" .env
```

Dies sollte keine Ergebnisse liefern, wenn alle Platzhalter ersetzt wurden.

## Schritt 3: Plattform deployen

### Alle Services starten

Deployen Sie die komplette Plattform mit einem Befehl:

```bash
docker compose -f docker-compose.latest.yml up -d
```

Dieser Befehl wird:

- Alle notwendigen Docker Images herunterladen
- Erforderliche Netzwerke und Volumes erstellen
- Alle Plattform-Services in der richtigen Reihenfolge starten
- Service Discovery und Kommunikation konfigurieren

### Deployment-Fortschritt überwachen

Beobachten Sie den Deployment-Fortschritt:

```bash
# See all services starting
docker compose -f docker-compose.latest.yml logs -f

# Check service health status
docker compose -f docker-compose.latest.yml ps
```

**Erwartete Services:** Die Plattform umfasst diese Kern-Services:

- **Web-Interface** (aihub-web)
- **API** (aihub-api)
- **Authentifizierung** (Auth Services)
- **Datenbanken** (FerretDB, PostgreSQL, Valkey)
- **Vektor-Datenbank** (Milvus)
- **LLM-Proxy** (LiteLLM)
- **Dokumentenverarbeitung** (MinerU)
- **Observability** (Langfuse)
- **Nachrichten-Warteschlange** (NATS)
- **Speicher** (SeaweedFS)

### Auf Service-Initialisierung warten

Der anfängliche Start dauert 3-5 Minuten, während die Services initialisiert werden. Alle Services sollten den Status
"healthy" anzeigen:

```bash
# Wait for healthy status
docker compose -f docker-compose.latest.yml ps --format "table {{.Name}}\t{{.Status}}"
```

## Schritt 4: Erfolgreiches Deployment überprüfen

### Auf die Plattform zugreifen

1. **Stellen Sie sicher, dass Ihr Testbenutzer die Rolle "AIHubAdmin" in der Azure Enterprise Application zugewiesen
   bekommen hat.**

2. **Web-Interface:**

   - Lokal: `https://127.0.0.1.nip.io`
   - Produktion: `https://your-domain.com`

3. **Erwarteter Login-Workflow:**

   - Leitet zur Azure-Authentifizierung weiter
   - Nach dem Login kehrt man zur AI-Hub-Oberfläche zurück
   - Das Haupt-Dashboard sollte sichtbar sein

## Zusammenfassung: Hauptunterschiede zwischen Deployments

| Funktion                  | Produktion (`docker-compose.latest.yml`) | Lokal (`docker-compose.local.yml`) |
| :------------------------ | :--------------------------------------- | :--------------------------------- |
| **SSL-Zertifikate**       | Let's Encrypt (automatisch)              | mkcert (manuelle Generierung)      |
| **Domain**                | Ihre Produktionsdomain                   | `127.0.0.1.nip.io`                 |
| **Konfigurationsdateien** | `*.latest.*` configs                     | `*.local.*` configs                |
| **Zweck**                 | Produktions-Deployments                  | Lokales Deployment und Entwicklung |

::: warning
Verwenden Sie niemals selbstsignierte SSL-Zertifikate in der Produktion. Die lokale Deployment-Konfiguration ist
ausschließlich für die Entwicklung und Tests auf Ihrer lokalen Maschine konzipiert.
:::
