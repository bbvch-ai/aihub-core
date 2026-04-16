---
title: Ein-Befehl-Deployment
source_sha: 9f8cf565b7a2c3695fcd417f6a8c1830e51da3ab76b1d519c6505af8f7e31e8a
---

# Ein-Befehl-Deployment: Starten Sie Ihre KI-Plattform

Die Swiss AI Hub Plattform wird mit einem einzigen Docker Compose Befehl deployt. Dieser optimierte Prozess lässt Ihre
vollständige KI-Infrastruktur in Minutenschnelle, nicht stundenlang, laufen.

## Schnellinstallation

Führen Sie einen einzigen Befehl aus, um die Plattform herunterzuladen, zu entpacken und einzurichten:

```bash
curl -fsSL https://raw.githubusercontent.com/bbvch-ai/aihub-core/main/install.sh | bash
```

Der Installer erkennt automatisch GPU-Hardware, lädt das richtige Release-Bundle herunter und generiert alle Secrets.
Danach bearbeiten Sie `.env` und führen `docker compose up -d` aus.

| Flag                | Default          | Beschreibung                     |
| :------------------ | :--------------- | :------------------------------- |
| `--version VERSION` | latest           | An ein bestimmtes Release pinnen |
| `--gpu`             | auto-detect      | GPU-Bundle erzwingen             |
| `--cpu`             | auto-detect      | Nur-CPU-Bundle erzwingen         |
| `--dir PATH`        | `./swiss-ai-hub` | Installationsverzeichnis         |
| `--help`            |                  | Nutzung anzeigen                 |

**Beispiele:**

```bash
# Mit GPU-Bundle in ein benutzerdefiniertes Verzeichnis installieren
curl -fsSL https://raw.githubusercontent.com/bbvch-ai/aihub-core/main/install.sh | bash -s -- --gpu --dir /opt/swiss-ai-hub

# Eine bestimmte Version pinnen
curl -fsSL https://raw.githubusercontent.com/bbvch-ai/aihub-core/main/install.sh | bash -s -- --version v0.269.2
```

**Upgrade:** Führen Sie den Installer erneut mit demselben `--dir` aus. Er erkennt die bestehende Installation, sichert
Ihre `.env`-Datei, ersetzt Bundle-Dateien, stellt die `.env`-Datei wieder her und meldet alle neuen Umgebungsvariablen,
die im Release hinzugefügt wurden.

______________________________________________________________________

## Bereitstellungsübersicht

::: tip Zwei Deployment-Optionen
Der Swiss AI Hub unterstützt zwei Deployment-Modi. Befolgen Sie für beide die gleichen Schritte und verwenden Sie die
entsprechenden Befehle für Ihren Deployment-Typ:

- **Produktions-Deployment**: Deployen Sie auf einem Server mit einem echten Domainnamen (z.B.
  `swiss-ai-hub.yourcompany.com`)
  - Verwendet das CPU- oder GPU-Release-Bundle von GitHub Releases
  - Verwendet Let's Encrypt für automatische SSL-Zertifikate
  - Erfordert eine DNS-Konfiguration, die auf Ihren Server zeigt
- **Lokales Deployment**: Auf Ihrer lokalen Maschine für Entwicklung/Tests ausführen
  - Verwendet `infra/docker-compose.local.yml` aus dem Repository
  - Verwendet selbstsignierte SSL-Zertifikate (mkcert)
  - Verwendet die Domain `127.0.0.1.nip.io` (löst sich automatisch zu localhost auf)

Jeder Schritt unten zeigt Befehle für beide Deployment-Typen. Befolgen Sie einfach die Befehle, die Ihrem gewählten
Deployment-Modus entsprechen.
:::

______________________________________________________________________

## Schritt 1: Deployment-Dateien herunterladen

**Für die Produktion:**

Laden Sie das neueste Release-Bundle von [GitHub Releases](https://github.com/bbvch-ai/aihub-core/releases) herunter.
Jedes Release bietet zwei eigenständige Bundles:

- `swissaihub-<version>.tar.gz` — Nur-CPU-Deployment
- `swissaihub-<version>-gpu.tar.gz` — GPU-fähiges Deployment (inklusive vLLM, GPU-beschleunigte Inferenz)

```bash
# Legen Sie die Version fest, die Sie deployen möchten
VERSION="v0.266.0"  # Ersetzen Sie dies durch die gewünschte Version

# Laden Sie das Release-Bundle herunter und entpacken Sie es (CPU-Beispiel)
mkdir swiss-ai-hub && cd swiss-ai-hub
curl -L "https://github.com/bbvch-ai/aihub-core/releases/download/${VERSION}/swissaihub-${VERSION}.tar.gz" \
  | tar -xz

# Für ein GPU-fähiges Deployment verwenden Sie stattdessen:
# curl -L "https://github.com/bbvch-ai/aihub-core/releases/download/${VERSION}/swissaihub-${VERSION}-gpu.tar.gz" \
#   | tar -xz
```

Das Release-Bundle enthält alles Notwendige für das Deployment: `docker-compose.yml`, alle
Service-Konfigurationsdateien, eine `.env.template` und das `setup-env.sh`-Skript.

**Für lokales Deployment:**

```bash
# Repository klonen
git clone https://github.com/bbvch-ai/aihub-core.git
cd swiss-ai-hub

# SSL-Zertifikate mit mkcert generieren
mkcert -install  # Lokale CA installieren (nur einmalig erforderlich)
make local-cert
```

::: tip Was ist nip.io?
Die Domain `*.127.0.0.1.nip.io` löst sich automatisch zu Ihrem Localhost (127.0.0.1) auf und bietet eine
Wildcard-DNS-Auflösung, ohne dass Sie Ihre Hosts-Datei ändern müssen. Dies ermöglicht Subdomain-basiertes Routing in der
lokalen Entwicklung.
:::

______________________________________________________________________

## Schritt 2: Umgebungsvariablen konfigurieren

### Umgebungskonfiguration generieren

**Für die Produktion (Release-Bundle):**

Das Release-Bundle enthält ein `setup-env.sh`-Skript, das eine `.env`-Datei aus der enthaltenen `.env.template`
generiert. Es erstellt automatisch einzigartige Secrets für alle Datenbankpasswörter, Tokens und Signierschlüssel:

```bash
# .env mit automatisch generierten Secrets erstellen
./setup-env.sh
```

::: details Was macht setup-env.sh?
Das Skript liest `.env.template` und ersetzt alle `REPLACE_WITH_*` Platzhalter durch kryptographisch sichere
Zufallswerte. Jeder Platzhalter erhält sein eigenes einzigartiges Secret. Das Skript benötigt nur `openssl` und `bash` –
keine Python- oder andere Abhängigkeiten.

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

Nachdem Sie Ihre `.env`-Datei generiert haben, überprüfen Sie diese und füllen Sie die Werte aus, die eine manuelle
Konfiguration erfordern:

**Kritische Werte zum Ersetzen:**

1. **Domain** — Setzen Sie `DOMAIN` auf Ihre Produktionsdomain (z.B. `swiss-ai-hub.yourcompany.com`) oder auf
   `127.0.0.1.nip.io` für lokale Tests

2. **Authentifizierungswerte** (aus den Voraussetzungen):

   - `REPLACE_WITH_YOUR_CLIENT_ID` → Ihre Azure App Registration Client ID
   - `REPLACE_WITH_YOUR_CLIENT_SECRET` → Ihr Azure App Registration Client Secret
   - `REPLACE_WITH_YOUR_TENANT_ID` → Ihre Azure Tenant ID

3. **Zugriff auf KI-Modelle** (Swiss LLM Cloud — für Nicht-GPU-Deployments erforderlich):

   - `REPLACE_WITH_SWISS_LLM_CLOUD_URL` → Ihr Swiss LLM Cloud Endpunkt für Textgenerierung
   - `REPLACE_WITH_SWISS_LLM_CLOUD_KEY` → Ihr Swiss LLM Cloud API-Schlüssel
   - Konfigurieren Sie die verbleibenden Endpunktpaare für Embedding, Reranking, Whisper und OCR

4. **Experten-Eskalation** (optional — für Expert-in-the-Loop-Funktionen):

   - `REPLACE_WITH_TEAMS_CHANNEL_ID` → Ihre Teams Channel ID (Format: `19:xxx@thread.tacv2`)
   - `REPLACE_WITH_TEAMS_TENANT_ID` → Ihre Azure AD Tenant ID
   - `REPLACE_WITH_TEAMS_BOT_ID` → Ihre Azure Bot Service Anwendungs-ID

::: info Vereinfachte Konfiguration
Interne Service-Endpunkte (wie Datenbank-URLs, Message Queues usw.) sind in den Docker Compose Dateien fest codiert. Sie
müssen nur Anmeldeinformationen und externe Serviceverbindungen konfigurieren. Alle Datenbankpasswörter, Tokens und
Signierschlüssel werden automatisch von `setup-env.sh` generiert.
:::

### Umgebungsvalidierung

Vor dem Deployment überprüfen Sie Ihre Konfiguration:

```bash
# Auf Platzhalterwerte prüfen, die noch ersetzt werden müssen
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

- Alle notwendigen Docker-Images herunterladen
- Erforderliche Netzwerke und Volumes erstellen
- Alle Plattform-Services in der richtigen Reihenfolge starten
- Service Discovery und Kommunikation konfigurieren

### Deployment-Fortschritt überwachen

Beobachten Sie den Deployment-Fortschritt:

```bash
# Alle Services beim Starten beobachten
docker compose logs -f

# Service-Gesundheitsstatus prüfen
docker compose ps
```

**Erwartete Services:** Die Plattform umfasst diese Kernservices:

- **Web-Oberfläche** (swiss-ai-hub-web)
- **API** (swiss-ai-hub-api)
- **Authentifizierung** (auth services)
- **Datenbanken** (FerretDB, PostgreSQL, Valkey)
- **Vektor-Datenbank** (Milvus)
- **LLM Proxy** (LiteLLM)
- **Dokumentenverarbeitung** (MinerU)
- **Observability** (Langfuse)
- **Nachrichtenwarteschlange** (NATS)
- **Speicher** (SeaweedFS)

### Warten auf Service-Initialisierung

Der anfängliche Start dauert 3-5 Minuten, während die Services initialisiert werden. Alle Services sollten den Status
„healthy“ anzeigen:

```bash
# Auf den Status „healthy“ warten
docker compose ps --format "table {{.Name}}\t{{.Status}}"
```

______________________________________________________________________

## Schritt 4: Erfolgreiches Deployment überprüfen

### Auf die Plattform zugreifen

1. **Stellen Sie sicher, dass Ihr Benutzer, mit dem Sie testen, die Rollen "AIHubAdmin" und "AIHubSysAdmin" in der Azure
   Enterprise Application zugewiesen bekommen hat**

2. **Web-Oberfläche:**

   - Produktion: `https://your-domain.com`

3. **Erwarteter Login-Flow:**

   - Leitet zur Azure-Authentifizierung um
   - Nach dem Login kehrt die Benutzeroberfläche des Swiss AI Hub zurück
   - Das Haupt-Dashboard sollte sichtbar sein
