---
title: Deployment per Einzelbefehl
source_sha: "157fd620ff6798511e6b9e2f3827839c91620a355c4fd42b46b61de12caa0f3d"
---

# Deployment per Einzelbefehl: Starten Sie Ihre KI-Plattform

Die Swiss AI Hub Plattform lässt sich mit einem einzigen Docker Compose Befehl deployen. Dieser optimierte Prozess bringt Ihre komplette KI-Infrastruktur in Minutenschnelle, nicht in Stunden, zum Laufen.

## Schnelle Installation

Führen Sie einen einzigen Befehl aus, um die Plattform herunterzuladen, zu entpacken und einzurichten:

```bash
curl -fsSL https://raw.githubusercontent.com/bbvch-ai/aihub-core/main/install.sh | bash
```

Der Installer erkennt automatisch GPU-Hardware, lädt das korrekte Release-Bundle herunter und generiert alle Secrets. Danach bearbeiten Sie die `.env`-Datei und führen `docker compose up -d` aus.

| Parameter           | Standard         | Beschreibung                       |
| ------------------- | ---------------- | ---------------------------------- |
| `--version VERSION` | latest           | Auf eine bestimmte Version pinnen |
| `--gpu`             | auto-detect      | GPU-Bundle erzwingen               |
| `--cpu`             | auto-detect      | Nur CPU-Bundle erzwingen           |
| `--dir PATH`        | `./swiss-ai-hub` | Installationsverzeichnis           |
| `--help`            |                  | Nutzung anzeigen                   |

**Beispiele:**

```bash
# Install with GPU bundle to a custom directory
curl -fsSL https://raw.githubusercontent.com/bbvch-ai/aihub-core/main/install.sh | bash -s -- --gpu --dir /opt/swiss-ai-hub

# Pin a specific version
curl -fsSL https://raw.githubusercontent.com/bbvch-ai/aihub-core/main/install.sh | bash -s -- --version v0.269.2
```

**Upgrade durchführen:** Führen Sie den Installer erneut mit demselben `--dir` aus. Er erkennt die bestehende Installation, sichert Ihre `.env`-Datei, ersetzt Bundle-Dateien, stellt `.env` wieder her und berichtet über alle neuen Umgebungsvariablen, die im Release hinzugefügt wurden.

______________________________________________________________________

## Deployment-Übersicht

::: tip Zwei Deployment-Optionen
Der Swiss AI Hub unterstützt zwei Deployment-Modi. Befolgen Sie für beide die gleichen Schritte und verwenden Sie die passenden Befehle für Ihren Deployment-Typ:

-   **Produktions-Deployment**: Deployment auf einem Server mit einem echten Domainnamen (z.B. `swiss-ai-hub.yourcompany.com`)

    -   Verwendet das CPU- oder GPU-Release-Bundle von GitHub Releases
    -   Verwendet Let's Encrypt für automatische SSL-Zertifikate
    -   Erfordert eine DNS-Konfiguration, die auf Ihren Server zeigt

-   **Lokales Deployment**: Ausführung auf Ihrer lokalen Maschine für Entwicklung/Tests

    -   Verwendet `infra/docker-compose.local.yml` aus dem Repository
    -   Verwendet selbstsignierte SSL-Zertifikate (mkcert)
    -   Verwendet die Domain `127.0.0.1.nip.io` (löst automatisch zu localhost auf)

Jeder der folgenden Schritte zeigt Befehle für beide Deployment-Typen. Folgen Sie einfach den Befehlen, die Ihrem gewählten Deployment-Modus entsprechen.
:::

______________________________________________________________________

## Schritt 1: Deployment-Dateien abrufen

**Für die Produktion:**

Laden Sie das neueste Release-Bundle von [GitHub Releases](https://github.com/bbvch-ai/aihub-core/releases) herunter. Jedes Release bietet zwei eigenständige Bundles:

-   `swissaihub-<version>.tar.gz` – Nur-CPU-Deployment
-   `swissaihub-<version>-gpu.tar.gz` – GPU-fähiges Deployment (inklusive vLLM, GPU-beschleunigte Inferenz)

```bash
# Set the version you want to deploy
VERSION="v0.266.0"  # Replace with the desired version

# Download and extract the release bundle (CPU example)
mkdir swiss-ai-hub && cd swiss-ai-hub
curl -L "https://github.com/bbvch-ai/aihub-core/releases/download/${VERSION}/swissaihub-${VERSION}.tar.gz" \
  | tar -xz

# For GPU-enabled deployment, use this instead:
# curl -L "https://github.com/bbvch-ai/aihub-core/releases/download/${VERSION}/swissaihub-${VERSION}-gpu.tar.gz" \
#   | tar -xz
```

Das Release-Bundle enthält alles Notwendige für das Deployment: `docker-compose.yml`, alle Service-Konfigurationsdateien, eine `.env.template` und das Skript `setup-env.sh`.

**Für lokales Deployment:**

```bash
# Clone the repository
git clone https://github.com/bbvch-ai/aihub-core.git
cd swiss-ai-hub

# Generate SSL certificates with mkcert
mkcert -install  # Install local CA (only needed once)
make local-cert
```

::: tip Was ist nip.io?
Die Domain `*.127.0.0.1.nip.io` löst automatisch zu Ihrem Localhost (127.0.0.1) auf und bietet eine Wildcard-DNS-Auflösung, ohne dass Sie Ihre Hosts-Datei ändern müssen. Dies ermöglicht Subdomain-basiertes Routing in der lokalen Entwicklung.
:::

______________________________________________________________________

## Schritt 2: Umgebungsvariablen konfigurieren

### Umgebungskonfiguration generieren

**Für die Produktion (Release-Bundle):**

Das Release-Bundle enthält ein `setup-env.sh`-Skript, das eine `.env`-Datei aus der enthaltenen `.env.template` generiert. Es erstellt automatisch einzigartige Secrets für alle Datenbankpasswörter, Tokens und Signierschlüssel:

```bash
# Generate .env with auto-generated secrets
./setup-env.sh
```

::: details Was macht setup-env.sh?
Das Skript liest `.env.template` und ersetzt alle `REPLACE_WITH_*`-Platzhalter durch kryptografisch sichere Zufallswerte. Jeder Platzhalter erhält ein eigenes, einzigartiges Secret. Das Skript benötigt nur `openssl` und `bash` – kein Python oder andere Abhängigkeiten sind erforderlich.

```bash
# Optionen:
./setup-env.sh                              # Standard: .env.template → .env
./setup-env.sh -t custom.template -o out.env  # Benutzerdefinierte Pfade
./setup-env.sh --force                      # Bestehende .env überschreiben
```
:::

**Für lokales Deployment:**

```bash
cp .env.dev .env
```

### Verbleibende Werte konfigurieren

Nachdem Sie Ihre `.env`-Datei generiert haben, überprüfen Sie diese und füllen Sie die Werte aus, die eine manuelle Konfiguration erfordern:

**Kritische Werte, die ersetzt werden müssen:**

1.  **Domain** – Setzen Sie `DOMAIN` auf Ihre Produktionsdomain (z.B. `swiss-ai-hub.yourcompany.com`) oder `127.0.0.1.nip.io` für lokale Tests.

2.  **Authentifizierungswerte** (aus den Voraussetzungen):

    -   `REPLACE_WITH_YOUR_CLIENT_ID` → Ihre Azure App Registration Client ID
    -   `REPLACE_WITH_YOUR_CLIENT_SECRET` → Ihr Azure App Registration Client Secret
    -   `REPLACE_WITH_YOUR_TENANT_ID` → Ihre Azure Tenant ID

3.  **KI-Modellzugriff** (Swiss LLM Cloud – erforderlich für Nicht-GPU-Deployments):

    -   `REPLACE_WITH_SWISS_LLM_CLOUD_URL` → Ihr Swiss LLM Cloud Endpunkt für Textgenerierung
    -   `REPLACE_WITH_SWISS_LLM_CLOUD_KEY` → Ihr Swiss LLM Cloud API Schlüssel
    -   Konfigurieren Sie die verbleibenden Endpunktpaare für Embedding, Reranking, Whisper und OCR

4.  **Experten-Eskalation** (optional – für Expert-in-the-Loop-Funktionen):

    -   `REPLACE_WITH_TEAMS_CHANNEL_ID` → Ihre Teams Kanal-ID (Format: `19:xxx@thread.tacv2`)
    -   `REPLACE_WITH_TEAMS_TENANT_ID` → Ihre Azure AD Tenant ID
    -   `REPLACE_WITH_TEAMS_BOT_ID` → Ihre Azure Bot Service Application ID

::: info Vereinfachte Konfiguration
Interne Service-Endpunkte (wie Datenbank-URLs, Message Queues usw.) sind in den Docker Compose-Dateien fest kodiert. Sie müssen nur Anmeldeinformationen und externe Service-Verbindungen konfigurieren. Alle Datenbankpasswörter, Tokens und Signierschlüssel werden automatisch von `setup-env.sh` generiert.
:::

### Umgebungsvalidierung

Überprüfen Sie vor dem Deployment Ihre Konfiguration:

```bash
# Check for placeholder values that still need replacement
grep -n "REPLACE_WITH" .env
```

Dies sollte keine Ergebnisse zurückliefern, wenn alle Platzhalter ersetzt wurden.

______________________________________________________________________

## Schritt 3: Plattform deployen

### Alle Services starten

Deployen Sie die komplette Plattform mit einem Befehl:

**Für die Produktion (Release-Bundle):**

```bash
docker compose up -d
```

Dieser Befehl wird:

-   Alle notwendigen Docker-Images herunterladen
-   Erforderliche Netzwerke und Volumes erstellen
-   Alle Plattform-Services in der richtigen Reihenfolge starten
-   Service Discovery und Kommunikation konfigurieren

### Deployment-Fortschritt überwachen

Beobachten Sie den Deployment-Fortschritt:

```bash
# See all services starting
docker compose logs -f

# Check service health status
docker compose ps
```

**Erwartete Services:** Die Plattform umfasst diese Kern-Services:

-   **Web-Oberfläche** (swiss-ai-hub-web)
-   **API** (swiss-ai-hub-api)
-   **Authentifizierung** (Auth Services)
-   **Datenbanken** (FerretDB, PostgreSQL, Valkey)
-   **Vektordatenbank** (Milvus)
-   **LLM Proxy** (LiteLLM)
-   **Dokumentenverarbeitung** (MinerU)
-   **Observability** (Langfuse)
-   **Message Queue** (NATS)
-   **Storage** (SeaweedFS)

### Warten Sie auf die Service-Initialisierung

Der erste Start dauert 3-5 Minuten, während die Services initialisieren. Alle Services sollten den Status „healthy“ anzeigen:

```bash
# Wait for healthy status
docker compose ps --format "table {{.Name}}\t{{.Status}}"
```

______________________________________________________________________

## Schritt 4: Erfolgreiches Deployment verifizieren

### Plattform aufrufen

1.  **Stellen Sie sicher, dass Ihr Testbenutzer die Rollen „AIHubAdmin“ und „AIHubSysAdmin“ in der Azure Enterprise Application zugewiesen bekommen hat.**

2.  **Web-Oberfläche:**

    -   Produktion: `https://your-domain.com`

3.  **Erwarteter Login-Flow:**

    -   Leitet zur Azure-Authentifizierung weiter
    -   Nach dem Login kehrt sie zur Swiss AI Hub-Oberfläche zurück
    -   Sie sollten das Haupt-Dashboard sehen
