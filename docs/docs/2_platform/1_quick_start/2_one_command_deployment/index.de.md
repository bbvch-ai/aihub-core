---
title: One-Command-Deployment
source_sha: "17051efa2c68e2edc3bb437431275e36a7f35ce8a3c0e2c80e63f0fa16103a23"
---

# One-Command-Deployment: Starten Sie Ihre KI-Plattform

Die Swiss AI Hub Plattform wird mit einem einzigen Docker Compose-Befehl deployed. Dieser optimierte Prozess bringt Ihre komplette KI-Infrastruktur in Minutenschnelle, nicht stundenweise, zum Laufen.

## Schnellinstallation

Führen Sie einen einzigen Befehl aus, um die Plattform herunterzuladen, zu extrahieren und einzurichten:

```bash
curl -fsSL https://raw.githubusercontent.com/bbvch-ai/swiss-ai-hub/main/install.sh | bash
```

Der Installer erkennt automatisch GPU-Hardware, lädt das korrekte Release-Bundle herunter und generiert alle Secrets. Bearbeiten Sie anschließend die `.env`-Datei und führen Sie `docker compose up -d` aus.

| Flag                | Standardwert          | Beschreibung                          |
| ------------------- | --------------------- | ------------------------------------- |
| `--version VERSION` | latest                | An eine bestimmte Release-Version binden |
| `--gpu`             | auto-detect           | GPU-Bundle erzwingen                  |
| `--cpu`             | auto-detect           | Nur-CPU-Bundle erzwingen              |
| `--dir PATH`        | `./swiss-ai-hub`      | Installationsverzeichnis              |
| `--help`            |                       | Nutzung anzeigen                      |

**Beispiele:**

```bash
# Installieren Sie mit GPU-Bundle in einem benutzerdefinierten Verzeichnis
curl -fsSL https://raw.githubusercontent.com/bbvch-ai/swiss-ai-hub/main/install.sh | bash -s -- --gpu --dir /opt/swiss-ai-hub

# Eine spezifische Version festlegen
curl -fsSL https://raw.githubusercontent.com/bbvch-ai/swiss-ai-hub/main/install.sh | bash -s -- --version v0.269.2
```

**Upgrade:** Führen Sie den Installer erneut mit demselben `--dir` aus. Er erkennt die bestehende Installation, sichert Ihre `.env`-Datei, ersetzt Bundle-Dateien, stellt die `.env`-Datei wieder her und meldet alle neuen Umgebungsvariablen, die in der Release-Version hinzugefügt wurden.

______________________________________________________________________

## Deployment-Übersicht

::: tip Zwei Deployment-Optionen
Die Swiss AI Hub unterstützt zwei Deployment-Modi. Befolgen Sie für beide die gleichen Schritte und verwenden Sie die entsprechenden Befehle für Ihren Deployment-Typ:

- **Produktions-Deployment**: Deployen Sie auf einem Server mit einem echten Domainnamen (z.B. `swiss-ai-hub.yourcompany.com`)

  - Verwendet das CPU- oder GPU-Release-Bundle von GitHub Releases
  - Verwendet Let's Encrypt für automatische SSL-Zertifikate
  - Erfordert eine DNS-Konfiguration, die auf Ihren Server zeigt

- **Lokales Deployment**: Führen Sie es auf Ihrem lokalen Rechner für Entwicklung/Tests aus

  - Verwendet `infra/docker-compose.local.yml` aus dem Repository
  - Verwendet selbstsignierte SSL-Zertifikate (mkcert)
  - Verwendet die Domain `127.0.0.1.nip.io` (löst sich automatisch zu localhost auf)

Jeder der folgenden Schritte zeigt Befehle für beide Deployment-Typen. Befolgen Sie einfach die Befehle, die Ihrem gewählten Deployment-Modus entsprechen.
:::

______________________________________________________________________

## Schritt 1: Deployment-Dateien beziehen

**Für die Produktion:**

Laden Sie das neueste Release-Bundle von [GitHub Releases](https://github.com/bbvch-ai/swiss-ai-hub/releases) herunter. Jedes Release bietet zwei eigenständige Bundles:

- `swissaihub-<version>.tar.gz` — Nur-CPU-Deployment
- `swissaihub-<version>-gpu.tar.gz` — GPU-fähiges Deployment (enthält vLLM, GPU-beschleunigte Inferenz)

```bash
# Setzen Sie die Version, die Sie deployen möchten
VERSION="v0.266.0"  # Ersetzen Sie dies durch die gewünschte Version

# Release-Bundle herunterladen und extrahieren (CPU-Beispiel)
mkdir swiss-ai-hub && cd swiss-ai-hub
curl -L "https://github.com/bbvch-ai/swiss-ai-hub/releases/download/${VERSION}/swissaihub-${VERSION}.tar.gz" \
  | tar -xz

# Für GPU-fähiges Deployment verwenden Sie stattdessen:
# curl -L "https://github.com/bbvch-ai/swiss-ai-hub/releases/download/${VERSION}/swissaihub-${VERSION}-gpu.tar.gz" \
#   | tar -xz
```

Das Release-Bundle enthält alles Notwendige für das Deployment: `docker-compose.yml`, alle Service-Konfigurationsdateien, eine `.env.template` und das `setup-env.sh`-Skript.

**Für lokales Deployment:**

```bash
# Das Repository klonen
git clone https://github.com/bbvch-ai/swiss-ai-hub.git
cd swiss-ai-hub

# SSL-Zertifikate mit mkcert generieren
mkcert -install  # Lokale CA installieren (nur einmal erforderlich)
make local-cert
```

::: tip Was ist nip.io?
Die Domain `*.127.0.0.1.nip.io` löst sich automatisch zu Ihrem Localhost (127.0.0.1) auf und bietet Wildcard-DNS-Auflösung, ohne dass Sie Ihre Hosts-Datei ändern müssen. Dies ermöglicht Subdomain-basiertes Routing in der lokalen Entwicklung.
:::

______________________________________________________________________

## Schritt 2: Umgebungsvariablen konfigurieren

### Umgebungskonfiguration generieren

**Für die Produktion (Release-Bundle):**

Das Release-Bundle enthält ein `setup-env.sh`-Skript, das eine `.env`-Datei aus der enthaltenen `.env.template` generiert. Es erstellt automatisch eindeutige Secrets für alle Datenbankpasswörter, Tokens und Signierschlüssel:

```bash
# .env mit automatisch generierten Secrets erstellen
./setup-env.sh
```

::: details Was macht setup-env.sh?
Das Skript liest `.env.template` und ersetzt alle `REPLACE_WITH_*` Platzhalter durch kryptographisch sichere Zufallswerte. Jeder Platzhalter erhält ein eigenes eindeutiges Secret. Das Skript benötigt nur `openssl` und `bash` — kein Python oder andere Abhängigkeiten sind erforderlich.

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

1.  **Domain** — Setzen Sie `DOMAIN` auf Ihre Produktionsdomain (z.B. `swiss-ai-hub.yourcompany.com`) oder auf `127.0.0.1.nip.io` für lokale Tests

2.  **Authentifizierungswerte** (aus den Voraussetzungen):

    -   `REPLACE_WITH_YOUR_CLIENT_ID` → Ihre Azure App Registration Client ID
    -   `REPLACE_WITH_YOUR_CLIENT_SECRET` → Ihr Azure App Registration Client Secret
    -   `REPLACE_WITH_YOUR_TENANT_ID` → Ihre Azure Tenant ID

3.  **KI-Modellzugriff** (Swiss LLM Cloud — erforderlich für Nicht-GPU-Deployments):

    -   `REPLACE_WITH_SWISS_LLM_CLOUD_URL` → Ihr Swiss LLM Cloud Textgenerierungs-Endpoint
    -   `REPLACE_WITH_SWISS_LLM_CLOUD_KEY` → Ihr Swiss LLM Cloud API-Schlüssel
    -   Konfigurieren Sie die verbleibenden Endpoint-Paare für Embedding, Reranking, Whisper und OCR

4.  **Experten-Eskalation** (optional — für Expert-in-the-Loop-Funktionen):

    -   `REPLACE_WITH_TEAMS_CHANNEL_ID` → Ihre Teams Kanal-ID (Format: `19:xxx@thread.tacv2`)
    -   `REPLACE_WITH_TEAMS_TENANT_ID` → Ihre Azure AD Tenant ID
    -   `REPLACE_WITH_TEAMS_BOT_ID` → Ihre Azure Bot Service Anwendungs-ID

::: info Vereinfachte Konfiguration
Interne Service-Endpoints (wie Datenbank-URLs, Message Queues usw.) sind in den Docker Compose-Dateien fest kodiert. Sie müssen lediglich Anmeldeinformationen und externe Service-Verbindungen konfigurieren. Alle Datenbankpasswörter, Tokens und Signierschlüssel werden automatisch von `setup-env.sh` generiert.
:::

### Umgebungsvalidierung

Vor dem Deployment, überprüfen Sie Ihre Konfiguration:

```bash
# Nach Platzhalterwerten suchen, die noch ersetzt werden müssen
grep -n "REPLACE_WITH" .env
```

Dies sollte keine Ergebnisse liefern, wenn alle Platzhalter ersetzt wurden.

______________________________________________________________________

## Schritt 3: Plattform deployen

### Alle Services starten

Deployen Sie die komplette Plattform mit einem Befehl:

**Für die Produktion (Release-Bundle):**

```bash
docker compose up -d
```

Dieser Befehl wird:

-   Alle notwendigen Docker Images herunterladen
-   Erforderliche Netzwerke und Volumes erstellen
-   Alle Plattform-Services in der richtigen Reihenfolge starten
-   Service Discovery und Kommunikation konfigurieren

### Deployment-Fortschritt überwachen

Beobachten Sie den Deployment-Fortschritt:

```bash
# Alle startenden Services anzeigen
docker compose logs -f

# Den Service-Health-Status überprüfen
docker compose ps
```

**Erwartete Services:** Die Plattform umfasst diese Kern-Services:

-   **Web-Interface** (swiss-ai-hub-web)
-   **API** (swiss-ai-hub-api)
-   **Authentifizierung** (Auth-Services)
-   **Datenbanken** (FerretDB, PostgreSQL, Valkey)
-   **Vektor-Datenbank** (Milvus)
-   **LLM-Proxy** (LiteLLM)
-   **Dokumentenverarbeitung** (MinerU)
-   **Observability** (Langfuse)
-   **Message Queue** (NATS)
-   **Speicher** (SeaweedFS)

### Auf Service-Initialisierung warten

Der initiale Start dauert 3-5 Minuten, während die Services initialisiert werden. Alle Services sollten den Status "healthy" anzeigen:

```bash
# Auf "healthy" Status warten
docker compose ps --format "table {{.Name}}\t{{.Status}}"
```

______________________________________________________________________

## Schritt 4: Erfolgreiches Deployment überprüfen

### Auf die Plattform zugreifen

1.  **Stellen Sie sicher, dass Ihr Testbenutzer die Rollen "AIHubAdmin" und "AIHubSysAdmin" in der Azure Enterprise Application zugewiesen bekommen hat.**

2.  **Web-Interface:**

    -   Produktion: `https://your-domain.com`

3.  **Erwarteter Login-Workflow:**

    -   Leitet zur Azure-Authentifizierung um
    -   Nach dem Login kehrt er zur Swiss AI Hub-Oberfläche zurück
    -   Sollte das Haupt-Dashboard anzeigen
