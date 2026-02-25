---
title: Sicherung und Wiederherstellung
source_sha: fa1fc5c429e6a007879a92c6aa2099c00781971f997932f5375b79a9a6c77cad
---

# Sicherung und Wiederherstellung

## Übersicht

Jede Instanz verfügt über unabhängige Backups. Datenisolation zwischen Instanzen. Wiederherstellungsvorgänge
beeinflussen andere Instanzen nicht.

::: info Kontext Multi-Instancing
Dieses Kapitel geht von einem Multi-Instancing-Deployment-Modell aus, bei dem jede Organisation ihre eigene isolierte
AI-Hub-Instanz besitzt. Für Multi-Tenancy (logische Trennung innerhalb einer einzelnen Instanz) siehe
[Multi-Tenancy](../../16_multi_tenancy/).
:::

## Backup-Ansätze

Sie können den AI-Hub mittels VM-Snapshots oder Komponenten-Level-Backups sichern.

VM-Snapshots erfassen den gesamten Zustand der virtuellen Maschine. Sie stellen das gesamte System auf einmal wieder
her. Komponenten-Level-Backups handhaben einzelne Datenspeicher separat, sodass Sie bestimmte Teile wiederherstellen
können.

______________________________________________________________________

## VM-Snapshots

VM-Snapshots erfassen alles: OS, Docker, Daten, Konfiguration. Sie stellen die gesamte VM in einem einzigen Vorgang
wieder her. Es werden keine Backup-Skripte benötigt. Alle Services sind zum selben Zeitpunkt konsistent.

Die Backup-Größen sind groß, da Sie die gesamte Festplatte kopieren. Backup-Zeiten sind länger. Sie können einzelne
Datenbanken nicht selektiv wiederherstellen. Die VM muss gestoppt werden, oder Sie benötigen einen Snapshot-fähigen
Hypervisor.

Stoppen Sie AI-Hub-Services vor dem Erstellen eines Snapshots mit `docker compose down`. Alternativ verwenden Sie
anwendungskonsistente Snapshots (Azure mit VM-Agent, VMware mit Quiesce). Erstellen Sie Snapshots vor größeren Updates.
Testen Sie Wiederherstellungen regelmäßig.

______________________________________________________________________

## Komponenten-Level-Backups

### Was gesichert werden muss

PostgreSQL speichert mehrere Datenbanken: OpenWebUI, Langfuse, Dagster und LiteLLM. Eine separate PostgreSQL-Instanz
speichert das FerretDB-Backend. Verwenden Sie pg_basebackup für vollständige Backups und WAL Archiving für die
Point-in-Time-Recovery.

FerretDB speichert Agent-Konfigurationen, Prozessdefinitionen, Chat-Verläufe, Benutzer-Sessions und
Knowledge-Base-Metadaten. Das PostgreSQL-Backup für die FerretDB-Instanz deckt dies ab. Optional können Sie
MongoDB-formatierte Exporte für die Portabilität erstellen.

Milvus speichert Vektoreinbettungen für RAG. Exportieren Sie Collections in S3-kompatiblen Speicher. Einbettungen können
bei Bedarf aus Quelldokumenten neu generiert werden.

SeaweedFS speichert vom Benutzer hochgeladene Dokumente, RAG-Knowledge-Base-Dateien und Chat-Anhänge. Der SeaweedFS
Filer verwendet etcd für die Metadatenspeicherung (gesichert mit etcd-Snapshots unten). Sichern Sie die eigentlichen
Dateidaten mit S3-kompatiblen Synchronisierungstools.

Valkey speichert Cache-Daten und WebSocket-Session-Status für OpenWebUI. Valkey persistiert automatisch auf der
Festplatte. Sichern Sie das Datenvolumen.

NATS speichert Event-Streams und Nachrichtenpersistenz für die ereignisgesteuerte Architektur. Sichern Sie das
Datenvolumen.

etcd speichert Milvus-Koordinationsmetadaten, SeaweedFS-Filer-Metadaten und Service-Discovery-Informationen. Verwenden
Sie Snapshot-basierte Backups.

Die Konfiguration umfasst Umgebungsvariablen, SSL-Zertifikate und Docker Compose-Dateien. Verschlüsseln Sie Backups.
Speichern Sie Verschlüsselungsschlüssel separat (HSM, Key Management Services, mehrere sichere Speicherorte).

______________________________________________________________________

## Backup-Automatisierung

Automatisieren Sie Backup-Aufgaben mit Cron oder ähnlichen Schedulern. Planen Sie Backups während Perioden geringer
Auslastung, um Leistungseinbußen zu vermeiden. Überprüfen Sie die Backup-Integrität regelmäßig und alarmieren Sie bei
Fehlern.

______________________________________________________________________
