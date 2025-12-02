---
title: Ein-Befehl-Deployment
source_sha: "e7f1f74d6dea7b51342a596afed822bbe75276bba48e48a3337578421deb52d4"
---

# Ein-Befehl-Deployment: Ihre KI-Plattform starten

Die Swiss AI Hub Plattform wird mit einem einzigen Docker Compose Befehl deployt. Dieser optimierte Prozess lässt Ihre komplette KI-Infrastruktur in Minuten statt Stunden einsatzbereit sein.

## Deployment-Übersicht

::: tip Zwei Deployment-Optionen
Der Swiss AI Hub unterstützt zwei Deployment-Modi. Befolgen Sie für beide die gleichen Schritte und verwenden Sie die passenden Befehle für Ihren Deployment-Typ:

- **Produktions-Deployment**: Deployment auf einem Server mit einem echten Domainnamen (z.B. `aihub.yourcompany.com`)

  - Verwendet `docker-compose.latest.yml`
  - Verwendet Let's Encrypt für automatische SSL-Zertifikate
  - Erfordert eine DNS-Konfiguration, die auf Ihren Server zeigt

- **Lokales Deployment**: Auf Ihrer lokalen Maschine für Entwicklung/Tests ausführen

  - Verwendet `docker-compose.local.yml`
  - Verwendet selbstsignierte SSL-Zertifikate (mkcert)
  - Verwendet die Domain `127.0.0.1.nip.io` (löst automatisch zu localhost auf)

Jeder der folgenden Schritte zeigt Befehle für beide Deployment-Typen. Befolgen Sie einfach die Befehle, die Ihrem gewählten Deployment-Modus entsprechen.
:::

---

## Schritt 1: Deployment-Dateien abrufen

**Für die Produktion:**

```bash
# Deployment-Verzeichnis erstellen
mkdir swiss-ai-hub-deployment
cd swiss-ai-hub-deployment

# Produktions-Deployment-Konfiguration herunterladen
curl -O https://raw.githubusercontent.com/bbvch-ai/aihub-core/main/docker-compose.latest.yml

# configs-Verzeichnis herunterladen
curl -L https://github.com/bbvch-ai/aihub-core/tarball/main | tar -xz --strip=2 "*/configs"
```

**Für lokales Deployment:**

```bash
# Deployment-Verzeichnis erstellen
mkdir swiss-ai-hub-deployment
cd swiss-ai-hub-deployment

# Lokale Deployment-Konfiguration herunterladen
curl -O https://raw.githubusercontent.com/bbvch-ai/aihub-core/main/docker-compose.local.yml

# configs-Verzeichnis herunterladen
curl -L https://github.com/bbvch-ai/aihub-core/tarball/main | tar -xz --strip=2 "*/configs"

# SSL-Zertifikate mit mkcert generieren
mkcert -install  # Lokale CA installieren (nur einmal erforderlich)
mkcert -key-file configs/traefik/certs/dev-key.pem -cert-file configs/traefik/certs/dev-cert.pem \
  "localhost" "*.localhost" \
  "127.0.0.1.nip.io" "*.127.0.0.1.nip.io"
```

::: tip Was ist nip.io?
Die Domain `*.127.0.0.1.nip.io` löst automatisch zu Ihrem Localhost (127.0.0.1) auf und bietet eine Wildcard-DNS-Auflösung, ohne dass Sie Ihre Hosts-Datei ändern müssen. Dies ermöglicht ein Subdomain-basiertes Routing in der lokalen Entwicklung.
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
# GRUNDLEGENDE PLATTFORMKONFIGURATION
# =============================================================================

LOG_LEVEL="WARNING"                    # Optionen: CRITICAL, ERROR, WARNING, INFO, DEBUG
ENV="prod"                             # Optionen: dev, test, prod
DOMAIN="REPLACE_WITH_YOUR_DOMAIN"

# Traefik Konfiguration
ACME_EMAIL="admin@your-company.com"
ADMIN_PASSWORD_HASH=""                 # Generieren mit: htpasswd -nb admin yourpassword

# =============================================================================
# AUTHENTIFIZIERUNGSKONFIGURATION
# =============================================================================

# Allgemeine Authentifizierungseinstellungen
AUTH_ENABLE_API_ACCESS="True"
AUTH_OPEN_WEBUI_SIGNING_SECRET="REPLACE_WITH_RANDOM_STRING"
AUTH_IDENTITY_PROVIDER="azure"

# OAuth2 Konfiguration (aus der Voraussetzungen-Einrichtung)
OAUTH_CLIENT_ID="REPLACE_WITH_YOUR_CLIENT_ID"
OAUTH_CLIENT_SECRET="REPLACE_WITH_YOUR_CLIENT_SECRET"
OAUTH_AUTHORITY_URL="https://login.microsoftonline.com/REPLACE_WITH_YOUR_TENANT_ID"
OAUTH_PROVIDER_NAME="azure"
OAUTH_TENANT_ID="REPLACE_WITH_YOUR_TENANT_ID"
OAUTH_COOKIE_SECRET="REPLACE_WITH_16_HEX_CHARS"

# =============================================================================
# PLATTFORMZUGANGSKONFIGURATION
# =============================================================================

# Superuser-Konfiguration
SUPERUSER_ENABLED="True"
SUPERUSER_NAME="AI-Hub Superuser"
SUPERUSER_EMAIL="admin@your-company.com"
SUPERUSER_OID="REPLACE_WITH_RANDOM_STRING"
SUPERUSER_ROLE="AIHubSuperuser"
SUPERUSER_TOKEN="REPLACE_WITH_RANDOM_STRING"

# Plattform-Einstellungen
AIHUB_API_VERSION="dev"
AIHUB_FRONTEND_ORIGIN="https://REPLACE_WITH_YOUR_DOMAIN"
AIHUB_CREATE_DEFAULT_ROLES="True"

# =============================================================================
# KI-MODELLZUGRIFF (Mindestens einen konfigurieren)
# =============================================================================

# Azure OpenAI (Empfohlen)
AZURE_OPENAI_BASE_URL="REPLACE_WITH_AZURE_OPENAI_BASE_URL"
AZURE_OPENAI_KEY="REPLACE_WITH_AZURE_OPENAI_KEY"

# Google Gemini (Alternative)
GEMINI_API_KEY="REPLACE_WITH_GEMINI_KEY"

# Swiss LLM Cloud (Optional)
SWISS_LLM_CLOUD_API_URL=""                # Optional: Swiss LLM Cloud Endpunkt-URL
SWISS_LLM_CLOUD_API_KEY=""                # Optional: Swiss LLM Cloud API-Schlüssel

# Cohere (Optional)
COHERE_API_BASE=""                        # Optional: Cohere API Basis-URL
COHERE_API_KEY=""                         # Optional: Cohere API-Schlüssel

# Hugging Face (Optional)
HUGGINGFACE_API_KEY=""                    # Optional: Für den Zugriff auf Hugging Face Modelle

# =============================================================================
# LITELLM PROXY-KONFIGURATION
# =============================================================================

LITELLM_UI_USERNAME="admin"
LITELLM_UI_PASSWORD="REPLACE_WITH_RANDOM_STRING"
LITELLM_MASTER_KEY="REPLACE_WITH_RANDOM_STRING"
LITE_LLM_PROXY_BASE_URL="http://litellm:4000"
LITE_LLM_PROXY_API_KEY="REPLACE_WITH_RANDOM_STRING"

# =============================================================================
# DATENBANKKONFIGURATION
# =============================================================================

# PostgreSQL
POSTGRES_USER="admin"
POSTGRES_PASSWORD="REPLACE_WITH_RANDOM_STRING"

# FerretDB (MongoDB-kompatibel)
MONGO_USERNAME="admin"
MONGO_PASSWORD="REPLACE_WITH_RANDOM_STRING"
MONGO_CONNECTION_STRING="mongodb://admin:REPLACE_WITH_SAME_MONGO_PASSWORD@ferretdb:27017/"

# Valkey (Redis-kompatibel)
REDIS_URL="redis://localhost:6379"

# =============================================================================
# SPEICHERKONFIGURATION
# =============================================================================

# SeaweedFS S3 Speicher
# Hinweis: Die S3-API ist unter s3.${DOMAIN} mit AWS-Signaturauthentifizierung verfügbar
# Die Filer-Web-UI ist nur intern (nicht extern zugänglich)
SEAWEEDFS_ROOT_USER="admin"
SEAWEEDFS_ROOT_PASSWORD="REPLACE_WITH_RANDOM_STRING"
S3_STORAGE_ENDPOINT="http://seaweedfs:9000"           # S3-API-Endpunkt (Produktion verwendet https://s3.${DOMAIN})
S3_STORAGE_ACCESS_KEY="admin"                         # Muss mit SEAWEEDFS_ROOT_USER übereinstimmen
S3_STORAGE_SECRET_KEY="REPLACE_WITH_SAME_SEAWEEDFS_PASSWORD"
S3_STORAGE_URL_SIGNING_SECRET="REPLACE_WITH_RANDOM_STRING"

# =============================================================================
# SERVICE-ENDPUNKTE (Intern - Nicht ändern)
# =============================================================================

DOCLING_API_ENDPOINT="http://docling:5001"
DOCLING_API_TIMEOUT="600"
PHOENIX_SECRET="REPLACE_WITH_RANDOM_STRING"
PHOENIX_ENDPOINT="http://phoenix:6006"
NATS_ENDPOINT="nats://localhost:4222"
DAGSTER_HOME="~/.dagster_home"
DAGSTER_OAUTH_ALLOWED_GROUPS="AIHubDeveloper"
# SEAWEEDFS_OAUTH_ALLOWED_GROUPS - Veraltet (Filer ist nur intern, nicht mehr extern zugänglich)
JUPYTER_TOKEN="REPLACE_WITH_RANDOM_STRING"
MILVUS_DIMENSION="3072"

# =============================================================================
# OBSERVABILITY-KONFIGURATION
# =============================================================================

# OpenTelemetry Cloud Exporter (Optional - für Produktionsüberwachung)
OTEL_ENABLED="true"                           # OTEL-Sammlung aktivieren/deaktivieren
OTEL_EXPORTER_OTLP_PROTOCOL="grpc"           # Protokoll für OTEL-Export
OTEL_CLOUD_ENDPOINT="localhost:4317"         # Cloud OTEL-Endpunkt (z.B. Grafana Cloud: "otlp.grafana.net:443")
OTEL_CLOUD_HEADERS=""                         # Authentifizierungs-Header (z.B. "Authorization=Bearer IHR_TOKEN")

# =============================================================================
# BOT-ENTWICKLUNGSKONFIGURATION
# =============================================================================

BOT_AUTH_FAKE_NAME="Bot"
BOT_AUTH_FAKE_EMAIL="bot@bot.com"
BOT_AUTH_FAKE_OID="00000000-0000-0000-0000-000000000000"
BOT_AUTH_FAKE_ROLES="AIHubBot"

# =============================================================================
# OPTIONALE INTEGRATIONEN
# =============================================================================

# Jina AI Search (Optional)
JINA_API_KEY=""

# OpenTelemetry Konfiguration (Optional)
OTEL_ENABLED="False"
OTEL_EXPORTER_OTLP_PROTOCOL="grpc"
OTEL_CLOUD_ENDPOINT=""
OTEL_CLOUD_HEADERS=""

# Signoz Telemetry (Optional)
SIGNOZ_INGESTION_CLOUD_ENDPOINT=""
SIGNOZ_INGESTION_KEY=""

```

### Konfigurationsrichtlinien

**Kritische Werte, die ersetzt werden müssen:**

1.  **Authentifizierungswerte** (aus den Voraussetzungen):

    - `REPLACE_WITH_YOUR_CLIENT_ID` → Ihre Azure App Registration Client ID
    - `REPLACE_WITH_YOUR_CLIENT_SECRET` → Ihr Azure App Registration Client Secret
    - `REPLACE_WITH_YOUR_TENANT_ID` → Ihre Azure Tenant ID (erscheint zweimal)

2.  **KI-Modellzugriff** (mindestens einen konfigurieren):

    - `REPLACE_WITH_AZURE_OPENAI_BASE_URL` → Ihre Azure OpenAI Endpunkt-URL
    - `REPLACE_WITH_AZURE_OPENAI_KEY` → Ihr Azure OpenAI API-Schlüssel
    - `REPLACE_WITH_GEMINI_KEY` → Ihr Google Gemini API-Schlüssel

3.  **Zufällige Zeichenketten** (eindeutige Werte generieren):

    - Ersetzen Sie alle `REPLACE_WITH_RANDOM_STRING` durch eindeutige zufällige Zeichenketten (verwenden Sie `openssl rand -hex 32`)
    - Ersetzen Sie `REPLACE_WITH_16_HEX_CHARS` durch eine 16-Byte-Hex-Zeichenkette (verwenden Sie `openssl rand -hex 16`)
    - Verwenden Sie unterschiedliche Werte für jeden Platzhalter
    - Mindestens 32 Zeichen für die Sicherheit empfohlen

**Domain-Konfiguration:**

- Für lokale Tests: Behalten Sie `AIHUB_FRONTEND_ORIGIN="https://127.0.0.1.nip.io"` bei
- Für die Produktion: Ändern Sie dies auf Ihre tatsächliche Domain (z.B. `https://aihub.your-company.com`)

::: tip Zufällige Zeichenketten generieren
Verwenden Sie diese Befehle, um sichere zufällige Zeichenketten zu generieren:

```bash
# Für die meisten Secrets (64 Zeichen)
openssl rand -hex 32

# Für OAUTH_COOKIE_SECRET (32 Zeichen)
openssl rand -hex 16
```

Führen Sie den entsprechenden Befehl für jeden Platzhalter aus.
:::

### Umgebungsvalidierung

Überprüfen Sie vor dem Deployment Ihre Konfiguration:

```bash
# Auf Platzhalterwerte prüfen, die ersetzt werden müssen
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
- Service Discovery und Kommunikation konfigurieren

### Deployment-Fortschritt überwachen

Beobachten Sie den Deployment-Fortschritt:

```bash
# Alle startenden Services anzeigen
docker compose -f docker-compose.latest.yml logs -f

# Service-Health-Status überprüfen
docker compose -f docker-compose.latest.yml ps
```

**Erwartete Services:** Die Plattform umfasst diese Kernservices:

- **Web-Oberfläche** (aihub-web)
- **API** (aihub-api)
- **Authentifizierung** (Auth-Services)
- **Datenbanken** (FerretDB, PostgreSQL, Valkey)
- **Vektordatenbank** (Milvus)
- **LLM-Proxy** (LiteLLM)
- **Dokumentenverarbeitung** (Docling)
- **Observability** (Phoenix)
- **Nachrichtenwarteschlange** (NATS)
- **Speicher** (SeaweedFS)

### Auf Service-Initialisierung warten

Der erstmalige Start dauert 3-5 Minuten, während sich die Services initialisieren. Alle Services sollten den Status „healthy“ anzeigen:

```bash
# Auf Healthy-Status warten
docker compose -f docker-compose.latest.yml ps --format "table {{.Name}}\t{{.Status}}"
```

## Schritt 4: Erfolgreiches Deployment überprüfen

### Auf die Plattform zugreifen

1.  Stellen Sie sicher, dass Ihr Benutzer, mit dem Sie testen, die Rolle „AIHubAdmin“ in der Azure Enterprise Application zugewiesen bekommen hat

2.  **Web-Oberfläche:**

    - Lokal: `https://127.0.0.1.nip.io`
    - Produktion: `https://your-domain.com`

3.  **Erwarteter Login-Flow:**

    - Leitet zur Azure-Authentifizierung weiter
    - Nach dem Login kehrt die Oberfläche zum AI-Hub zurück
    - Das Haupt-Dashboard sollte angezeigt werden

## Zusammenfassung: Hauptunterschiede zwischen Deployments

| Merkmal             | Produktion (`docker-compose.latest.yml`) | Lokal (`docker-compose.local.yml`) |
| :------------------ | :--------------------------------------- | :--------------------------------- |
| **SSL-Zertifikate** | Let's Encrypt (automatisch)              | mkcert (manuelle Generierung)      |
| **Domain**          | Ihre Produktions-Domain                  | `127.0.0.1.nip.io`                 |
| **Konfigurationsdateien** | `*.latest.*` configs                     | `*.local.*` configs                |
| **Zweck**           | Produktions-Deployments                  | Lokales Deployment und Entwicklung |

::: warning
Verwenden Sie niemals selbstsignierte SSL-Zertifikate in der Produktion. Die lokale Deployment-Konfiguration ist ausschließlich für die Entwicklung und Tests auf Ihrer lokalen Maschine vorgesehen.
:::
