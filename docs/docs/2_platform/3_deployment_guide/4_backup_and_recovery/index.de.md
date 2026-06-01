---
title: Sicherung und Wiederherstellung
source_sha: 198e889b47930d4e1fd9afc4cf0859c5356d393a1d61ecbb36f2532d22af406a
---

# Sicherung und Wiederherstellung

## Übersicht

Der Swiss AI Hub enthält einen automatisierten Backup-Service, der periodisch alle zustandsbehafteten Services in den
internen SeaweedFS S3-Speicher (`s3://backups/`) sichert. Backups werden täglich (1 Uhr MEZ) mit automatischer
Bereinigungsroutine ausgeführt. Der Backup-Service ist eine eigenständige Dagster-Instanz mit einer Web-UI für
Monitoring, manuelle Auslösung und parametrisierte Wiederherstellungen.

Jede Instanz verfügt über unabhängige Backups. Datenisolation zwischen den Instanzen. Wiederherstellungsvorgänge
beeinflussen andere Instanzen nicht.

::: info Multi-Instancing-Kontext
Dieses Kapitel geht von einem Multi-Instancing-Bereitstellungsmodell aus, bei dem jede Organisation ihre eigene
isolierte Swiss AI Hub-Instanz besitzt. Für Multi-Tenancy (logische Trennung innerhalb einer einzelnen Instanz) siehe
[Multi-Tenancy](../../16_multi_tenancy/).
:::

______________________________________________________________________

## Was gesichert wird

| Service               | Methode                                                  | Daten                                                         |
| --------------------- | -------------------------------------------------------- | ------------------------------------------------------------- |
| PostgreSQL (main)     | `pg_dumpall` + `pg_dump`                                 | OpenWebUI, Langfuse, Dagster, LiteLLM databases               |
| PostgreSQL (FerretDB) | `pg_dumpall` + `pg_dump` + `COPY` (DocumentDB catalog\*) | Agent-Konfigurationen, Benutzer, Threads, Tokens, RBAC-Rollen |
| Milvus                | `milvus-backup` (official tool)                          | Vektor-Sammlungen mit konsistenten Metadaten                  |
| Neo4j                 | `neo4j-admin` via temp container                         | Agent-Speicher-Graphen (Mem0)                                 |
| ClickHouse            | `BACKUP TO Disk('backup_s3', ...)` SQL command           | Langfuse-Traces, -Beobachtungen, -Scores                      |
| Valkey                | `BGSAVE` + RDB copy (+ temp container on restore)        | Cache und Session-Zustand (RDB-Snapshot)                      |
| NATS                  | `nats` CLI stream backup                                 | JetStream-Streams                                             |

### Was von der Plattform NICHT gesichert wird

**SeaweedFS-Bucket-Daten** (vom Benutzer hochgeladene Dokumente, Wissensdatenbankdateien, Chat-Anhänge) liegen in der
Verantwortung der Infrastruktur-Ebene. Verwenden Sie VM-Snapshots, rclone sync oder externe S3-Replikation, um diese
Daten zu schützen. Die Plattform kann SeaweedFS nicht in sich selbst sichern.

Alle Service-Backups sind erforderlich. Ein fehlendes Backup für einen Service blockiert die Wiederherstellung.

______________________________________________________________________

## Konfiguration

Konfigurieren Sie den Backup-Service über Umgebungsvariablen in `.env.dev` (Entwicklung) oder `.env.prod` (Produktion):

```bash
BACKUP_RETENTION_DAYS="7"            # Keep backups for N days (dev: 7, prod: 30)
BACKUP_MINIMUM_KEEP="3"             # Minimum backups preserved regardless of age
BACKUP_S3_BUCKET="backups"           # S3 bucket name for backup storage
```

Der Backup-Zeitplan (täglich um 1 Uhr MEZ) ist in Dagster definiert und kann über die Dagster-UI ein- oder ausgeschaltet
werden.

::: warning Backup- und Pipeline-Zeitpläne dürfen sich nicht überschneiden
Das Backup stoppt alle Anwendungs-Container, einschliesslich der Pipeline-Dagster-Instanz. Die Standard-Zeitpläne sind
gestaffelt: Backup um 1:00 Uhr, Pipeline-Beobachtung um 2:00 Uhr, Pipeline-Bereinigung um 3:00 Uhr. Wenn Sie einen
Zeitplan ändern, stellen Sie sicher, dass das Backup beendet ist, bevor der erste Pipeline-Job beginnt — ein während
eines Pipeline-Jobs laufendes Backup würde diesen mitten in der Ausführung abbrechen.
:::

______________________________________________________________________

## Wie Backups funktionieren

Jedes Backup stoppt alle verwalteten Container parallel, bevor Snapshots erstellt werden, um die transaktionale
Konsistenz über alle Datenbanken hinweg zu gewährleisten. Container mit den Präfixen `backup-`, `seaweedfs-`, `etcd` und
`traefik` sind vom Stopp-/Start-Zyklus ausgenommen — SeaweedFS wird für den S3-Zugriff benötigt, etcd für
Milvus-Metadaten und Traefik für die Ingress-Verfügbarkeit während der Backups.

Jeder Service wird mit seinem nativen Backup-Tool gesichert. Nachdem alle Services gesichert wurden, startet die
Plattform alle zuvor laufenden Container parallel neu. Docker Compose Neustart-Richtlinien stellen sicher, dass die
Services einen gesunden Zustand erreichen, selbst wenn einige starten, bevor ihre Abhängigkeiten bereit sind. Schlägt
das Backup während der Ausführung fehl, startet ein Fehler-Hook automatisch alle verwalteten Container als
Sicherheitsmassnahme neu.

Um ein manuelles Backup auszulösen, öffnen Sie die Dagster-UI unter `http://localhost:3004`, navigieren Sie zu den
Backup-Assets und klicken Sie auf „Materialize“.

### Neo4j Sibling-Container

Die Neo4j Community Edition unterstützt keine Online-Backups — `neo4j-admin database dump` erfordert exklusiven Zugriff
auf das `/data`-Verzeichnis und kann nicht ausgeführt werden, während der Neo4j-Prozess eine Sperre darauf hält. Da ein
gestoppter Docker-Container ebenfalls keine Befehle ausführen kann, startet der Backup-Service einen **temporären
Sibling-Container** unter Verwendung desselben Neo4j-Images und desselben `/data`-Volumes (beide werden automatisch zur
Laufzeit vom Produktions-Container erkannt). Der Sibling führt `neo4j-admin` aus, kopiert die Dump-Datei heraus und wird
sofort danach entfernt. Ein ähnlicher Sibling wird für die Wiederherstellung verwendet.

Sie werden möglicherweise einen kurzlebigen Container namens `neo4j-dump-<id>` oder `neo4j-restore-<id>` während der
Backup-/Wiederherstellungsläufe bemerken — dies ist erwartet und wird automatisch bereinigt.

### \* DocumentDB Katalog-Workaround

PostgreSQLs `pg_dump` überspringt stillschweigend Daten für Tabellen, die von Erweiterungen besessen werden — es geht
davon aus, dass `CREATE EXTENSION` diese während der Wiederherstellung neu befüllen wird. Die DocumentDB-Erweiterung
(die vom PostgreSQL-Backend von FerretDB verwendet wird) besitzt ihre Katalogtabellen
(`documentdb_api_catalog.collections` und `collection_indexes`), registriert sie jedoch nicht für die Aufnahme in den
Dump. Die übliche Lösung (`pg_extension_config_dump()`) kann nicht extern aufgerufen werden — PostgreSQL beschränkt dies
auf `CREATE EXTENSION`-Skripte.

Ohne einen Workaround würde eine Wiederherstellung alle Dokumentdaten intakt, aber einen leeren Katalog aufweisen —
FerretDB würde null Sammlungen melden. Der Backup-Service handhabt dies automatisch: Während des Backups extrahiert er
Katalogzeilen separat mittels `COPY TO STDOUT` in ein `ext-catalog.sql.gz`-Artefakt, und während der Wiederherstellung
spielt er dieses SQL nach `pg_restore` ab. Es ist keine Bedieneraktion erforderlich.

______________________________________________________________________

## Backups auflisten

Öffnen Sie die Dagster-UI unter `http://localhost:3004`, um die Backup-Asset-Ansicht zu sehen, die auf einen Blick die
Backup-Historie anzeigt. Die Asset-Metadaten umfassen den Zeitstempel und das S3-Präfix für jedes Backup.

______________________________________________________________________

## Wiederherstellung

### Vollständige Systemwiederherstellung

Stellt die gesamte Plattform auf ein bestimmtes Backup wieder her. Stoppt alle Services, stellt jede Datenbank wieder
her und startet dann alle Container neu.

Um eine vollständige Wiederherstellung durchzuführen, öffnen Sie die Dagster-UI unter `http://localhost:3004`,
navigieren Sie zu Jobs -> `full_restore_job`, wählen Sie einen Backup-Zeitstempel aus dem Partition-Dropdown und klicken
Sie auf „Launch Run“.

Der Wiederherstellungsprozess folgt drei Phasen:

1. **Vollständiger Stopp**: Alle Anwendungs- und Datenbank-Container werden gestoppt (ausser SeaweedFS, das für den
   S3-Zugriff benötigt wird)
2. **Daten wiederherstellen**: Jeder Service wird aus seinem Backup wiederhergestellt. PostgreSQL-Instanzen werden
   temporär für den SQL-Import gestartet. Milvus wird temporär für die milvus-backup Restore-API gestartet.
3. **Vollständiger Start**: Alle zuvor laufenden Container werden neu gestartet. Docker Compose Neustart-Richtlinien
   stellen sicher, dass die Services einen gesunden Zustand erreichen, selbst wenn einige starten, bevor ihre
   Abhängigkeiten bereit sind.

::: warning Verhalten bei Wiederherstellungsfehlern
Bei einem Fehler während der Wiederherstellung werden Container absichtlich **nicht** automatisch neu gestartet. Der
Bediener muss den Fehler untersuchen und entscheiden, ob er es erneut versuchen oder von einem anderen Backup
wiederherstellen möchte. Dies ist eine bewusste Sicherheitsmassnahme — ein automatischer Neustart nach einer teilweisen
Wiederherstellung könnte das System in einem inkonsistenten Zustand hinterlassen.
:::

______________________________________________________________________

## VM-Snapshots

VM-Snapshots bleiben eine gültige ergänzende Strategie, insbesondere zum Schutz von SeaweedFS-Daten. Sie erfassen alles:
OS, Docker, Daten, Konfiguration. Sie stellen die gesamte VM in einem einzigen Vorgang wieder her.

Stoppen Sie Swiss AI Hub Services, bevor Sie einen Snapshot mit `docker compose down` erstellen. Alternativ können Sie
anwendungskonsistente Snapshots verwenden (Azure mit VM-Agent, VMware mit Quiescing). Erstellen Sie Snapshots vor
grösseren Updates.

______________________________________________________________________

## Kontinuierliche Postgres-Wartung

Dieselbe Dagster-Instanz, die Backups durchführt, führt auch eine **kontinuierliche Postgres-Gesundheitswartung** durch,
damit die `event_logs`- und `runs`-Tabellen der Plattform bei langlebigen Deployments nicht unbegrenzt wachsen. Zwei
zusätzliche Jobs sind in dieselbe Backup-Dagster-UI unter `http://localhost:3004` integriert:

- **`dagster_cleanup_job`** — Sonntags um 3 Uhr MEZ. Bereinigt ausführliche Python-Logs und kuratierte Framework-interne
  Ereignisse (`HANDLED_OUTPUT`, `LOADED_INPUT`, `ENGINE_EVENT`, `ASSET_MATERIALIZATION_PLANNED`, `STEP_OUTPUT`) nach
  Ablauf ihrer Aufbewahrungsfristen. Stellt idempotent sicher, dass die Bereinigungsabfrageindizes existieren und wendet
  eine straffere Autovacuum-Optimierung auf die umfangreichen Tabellen an.
- **`postgres_repack_job`** — am ersten Sonntag jedes Monats um 4 Uhr morgens. Führt `pg_repack` auf `event_logs`,
  `runs` und `job_ticks` aus, um Speicherseiten an das Betriebssystem zurückzugeben (ein einfaches `VACUUM` markiert nur
  tote Zeilen intern als wiederverwendbar).

**UI-sicher konstruiert**: Die Bereinigung löscht niemals Zeilen, von denen die Dagster-UI abhängt
(`ASSET_MATERIALIZATION`, `STEP_SUCCESS`, `STEP_FAILURE`, `RUN_SUCCESS`, `RUN_FAILURE`, die `runs`-Tabelle,
Asset-Katalog, Sensor-Cursor).

**Gegenseitig exklusiv mit Backup**: Jeder Job, der Postgres betrifft, trägt einen `postgres-mutex`-Tag. Der
Run-Koordinator des Backup-Dagster begrenzt die Parallelität für diesen Tag auf eins, sodass Bereinigungs- oder
Repack-Ticks hinter einem noch laufenden Backup in die Warteschlange gestellt werden, anstatt gleichzeitig zu starten.
Innerhalb jedes Laufs bleibt die Intra-Run-Parallelität (z.B. parallele Backups pro Service) unberührt.

**`pg_repack` wird im Plattform-Postgres-Image ausgeliefert**: Das projektverwaltete Image erweitert
`pgvector/pgvector:pg17` um `postgresql-17-repack`, und die Erweiterung wird beim ersten Start in der
`dagster`-Datenbank registriert. Deployments, die ein fremdes Postgres-Image ohne die Erweiterung verwenden,
funktionieren weiterhin — repack meldet einen sauberen Skip in den Lauf-Metadaten; die Bereinigung funktioniert
bedingungslos.

### Konfiguration

```bash
# Retention windows (defaults follow the official Dagster docs recipe)
DAGSTER_DEBUG_LOG_RETENTION_DAYS="7"
DAGSTER_INFO_LOG_RETENTION_DAYS="60"
DAGSTER_WARNING_LOG_RETENTION_DAYS="60"
DAGSTER_UNIMPORTANT_EVENT_RETENTION_DAYS="30"

# Per-DELETE row cap — protects against WAL-flooding on first run against a backlogged DB
DAGSTER_CLEANUP_BATCH_LIMIT="1000000"

# Kill switch — set to true and the maintenance handlers no-op; backup is unaffected
MAINTENANCE_DISABLED="false"

DAGSTER_DB="dagster"
POSTGRES_PORT="5432"
```

Eine stark überlastete DB entlastet sich über mehrere wöchentliche Ticks (`DAGSTER_CLEANUP_BATCH_LIMIT` Zeilen pro Tick
× 4 Cleanup-Handler). Bediener, die eine schnellere anfängliche Entlastung wünschen, können `dagster_cleanup_job`
manuell wiederholt über die Dagster-UI starten.

______________________________________________________________________

## Backup-Speicherlayout

Jedes Backup wird in einem flachen, mit Zeitstempel versehenen Verzeichnis gespeichert:

```
s3://backups/
  2026-02-17_02-00-00/
    postgres-main/
      globals.sql.gz
      openwebui.dump
      langfuse.dump
      dagster.dump
      litellm.dump
    postgres-ferretdb/
      globals.sql.gz
      ferretdb.dump
      ext-catalog.sql.gz
    milvus_backup_2026_02_17_02_00_00/...
    neo4j.dump
    clickhouse/
      backup_2026_02_17_02_00_00/...
    valkey.rdb
    nats-jetstream.tar.gz
  2026-02-18_02-00-00/
    ...
```

______________________________________________________________________
