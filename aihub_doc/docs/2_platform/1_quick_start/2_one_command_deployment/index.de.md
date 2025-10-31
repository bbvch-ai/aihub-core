---
title: Ein-Befehl-Bereitstellung
source_sha: 0bfb670b7ba98c7a6969c92457c7b4279a6f2322af7ebd7ad0f1e6abc19bf1fe
---

# Ein-Befehl-Bereitstellung: Starten Sie Ihre KI-Plattform

Die Swiss AI Hub Plattform wird mit einem einzigen Docker Compose Befehl bereitgestellt. Dieser optimierte Prozess
bringt Ihre vollständige KI-Infrastruktur in Minuten, nicht Stunden, zum Laufen.

## Bereitstellungsübersicht

Die Bereitstellung besteht aus drei einfachen Schritten:

1. **Herunterladen** der Bereitstellungskonfiguration
2. **Konfigurieren** der Umgebungsvariablen mit Ihren Einstellungen
3. **Bereitstellen** mit einem Befehl

Die gesamte Plattform läuft als containerisierte Services, die Service Discovery, Netzwerkkonfiguration und
Start-Orchestrierung automatisch verwalten.

## Schritt 1: Bereitstellungsdateien herunterladen

### Docker Compose Konfiguration beziehen

Laden Sie die neueste Bereitstellungskonfiguration herunter:

```bash
# Create deployment directory
mkdir swiss-ai-hub-deployment
cd swiss-ai-hub-deployment

# Download the latest deployment configuration
curl -O https://raw.githubusercontent.com/bbvch-ai/aihub-core/main/docker-compose.latest.yml
```

Alternativ können Sie zum [aihub-core Repository](https://github.com/bbvch-ai/aihub-core) navigieren und
`docker-compose.latest.yml` manuell herunterladen.

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
SUPERUSER_EMAIL="admin@your-company.com"              # Ersetzen Sie dies mit der Administrator-E-Mail
SUPERUSER_OID="REPLACE_WITH_RANDOM_STRING_3"
SUPERUSER_ROLE="AIHubSuperuser"
SUPERUSER_TOKEN="REPLACE_WITH_RANDOM_STRING_4"

# Platform Settings
AIHUB_API_VERSION="dev"
AIHUB_FRONTEND_ORIGIN="https://127.0.0.1.nip.io"     # Für die Produktionsumgebung ändern
AIHUB_CREATE_DEFAULT_ROLES="True"

# =============================================================================
# AI MODEL ACCESS (Configure at least one)
# =============================================================================

# Azure OpenAI (Empfohlen)
AZURE_OPENAI_KEY="REPLACE_WITH_AZURE_OPENAI_KEY"
AZURE_OPENAI_KEY_IMAGE="REPLACE_WITH_AZURE_OPENAI_KEY"
AZURE_OPENAI_KEY_AUDIO="REPLACE_WITH_AZURE_OPENAI_KEY"

# Google Gemini (Alternative)
GEMINI_API_KEY="REPLACE_WITH_GEMINI_KEY"

# =============================================================================
# LITELLM PROXY KONFIGURATION
# =============================================================================

LITELLM_UI_USERNAME="admin"
LITELLM_UI_PASSWORD="REPLACE_WITH_RANDOM_STRING_5"
LITELLM_MASTER_KEY="REPLACE_WITH_RANDOM_STRING_6"
LITE_LLM_PROXY_BASE_URL="http://litellm:4000"
LITE_LLM_PROXY_API_KEY="REPLACE_WITH_RANDOM_STRING_7"

# =============================================================================
# DATENBANKKONFIGURATION
# =============================================================================

# PostgreSQL
POSTGRES_USER="admin"
POSTGRES_PASSWORD="REPLACE_WITH_RANDOM_STRING_8"

# FerretDB (MongoDB-kompatibel)
MONGO_USERNAME="admin"
MONGO_PASSWORD="REPLACE_WITH_RANDOM_STRING_9"
MONGO_CONNECTION_STRING="mongodb://admin:REPLACE_WITH_SAME_MONGO_PASSWORD@ferretdb:27017/"

# Valkey (Redis-kompatibel)
REDIS_URL="redis://localhost:6379"

# =============================================================================
# SPEICHERKONFIGURATION
# =============================================================================

# SeaweedFS S3 Speicher
SEAWEEDFS_ROOT_USER="admin"
SEAWEEDFS_ROOT_PASSWORD="REPLACE_WITH_RANDOM_STRING_10"
S3_STORAGE_ENDPOINT="http://seaweedfs:8333"
S3_STORAGE_ACCESS_KEY="admin"                         # Muss mit SEAWEEDFS_ROOT_USER übereinstimmen
S3_STORAGE_SECRET_KEY="REPLACE_WITH_SAME_SEAWEEDFS_PASSWORD"

# =============================================================================
# SERVICE-ENDPUNKTE (Intern - Nicht ändern)
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
# OPTIONALE INTEGRATIONEN
# =============================================================================

# Jina AI Suche (Optional)
# JINA_API_KEY="your_jina_api_key"
```

### Konfigurationsrichtlinien

**Kritische Werte, die ersetzt werden müssen:**

1. **Authentifizierungswerte** (aus den Voraussetzungen):

   - `REPLACE_WITH_YOUR_CLIENT_ID` → Ihre Azure App Registration Client ID
   - `REPLACE_WITH_YOUR_CLIENT_SECRET` → Ihr Azure App Registration Client Secret
   - `REPLACE_WITH_YOUR_TENANT_ID` → Ihre Azure Tenant ID (erscheint zweimal)

2. **KI-Modellzugriff** (mindestens einen konfigurieren):

   - `REPLACE_WITH_AZURE_OPENAI_KEY` → Ihr Azure OpenAI API-Schlüssel
   - `REPLACE_WITH_GEMINI_KEY` → Ihr Google Gemini API-Schlüssel

3. **Zufällige Zeichenketten** (eindeutige Werte generieren):

   - Ersetzen Sie alle `REPLACE_WITH_RANDOM_STRING_X` durch eindeutige, zufällige Zeichenketten
   - Verwenden Sie unterschiedliche Werte für jeden Platzhalter
   - Mindestens 32 Zeichen werden für die Sicherheit empfohlen

**Domain-Konfiguration:**

- Für lokale Tests: Behalten Sie `AIHUB_FRONTEND_ORIGIN="https://127.0.0.1.nip.io"` bei
- Für die Produktion: Ändern Sie dies auf Ihre tatsächliche Domain (z.B. `https://ai-hub.your-company.com`)

::: tip Zufällige Zeichenketten generieren
Verwenden Sie diesen Befehl, um sichere zufällige Zeichenketten zu generieren:

```bash
openssl rand -hex 32
```

Führen Sie ihn mehrmals aus, um verschiedene Werte für jeden Platzhalter zu erhalten.
:::

### Umgebungsvalidierung

Vor der Bereitstellung überprüfen Sie Ihre Konfiguration:

```bash
# Check for placeholder values that need replacement
grep -n "REPLACE_WITH" .env
```

Dies sollte keine Ergebnisse liefern, wenn alle Platzhalter ersetzt wurden.

## Schritt 3: Plattform bereitstellen

### Alle Dienste starten

Stellen Sie die vollständige Plattform mit einem Befehl bereit:

```bash
docker compose -f docker-compose.latest.yml up -d
```

Dieser Befehl wird:

- Alle notwendigen Docker-Images herunterladen
- Erforderliche Netzwerke und Volumes erstellen
- Alle Plattformdienste in der richtigen Reihenfolge starten
- Service Discovery und Kommunikation konfigurieren

### Bereitstellungsfortschritt überwachen

Beobachten Sie den Bereitstellungsfortschritt:

```bash
# See all services starting
docker compose -f docker-compose.latest.yml logs -f

# Check service health status
docker compose -f docker-compose.latest.yml ps
```

**Erwartete Dienste:** Die Plattform umfasst diese Kerndienste:

- **Web-Oberfläche** (aihub-web)
- **API** (aihub-api)
- **Authentifizierung** (auth services)
- **Datenbanken** (FerretDB, PostgreSQL, Valkey)
- **Vektordatenbank** (Milvus)
- **LLM Proxy** (LiteLLM)
- **Dokumentenverarbeitung** (Docling)
- **Beobachtbarkeit** (Phoenix)
- **Nachrichtenwarteschlange** (NATS)
- **Speicher** (SeaweedFS)

### Warten auf Service-Initialisierung

Der erstmalige Start dauert 3-5 Minuten, während sich die Dienste initialisieren. Alle Dienste sollten den Status
„healthy“ (fehlerfrei) anzeigen:

```bash
# Wait for healthy status
docker compose -f docker-compose.latest.yml ps --format "table {{.Name}}\t{{.Status}}"
```

## Schritt 4: Erfolgreiche Bereitstellung überprüfen

### Auf die Plattform zugreifen

1. **Stellen Sie sicher, dass Ihr Testbenutzer die Rolle „AIHubAdmin“ in der Azure Enterprise Application zugewiesen
   bekommen hat.**

2. **Web-Oberfläche:**

   - Lokal: `https://127.0.0.1.nip.io`
   - Produktion: `https://your-domain.com`

3. **Erwarteter Anmeldeablauf:**

   - Weiterleitung zur Azure-Authentifizierung
   - Nach der Anmeldung Rückkehr zur AI-Hub-Oberfläche
   - Sie sollten das Haupt-Dashboard sehen
