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
# AI-Hub Produktions-Umgebungskonfiguration
# =============================================================================
# Diese Datei enthält NUR die Umgebungsvariablen, die konfiguriert werden müssen.
# Alle internen Docker-Netzwerk-Endpunkte sind in den Compose-Dateien hartcodiert.
# =============================================================================

# -----------------------------------------------------------------------------
# Allgemeine Einstellungen
# -----------------------------------------------------------------------------
LOG_LEVEL="INFO"
ENV="prod"
DOMAIN="REPLACE_WITH_YOUR_DOMAIN"

# Let's Encrypt / Traefik
ACME_EMAIL="admin@your-company.com"
ADMIN_PASSWORD_HASH=""

# -----------------------------------------------------------------------------
# API-Schlüssel (Externe Dienste) - Mindestens einen LLM-Anbieter konfigurieren
# -----------------------------------------------------------------------------
AZURE_OPENAI_KEY="REPLACE_WITH_AZURE_OPENAI_KEY"
AZURE_OPENAI_BASE_URL="REPLACE_WITH_AZURE_OPENAI_BASE_URL"
GEMINI_API_KEY=""
JINA_API_KEY=""
HUGGINGFACE_API_KEY=""

# Optionale Anbieter
SWISS_LLM_CLOUD_API_BASE_URL=""
SWISS_LLM_CLOUD_API_KEY=""
COHERE_API_BASE=""
COHERE_API_KEY=""

# -----------------------------------------------------------------------------
# OAuth2 / OIDC Konfiguration (ERFORDERLICH)
# -----------------------------------------------------------------------------
AUTH_IDENTITY_PROVIDER="azure"
OAUTH_PROVIDER_NAME="Azure AD"
OAUTH_CLIENT_ID="REPLACE_WITH_YOUR_CLIENT_ID"
OAUTH_CLIENT_SECRET="REPLACE_WITH_YOUR_CLIENT_SECRET"
OAUTH_AUTHORITY_URL="https://login.microsoftonline.com/REPLACE_WITH_YOUR_TENANT_ID"
OAUTH_TENANT_ID="REPLACE_WITH_YOUR_TENANT_ID"
OAUTH_COOKIE_SECRET_DAGSTER="REPLACE_WITH_16_HEX_CHARS"
OAUTH_COOKIE_SECRET_SEAWEEDFS="REPLACE_WITH_16_HEX_CHARS"
OAUTH_COOKIE_SECRET_ATTU="REPLACE_WITH_16_HEX_CHARS"

# Azure-spezifische OAuth (gleiche Werte wie oben)
AZURE_CLIENT_ID="REPLACE_WITH_YOUR_CLIENT_ID"
AZURE_TENANT_ID="REPLACE_WITH_YOUR_TENANT_ID"
AZURE_CLIENT_SECRET="REPLACE_WITH_YOUR_CLIENT_SECRET"

# OAuth Custom Branding (optional)
OAUTH_CUSTOM_SIGN_IN_LOGO=""

# -----------------------------------------------------------------------------
# Authentifizierung & Sicherheit (ERFORDERLICH - Neue Secrets generieren!)
# -----------------------------------------------------------------------------
AUTH_OPEN_WEBUI_SIGNING_SECRET="REPLACE_WITH_RANDOM_STRING"

# Superuser-Konfiguration
SUPERUSER_ENABLED="True"
SUPERUSER_NAME="AI-Hub Superuser"
SUPERUSER_EMAIL="admin@your-company.com"
SUPERUSER_OID="REPLACE_WITH_RANDOM_STRING"
SUPERUSER_ROLE="AIHubSuperuser"
SUPERUSER_TOKEN="REPLACE_WITH_RANDOM_STRING"

# -----------------------------------------------------------------------------
# Datenbank-Zugangsdaten (ERFORDERLICH - Starke Passwörter verwenden!)
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
# Öffentlicher Endpunkt für presigned URLs (automatisch als https://s3.${DOMAIN} in docker-compose konfiguriert)
# S3_STORAGE_PUBLIC_ENDPOINT wird automatisch gesetzt - nur überschreiben bei benutzerdefinierter S3-Domain

# -----------------------------------------------------------------------------
# LiteLLM Konfiguration (ERFORDERLICH)
# -----------------------------------------------------------------------------
LITELLM_UI_USERNAME="admin"
LITELLM_UI_PASSWORD="REPLACE_WITH_RANDOM_STRING"
LITELLM_MASTER_KEY="REPLACE_WITH_RANDOM_STRING"

# -----------------------------------------------------------------------------
# Service-Konfiguration
# -----------------------------------------------------------------------------
JUPYTER_TOKEN="REPLACE_WITH_RANDOM_STRING"
PHOENIX_SECRET="REPLACE_WITH_RANDOM_STRING"

# Docling-Konfiguration
DOCLING_API_TIMEOUT="600"
DOCLING_VLM_MODEL_NAME="text-generation/ocr"
DOCLING_HTTP_RETRIES=3

# Milvus-Konfiguration (muss mit den Dimensionen Ihres Embedding-Modells übereinstimmen)
MILVUS_DIMENSION="3072"

# -----------------------------------------------------------------------------
# AI-Hub Anwendungseinstellungen
# -----------------------------------------------------------------------------
AIHUB_API_VERSION="latest"
AIHUB_CREATE_DEFAULT_ROLES="True"

# Admin-Einstellungen
ADMIN_EMAIL="admin@your-company.com"

# OAuth Gruppenbeschränkungen (Azure AD Gruppennamen)
OAUTH_ALLOWED_GROUPS_DAGSTER="AIHubAdmin"
OAUTH_ALLOWED_GROUPS_SEAWEEDFS="AIHubAdmin"
OAUTH_ALLOWED_GROUPS_ATTU="AIHubAdmin"

# -----------------------------------------------------------------------------
# Expert Asking Agent Konfiguration (Optional - für Experten-Eskalation)
# -----------------------------------------------------------------------------
# Kanaltyp: "teams" oder "slack"
EXPERT_ASKING_CHANNEL_TYPE="teams"

# Teams-Konfiguration (erforderlich wenn EXPERT_ASKING_CHANNEL_TYPE="teams")
TEAMS_CHANNEL_ID="REPLACE_WITH_TEAMS_CHANNEL_ID"
TEAMS_TENANT_ID="REPLACE_WITH_TEAMS_TENANT_ID"
TEAMS_BOT_ID="REPLACE_WITH_TEAMS_BOT_ID"

# Slack-Konfiguration (erforderlich wenn EXPERT_ASKING_CHANNEL_TYPE="slack")
SLACK_CHANNEL_ID=""
SLACK_SERVICE_URL="https://slack.botframework.com"

# -----------------------------------------------------------------------------
# OpenTelemetry Konfiguration (Optional)
# -----------------------------------------------------------------------------
OTEL_ENABLED="true"
OTEL_EXPORTER_OTLP_PROTOCOL="grpc"
OTEL_RESOURCE_SERVICE_VERSION="1.0.0"
OTEL_RESOURCE_SERVICE_NAMESPACE="swiss-ai-hub"

# Cloud OTEL (optional - für externe Observability-Plattformen)
OTEL_CLOUD_ENDPOINT="placeholder:1234"
OTEL_CLOUD_HEADERS=""
```

### Konfigurationsrichtlinien

**Kritische Werte zum Ersetzen:**

1. **Domain** - Setzen Sie `DOMAIN` auf Ihre Produktions-Domain (z.B. `aihub.yourcompany.com`) oder `127.0.0.1.nip.io`
   für lokale Tests

2. **Authentifizierungswerte** (aus den Voraussetzungen):

   - `REPLACE_WITH_YOUR_CLIENT_ID` → Ihre Azure App Registration Client ID
   - `REPLACE_WITH_YOUR_CLIENT_SECRET` → Ihr Azure App Registration Client Secret
   - `REPLACE_WITH_YOUR_TENANT_ID` → Ihre Azure Tenant ID

3. **KI-Modellzugriff** (mindestens einen konfigurieren):

   - `REPLACE_WITH_AZURE_OPENAI_BASE_URL` → Ihre Azure OpenAI Endpunkt-URL
   - `REPLACE_WITH_AZURE_OPENAI_KEY` → Ihr Azure OpenAI API-Schlüssel

4. **Secrets** (eindeutige Werte für jeden generieren):

   - Ersetzen Sie alle `REPLACE_WITH_RANDOM_STRING` mit: `openssl rand -hex 32`
   - Ersetzen Sie `REPLACE_WITH_16_HEX_CHARS` mit: `openssl rand -hex 16`

5. **Experten-Eskalation** (optional - für Expert-in-the-Loop-Funktionen):

   - `REPLACE_WITH_TEAMS_CHANNEL_ID` → Ihre Teams-Kanal-ID (Format: `19:xxx@thread.tacv2`)
   - `REPLACE_WITH_TEAMS_TENANT_ID` → Ihre Azure AD Tenant ID
   - `REPLACE_WITH_TEAMS_BOT_ID` → Ihre Azure Bot Service Application ID

::: info Vereinfachte Konfiguration
Interne Service-Endpunkte (wie Datenbank-URLs, Message Queues, etc.) sind jetzt in den Docker Compose-Dateien
hartcodiert. Sie müssen nur Zugangsdaten und externe Service-Verbindungen konfigurieren.
:::

::: tip Zufällige Zeichenketten generieren
Verwenden Sie diese Befehle, um sichere zufällige Zeichenketten zu generieren:

```bash
# Für die meisten Secrets (64 Zeichen)
openssl rand -hex 32

# Für OAuth Cookie Secrets (32 Zeichen jeweils - separat für jeden Service generieren)
openssl rand -hex 16  # Für OAUTH_COOKIE_SECRET_DAGSTER, OAUTH_COOKIE_SECRET_ATTU, ...
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
