---
title: Deployment mit einem Befehl
source_sha: 87723bd9334813821bc5e71cf1a1d19542f88507095369395762d1bda81d88fd
---

# Deployment mit einem Befehl: Starten Sie Ihre KI-Plattform

Die Swiss AI Hub Plattform wird mit einem einzigen Docker Compose Befehl deployed. Dieser optimierte Prozess bringt Ihre
komplette KI-Infrastruktur in Minuten, nicht Stunden, zum Laufen.

## Deployment-Übersicht

::: tip Zwei Deployment-Optionen
Der Swiss AI Hub unterstützt zwei Deployment-Modi. Befolgen Sie die gleichen Schritte für beide, indem Sie die
entsprechenden Befehle für Ihren Deployment-Typ verwenden:

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

---

## Schritt 1: Deployment-Dateien abrufen

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

**Für das lokale Deployment:**

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
Wildcard-DNS-Auflösung, ohne dass Sie Ihre Hosts-Datei ändern müssen. Dies ermöglicht subdomainbasiertes Routing in der
lokalen Entwicklung.
:::

---

## Schritt 2: Umgebungsvariablen konfigurieren

### Umgebungskonfiguration erstellen

Erstellen Sie eine `.env`-Datei mit Ihren Konfigurationseinstellungen:

```bash
touch .env
```

### Essenzielle Konfigurationsvorlage

Kopieren Sie diese Vorlage in Ihre `.env`-Datei und ersetzen Sie die Platzhalterwerte:

```env
# =============================================================================
# BASIC PLATFORM CONFIGURATION
# =============================================================================

LOG_LEVEL="WARNING"                    # Options: CRITICAL, ERROR, WARNING, INFO, DEBUG
ENV="prod"                             # Options: dev, test, prod
DOMAIN="REPLACE_WITH_YOUR_DOMAIN"

# Traefik Configuration
ACME_EMAIL="admin@your-company.com"
ADMIN_PASSWORD_HASH=""                 # Generate with: htpasswd -nb admin yourpassword

# =============================================================================
# AUTHENTICATION CONFIGURATION
# =============================================================================

# General Authentication Settings
AUTH_ENABLE_API_ACCESS="True"
AUTH_OPEN_WEBUI_SIGNING_SECRET="REPLACE_WITH_RANDOM_STRING"
AUTH_IDENTITY_PROVIDER="azure"

# OAuth2 Configuration (from Prerequisites setup)
OAUTH_CLIENT_ID="REPLACE_WITH_YOUR_CLIENT_ID"
OAUTH_CLIENT_SECRET="REPLACE_WITH_YOUR_CLIENT_SECRET"
OAUTH_AUTHORITY_URL="https://login.microsoftonline.com/REPLACE_WITH_YOUR_TENANT_ID"
OAUTH_PROVIDER_NAME="azure"
OAUTH_TENANT_ID="REPLACE_WITH_YOUR_TENANT_ID"
OAUTH_COOKIE_SECRET_DAGSTER="REPLACE_WITH_16_HEX_CHARS"
OAUTH_COOKIE_SECRET_SEAWEEDFS="REPLACE_WITH_16_HEX_CHARS"
OAUTH_COOKIE_SECRET_ATTU="REPLACE_WITH_16_HEX_CHARS"

# =============================================================================
# PLATFORM ACCESS CONFIGURATION
# =============================================================================

# Superuser Configuration
SUPERUSER_ENABLED="True"
SUPERUSER_NAME="AI-Hub Superuser"
SUPERUSER_EMAIL="admin@your-company.com"
SUPERUSER_OID="REPLACE_WITH_RANDOM_STRING"
SUPERUSER_ROLE="AIHubSuperuser"
SUPERUSER_TOKEN="REPLACE_WITH_RANDOM_STRING"

# Platform Settings
AIHUB_API_VERSION="dev"
AIHUB_FRONTEND_ORIGIN="https://REPLACE_WITH_YOUR_DOMAIN"
AIHUB_CREATE_DEFAULT_ROLES="True"

# =============================================================================
# AI MODEL ACCESS (Configure at least one)
# =============================================================================

# Azure OpenAI (Recommended)
AZURE_OPENAI_BASE_URL="REPLACE_WITH_AZURE_OPENAI_BASE_URL"
AZURE_OPENAI_KEY="REPLACE_WITH_AZURE_OPENAI_KEY"

# Google Gemini (Alternative)
GEMINI_API_KEY="REPLACE_WITH_GEMINI_KEY"

# Swiss LLM Cloud (Optional)
SWISS_LLM_CLOUD_API_BASE_URL=""                # Optional: Swiss LLM Cloud endpoint URL
SWISS_LLM_CLOUD_API_KEY=""                # Optional: Swiss LLM Cloud API key

# Cohere (Optional)
COHERE_API_BASE=""                        # Optional: Cohere API base URL
COHERE_API_KEY=""                         # Optional: Cohere API key

# Hugging Face (Optional)
HUGGINGFACE_API_KEY=""                    # Optional: For Hugging Face model access

# =============================================================================
# LITELLM PROXY CONFIGURATION
# =============================================================================

LITELLM_UI_USERNAME="admin"
LITELLM_UI_PASSWORD="REPLACE_WITH_RANDOM_STRING"
LITELLM_MASTER_KEY="REPLACE_WITH_RANDOM_STRING"
LITE_LLM_PROXY_BASE_URL="http://litellm:4000"
LITE_LLM_PROXY_API_KEY="REPLACE_WITH_RANDOM_STRING"

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# PostgreSQL
POSTGRES_USER="admin"
POSTGRES_PASSWORD="REPLACE_WITH_RANDOM_STRING"

# FerretDB (MongoDB-compatible)
MONGO_USERNAME="admin"
MONGO_PASSWORD="REPLACE_WITH_RANDOM_STRING"
MONGO_CONNECTION_STRING="mongodb://admin:REPLACE_WITH_SAME_MONGO_PASSWORD@ferretdb:27017/"

# Valkey (Redis-compatible)
REDIS_URL="redis://localhost:6379"

# =============================================================================
# STORAGE CONFIGURATION
# =============================================================================

# SeaweedFS S3 Storage
SEAWEEDFS_ROOT_USER="admin"
SEAWEEDFS_ROOT_PASSWORD="REPLACE_WITH_RANDOM_STRING"
S3_STORAGE_ENDPOINT="http://seaweedfs:8333"
S3_STORAGE_ACCESS_KEY="admin"                         # Must match SEAWEEDFS_ROOT_USER
S3_STORAGE_SECRET_KEY="REPLACE_WITH_SAME_SEAWEEDFS_PASSWORD"
S3_STORAGE_URL_SIGNING_SECRET="REPLACE_WITH_RANDOM_STRING"

# =============================================================================
# SERVICE ENDPOINTS (Internal - Don't Change)
# =============================================================================

DOCLING_API_BASE_URL="http://docling:5001"
DOCLING_API_TIMEOUT="600"
DOCLING_HTTP_RETRIES=3
PHOENIX_SECRET="REPLACE_WITH_RANDOM_STRING"
PHOENIX_ENDPOINT="http://phoenix:6006"
NATS_ENDPOINT="nats://localhost:4222"
DAGSTER_HOME="~/.dagster_home"
OAUTH_ALLOWED_GROUPS_DAGSTER="AIHubDeveloper"
OAUTH_ALLOWED_GROUPS_SEAWEEDFS="AIHubDeveloper"
JUPYTER_TOKEN="REPLACE_WITH_RANDOM_STRING"
MILVUS_DIMENSION="3072"

# =============================================================================
# OBSERVABILITY CONFIGURATION
# =============================================================================

# OpenTelemetry Cloud Exporter (Optional - for production monitoring)
OTEL_ENABLED="true"                           # Enable/disable OTEL collection
OTEL_EXPORTER_OTLP_PROTOCOL="grpc"           # Protocol for OTEL export
OTEL_CLOUD_ENDPOINT="localhost:4317"         # Cloud OTEL endpoint (e.g., Grafana Cloud: "otlp.grafana.net:443")
OTEL_CLOUD_HEADERS=""                         # Authentication headers (e.g., "Authorization=Bearer YOUR_TOKEN")

# =============================================================================
# BOT DEVELOPMENT CONFIGURATION
# =============================================================================

BOT_AUTH_FAKE_NAME="Bot"
BOT_AUTH_FAKE_EMAIL="bot@bot.com"
BOT_AUTH_FAKE_OID="00000000-0000-0000-0000-000000000000"
BOT_AUTH_FAKE_ROLES="AIHubBot"

# =============================================================================
# OPTIONAL INTEGRATIONS
# =============================================================================

# Jina AI Search (Optional)
JINA_API_KEY=""

# OpenTelemetry Configuration (Optional)
OTEL_ENABLED="False"
OTEL_EXPORTER_OTLP_PROTOCOL="grpc"
OTEL_CLOUD_ENDPOINT=""
OTEL_CLOUD_HEADERS=""

# Signoz Telemetry (Optional)
SIGNOZ_INGESTION_CLOUD_ENDPOINT=""
SIGNOZ_INGESTION_KEY=""

```

### Konfigurationsrichtlinien

**Kritische Werte zum Ersetzen:**

1. **Authentifizierungswerte** (aus den Voraussetzungen):

   - `REPLACE_WITH_YOUR_CLIENT_ID` → Ihre Azure App Registration Client ID
   - `REPLACE_WITH_YOUR_CLIENT_SECRET` → Ihr Azure App Registration Client Secret
   - `REPLACE_WITH_YOUR_TENANT_ID` → Ihre Azure Tenant ID (erscheint zweimal)

2. **KI-Modellzugriff** (mindestens einen konfigurieren):

   - `REPLACE_WITH_AZURE_OPENAI_BASE_URL` → Ihre Azure OpenAI Endpunkt-URL
   - `REPLACE_WITH_AZURE_OPENAI_KEY` → Ihr Azure OpenAI API-Schlüssel
   - `REPLACE_WITH_GEMINI_KEY` → Ihr Google Gemini API-Schlüssel

3. **Zufällige Zeichenketten** (eindeutige Werte generieren):

   - Ersetzen Sie alle `REPLACE_WITH_RANDOM_STRING` durch eindeutige zufällige Zeichenketten (verwenden Sie
     `openssl rand -hex 32`)
   - Ersetzen Sie `REPLACE_WITH_16_HEX_CHARS` durch eine 16-Byte-Hex-Zeichenkette (verwenden Sie `openssl rand -hex 16`)
   - Verwenden Sie unterschiedliche Werte für jeden Platzhalter
   - Mindestens 32 Zeichen werden für die Sicherheit empfohlen

**Domain-Konfiguration:**

- Für lokale Tests: Behalten Sie `AIHUB_FRONTEND_ORIGIN="https://127.0.0.1.nip.io"` bei
- Für die Produktion: Ändern Sie dies zu Ihrer tatsächlichen Domain (z.B. `https://aihub.your-company.com`)

::: tip Zufällige Zeichenketten generieren
Verwenden Sie diese Befehle, um sichere zufällige Zeichenketten zu generieren:

```bash
# For most secrets (64 characters)
openssl rand -hex 32

# For OAuth cookie secrets (32 characters each - generate separately for each service)
openssl rand -hex 16  # For OAUTH_COOKIE_SECRET_DAGSTER
openssl rand -hex 16  # For OAUTH_COOKIE_SECRET_SEAWEEDFS
openssl rand -hex 16  # For OAUTH_COOKIE_SECRET_ATTU
```

Führen Sie den entsprechenden Befehl für jeden Platzhalter aus.
:::

### Umgebungsvalidierung

Vor dem Deployment überprüfen Sie Ihre Konfiguration:

```bash
# Check for placeholder values that need replacement
grep -n "REPLACE_WITH" .env
```

Dies sollte keine Ergebnisse liefern, wenn alle Platzhalter ersetzt wurden.

## Schritt 3: Die Plattform deployen

### Alle Services starten

Deployen Sie die komplette Plattform mit einem Befehl:

```bash
docker compose -f docker-compose.latest.yml up -d
```

Dieser Befehl wird:

- Alle notwendigen Docker-Images herunterladen
- Erforderliche Netzwerke und Volumes erstellen
- Alle Plattform-Services in der richtigen Reihenfolge starten
- Service-Discovery und Kommunikation konfigurieren

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
- **Authentifizierung** (auth services)
- **Datenbanken** (FerretDB, PostgreSQL, Valkey)
- **Vektor-Datenbank** (Milvus)
- **LLM-Proxy** (LiteLLM)
- **Dokumentenverarbeitung** (Docling)
- **Observability** (Phoenix)
- **Message Queue** (NATS)
- **Speicher** (SeaweedFS)

### Warten auf Service-Initialisierung

Der erste Start dauert 3-5 Minuten, während sich die Services initialisieren. Alle Services sollten den Status "healthy"
anzeigen:

```bash
# Wait for healthy status
docker compose -f docker-compose.latest.yml ps --format "table {{.Name}}\t{{.Status}}"
```

## Schritt 4: Erfolgreiches Deployment überprüfen

### Auf die Plattform zugreifen

1. **Stellen Sie sicher, dass Ihrem Benutzer, mit dem Sie testen, die Rolle "AIHubAdmin" in der Azure Enterprise
   Application zugewiesen ist**

2. **Web-Interface:**

   - Lokal: `https://127.0.0.1.nip.io`
   - Produktion: `https://your-domain.com`

3. **Erwarteter Login-Flow:**

   - Leitet zur Azure-Authentifizierung weiter
   - Nach dem Login kehrt die Oberfläche zum AI-Hub zurück
   - Das Haupt-Dashboard sollte sichtbar sein

## Zusammenfassung: Wichtige Unterschiede zwischen Deployments

| Merkmal                   | Produktion (`docker-compose.latest.yml`) | Lokal (`docker-compose.local.yml`) |
| :------------------------ | :--------------------------------------- | :--------------------------------- |
| **SSL-Zertifikate**       | Let's Encrypt (automatisch)              | mkcert (manuelle Generierung)      |
| **Domain**                | Ihre Produktions-Domain                  | `127.0.0.1.nip.io`                 |
| **Konfigurationsdateien** | `*.latest.*` configs                     | `*.local.*` configs                |
| **Zweck**                 | Produktions-Deployments                  | Lokales Deployment und Entwicklung |

::: warning
Verwenden Sie niemals selbstsignierte SSL-Zertifikate in der Produktion. Die Konfiguration für das lokale Deployment ist
ausschließlich für die Entwicklung und Tests auf Ihrer lokalen Maschine konzipiert.
:::
