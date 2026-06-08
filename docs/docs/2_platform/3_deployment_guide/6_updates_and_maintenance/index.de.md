---
title: Updates & Wartung
source_sha: b734d133a640fe74a2daff07691d6d1cbd8644b4a6502e81cfb95dd37ddeaa84
---

# Updates und Wartung

## Architektur

Der Swiss AI Hub trennt die Kernplattformkomponenten vom kundenspezifischen Code. Die Kernplattform (dieses Repository)
enthält gemeinsame Basiskomponenten wie API, Web, Dagster und Bot. Kunden-Repositories enthalten benutzerdefinierte
Agents, Pipelines und Prozesse. Beide verwenden unabhängige semantische Versionierung und können separat aktualisiert
werden.

Kundenseitiger Code fixiert sich über `pyproject.toml` auf eine bestimmte Core-Version:

```toml
[project.dependencies]
swiss-ai-hub = { git = "https://github.com/bbvch-ai/aihub-core.git", tag = "v1.2.3" }
```

Das bedeutet, dass Core-Updates Kunden-Deployments nicht automatisch beeinflussen. Kunden steuern, wann sie neue
Core-Versionen übernehmen.

______________________________________________________________________

## Versionierung

Die Kernplattform verwendet semantische Versionierung:

- Major (X.0.0): Breaking Changes und Architekturanpassungen
- Minor (0.X.0): Neue Funktionen, abwärtskompatible Änderungen
- Patch (0.0.X): Bugfixes und Sicherheitspatches

Es sind drei Versionstags verfügbar:

| Tag       | Beschreibung                | Stabilität |
| --------- | --------------------------- | ---------- |
| `latest`  | Neueste stabile Version     | Hoch       |
| `nightly` | Neuester Entwicklungs-Build | Mittel     |
| `v1.2.3`  | Spezifischer Versionstag    | Höchste    |

Kundenseitiger Code verwendet eigene, unabhängige Versionsnummern.

### Release-Prozess

Wenn ein PR mit einem Versions-Label (`major`, `minor` oder `patch`) in `main` gemerged wird, berechnet CI/CD die neue
Version, erstellt einen Git-Tag und erstellt alle betroffenen Services. Docker-Images werden mit dem Versionstag unter
`ghcr.io/bbvch-ai/aihub-core/*` veröffentlicht. Ein Changelog wird automatisch generiert.

Jede Version veröffentlicht zudem eigenständige Deployment-Bundles als GitHub Release Assets:

- `swissaihub-<version>.tar.gz` — CPU-only Deployment-Bundle
- `swissaihub-<version>-gpu.tar.gz` — GPU-fähiges Deployment-Bundle

Diese Bundles enthalten alles, was für ein Deployment benötigt wird: `docker-compose.yml` mit versionsgebundenen
Image-Tags, alle Service-Konfigurationsdateien, eine `.env.template` mit Platzhalter-Secrets und ein
`setup-env.sh`-Skript, das eine `.env`-Datei mit kryptographisch sicheren Zufallswerten für alle Passwörter, Tokens und
Signierschlüssel generiert.

Beispiel Core-Images:

```
ghcr.io/bbvch-ai/aihub-core/api:v1.2.3
ghcr.io/bbvch-ai/aihub-core/dagster:v1.2.3
ghcr.io/bbvch-ai/aihub-core/web:v1.2.3
```

Kundenseitiger Code folgt dem gleichen CI/CD-Muster:

```
ghcr.io/bbvch-ai/aihub-core-<customer>/agent:v1.2.3
ghcr.io/bbvch-ai/aihub-core-<customer>/pipeline:v1.2.3
```

Durchsuchen Sie alle Releases unter
[github.com/bbvch-ai/aihub-core/releases](https://github.com/bbvch-ai/aihub-core/releases).

______________________________________________________________________

## Updates

### Core-Plattform-Updates

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
Die `docker-compose.yml` des Release-Bundles referenziert bereits die korrekten versionsgebundenen Image-Tags.
Kundenseitiger Code läuft unverändert weiter.

Major Core-Updates mit Breaking Changes erfordern koordinierte Updates. Kundenseitiger Code muss aktualisiert werden, um
mit der neuen Core-Version zu funktionieren. Sowohl Core- als auch kundenseitiger Code werden während eines
Wartungsfensters gemeinsam aktualisiert.

### Kundenseitige Code-Updates

Kundenseitiger Code kann unabhängig aktualisiert werden, wenn die Core-Versionsfixierung unverändert bleibt.
Aktualisieren Sie die Kunden-Image-Tags in `docker-compose.yml`, ziehen Sie die neuen Images und starten Sie die
Kunden-Services neu.

Wenn kundenseitiger Code eine neue Core-Version übernimmt, aktualisieren Sie die Core-Versionsfixierung in
`pyproject.toml`, erstellen Sie die Kunden-Images neu und deployen Sie dann sowohl Core- als auch Kunden-Updates
zusammen.

______________________________________________________________________

## Rollbacks

### VM-Snapshots

VM-Snapshots erfassen den gesamten Systemzustand. Ein Rollback stellt die komplette VM aus einem Pre-Update-Snapshot
wieder her und setzt alle Services gleichzeitig in ihren vorherigen Zustand zurück.

### Versionstags

Wenn die Daten mit der vorherigen Version kompatibel bleiben, führen Sie ein Rollback durch, indem Sie das vorherige
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

Core- und kundenseitiger Code können unabhängig voneinander zurückgerollt werden, wenn sie separat aktualisiert wurden.
Wenn beide zusammen aktualisiert wurden, rollen Sie zuerst den Core und dann den kundenseitigen Code zurück.

______________________________________________________________________

## Kompatibilität

Kundenseitiger Code fixiert sich auf bestimmte Core-Versionen, um die Stabilität zu gewährleisten. Eine
Kompatibilitätsmatrix verfolgt, welche Kundenversionen mit welchen Core-Versionen funktionieren:

| Kundenversion | Core-Version | Status      | Anmerkungen            |
| ------------- | ------------ | ----------- | ---------------------- |
| v1.0.0        | v0.1.2       | Legacy      | Ende der Unterstützung |
| v1.1.0        | v1.2.3       | Unterstützt | Aktuelle Produktion    |
| v1.2.0        | v1.2.3       | Unterstützt | Neueste Funktionen     |
| v2.0.0        | v2.3.4       | Testphase   | Nächste Major Release  |

Staging-Umgebungen sollten der Produktionsinfrastruktur entsprechen und repräsentative Datensätze verwenden, um die
Kompatibilität vor Produktions-Updates zu testen.

______________________________________________________________________

## Monitoring

Der Observability Stack umfasst Langfuse für KI-spezifisches Tracing, OpenTelemetry für verteiltes Tracing und optional
SigNoz Cloud für externe Metriken und Logs. Überwachen Sie Core-Services (API, Web, Dagster) und Kunden-Services
(Agents, Pipelines, Prozesse) während und nach Updates.

______________________________________________________________________

## Kontinuierliche Postgres-Wartung

Die Plattform beinhaltet eine automatisierte Datenbankwartung, die Operatoren nicht manuell planen müssen. Zwei Jobs
laufen in derselben Dagster-Instanz als Backup (UI unter `http://localhost:3004`) und halten die `dagster`-Datenbank
über die Zeit begrenzt: Das wöchentliche `dagster_cleanup_job` entfernt ausführliche Log-Einträge und temporäre
Framework-Ereignisse aus den `event_logs`, und das monatliche `postgres_repack_job` gibt über `pg_repack` Speicherplatz
auf der Festplatte frei. Beide sind gegenseitig exklusiv mit Backups über die Tag-Concurrency des Dagster
Run-Coordinators.

Das sorgt dafür, dass der Postgres-Footprint eines 5 Jahre alten Deployments mit dem eines 3 Monate alten vergleichbar
bleibt. Siehe [Backup und Wiederherstellung](../4_backup_and_recovery/#continuous-postgres-maintenance) für
Aufbewahrungsfristen und den `MAINTENANCE_DISABLED` Kill-Switch.

______________________________________________________________________

## Verwandte Dokumentation

- [Deployment-Optionen](../1_deployment_options/) – Pro-Instanz-Architektur
- [Multi-Tenancy](../../16_multi_tenancy/) – Logische Trennung innerhalb von Instanzen
- [Backup und Wiederherstellung](../4_backup_and_recovery/) – Backup-Strategien
- [Core-Komponenten](../../../1_vision_and_positioning/3_core_components/) – Komponentenabhängigkeiten
