---
title: Ein-Befehl-Deployment
source_sha: b4681a3f51fb8fe8247664caec106a917fff27fc34f096a833d9364300a3fbed
---

# Ein-Befehl-Deployment: Starten Sie Ihre KI-Plattform

Die Swiss AI Hub Plattform wird mit einem einzigen Docker Compose Befehl deployt. Dieser optimierte Prozess bringt Ihre
gesamte KI-Infrastruktur in Minuten, nicht Stunden, zum Laufen.

## Deployment-Übersicht

::: tip Zwei Deployment-Optionen
Der Swiss AI Hub unterstützt zwei Deployment-Modi. Befolgen Sie für beide die gleichen Schritte und verwenden Sie die
entsprechenden Befehle für Ihren Deployment-Typ:

- **Produktions-Deployment**: Deployment auf einem Server mit einem realen Domainnamen (z.B. `aihub.yourcompany.com`)

  - Verwendet `docker-compose.latest.yml`
  - Verwendet Let's Encrypt für automatische SSL-Zertifikate
  - Erfordert eine DNS-Konfiguration, die auf Ihren Server verweist

- **Lokales Deployment**: Ausführung auf Ihrem lokalen Rechner für Entwicklung/Tests

  - Verwendet `docker-compose.local.yml`
  - Verwendet selbstsignierte SSL-Zertifikate (mkcert)
  - Verwendet die Domain `127.0.0.1.nip.io` (löst automatisch zu localhost auf)

Jeder untenstehende Schritt zeigt Befehle für beide Deployment-Typen. Folgen Sie einfach den Befehlen, die Ihrem
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
Die Domain `*.127.0.0.1.nip.io` löst sich automatisch auf Ihr Localhost (127.0.0.1) auf und bietet eine
Wildcard-DNS-Auflösung, ohne dass Sie Ihre Hosts-Datei ändern müssen. Dies ermöglicht Subdomain-basiertes Routing in der
lokalen Entwicklung.
:::

---

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
AUTH_IDENTITY_PROVIDER="azure"
OAUTH_PROVIDER_NAME="Azure AD"
OAUTH_CLIENT_ID="REPLACE_WITH_YOUR_CLIENT_ID"
OAUTH_CLIENT_SECRET="REPLACE_WITH_YOUR_CLIENT_SECRET"
OAUTH_AUTHORITY_URL="https://login.microsoftonline.com/REPLACE_WITH_YOUR_TENANT_ID"
OAUTH_TENANT_ID="REPLACE_WITH_YOUR_TENANT_ID"
OAUTH_COOKIE_SECRET="REPLACE_WITH_16_HEX_CHARS"

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
SUPERUSER_ENABLED="True"
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
PHOENIX_SECRET="REPLACE_WITH_RANDOM_STRING"

# Docling Configuration
DOCLING_API_TIMEOUT="600"
DOCLING_VLM_MODEL_NAME="text-generation/ocr"
DOCLING_HTTP_RETRIES=3

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
DAGSTER_OAUTH_ALLOWED_GROUPS="AIHubAdmin"
SEAWEEDFS_OAUTH_ALLOWED_GROUPS="AIHubAdmin"

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
   für lokale Tests.

2. **Authentifizierungswerte** (aus den Voraussetzungen):

   - `REPLACE_WITH_YOUR_CLIENT_ID` → Ihre Azure App Registration Client ID
   - `REPLACE_WITH_YOUR_CLIENT_SECRET` → Ihr Azure App Registration Client Secret
   - `REPLACE_WITH_YOUR_TENANT_ID` → Ihre Azure Tenant ID

3. **KI-Modellzugriff** (konfigurieren Sie mindestens einen):

   - `REPLACE_WITH_AZURE_OPENAI_BASE_URL` → Ihre Azure OpenAI Endpunkt-URL
   - `REPLACE_WITH_AZURE_OPENAI_KEY` → Ihr Azure OpenAI API-Schlüssel

4. **Geheimnisse** (generieren Sie für jedes eindeutige Werte):

   - Ersetzen Sie alle `REPLACE_WITH_RANDOM_STRING` durch: `openssl rand -hex 32`
   - Ersetzen Sie `REPLACE_WITH_16_HEX_CHARS` durch: `openssl rand -hex 16`

5. **Experten-Eskalation** (optional – für Expert-in-the-Loop-Funktionen):

   - `REPLACE_WITH_TEAMS_CHANNEL_ID` → Ihre Teams Kanal-ID (Format: `19:xxx@thread.tacv2`)
   - `REPLACE_WITH_TEAMS_TENANT_ID` → Ihre Azure AD Tenant ID
   - `REPLACE_WITH_TEAMS_BOT_ID` → Ihre Azure Bot Service Anwendungs-ID

::: info Vereinfachte Konfiguration
Interne Service-Endpunkte (wie Datenbank-URLs, Nachrichtenwarteschlangen usw.) sind jetzt in den Docker Compose Dateien
fest codiert. Sie müssen nur noch Anmeldeinformationen und externe Service-Verbindungen konfigurieren.
:::

::: tip Zufällige Zeichenketten generieren
Verwenden Sie diese Befehle, um sichere Zufallszeichenketten zu generieren:

```bash
# Für die meisten Geheimnisse (64 Zeichen)
openssl rand -hex 32

# Für OAUTH_COOKIE_SECRET (32 Zeichen)
openssl rand -hex 16
```

Führen Sie den entsprechenden Befehl für jeden Platzhalter aus.
:::

### Umgebungsvalidierung

Vor dem Deployment überprüfen Sie Ihre Konfiguration:

```bash
# Auf Platzhalterwerte prüfen, die ersetzt werden müssen
grep -n "REPLACE_WITH" .env
```

Dies sollte keine Ergebnisse liefern, wenn alle Platzhalter ersetzt wurden.

## Schritt 3: Die Plattform deployen

### Alle Services starten

Deployen Sie die gesamte Plattform mit einem Befehl:

```bash
docker compose -f docker-compose.latest.yml up -d
```

Dieser Befehl wird:

- Alle notwendigen Docker-Images herunterladen
- Erforderliche Netzwerke und Volumes erstellen
- Alle Plattform-Services in der richtigen Reihenfolge starten
- Service Discovery und Kommunikation konfigurieren

### Deployment-Fortschritt überwachen

Beobachten Sie den Deployment-Fortschritt:

```bash
# Alle startenden Services anzeigen
docker compose -f docker-compose.latest.yml logs -f

# Service-Gesundheitsstatus prüfen
docker compose -f docker-compose.latest.yml ps
```

**Erwartete Services:** Die Plattform umfasst diese Kern-Services:

- **Web-Oberfläche** (aihub-web)
- **API** (aihub-api)
- **Authentifizierung** (Auth Services)
- **Datenbanken** (FerretDB, PostgreSQL, Valkey)
- **Vektordatenbank** (Milvus)
- **LLM-Proxy** (LiteLLM)
- **Dokumentenverarbeitung** (Docling)
- **Observability** (Phoenix)
- **Nachrichtenwarteschlange** (NATS)
- **Speicher** (SeaweedFS)

### Auf Service-Initialisierung warten

Der initiale Start dauert 3-5 Minuten, während sich die Services initialisieren. Alle Services sollten den Status
"healthy" anzeigen:

```bash
# Auf gesunden Status warten
docker compose -f docker-compose.latest.yml ps --format "table {{.Name}}\t{{.Status}}"
```

## Schritt 4: Erfolgreiches Deployment überprüfen

### Auf die Plattform zugreifen

1. **Stellen Sie sicher, dass Ihrem Benutzer, mit dem Sie testen, die Rolle "AIHubAdmin" in der Azure Enterprise
   Application zugewiesen ist.**

2. **Web-Oberfläche:**

   - Lokal: `https://127.0.0.1.nip.io`
   - Produktion: `https://your-domain.com`

3. **Erwarteter Anmeldeablauf:**

   - Leitet zur Azure-Authentifizierung weiter
   - Nach der Anmeldung kehrt die Oberfläche zum AI-Hub zurück
   - Das Haupt-Dashboard sollte sichtbar sein

## Zusammenfassung: Hauptunterschiede zwischen den Deployments

| Funktion                  | Produktion (`docker-compose.latest.yml`) | Lokal (`docker-compose.local.yml`) |
| :------------------------ | :--------------------------------------- | :--------------------------------- |
| **SSL-Zertifikate**       | Let's Encrypt (automatisch)              | mkcert (manuelle Generierung)      |
| **Domain**                | Ihre Produktionsdomain                   | `127.0.0.1.nip.io`                 |
| **Konfigurationsdateien** | `*.latest.*` Konfigurationen             | `*.local.*` Konfigurationen        |
| **Zweck**                 | Produktions-Deployments                  | Lokales Deployment und Entwicklung |

::: warning
Verwenden Sie niemals selbstsignierte SSL-Zertifikate in der Produktion. Die Konfiguration für das lokale Deployment ist
ausschließlich für die Entwicklung und Tests auf Ihrem lokalen Rechner vorgesehen.
:::
