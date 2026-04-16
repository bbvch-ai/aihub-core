---
title: Backup und Wiederherstellung
source_sha: "0cf6e60d9caab0d0f3f115825638c3c2d8011c4b0a55afe23a30bce858b9be36"
---

# Backup und Wiederherstellung

## Übersicht

Der Swiss AI Hub umfasst einen automatisierten Backup-Service, der periodisch alle zustandsbehafteten Services in den internen SeaweedFS S3-Speicher (`s3://backups/`) sichert. Backups werden täglich (1:00 Uhr Europe/Zurich) mit automatischer Aufbewahrungsbereinigung durchgeführt. Der Backup-Service ist eine eigenständige Dagster-Instanz mit einer Web-UI für Monitoring, manuelle Auslösung und parametrisierte Wiederherstellungen.

Jede Instanz verfügt über unabhängige Backups. Datenisolation zwischen den Instanzen. Wiederherstellungsvorgänge wirken sich nicht auf andere Instanzen aus.

::: info Multi-instancing context
Dieses Kapitel geht von einem Multi-Instancing-Deployment-Modell aus, bei dem jede Organisation ihre eigene isolierte Swiss AI Hub-Instanz besitzt. Für Multi-Tenancy (logische Trennung innerhalb einer einzelnen Instanz) siehe [Multi-Tenancy](../../16_multi_tenancy/).
:::

______________________________________________________________________

## Was gesichert wird

| Service               | Methode                                                  | Daten                                              |
| --------------------- | -------------------------------------------------------- | ------------------------------------------------- |
| PostgreSQL (main)     | `pg_dumpall` + `pg_dump`                                 | OpenWebUI-, Langfuse-, Dagster-, LiteLLM-Datenbanken |
| PostgreSQL (FerretDB) | `pg_dumpall` + `pg_dump` + `COPY` (DocumentDB Katalog\*) | Agent-Konfigurationen, Benutzer, Threads, Tokens, RBAC-Rollen |
| Milvus                | `milvus-backup` (offizielles Tool)                       | Vektor-Sammlungen mit konsistenten Metadaten       |
| Neo4j                 | `neo4j-admin` via temporärem Container                   | Agent-Speicherdiagramme (Mem0)                     |
| ClickHouse            | `BACKUP TO Disk('backup_s3', ...)` SQL-Befehl            | Langfuse-Traces, Beobachtungen, Scores             |
| Valkey                | `BGSAVE` + RDB-Kopie (+ temporärer Container bei Wiederherstellung) | Cache- und Session-Zustand (RDB-Snapshot)        |
| NATS                  | `nats` CLI Stream-Backup                                 | JetStream-Streams                                 |

### Was NICHT von der Plattform gesichert wird

SeaweedFS-Bucket-Daten (vom Benutzer hochgeladene Dokumente, Wissensbasisdateien, Chat-Anhänge) liegen in der Verantwortung der Infrastrukturschicht. Verwenden Sie VM-Snapshots, rclone sync oder externe S3-Replikation, um diese Daten zu schützen. Die Plattform kann SeaweedFS nicht in sich selbst sichern.

Alle Service-Backups sind erforderlich. Ein fehlendes Backup für einen Service blockiert die Wiederherstellung.

______________________________________________________________________

## Konfiguration

Konfigurieren Sie den Backup-Service über Umgebungsvariablen in `.env.dev` (Entwicklung) oder `.env.prod` (Produktion):

```bash
BACKUP_RETENTION_DAYS="7"            # Backups für N Tage aufbewahren (dev: 7, prod: 30)
BACKUP_MINIMUM_KEEP="3"             # Mindestanzahl an Backups, die unabhängig vom Alter erhalten bleiben
BACKUP_S3_BUCKET="backups"           # S3-Bucket-Name für die Backup-Speicherung
```

Der Backup-Zeitplan (täglich um 1:00 Uhr Europe/Zurich) ist in Dagster definiert und kann über die Dagster-UI ein- oder ausgeschaltet werden.

::: warning Backup- und Pipeline-Zeitpläne dürfen sich nicht überlappen
Das Backup stoppt alle Anwendungs-Container, einschliesslich der Pipeline Dagster-Instanz. Die Standard-Zeitpläne sind gestaffelt: Backup um 1:00 Uhr, Pipeline-Überwachung um 2:00 Uhr, Pipeline-Bereinigung um 3:00 Uhr. Wenn Sie einen Zeitplan ändern, stellen Sie sicher, dass das Backup abgeschlossen ist, bevor der erste Pipeline-Job beginnt – ein während eines Pipeline-Jobs laufendes Backup würde diesen mitten in der Ausführung beenden.
:::

______________________________________________________________________

## Wie Backups funktionieren

Jedes Backup stoppt alle verwalteten Container parallel, bevor Snapshots erstellt werden, um die transaktionale Konsistenz über alle Datenbanken hinweg zu gewährleisten. Container mit den Präfixen `backup-`, `seaweedfs-`, `etcd` und `traefik` sind vom Stop-/Start-Zyklus ausgeschlossen – SeaweedFS wird für den S3-Zugriff benötigt, etcd für Milvus-Metadaten und Traefik für die Ingress-Verfügbarkeit während der Backups.

Jeder Service wird mit seinem nativen Backup-Tool gesichert. Nachdem alle Services gesichert wurden, startet die Plattform alle zuvor laufenden Container parallel neu. Docker Compose Restart-Policies stellen sicher, dass Services einen gesunden Zustand erreichen, selbst wenn einige vor ihren Abhängigkeiten starten. Wenn das Backup während der Ausführung fehlschlägt, startet ein Failure Hook automatisch alle verwalteten Container als Sicherheitsmassnahme neu.

Um ein manuelles Backup auszulösen, öffnen Sie die Dagster-UI unter `http://localhost:3004`, navigieren Sie zu den Backup-Assets und klicken Sie auf „Materialize“.

### Neo4j Sibling-Container

Die Neo4j Community Edition unterstützt keine Online-Backups – `neo4j-admin database dump` erfordert exklusiven Zugriff auf das `/data`-Verzeichnis und kann nicht ausgeführt werden, solange der Neo4j-Prozess eine Sperre darauf hält. Da ein gestoppter Docker-Container ebenfalls keine Befehle ausführen kann, startet der Backup-Service einen **temporären Sibling-Container** unter Verwendung desselben Neo4j-Images und desselben `/data`-Volumes (beides wird zur Laufzeit automatisch vom Produktions-Container erkannt). Der Sibling führt `neo4j-admin` aus, kopiert die Dump-Datei heraus und wird unmittelbar danach entfernt. Ein ähnlicher Sibling wird für die Wiederherstellung verwendet.

Möglicherweise bemerken Sie einen kurzlebigen Container namens `neo4j-dump-<id>` oder `neo4j-restore-<id>` während der Backup-/Wiederherstellungsläufe – dies ist beabsichtigt und wird automatisch bereinigt.

### \* DocumentDB Katalog-Workaround

PostgreSQLs `pg_dump` überspringt stillschweigend Daten für Tabellen, die Erweiterungen gehören – es geht davon aus, dass `CREATE EXTENSION` diese während der Wiederherstellung neu befüllen wird. Die DocumentDB-Erweiterung (verwendet vom PostgreSQL-Backend von FerretDB) besitzt ihre Katalogtabellen (`documentdb_api_catalog.collections` und `collection_indexes`), registriert diese jedoch nicht für die Aufnahme in den Dump. Der übliche Fix (`pg_extension_config_dump()`) kann nicht extern aufgerufen werden – PostgreSQL beschränkt ihn auf `CREATE EXTENSION`-Skripte.

Ohne einen Workaround hätte eine Wiederherstellung alle Dokumentdaten intakt, aber einen leeren Katalog – FerretDB würde null Kollektionen melden. Der Backup-Service handhabt dies automatisch: Während des Backups extrahiert er Katalogzeilen separat mittels `COPY TO STDOUT` in ein `ext-catalog.sql.gz`-Artefakt, und während der Wiederherstellung spielt er diese SQL-Befehle nach `pg_restore` erneut ab. Es ist keine Bedieneraktion erforderlich.

______________________________________________________________________

## Backups auflisten

Öffnen Sie die Dagster-UI unter `http://localhost:3004`, um die Backup-Asset-Ansicht zu sehen, die die Backup-Historie auf einen Blick darstellt. Die Asset-Metadaten umfassen Zeitstempel und S3-Präfix für jedes Backup.

______________________________________________________________________

## Wiederherstellung

### Vollständige Systemwiederherstellung

Stellt die gesamte Plattform auf ein bestimmtes Backup wieder her. Stoppt alle Services, stellt jede Datenbank wieder her und startet dann alle Container neu.

Um eine vollständige Wiederherstellung durchzuführen, öffnen Sie die Dagster-UI unter `http://localhost:3004`, navigieren Sie zu Jobs -> `full_restore_job`, wählen Sie einen Backup-Zeitstempel aus dem Partitions-Dropdown und klicken Sie auf „Launch Run“.

Der Wiederherstellungsprozess folgt drei Phasen:

1.  **Vollständiger Stopp**: Alle Anwendungs- und Datenbank-Container werden gestoppt (ausser SeaweedFS, das für den S3-Zugriff benötigt wird).
2.  **Datenwiederherstellung**: Jeder Service wird aus seinem Backup wiederhergestellt. PostgreSQL-Instanzen werden temporär für den SQL-Import gestartet. Milvus wird temporär für die milvus-backup Wiederherstellungs-API gestartet.
3.  **Vollständiger Start**: Alle zuvor laufenden Container werden neu gestartet. Docker Compose Restart-Policies stellen sicher, dass Services einen gesunden Zustand erreichen, selbst wenn einige vor ihren Abhängigkeiten bereit sind.

::: warning Verhalten bei Wiederherstellungsfehlern
Bei einem Fehlschlag während der Wiederherstellung werden Container absichtlich **nicht** automatisch neu gestartet. Der Bediener muss den Fehler untersuchen und entscheiden, ob ein erneuter Versuch unternommen oder von einem anderen Backup wiederhergestellt werden soll. Dies ist eine bewusste Sicherheitsmassnahme – ein automatischer Neustart nach einer teilweisen Wiederherstellung könnte das System in einem inkonsistenten Zustand hinterlassen.
:::

______________________________________________________________________

## VM-Snapshots

VM-Snapshots bleiben eine gültige ergänzende Strategie, insbesondere zum Schutz von SeaweedFS-Daten. Sie erfassen alles: OS, Docker, Daten, Konfiguration. Sie stellen die gesamte VM in einem einzigen Vorgang wieder her.

Stoppen Sie die Swiss AI Hub Services, bevor Sie einen Snapshot mit `docker compose down` erstellen. Alternativ verwenden Sie anwendungskonsistente Snapshots (Azure mit VM-Agent, VMware mit Quiesce). Erstellen Sie Snapshots vor wichtigen Updates.

______________________________________________________________________

## Layout der Backup-Speicherung

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
