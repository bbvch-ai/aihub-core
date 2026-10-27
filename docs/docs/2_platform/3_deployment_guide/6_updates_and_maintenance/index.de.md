---
title: Updates & Wartung
source_sha: c9d26af9c23ae818e19f8140ed176a29b3409ac9f57f51ed6db596c939236435
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

### Neue Speicher-Buckets

`seaweedfs-init` legt bei jedem Lauf alle fehlenden SeaweedFS-Buckets an, und `docker compose up -d` startet es bei
jedem Aufruf erneut. Das obige Update legt deshalb die Buckets an, die ein Release hinzufügt. Nur ein Update, das
ausgewählte Services startet, etwa `docker compose up -d <service>` oder `--no-deps`, überspringt es. Führen Sie es dann
selbst aus:

```bash
docker compose up seaweedfs-init
```

Ein fehlender Bucket scheitert zur Laufzeit, nicht beim Start. Ohne den Bucket `parse-cache` scheitert jedes
MinerU-Parsing eines Dokuments mit `NoSuchBucket`. Office-Dokumente werden weiterhin geparst, nur ohne Cache, sodass
jeder Lesevorgang sie erneut konvertiert und eine Warnung protokolliert. Der Bucket speichert geparste Dokumente nach
Inhalts-Hash zwischen, und Einträge laufen nach 7 Tagen ab. Ein abgelaufener Eintrag wird erneut geparst, daher braucht
nichts davon ein Backup.

Der Bucket `sandbox-files` enthält den Einweg-Spiegel des Code-Sandbox-Home-Verzeichnisses jedes Benutzers (die Dateien
hinter **Meine Dateien**). Er wird auf die gleiche Weise angelegt und benötigt `SANDBOX_MIRROR_S3_ACCESS_KEY`,
`SANDBOX_MIRROR_S3_SECRET_KEY` und `SANDBOX_MIRROR_INTERVAL_SECONDS` in Ihrer `.env` (der Prüfschritt oben zeigt sie
an). Der Spiegel verwendet eine auf diesen Bucket beschränkte S3-Identität, erstellen Sie `seaweedfs-s3` daher neu,
damit die Identität wirksam wird. In der Sandbox gelöschte oder überschriebene Dateien werden 7 Tage lang unter
`.deleted/` aufbewahrt.

### Ablauf von Bucket-Inhalten

Vier Bereiche laufen von selbst ab: `dagster` nach 1 Tag sowie `parse-cache`, `sandbox-files/.deleted/` und
`agent-files` nach 7 Tagen. Der einmalig laufende Service `seaweedfs-ttl-init` schreibt diese bei jedem Lauf als
TTL-Regeln des SeaweedFS-Filers, und `seaweedfs-init` wartet auf ihn, sodass auch `docker compose up seaweedfs-init` sie
anwendet. Sein Log listet jede Regel auf, die er geprüft hat:

```bash
docker compose logs seaweedfs-ttl-init
```

Konnte eine Regel nicht geschrieben werden, erscheint der Service als `Exited (1)`, und sein Log nennt die fehlende
Regel. Der Rest des Stacks startet trotzdem, aber Objekte, die bis zum nächsten erfolgreichen Lauf geschrieben werden,
laufen nie ab. Führen Sie ihn erneut aus, sobald der Filer erreichbar ist:

```bash
docker compose up seaweedfs-ttl-init
```

Der Ablaufzeitpunkt eines Objekts wird beim Schreiben festgelegt. Eine geänderte Regel betrifft nur neue Objekte.

::: warning
Wenden Sie auf diese Buckets niemals eine S3-Lifecycle-Konfiguration (`put-bucket-lifecycle-configuration`) an. Seit
SeaweedFS 4.32 lassen Lifecycle-Konfigurationen Objekte nur über einen Admin- und Worker-Service ablaufen, den die
Plattform nicht betreibt, und das Anwenden einer solchen Konfiguration löscht die TTL-Regel, die SeaweedFS 4.01 für
diesen Bucket angelegt hat, sodass nichts mehr abläuft, was danach geschrieben wird. Siehe ADR
`2026_10_27_bucket_expiry_via_filer_ttl`.
:::

### Zustand des SeaweedFS-Masters

Der Master speichert die Identität des Clusters in seinem Datenverzeichnis. Geht dieses Verzeichnis verloren oder wird
es aus einem anderen Zeitpunkt als die Volume-Daten wiederhergestellt, legt der Master keine Volumes mehr an, sobald ein
Volume-Server die ihm bekannte Identität meldet, und Schreibvorgänge scheitern, sobald die vorhandenen Volumes voll
sind. Nachdem Sie geprüft haben, dass keine Daten fehlen, nehmen Sie das Anlegen von Volumes wieder auf:

```bash
docker compose exec seaweedfs-master sh -c 'echo volume.growth.resume | weed shell -master=localhost:9333'
```

Erstellen Sie vor einem SeaweedFS-Upgrade einen gemeinsamen Snapshot aller `seaweedfs-*`-Volumes und von etcd, und
stellen Sie sie gemeinsam wieder her.

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

::: warning Dienste mit ausschliesslich vorwärtsgerichteten Migrationen lassen sich so nicht zurückrollen
«Wenn die Daten kompatibel bleiben» ist die entscheidende Bedingung, und sie gilt nicht für jeden Dienst. Langfuse führt
beim Start ausschliesslich vorwärtsgerichtete Postgres- und ClickHouse-Migrationen aus. Sobald ein Update diese
angewendet hat, stellt das Herunterladen des vorherigen Bundles die älteren **Binaries** gegen das neuere **Schema**
wieder her. Einen unterstützten Downgrade-Pfad gibt es nicht.

Auch das Wiederherstellen eines Backups von vor dem Update ist kein Rollback: Die Wiederherstellung prüft nur, ob die
erwarteten Artefakte vorhanden sind, enthält keine Schema-Versionsmarkierung und setzt Postgres und ClickHouse
unabhängig voneinander zurück — ohne Konsistenzprüfung zwischen beiden und ohne anschliessenden Migrationsschritt.

Erstellen Sie vor einem Release-Update, das Langfuse anhebt, ein Backup, das Sie als einmalig betrachten, und planen Sie
die Wiederherstellung vorwärts statt als Rollback.
:::

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
