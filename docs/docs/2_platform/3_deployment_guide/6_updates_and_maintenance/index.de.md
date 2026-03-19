---
title: Updates & Wartung
source_sha: 4c9c2715d35722080da9fe3ab465405fd5728ae5dbaea8631baa861b4ee342b3
---

# Updates und Wartung

## Architektur

Der Swiss AI Hub trennt die Kernplattform-Komponenten vom kundenspezifischen Code. Die Kernplattform (dieses Repository)
enthält gemeinsame Basiskomponenten wie API, Web, Dagster und Bot. Kunden-Repositories enthalten benutzerdefinierte
Agents, Pipelines und Prozesse. Beide verwenden eine unabhängige semantische Versionierung und können separat
aktualisiert werden.

Kunden-Code bindet an eine spezifische Kernversion über `pyproject.toml`:

```toml
[project.dependencies]
swiss-ai-hub = { git = "https://github.com/bbvch-ai/aihub-core.git", tag = "v1.2.3" }
```

Dies bedeutet, dass Kern-Updates Kunden-Deployments nicht automatisch beeinflussen. Kunden steuern, wann sie neue
Kernversionen übernehmen.

______________________________________________________________________

## Versionierung

Die Kernplattform verwendet semantische Versionierung:

- Major (X.0.0): Breaking Changes und architektonische Updates
- Minor (0.X.0): Neue Features, abwärtskompatible Änderungen
- Patch (0.0.X): Bugfixes und Sicherheitspatches

Drei Versions-Tags sind verfügbar:

| Tag       | Beschreibung                | Stabilität |
| --------- | --------------------------- | ---------- |
| `latest`  | Neueste stabile Version     | Hoch       |
| `nightly` | Neuester Entwicklungs-Build | Mittel     |
| `v1.2.3`  | Spezifischer Versions-Tag   | Höchste    |

Kunden-Code verwendet eigene unabhängige Versionsnummern.

### Release-Prozess

Wenn ein PR mit einem Versions-Label (`major`, `minor` oder `patch`) in `main` zusammengeführt wird, berechnet CI/CD die
neue Version, erstellt einen Git-Tag und erstellt alle betroffenen Services. Docker-Images werden mit dem Versions-Tag
auf `ghcr.io/bbvch-ai/aihub-core/*` veröffentlicht. Ein Changelog wird automatisch generiert.

Jede Version veröffentlicht auch eigenständige Deployment-Bundles als GitHub Release Assets:

- `swissaihub-<version>.tar.gz` — Deployment-Bundle nur für CPU
- `swissaihub-<version>-gpu.tar.gz` — Deployment-Bundle mit GPU-Unterstützung

Diese Bundles enthalten alles, was für das Deployment benötigt wird: `docker-compose.yml` mit versionsgebundenen
Image-Tags, alle Service-Konfigurationsdateien, eine `.env.template` mit Platzhalter-Secrets und ein
`setup-env.sh`-Skript, das eine `.env`-Datei mit kryptografisch sicheren Zufallswerten für alle Passwörter, Tokens und
Signierschlüssel generiert.

Beispiel Kern-Images:

```
ghcr.io/bbvch-ai/aihub-core/api:v1.2.3
ghcr.io/bbvch-ai/aihub-core/dagster:v1.2.3
ghcr.io/bbvch-ai/aihub-core/web:v1.2.3
```

Kunden-Code folgt dem gleichen CI/CD-Muster:

```
ghcr.io/bbvch-ai/aihub-core-<customer>/agent:v1.2.3
ghcr.io/bbvch-ai/aihub-core-<customer>/pipeline:v1.2.3
```

Alle Releases durchsuchen unter
[github.com/bbvch-ai/aihub-core/releases](https://github.com/bbvch-ai/aihub-core/releases).

______________________________________________________________________

## Updates

### Kernplattform-Updates

Laden Sie das neue Release-Bundle von [GitHub Releases](https://github.com/bbvch-ai/aihub-core/releases) herunter und
entpacken Sie es neben Ihrem aktuellen Deployment:

```bash
# Download the new version
VERSION="v1.3.0"
curl -L "https://github.com/bbvch-ai/aihub-core/releases/download/${VERSION}/swissaihub-${VERSION}.tar.gz" \
  | tar -xz -C /tmp/swissaihub-update

# Copy your existing .env into the new bundle
cp .env /tmp/swissaihub-update/.env

# Review any new environment variables added in the release
diff <(grep -oP '^[A-Z_]+=' .env.template) <(grep -oP '^[A-Z_]+=' /tmp/swissaihub-update/.env.template)

# Replace the deployment files
cp -r /tmp/swissaihub-update/* .

# Pull new images and restart
docker compose pull
docker compose up -d
```

Abwärtskompatible Updates (Patch- und Minor-Versionen) erfordern lediglich das Pulling neuer Images und einen Neustart.
Das `docker-compose.yml` des Release-Bundles verweist bereits auf die korrekten versionsgebundenen Image-Tags.
Kunden-Code läuft unverändert weiter.

Große Kern-Updates mit Breaking Changes erfordern koordinierte Updates. Der Kunden-Code muss aktualisiert werden, um mit
der neuen Kernversion zu funktionieren. Sowohl der Kern- als auch der Kunden-Code werden gemeinsam während eines
Wartungsfensters aktualisiert.

### Kunden-Code-Updates

Kunden-Code kann unabhängig aktualisiert werden, wenn der Kernversions-Pin unverändert bleibt. Aktualisieren Sie die
Kunden-Image-Tags in `docker-compose.yml`, ziehen Sie die neuen Images und starten Sie die Kunden-Services neu.

Wenn Kunden-Code eine neue Kernversion übernimmt, aktualisieren Sie den Kernversions-Pin in `pyproject.toml`, erstellen
Sie die Kunden-Images neu und deployen Sie dann sowohl Kern- als auch Kunden-Updates zusammen.

______________________________________________________________________

## Rollbacks

### VM-Snapshots

VM-Snapshots erfassen den gesamten Systemzustand. Ein Rollback stellt die komplette VM von einem Pre-Update-Snapshot
wieder her und versetzt alle Services gleichzeitig in ihren vorherigen Zustand zurück.

### Versions-Tags

Wenn Daten mit der vorherigen Version kompatibel bleiben, führen Sie ein Rollback durch, indem Sie das vorherige
Release-Bundle herunterladen, Ihre `.env`-Datei wiederherstellen und neu starten:

```bash
# Download the previous version's bundle
PREVIOUS="v1.2.3"
curl -L "https://github.com/bbvch-ai/aihub-core/releases/download/${PREVIOUS}/swissaihub-${PREVIOUS}.tar.gz" \
  | tar -xz -C /tmp/swissaihub-rollback

# Restore previous compose and configs, keep your .env
cp .env /tmp/swissaihub-rollback/.env
cp -r /tmp/swissaihub-rollback/* .

# Roll back
docker compose pull
docker compose up -d
```

Kern- und Kunden-Code können unabhängig zurückgerollt werden, wenn sie separat aktualisiert wurden. Wenn beide zusammen
aktualisiert wurden, rollen Sie zuerst den Kern, dann den Kunden-Code zurück.

______________________________________________________________________

## Kompatibilität

Kunden-Code bindet an spezifische Kernversionen, um die Stabilität zu gewährleisten. Eine Kompatibilitätsmatrix
verfolgt, welche Kundenversionen mit welchen Kernversionen funktionieren:

| Kundenversion | Kernversion | Status      | Anmerkungen           |
| ------------- | ----------- | ----------- | --------------------- |
| v1.0.0        | v0.1.2      | Legacy      | End of Life           |
| v1.1.0        | v1.2.3      | Unterstützt | Aktuelle Produktion   |
| v1.2.0        | v1.2.3      | Unterstützt | Neueste Features      |
| v2.0.0        | v2.3.4      | Testen      | Nächste Major Release |

Staging-Umgebungen sollten der Produktionsinfrastruktur entsprechen und repräsentative Datensätze für die
Kompatibilitätstests vor Produktions-Updates verwenden.

______________________________________________________________________

## Monitoring

Der Observability Stack umfasst Langfuse für KI-spezifisches Tracing, OpenTelemetry für verteiltes Tracing und optional
SigNoz Cloud für externe Metriken und Logs. Überwachen Sie Kern-Services (API, Web, Dagster) und Kunden-Services
(Agents, Pipelines, Prozesse) während und nach Updates.

______________________________________________________________________

## Verwandte Dokumentation

- [Deployment-Optionen](../1_deployment_options/) – Architektur pro Instanz
- [Multi-Tenancy](../../16_multi_tenancy/) – Logische Trennung innerhalb von Instanzen
- [Backup und Wiederherstellung](../4_backup_and_recovery/) – Backup-Strategien
- [Kernkomponenten](../../2_architecture/1_core_components/) – Komponentenabhängigkeiten
