---
title: Sicherung und Wiederherstellung
source_sha: a4f725d5da90be11bbe788b8d345cecdc52b1614d466e6082532bd88b689c800
---

# Sicherung und Wiederherstellung

## Überblick

Jede Instanz verfügt über unabhängige Backups. Datenisolation zwischen den Instanzen. Wiederherstellungsvorgänge wirken
sich nicht auf andere Instanzen aus.

::: info Kontext von Multi-Instancing
Dieses Kapitel geht von einem Multi-Instancing-Bereitstellungsmodell aus, bei dem jede Organisation ihre eigene
isolierte Swiss AI Hub-Instanz hat. Für Multi-Tenancy (logische Trennung innerhalb einer einzelnen Instanz) siehe
[Multi-Tenancy](../../16_multi_tenancy/).
:::

## Sicherungsansätze

Sie können den Swiss AI Hub mithilfe von VM-Snapshots oder Komponenten-Backups sichern.

VM-Snapshots erfassen den gesamten Zustand der virtuellen Maschine. Sie stellen das gesamte System auf einmal wieder
her. Komponenten-Backups behandeln einzelne Datenspeicher separat, sodass Sie bestimmte Teile wiederherstellen können.

______________________________________________________________________

## VM-Snapshots

VM-Snapshots erfassen alles: OS, Docker, Daten, Konfiguration. Sie stellen die gesamte VM in einem Vorgang wieder her.
Es werden keine Backup-Skripte benötigt. Alle Services sind zum gleichen Zeitpunkt konsistent.

Backup-Grössen sind gross, da Sie die gesamte Festplatte kopieren. Backup-Zeiten sind länger. Sie können einzelne
Datenbanken nicht selektiv wiederherstellen. Die VM muss gestoppt werden, oder Sie benötigen einen Snapshot-fähigen
Hypervisor.

Stoppen Sie die Swiss AI Hub-Services, bevor Sie einen Snapshot mit `docker compose down` erstellen. Alternativ können
Sie anwendungskonsistente Snapshots verwenden (Azure mit VM-Agent, VMware mit Quiescing). Erstellen Sie Snapshots vor
grösseren Updates. Testen Sie Wiederherstellungen regelmässig.

______________________________________________________________________

## Komponenten-Backups

### Was gesichert werden muss

PostgreSQL speichert mehrere Datenbanken: OpenWebUI, Langfuse, Dagster und LiteLLM. Eine separate PostgreSQL-Instanz
speichert das FerretDB-Backend. Verwenden Sie pg_basebackup für vollständige Backups und WAL Archiving für die
Point-in-Time-Recovery.

FerretDB speichert Agent-Konfigurationen, Prozessdefinitionen, Chat-Verläufe, Benutzersitzungen und Metadaten der
Wissensdatenbank. Das PostgreSQL-Backup für die FerretDB-Instanz deckt dies ab. Optional können Sie
MongoDB-Format-Exporte für die Portabilität erstellen.

Milvus speichert Vektoreinbettungen für RAG. Exportieren Sie Sammlungen in S3-kompatiblen Speicher. Einbettungen können
bei Bedarf aus Quelldokumenten neu generiert werden.

SeaweedFS speichert von Benutzern hochgeladene Dokumente, RAG-Wissensdatenbankdateien und Chat-Anhänge. Der SeaweedFS
Filer verwendet etcd für die Metadatenspeicherung (gesichert mit etcd-Snapshots unten). Sichern Sie die eigentlichen
Dateidaten mit S3-kompatiblen Synchronisierungstools.

Valkey speichert Cache-Daten und den WebSocket-Sitzungsstatus für OpenWebUI. Valkey persistiert automatisch auf der
Festplatte. Sichern Sie das Datenvolume.

NATS speichert Event-Streams und die Nachrichtenpersistenz für die ereignisgesteuerte Architektur. Sichern Sie das
Datenvolume.

etcd speichert Milvus-Koordinationsmetadaten, SeaweedFS Filer-Metadaten und Service-Discovery-Informationen. Verwenden
Sie ein Snapshot-basiertes Backup.

Die Konfiguration umfasst Umgebungsvariablen, SSL-Zertifikate und Docker Compose-Dateien. Verschlüsseln Sie Backups.
Speichern Sie Verschlüsselungsschlüssel separat (HSM, Schlüsselverwaltungsdienste, mehrere sichere Speicherorte).

______________________________________________________________________

## Backup-Automatisierung

Automatisieren Sie Backup-Aufgaben mit Cron oder ähnlichen Schedulern. Planen Sie Backups während Perioden geringer
Auslastung, um Leistungseinbussen zu vermeiden. Überprüfen Sie regelmässig die Backup-Integrität und alarmieren Sie bei
Fehlern.

______________________________________________________________________
