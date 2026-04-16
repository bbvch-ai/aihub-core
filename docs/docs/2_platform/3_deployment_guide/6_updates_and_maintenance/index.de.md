---
title: Updates & Wartung
source_sha: "1f9207ec4a660fbeb24e59852eed720810b3c7ad95c7b833091ace7f68607fc5"
---

# Updates und Wartung

## Architektur

Der Swiss AI Hub trennt Kernplattformkomponenten von kundenspezifischem Code. Die Kernplattform (dieses Repository) enthält gemeinsam genutzte Basiskomponenten wie API, Web, Dagster und Bot. Kunden-Repositories enthalten benutzerdefinierte Agents, Pipelines und Prozesse. Beide verwenden unabhängige semantische Versionierung und können separat aktualisiert werden.

Kundencode wird über `pyproject.toml` an eine spezifische Kernversion gebunden:

```toml
[project.dependencies]
swiss-ai-hub = { git = "https://github.com/bbvch-ai/aihub-core.git", tag = "v1.2.3" }
```

Das bedeutet, dass Kern-Updates Kunden-Deployments nicht automatisch beeinflussen. Kunden steuern, wann sie neue Kernversionen übernehmen.

______________________________________________________________________

## Versionierung

Die Kernplattform verwendet semantische Versionierung:

- Major (X.0.0): Breaking Changes und Architektur-Updates
- Minor (0.X.0): Neue Features, abwärtskompatible Änderungen
- Patch (0.0.X): Bugfixes und Sicherheitspatches

Drei Versions-Tags sind verfügbar:

| Tag       | Beschreibung                | Stabilität |
| --------- | --------------------------- | ---------- |
| `latest`  | Neueste stabile Version     | Hoch       |
| `nightly` | Neuester Entwicklungs-Build | Mittel     |
| `v1.2.3`  | Spezifischer Versions-Tag   | Höchst     |

Kundencode verwendet eigene, unabhängige Versionsnummern.

### Release-Prozess

Wenn ein PR mit einem Versionslabel (`major`, `minor` oder `patch`) in `main` zusammengeführt wird, berechnet CI/CD die neue Version, erstellt einen Git-Tag und erstellt alle betroffenen Services. Docker-Images werden mit dem Versions-Tag in `ghcr.io/bbvch-ai/aihub-core/*` veröffentlicht. Ein Changelog wird automatisch generiert.

Jedes Release veröffentlicht auch eigenständige Deployment-Bundles als GitHub Release Assets:

- `swissaihub-<version>.tar.gz` — CPU-only Deployment-Bundle
- `swissaihub-<version>-gpu.tar.gz` — GPU-fähiges Deployment-Bundle

Diese Bundles enthalten alles, was für ein Deployment benötigt wird: `docker-compose.yml` mit an die Version gebundenen Image-Tags, alle Service-Konfigurationsdateien, eine `.env.template` mit Platzhalter-Secrets und ein `setup-env.sh`-Skript, das eine `.env`-Datei mit kryptografisch sicheren Zufallswerten für alle Passwörter, Tokens und Signierschlüssel generiert.

Beispiel Kern-Images:

```
ghcr.io/bbvch-ai/aihub-core/api:v1.2.3
ghcr.io/bbvch-ai/aihub-core/dagster:v1.2.3
ghcr.io/bbvch-ai/aihub-core/web:v1.2.3
```

Kundencode folgt dem gleichen CI/CD-Muster:

```
ghcr.io/bbvch-ai/aihub-core-<customer>/agent:v1.2.3
ghcr.io/bbvch-ai/aihub-core-<customer>/pipeline:v1.2.3
```

Alle Releases finden Sie unter [github.com/bbvch-ai/aihub-core/releases](https://github.com/bbvch-ai/aihub-core/releases).

______________________________________________________________________

## Updates

### Kernplattform-Updates

Laden Sie das neue Release-Bundle von [GitHub Releases](https://github.com/bbvch-ai/aihub-core/releases) herunter und entpacken Sie es neben Ihrem aktuellen Deployment:

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

Abwärtskompatible Updates (Patch- und Minor-Versionen) erfordern lediglich das Pulling neuer Images und einen Neustart. Die `docker-compose.yml` des Release-Bundles referenziert bereits die korrekten, an die Version gebundenen Image-Tags. Kundencode läuft unverändert weiter.

Major Core-Updates mit Breaking Changes erfordern koordinierte Updates. Kundencode muss aktualisiert werden, um mit der neuen Kernversion zu funktionieren. Sowohl Kern- als auch Kundencode werden gemeinsam während eines Wartungsfensters aktualisiert.

### Kundencode-Updates

Kundencode kann unabhängig aktualisiert werden, wenn die Kernversionsbindung unverändert bleibt. Aktualisieren Sie die Kundencode-Image-Tags in `docker-compose.yml`, pullen Sie die neuen Images und starten Sie die Kundenservices neu.

Wenn Kundencode eine neue Kernversion übernimmt, aktualisieren Sie die Kernversionsbindung in `pyproject.toml`, erstellen Sie die Kundencode-Images neu und deployen Sie dann sowohl Kern- als auch Kundencode-Updates gemeinsam.

______________________________________________________________________

## Rollbacks

### VM-Snapshots

VM-Snapshots erfassen den gesamten Systemzustand. Ein Rollback stellt die komplette VM von einem Pre-Update-Snapshot wieder her und versetzt alle Services gleichzeitig in ihren vorherigen Zustand zurück.

### Versions-Tags

Wenn die Daten mit der vorherigen Version kompatibel bleiben, führen Sie ein Rollback durch, indem Sie das vorherige Release-Bundle herunterladen, Ihre `.env`-Datei wiederherstellen und neu starten:

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

Kern- und Kundencode können unabhängig voneinander zurückgesetzt werden, wenn sie separat aktualisiert wurden. Wenn beide gemeinsam aktualisiert wurden, setzen Sie zuerst den Kern, dann den Kundencode zurück.

______________________________________________________________________

## Kompatibilität

Kundencode ist an spezifische Kernversionen gebunden, um Stabilität zu gewährleisten. Eine Kompatibilitätsmatrix verfolgt, welche Kundenversionen mit welchen Kernversionen funktionieren:

| Kundenversion | Kernversion | Status      | Hinweise             |
| ------------- | ----------- | ----------- | -------------------- |
| v1.0.0        | v0.1.2      | Veraltet    | End of Life          |
| v1.1.0        | v1.2.3      | Unterstützt | Aktuelle Produktion  |
| v1.2.0        | v1.2.3      | Unterstützt | Neueste Funktionen   |
| v2.0.0        | v2.3.4      | Testphase   | Nächstes Major Release |

Staging-Umgebungen sollten der Produktionsinfrastruktur entsprechen und repräsentative Datensätze verwenden, um die Kompatibilität vor Produktions-Updates zu testen.

______________________________________________________________________

## Monitoring

Der Observability-Stack umfasst Langfuse für KI-spezifisches Tracing, OpenTelemetry für verteiltes Tracing und optional SigNoz Cloud für externe Metriken und Logs. Überwachen Sie Kern-Services (API, Web, Dagster) und Kunden-Services (Agents, Pipelines, Prozesse) während und nach Updates.

______________________________________________________________________

## Verwandte Dokumentation

- [Deployment-Optionen](/de/docs/1_intro/1_deployment_options/) – Per-Instanz-Architektur
- [Multi-Tenancy](/de/docs/16_multi_tenancy/) – Logische Trennung innerhalb von Instanzen
- [Backup und Wiederherstellung](/de/docs/1_intro/4_backup_and_recovery/) – Backup-Strategien
- [Kernkomponenten](/de/docs/2_architecture/1_core_components/) – Komponentenabhängigkeiten
