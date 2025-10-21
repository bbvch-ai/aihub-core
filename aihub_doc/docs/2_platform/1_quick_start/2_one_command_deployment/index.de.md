---
title: Ein-Befehl-Bereitstellung
index: 2
source_sha: "b61d35fce1d5060c375b3a65f321a6d6b15fd3ab2f784e2516a678c23754b056"
---

# Ein-Befehl-Bereitstellung: Starten Sie Ihre KI-Plattform

Die Swiss AI Hub-Plattform wird mit einem einzigen Docker Compose-Befehl bereitgestellt. Dieser optimierte Prozess bringt Ihre gesamte KI-Infrastruktur in wenigen Minuten, nicht Stunden, zum Laufen.

## Bereitstellungsübersicht

Die Bereitstellung besteht aus drei einfachen Schritten:

1.  **Herunterladen** der Bereitstellungskonfiguration
2.  **Konfigurieren** der Umgebungsvariablen mit Ihren Einstellungen
3.  **Bereitstellen** mit einem Befehl

Die gesamte Plattform läuft als containerisierte Services, die Service Discovery, Netzwerk und Start-Orchestrierung automatisch handhaben.

## Schritt 1: Bereitstellungsdateien herunterladen

### Docker Compose Konfiguration erhalten

Laden Sie die neueste Bereitstellungskonfiguration herunter:

```bash
# Create deployment directory
mkdir swiss-ai-hub-deployment
cd swiss-ai-hub-deployment

# Download the latest deployment configuration
curl -O https://raw.githubusercontent.com/bbvch-ai/aihub-core/main/docker-compose.latest.yml
```

Alternativ navigieren Sie zum [aihub-core Repository](https://github.com/bbvch-ai/aihub-core) und laden die Datei `docker-compose.latest.yml` manuell herunter.

### Download überprüfen

Überprüfen Sie, ob Sie die Bereitstellungsdatei haben:

```bash
ls -la docker-compose.latest.yml
```

Sie sollten die Compose-Datei in Ihrem Bereitstellungsverzeichnis sehen.

## Schritt 2: Umgebungsvariablen konfigurieren

### Umgebungskonfiguration erstellen

Erstellen Sie eine `.env`-Datei mit Ihren Konfigurationseinstellungen:

```bash
touch .env
```

### Vorlage für die essentielle Konfiguration

Kopieren Sie diese Vorlage in Ihre `.env`-Datei und ersetzen Sie die Platzhalterwerte:

```env
# =============================================================================
# BASIC PLATFORM CONFIGURATION
# =============================================================================

LOG_LEVEL="WARNING"                    # Options: CRITICAL, ERROR, WARNING, INFO, DEBUG
ENV="prod"                            # Options: dev, test, prod

# =============================================================================
# AUTHENTICATION CONFIGURATION  
# =============================================================================

# General Authentication Settings
AUTH_ENABLE_API_ACCESS="True"
AUTH_OPEN_WEBUI_SIGNING_SECRET="REPLACE_WITH_RANDOM_STRING_1"
AUTH_IDENTITY_PROVIDER="azure"

# OAuth2 Configuration (from Prerequisites setup)
OAUTH_CLIENT_ID="REPLACE_WITH_YOUR_CLIENT_ID"
OAUTH_CLIENT_SECRET="REPLACE_WITH_YOUR_CLIENT_SECRET"  
OAUTH_AUTHORITY_URL="https://login.microsoftonline.com/REPLACE_WITH_YOUR_TENANT_ID"
OAUTH_PROVIDER_NAME="azure"
OAUTH_TENANT_ID="REPLACE_WITH_YOUR_TENANT_ID"
OAUTH_COOKIE_SECRET="REPLACE_WITH_RANDOM_STRING_2"

# =============================================================================
# PLATFORM ACCESS CONFIGURATION
# =============================================================================

# Superuser Configuration
SUPERUSER_ENABLED="True"
SUPERUSER_NAME="AI-Hub Administrator"
SUPERUSER_EMAIL="admin@your-company.com"              # Replace with admin email
SUPERUSER_OID="REPLACE_WITH_RANDOM_STRING_3"
SUPERUSER_ROLE="AIHubSuperuser"
SUPERUSER_TOKEN="REPLACE_WITH_RANDOM_STRING_4"

# Platform Settings
AIHUB_API_VERSION="dev"
AIHUB_FRONTEND_ORIGIN="https://127.0.0.1.nip.io"     # Change for production domain
AIHUB_CREATE_DEFAULT_ROLES="True"

# =============================================================================
# AI MODEL ACCESS (Configure at least one)
# =============================================================================

# Azure OpenAI (Recommended)
AZURE_OPENAI_KEY="REPLACE_WITH_AZURE_OPENAI_KEY"
AZURE_OPENAI_KEY_IMAGE="REPLACE_WITH_AZURE_OPENAI_KEY"
AZURE_OPENAI_KEY_AUDIO="REPLACE_WITH_AZURE_OPENAI_KEY"

# Google Gemini (Alternative)
GEMINI_API_KEY="REPLACE_WITH_GEMINI_KEY"

# =============================================================================
# LITELLM PROXY CONFIGURATION
# =============================================================================

LITELLM_UI_USERNAME="admin"
LITELLM_UI_PASSWORD="REPLACE_WITH_RANDOM_STRING_5"
LITELLM_MASTER_KEY="REPLACE_WITH_RANDOM_STRING_6"
LITE_LLM_PROXY_BASE_URL="http://litellm:4000"
LITE_LLM_PROXY_API_KEY="REPLACE_WITH_RANDOM_STRING_7"

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# PostgreSQL
POSTGRES_USER="admin"
POSTGRES_PASSWORD="REPLACE_WITH_RANDOM_STRING_8"

# MongoDB  
MONGO_USERNAME="admin"
MONGO_PASSWORD="REPLACE_WITH_RANDOM_STRING_9"
MONGO_CONNECTION_STRING="mongodb://admin:REPLACE_WITH_SAME_MONGO_PASSWORD@mongo:27017/"

# Redis (uses defaults)
REDIS_URL="redis://localhost:6379"

# =============================================================================
# STORAGE CONFIGURATION
# =============================================================================

# MinIO S3 Storage
MINIO_ROOT_USER="admin"
MINIO_ROOT_PASSWORD="REPLACE_WITH_RANDOM_STRING_10"
S3_STORAGE_ENDPOINT="http://minio:9000"
S3_STORAGE_ACCESS_KEY="admin"                         # Must match MINIO_ROOT_USER
S3_STORAGE_SECRET_KEY="REPLACE_WITH_SAME_MINIO_PASSWORD"

# =============================================================================
# SERVICE ENDPOINTS (Internal - Don't Change)
# =============================================================================

DOCLING_API_ENDPOINT="http://docling:5001"
DOCLING_API_TIMEOUT="600"
PHOENIX_SECRET="REPLACE_WITH_RANDOM_STRING_11"
PHOENIX_ENDPOINT="http://phoenix:6006"
NATS_ENDPOINT="nats://localhost:4222"
DAGSTER_HOME="~/.dagster_home"
JUPYTER_TOKEN="REPLACE_WITH_RANDOM_STRING_12"
MILVUS_URL="http://localhost"
MILVUS_DIMENSION="3072"

# =============================================================================
# OPTIONAL INTEGRATIONS
# =============================================================================

# Jina AI Search (Optional)
# JINA_API_KEY="your_jina_api_key"
```

### Konfigurationsrichtlinien

**Wichtige Werte, die ersetzt werden müssen:**

1.  **Authentifizierungswerte** (aus den Voraussetzungen):
    -   `REPLACE_WITH_YOUR_CLIENT_ID` → Ihre Azure App Registration Client ID
    -   `REPLACE_WITH_YOUR_CLIENT_SECRET` → Ihr Azure App Registration Client Secret
    -   `REPLACE_WITH_YOUR_TENANT_ID` → Ihre Azure Tenant ID (erscheint zweimal)
2.  **Zugriff auf KI-Modelle** (mindestens einen konfigurieren):
    -   `REPLACE_WITH_AZURE_OPENAI_KEY` → Ihr Azure OpenAI API-Schlüssel
    -   `REPLACE_WITH_GEMINI_KEY` → Ihr Google Gemini API-Schlüssel
3.  **Zufällige Zeichenfolgen** (generieren Sie eindeutige Werte):
    -   Ersetzen Sie alle `REPLACE_WITH_RANDOM_STRING_X` durch eindeutige zufällige Zeichenfolgen
    -   Verwenden Sie unterschiedliche Werte für jeden Platzhalter
    -   Mindestens 32 Zeichen werden aus Sicherheitsgründen empfohlen

**Domain-Konfiguration:**

-   Für lokale Tests: Behalten Sie `AIHUB_FRONTEND_ORIGIN="https://127.0.0.1.nip.io"` bei
-   Für die Produktion: Ändern Sie dies auf Ihre tatsächliche Domain (z.B. `https://ai-hub.your-company.com`)

::: tip Zufällige Zeichenfolgen generieren
Verwenden Sie diesen Befehl, um sichere zufällige Zeichenfolgen zu generieren:

```bash
openssl rand -hex 32
```

Führen Sie ihn mehrmals aus, um unterschiedliche Werte für jeden Platzhalter zu erhalten.
:::

### Umgebungsvalidierung

Vor der Bereitstellung überprüfen Sie Ihre Konfiguration:

```bash
# Check for placeholder values that need replacement
grep -n "REPLACE_WITH" .env
```

Dies sollte keine Ergebnisse liefern, wenn alle Platzhalter ersetzt wurden.

## Schritt 3: Die Plattform bereitstellen

### Alle Services starten

Stellen Sie die gesamte Plattform mit einem einzigen Befehl bereit:

```bash
docker compose -f docker-compose.latest.yml up -d
```

Dieser Befehl wird:

-   Alle notwendigen Docker-Images herunterladen
-   Erforderliche Netzwerke und Volumes erstellen
-   Alle Plattform-Services in der richtigen Reihenfolge starten
-   Service Discovery und Kommunikation konfigurieren

### Bereitstellungsfortschritt überwachen

Beobachten Sie den Bereitstellungsfortschritt:

```bash
# See all services starting
docker compose -f docker-compose.latest.yml logs -f

# Check service health status
docker compose -f docker-compose.latest.yml ps
```

**Erwartete Services:** Die Plattform umfasst diese Kern-Services:

-   **Web-Interface** (aihub-web)
-   **API** (aihub-api)
-   **Authentifizierung** (Auth-Services)
-   **Datenbanken** (MongoDB, PostgreSQL, Redis)
-   **Vektordatenbank** (Milvus)
-   **LLM-Proxy** (LiteLLM)
-   **Dokumentenverarbeitung** (Docling)
-   **Observability** (Phoenix)
-   **Nachrichtenwarteschlange** (NATS)
-   **Speicher** (MinIO)

### Warten auf die Service-Initialisierung

Der initiale Start dauert 3-5 Minuten, während die Services initialisiert werden. Alle Services sollten den Status „healthy“ anzeigen:

```bash
# Wait for healthy status
docker compose -f docker-compose.latest.yml ps --format "table {{.Name}}\t{{.Status}}"
```

## Schritt 4: Erfolgreiche Bereitstellung überprüfen

### Auf die Plattform zugreifen

1.  **Stellen Sie sicher, dass Ihrem Testbenutzer die Rolle „AIHubAdmin“ in der Azure Enterprise Application zugewiesen ist.**

2.  **Web-Interface:**
    -   Lokal: `https://127.0.0.1.nip.io`
    -   Produktion: `https://your-domain.com`

3.  **Erwarteter Login-Ablauf:**
    -   Leitet zur Azure-Authentifizierung weiter
    -   Nach dem Login kehrt die Oberfläche zum AI-Hub zurück
    -   Das Haupt-Dashboard sollte sichtbar sein
