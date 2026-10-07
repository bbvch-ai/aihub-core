---
title: Sicherung und Wiederherstellung
source_sha: 48f1f92dffa75fa34dc28be419cfe21c3208a1a22d9265a30b5ec59c635b0647
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

::: warning Ein Backup von vor einem Langfuse-Upgrade ist kein Rollback-Ziel
Die Wiederherstellung prüft nur, ob die erwarteten Artefakte **vorhanden** sind. Sie enthält keine
Schema-Versionsmarkierung und stellt ein unter einer älteren Langfuse-Version erstelltes Backup daher problemlos in
einem Stack mit einer neueren Version wieder her.

Langfuse umfasst zwei Speicher, die von unabhängigen Handlern wiederhergestellt werden: die Postgres-Datenbank
(`langfuse.dump`) und die ClickHouse-Tabellen (`clickhouse/`). ClickHouse wird mit einem nativen `BACKUP DATABASE`
gesichert, sodass die Wiederherstellung neben den Daten auch die **Tabellendefinitionen** zurücksetzt. Nichts prüft, ob
die beiden Speicher zueinander passen, und es folgt kein Migrationsschritt — das Schema bewegt sich erst wieder
vorwärts, wenn die Langfuse-Container das nächste Mal starten.

Behandeln Sie eine Langfuse-Versionsanhebung als Einbahnstrasse: Erstellen Sie vorher ein Backup zur Datenrettung,
planen Sie die Wiederherstellung aber vorwärts statt als Downgrade.
:::

### Sandbox-Dateien der Benutzer (My Files)

Die Homes der Benutzer in der Code-Sandbox (die Dateien hinter My Files) liegen auf dem Host-Volume, das unter
`<VOLUME_ROOT>/open-terminal` eingebunden ist. Der Service `sandbox-mirror` kopiert sie einseitig in den Bucket
`sandbox-files`, und zwar alle `SANDBOX_MIRROR_INTERVAL_SECONDS`; dabei bleiben Eigentümer, Gruppe, Modus und
Änderungszeitpunkt jeder Datei erhalten. Eine gelöschte oder überschriebene Datei wird eine Woche lang unter
`.deleted/<timestamp>/` aufbewahrt. Der Mirror schützt vor dem Verlust des Homes-Volumes, nicht vor dem Verlust von
SeaweedFS selbst; siehe [Was NICHT gesichert wird](#was-von-der-plattform-nicht-gesichert-wird).

So stellen Sie die Homes nach dem Verlust des Volumes wieder her:

1. Stoppen Sie **zuerst** den Mirror, dann die Sandbox. Ein laufender Mirror würde das leere Volume über den Bucket
   kopieren und jede Datei nach `.deleted/` verschieben.

   ```bash
   docker compose stop sandbox-mirror open-terminal
   ```

2. Kopieren Sie die Homes zurück, mit den eigenen Zugangsdaten des Mirrors und dem schreibbar eingebundenen Volume:

   ```bash
   docker compose run --rm --no-deps \
     -v "<VOLUME_ROOT>/open-terminal:/restore" \
     --entrypoint rclone sandbox-mirror \
     copy mirror:sandbox-files /restore --metadata --exclude "/.deleted/**"
   ```

   Dateien kommen mit ihrem Eigentümer und Modus zurück. Ordner nicht: Der Bucket enthält keine Ordner-Metadaten,
   weshalb jedes Home bis zum nächsten Schritt `root` gehört und den Modus `755` hat.

3. Erstellen Sie die Sandbox neu und starten Sie dann den Mirror wieder. Der neue Container richtet das Konto jedes
   Benutzers bei dessen nächster Anfrage ein; dadurch wird er wieder Eigentümer seines Homes und der Modus wird auf
   `2770` gesetzt, sodass nur er es lesen kann.

   ```bash
   docker compose up -d --force-recreate open-terminal
   docker compose up -d sandbox-mirror
   ```

   Wenn Sie das Neuerstellen überspringen, gehört jedes Home weiterhin `root`: Benutzer können nicht in ihre eigenen
   Dateien schreiben, und andere Benutzer können sie auflisten.

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

## Einmalig: Wissensspeicher mit lz4 neu komprimieren

Das PostgreSQL von FerretDB (`postgres-ferretdb`) läuft mit `default_toast_compression=lz4`. DocumentDB dekomprimiert
für jeden Filter, jede Projektion und jede Sortierung das ganze Dokument, und lz4 erledigt das etwa dreimal schneller
als das PostgreSQL-Standardverfahren `pglz`. Die Inhaltssuche und das Auflisten von Wissensdokumenten werden dadurch
2–4× schneller. Siehe ADR `2026_10_07_ferretdb_postgres_lz4_toast_compression`.

Die Einstellung gilt für jede Zeile, die geschrieben wird, sobald sie aktiv ist. Ältere Zeilen behalten pglz. Sie werden
korrekt gelesen, nur langsamer, bis sie sich ändern. **`ferretdb_lz4_rewrite_job`** komprimiert die bestehenden Zeilen
aller Wissensspeicher (`documents-data` in jeder Wissensdatenbank) neu. Führen Sie ihn einmal pro Deployment aus, nach
dem ersten Deployment mit der Einstellung. Er wird manuell gestartet und nie geplant.

### Vorbereitung

1. **Prüfen Sie, ob die Einstellung aktiv ist.** Der folgende Befehl muss `lz4` ausgeben:

   ```bash
   docker exec postgres-ferretdb psql -U "$MONGO_USERNAME" -d postgres -Atc 'show default_toast_compression'
   ```

   Gibt er `pglz` aus, erstellen Sie den Container mit derselben Compose-Datei, demselben Projektverzeichnis und
   derselben Env-Datei neu, die Ihr Deployment immer verwendet, zum Beispiel im Repository-Root mit
   `docker compose -f infra/docker-compose.<stage>.yml --env-file .env up -d postgres-ferretdb`. FerretDB ist dabei
   einige Sekunden nicht erreichbar. `docker restart` genügt nicht, weil der Container dann seinen alten Befehl behält.

   ::: warning
   Das Datenverzeichnis (`VOLUME_ROOT`, standardmässig `./.docker-volumes`) wird relativ zum Ordner der Compose-Datei
   aufgelöst. Eine Compose-Datei aus einem anderen Checkout oder Ordner bindet ein **leeres** Datenverzeichnis ein, und
   FerretDB liefert dann eine leere Instanz aus. Prüfen Sie danach in der Ausgabe von `docker inspect postgres-ferretdb`, dass `Mounts` → `Source`
   Ihr übliches Datenverzeichnis ist.
   :::

2. **Prüfen Sie Arbeitsumfang und Platzbedarf.** Führen Sie die Abfrage in
   `docker exec -it postgres-ferretdb psql -U "$MONGO_USERNAME" -d postgres` aus; `\gexec` führt eine Zählung pro
   Wissensdatenbank aus:

   ```sql
   select format(
       'select %L as database, count(*) filter (where pg_column_compression(document) = ''pglz'') as pglz_rows, '
       'count(*) as rows, pg_size_pretty(pg_total_relation_size(%L)) as size from documentdb_data.documents_%s',
       database_name, 'documentdb_data.documents_' || collection_id, collection_id)
   from documentdb_api_catalog.collections where collection_name = 'documents-data' \gexec
   ```

   Planen Sie freien Platz von etwa einem Drittel der Gesamtgrösse der Wissensspeicher ein: Die neu geschriebenen
   Tabellen wachsen um etwa ein Viertel und behalten diese Grösse.

3. **Wählen Sie ein ruhiges Zeitfenster**: kein Backup fällig und keine größere Ingestion im Gang.

### Job ausführen

1. Öffnen Sie in der Backup-Dagster-UI (`http://localhost:3004`) **Jobs → `ferretdb_lz4_rewrite_job`** und starten Sie
   ihn. Er bleibt *Queued*, solange ein Backup, Restore, Cleanup oder Repack den `postgres-mutex` hält.
2. **Prüfen Sie nach dem Lauf die Metadaten:**
   - `pglz_rows_after` ist `0`;
   - `collections_rewritten` nennt die neu geschriebenen Wissensdatenbanken;
   - `collections_skipped` zählt die, in denen keine pglz-Zeilen mehr waren.
3. **Starten Sie ihn optional ein zweites Mal.** Jede Collection wird dann übersprungen, was bestätigt, dass die
   Migration abgeschlossen ist.

Der Job läuft im laufenden Betrieb. Für jede Collection, die noch pglz-Zeilen hat:

- setzt er auf jeweils 50 Dokumenten ein temporäres Feld `_lz4_rewrite` auf oberster Ebene und entfernt es wieder;
  Inhalt und Schlüsselreihenfolge der Dokumente bleiben dabei unverändert;
- führt er alle 500 Dokumente `VACUUM` aus, damit der Platz der ersetzten Zeilenversionen wiederverwendet wird, und am
  Ende `VACUUM (ANALYZE)`.

Die Ingestion kann währenddessen weiter schreiben.

### Was zu erwarten ist

- **Dauer und Schreiblast:** Auf dem Dev-Stack dauerten 5'400 Zeilen (534 MB, meist Dokumente mit 100k Zeichen) 4,3
  Minuten. Jede Zeile wird zweimal geschrieben, das WAL wächst also um etwa die doppelte neu geschriebene Grösse. Bei
  grossen Speichern führen Sie den Job ausserhalb von Ingestion-Spitzen aus.
- **Der Speicherverbrauch wächst leicht und bleibt.** Derselbe Lauf liess die Tabellen von 534 auf 673 MB wachsen
  (+26 %). VACUUM macht Platz innerhalb von PostgreSQL wiederverwendbar, gibt ihn aber nicht an das Betriebssystem
  zurück; neue Ingestion füllt ihn mit der Zeit. `VACUUM FULL` würde ihn sofort zurückgeben, aber seine exklusive
  Sperre blockiert FerretDB, also führen Sie es nie während der Arbeitszeit aus.
- **Andere Collections** (Agent-Events, Threads, Konversationen) wechseln zu lz4, sobald ihre Zeilen geschrieben werden.
  Sie brauchen keinen Job.
- **Restores** schreiben jede Zeile mit dem Standard des Zielservers. Ein Restore auf einen Server mit der Einstellung
  braucht danach keinen Job; ein Restore auf einen Server ohne sie bringt pglz zurück.

### Häufige Fehler

| Symptom                                                             | Ursache                                                                                                               | Lösung                                                                                                                                           |
| ------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Schlägt fehl mit `default_toast_compression is pglz, not lz4`       | Die Einstellung ist nicht aktiv: Das Deployment lief nicht, oder der Container wurde neu gestartet statt neu erstellt | `postgres-ferretdb` wie oben mit `up -d` neu erstellen, dann erneut starten                                                                      |
| Bleibt *Queued*                                                     | Ein anderer Postgres-Job hält den Mutex                                                                               | Warten; das Backup nicht abbrechen                                                                                                               |
| Erfolgreich mit `skipped: MAINTENANCE_DISABLED`                     | `BACKUP_MAINTENANCE_DISABLED` ist `true`                                                                              | Für den Lauf auf `false` setzen                                                                                                                  |
| Verbindung zu `ferretdb:27017` abgelehnt                            | FerretDB läuft nicht, oder eine angepasste Compose-Datei hat `backup-code` aus dem Netzwerk `data` entfernt           | FerretDB starten oder das Netzwerk wiederherstellen                                                                                              |
| Schlägt fehl mit `N rows are still pglz after the rewrite`          | Zeilen konnten nicht neu geschrieben werden, z. B. weil FerretDB einen Schreibvorgang abgelehnt hat                   | Run-Log prüfen, dann erneut starten. Fertige Collections werden übersprungen                                                                     |
| Bricht mittendrin ab (Platte voll, Deployment, Verbindung verloren) | Der Lauf wurde unterbrochen                                                                                           | Bei Bedarf Platz schaffen, dann erneut starten. Übrig gebliebene `_lz4_rewrite`-Felder werden zuerst entfernt, ein erneuter Lauf ist also sicher |

Von Hand mit `UPDATE … SET document = document` neu zu komprimieren funktioniert nicht: PostgreSQL kopiert den
komprimierten Wert unverändert.

Ein **Rollback** bedeutet, das Flag `-c default_toast_compression=lz4` aus `postgres-ferretdb` zu entfernen. Neue Zeilen
sind dann wieder pglz, und lz4-Zeilen bleiben lesbar, es muss also nichts zurückmigriert werden. Jedes künftige
`postgres-ferretdb`-Image muss mit lz4-Unterstützung gebaut sein (`pg_config --configure | grep lz4`).

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
