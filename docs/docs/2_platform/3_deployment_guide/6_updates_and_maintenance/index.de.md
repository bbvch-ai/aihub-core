---
title: Updates & Wartung
source_sha: f9e25c228559bcc945fefdda92dc81bb72e70951fdcddc6803bf83bfb0047d59
---

# Updates und Wartung

## Architektur

Der Swiss AI Hub trennt Kernkomponenten der Plattform von kundenspezifischem Code. Die Kernplattform (dieses Repository)
enthält gemeinsame Basiskomponenten wie API, Web, Dagster und Bot. Kunden-Repositories enthalten kundenspezifische
Agents, Pipelines und Prozesse. Beide verwenden eine unabhängige semantische Versionierung und können separat
aktualisiert werden.

Kundenspezifischer Code verweist über `pyproject.toml` auf eine bestimmte Core-Version:

```toml
[project.dependencies]
swiss-ai-hub = { git = "https://github.com/bbvch-ai/swiss-ai-hub.git", tag = "v1.2.3" }
```

Das bedeutet, Core-Updates wirken sich nicht automatisch auf Kunden-Deployments aus. Kunden steuern, wann sie neue
Core-Versionen übernehmen.

______________________________________________________________________

## Versionierung

Die Core-Plattform verwendet semantische Versionierung:

- Major (X.0.0): Breaking Changes und architektonische Updates
- Minor (0.X.0): Neue Features, abwärtskompatible Änderungen
- Patch (0.0.X): Bugfixes und Sicherheitspatches

Drei Versionstags sind verfügbar:

| Tag       | Beschreibung                   | Stabilität |
| --------- | ------------------------------ | ---------- |
| `latest`  | Aktuellste stabile Version     | Hoch       |
| `nightly` | Aktuellster Entwicklungs-Build | Mittel     |
| `v1.2.3`  | Spezifischer Versionstag       | Höchst     |

Kundenspezifischer Code verwendet eigene, unabhängige Versionsnummern.

### Release-Prozess

Wenn ein PR mit einem Versionslabel (`major`, `minor` oder `patch`) in `main` gemergt wird, berechnet CI/CD die neue
Version, erstellt einen Git-Tag und baut alle betroffenen Services. Docker-Images werden mit dem Versionstag nach
`ghcr.io/bbvch-ai/swiss-ai-hub/*` veröffentlicht. Ein Changelog wird automatisch generiert.

Jeder Release veröffentlicht außerdem eigenständige Deployment-Bundles als GitHub Release Assets:

- `swissaihub-<version>.tar.gz` — Nur-CPU-Deployment-Bundle
- `swissaihub-<version>-gpu.tar.gz` — GPU-fähiges Deployment-Bundle

Diese Bundles enthalten alles, was für das Deployment benötigt wird: `docker-compose.yml` mit versionsgebundenen
Image-Tags, alle Service-Konfigurationsdateien, eine `.env.template` mit Platzhalter-Secrets und ein
`setup-env.sh`-Skript, das eine `.env`-Datei mit kryptografisch sicheren Zufallswerten für alle Passwörter, Tokens und
Signierschlüssel generiert.

Beispiel Core-Images:

```
ghcr.io/bbvch-ai/swiss-ai-hub/api:v1.2.3
ghcr.io/bbvch-ai/swiss-ai-hub/dagster:v1.2.3
ghcr.io/bbvch-ai/swiss-ai-hub/web:v1.2.3
```

Kundenspezifischer Code folgt dem gleichen CI/CD-Muster:

```
ghcr.io/bbvch-ai/swiss-ai-hub-<customer>/agent:v1.2.3
ghcr.io/bbvch-ai/swiss-ai-hub-<customer>/pipeline:v1.2.3
```

Alle Releases durchsuchen unter
[github.com/bbvch-ai/swiss-ai-hub/releases](https://github.com/bbvch-ai/swiss-ai-hub/releases).

______________________________________________________________________

## Updates

### Core-Plattform-Updates

Laden Sie das neue Release-Bundle von [GitHub Releases](https://github.com/bbvch-ai/swiss-ai-hub/releases) herunter und
entpacken Sie es neben Ihrem aktuellen Deployment:

```bash
# Download the new version
VERSION="v1.3.0"
curl -L "https://github.com/bbvch-ai/swiss-ai-hub/releases/download/${VERSION}/swissaihub-${VERSION}.tar.gz" \
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
Die `docker-compose.yml` des Release-Bundles verweist bereits auf die korrekten versionsgebundenen Image-Tags.
Kundenspezifischer Code läuft unverändert weiter.

Major Core-Updates mit Breaking Changes erfordern koordinierte Updates. Kundenspezifischer Code muss aktualisiert
werden, um mit der neuen Core-Version zu funktionieren. Sowohl Core- als auch Kundencode werden gemeinsam während eines
Wartungsfensters aktualisiert.

### Updates für kundenspezifischen Code

Kundenspezifischer Code kann unabhängig aktualisiert werden, solange die Core-Versionsbindung unverändert bleibt.
Aktualisieren Sie die Kunden-Image-Tags in `docker-compose.yml`, pullen Sie die neuen Images und starten Sie die
Kunden-Services neu.

Wenn kundenspezifischer Code eine neue Core-Version übernimmt, aktualisieren Sie die Core-Versionsbindung in
`pyproject.toml`, bauen Sie die Kunden-Images neu und deployen Sie dann Core- und Kunden-Updates gemeinsam.

______________________________________________________________________

## Rollbacks

### VM-Snapshots

VM-Snapshots erfassen den gesamten Systemzustand. Ein Rollback stellt die komplette VM von einem Pre-Update-Snapshot
wieder her und versetzt alle Services gleichzeitig in ihren vorherigen Zustand zurück.

### Versionstags

Wenn Daten mit der vorherigen Version kompatibel bleiben, führen Sie ein Rollback durch, indem Sie das vorherige
Release-Bundle herunterladen, Ihre `.env`-Datei wiederherstellen und neu starten:

```bash
# Download the previous version's bundle
PREVIOUS="v1.2.3"
curl -L "https://github.com/bbvch-ai/swiss-ai-hub/releases/download/${PREVIOUS}/swissaihub-${PREVIOUS}.tar.gz" \
  | tar -xz -C /tmp/swissaihub-rollback

# Restore previous compose and configs, keep your .env
cp .env /tmp/swissaihub-rollback/.env
cp -r /tmp/swissaihub-rollback/* .

# Roll back
docker compose pull
docker compose up -d
```

Core- und Kundencode können unabhängig zurückgerollt werden, wenn sie separat aktualisiert wurden. Wenn beide gemeinsam
aktualisiert wurden, rollen Sie zuerst den Core und dann den Kundencode zurück.

______________________________________________________________________

## Kompatibilität

Kundenspezifischer Code ist an bestimmte Core-Versionen gebunden, um Stabilität zu gewährleisten. Eine
Kompatibilitätsmatrix verfolgt, welche Kundenversionen mit welchen Core-Versionen funktionieren:

| Kundenversion | Core-Version | Status      | Anmerkungen            |
| ------------- | ------------ | ----------- | ---------------------- |
| v1.0.0        | v0.1.2       | Legacy      | Ende des Supports      |
| v1.1.0        | v1.2.3       | Unterstützt | Aktuelle Produktion    |
| v1.2.0        | v1.2.3       | Unterstützt | Neueste Features       |
| v2.0.0        | v2.3.4       | Testphase   | Nächster Major-Release |

Staging-Umgebungen sollten der Produktionsinfrastruktur entsprechen und repräsentative Datensätze verwenden, um die
Kompatibilität vor Produktions-Updates zu testen.

______________________________________________________________________

## Monitoring

Der Observability Stack umfasst Langfuse für KI-spezifisches Tracing, OpenTelemetry für verteiltes Tracing und optional
SigNoz Cloud für externe Metriken und Logs. Überwachen Sie Core-Services (API, Web, Dagster) und Kunden-Services
(Agents, Pipelines, Prozesse) während und nach Updates.

______________________________________________________________________

## Zugehörige Dokumentation

- [Deployment-Optionen](../1_deployment_options/) - Per-Instanz-Architektur
- [Multi-Tenancy](../../16_multi_tenancy/) - Logische Trennung innerhalb von Instanzen
- [Backup und Wiederherstellung](../4_backup_and_recovery/) - Backup-Strategien
- [Core-Komponenten](../../2_architecture/1_core_components/) - Komponentenabhängigkeiten
