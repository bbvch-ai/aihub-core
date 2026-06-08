---
title: Updates und Wartung
source_sha: 4ef2544a09c137e67593b10e5b04ef342e209ab24b5cad80325536c2e1087de7
---

# Updates und Wartung

## Architektur

Der Swiss AI Hub trennt die Kernplattformkomponenten von kundenspezifischem Code. Die Kernplattform (dieses Repository)
enthält gemeinsame Basiskomponenten wie API, Web, Dagster und Bot. Kunden-Repositories enthalten benutzerdefinierte
Agents, Pipelines und Prozesse. Beide verwenden eine unabhängige semantische Versionierung und können separat
aktualisiert werden.

Kundenspezifischer Code ist über `pyproject.toml` an eine bestimmte Core-Version gebunden:

```toml
[project.dependencies]
swiss-ai-hub = { git = "https://github.com/bbvch-ai/aihub-core.git", tag = "v1.2.3" }
```

Das bedeutet, dass Core-Updates Kunden-Deployments nicht automatisch beeinflussen. Kunden steuern, wann sie neue
Core-Versionen übernehmen.

______________________________________________________________________

## Versionierung

Die Kernplattform verwendet semantische Versionierung:

- Major (X.0.0): Breaking Changes und Architektur-Updates
- Minor (0.X.0): Neue Features, abwärtskompatible Änderungen
- Patch (0.0.X): Bugfixes und Sicherheits-Patches

Drei Versionstags sind verfügbar:

| Tag       | Beschreibung               | Stabilität |
| --------- | -------------------------- | ---------- |
| `latest`  | Neueste stabile Version    | Hoch       |
| `nightly` | Neuster Entwicklungs-Build | Mittel     |
| `v1.2.3`  | Spezifischer Versionstag   | Höchste    |

Kundenspezifischer Code verwendet eigene, unabhängige Versionsnummern.

### Release-Prozess

Wenn ein PR mit einem Versionslabel (`major`, `minor` oder `patch`) in `main` gemerged wird, berechnet CI/CD die neue
Version, erstellt einen Git-Tag und baut alle betroffenen Services. Docker-Images werden mit dem Versionstag nach
`ghcr.io/bbvch-ai/aihub-core/*` veröffentlicht. Ein Changelog wird automatisch generiert.

Jedes Release veröffentlicht auch eigenständige Deployment-Bundles als GitHub Release Assets:

- `swissaihub-<version>.tar.gz` — CPU-only Deployment-Bundle
- `swissaihub-<version>-gpu.tar.gz` — GPU-fähiges Deployment-Bundle

Diese Bundles enthalten alles, was für ein Deployment benötigt wird: `docker-compose.yml` mit versionsgebundenen
Image-Tags, alle Service-Konfigurationsdateien, eine `.env.template` mit Platzhalter-Secrets und ein
`setup-env.sh`-Skript, das eine `.env`-Datei mit kryptografisch sicheren Zufallswerten für alle Passwörter, Tokens und
Signaturschlüssel generiert.

Beispiel Core-Images:

```
ghcr.io/bbvch-ai/aihub-core/api:v1.2.3
ghcr.io/bbvch-ai/aihub-core/dagster:v1.2.3
ghcr.io/bbvch-ai/aihub-core/web:v1.2.3
```

Kundenspezifischer Code folgt dem gleichen CI/CD-Muster:

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
Die `docker-compose.yml` des Release-Bundles verweist bereits auf die korrekten versionsgebundenen Image-Tags.
Kundenspezifischer Code läuft unverändert weiter.

Große Core-Updates mit Breaking Changes erfordern koordinierte Aktualisierungen. Kundenspezifischer Code muss
aktualisiert werden, um mit der neuen Core-Version zu funktionieren. Sowohl Core- als auch kundenspezifischer Code
werden gemeinsam während eines Wartungsfensters aktualisiert.

### Updates des kundenspezifischen Codes

Kundenspezifischer Code kann unabhängig aktualisiert werden, wenn die Core-Versionsbindung unverändert bleibt.
Aktualisieren Sie die Image-Tags des Kunden in `docker-compose.yml`, pullen Sie die neuen Images und starten Sie die
Kunden-Services neu.

Wenn kundenspezifischer Code eine neue Core-Version übernimmt, aktualisieren Sie die Core-Versionsbindung in
`pyproject.toml`, bauen Sie die Kunden-Images neu, und deployen Sie dann sowohl Core- als auch Kunden-Updates zusammen.

______________________________________________________________________

## Rollbacks

### VM-Snapshots

VM-Snapshots erfassen den gesamten Systemzustand. Ein Rollback stellt die komplette VM von einem Pre-Update-Snapshot
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

Core- und kundenspezifischer Code können unabhängig voneinander zurückgerollt werden, wenn sie separat aktualisiert
wurden. Wenn beide zusammen aktualisiert wurden, rollen Sie zuerst den Core und dann den kundenspezifischen Code zurück.

______________________________________________________________________

## Kompatibilität

Kundenspezifischer Code ist an bestimmte Core-Versionen gebunden, um die Stabilität zu gewährleisten. Eine
Kompatibilitätsmatrix verfolgt, welche Kundenversionen mit welchen Core-Versionen funktionieren:

| Kundenversion | Core-Version | Status    | Anmerkungen            |
| ------------- | ------------ | --------- | ---------------------- |
| v1.0.0        | v0.1.2       | Legacy    | End of Life            |
| v1.1.0        | v1.2.3       | Supported | Aktuelle Produktion    |
| v1.2.0        | v1.2.3       | Supported | Neueste Features       |
| v2.0.0        | v2.3.4       | Testing   | Nächstes Major Release |

Staging-Umgebungen sollten der Produktionsinfrastruktur entsprechen und repräsentative Datensätze für
Kompatibilitätstests vor Produktions-Updates verwenden.

______________________________________________________________________

## Monitoring

Der Observability-Stack umfasst Langfuse für KI-spezifisches Tracing, OpenTelemetry für verteiltes Tracing und optional
SigNoz Cloud für externe Metriken und Logs. Überwachen Sie Core-Services (API, Web, Dagster) und Kunden-Services
(Agents, Pipelines, Prozesse) während und nach Updates.

______________________________________________________________________

## Kontinuierliche Postgres-Wartung

Die Plattform beinhaltet eine automatisierte Datenbankwartung, die Operatoren nicht manuell planen müssen. Zwei Jobs
laufen in derselben Dagster-Instanz als Backup (UI unter `http://localhost:3004`) und halten die `dagster`-Datenbank
über die Zeit begrenzt: Der wöchentliche `dagster_cleanup_job` entfernt ausführliche Log-Einträge und temporäre
Framework-Ereignisse aus `event_logs`, und der monatliche `postgres_repack_job` gibt über `pg_repack` Speicherplatz auf
der Festplatte frei. Beide sind gegenseitig exklusiv mit Backups über Dagsters Run-Coordinator-Tag-Concurrency.

Das ist es, was den Postgres-Footprint einer 5 Jahre alten Deployment-Umgebung mit dem einer 3 Monate alten vergleichbar
hält. Siehe [Backup und Wiederherstellung](../4_backup_and_recovery/#continuous-postgres-maintenance) für
Aufbewahrungsfenster und den `MAINTENANCE_DISABLED` Kill Switch.

______________________________________________________________________

## Verwandte Dokumentation

- [Deployment-Optionen](../1_deployment_options/) - Architektur pro Instanz
- [Multi-Tenancy](../../16_multi_tenancy/) - Logische Trennung innerhalb von Instanzen
- [Backup und Wiederherstellung](../4_backup_and_recovery/) - Backup-Strategien
- [Core-Komponenten](../../2_architecture/1_core_components/) - Komponentenabhängigkeiten
