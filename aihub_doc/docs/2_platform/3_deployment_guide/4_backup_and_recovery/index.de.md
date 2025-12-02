---
title: Sicherung und Wiederherstellung
source_sha: "7acfc89933335b101ef5bc8c7858911ba15dfd6806dca60fbaceaef557c919b7"
---

# Sicherung und Wiederherstellung

## Übersicht

Jede Instanz verfügt über unabhängige Backups. Datenisolation zwischen den Instanzen. Wiederherstellungsvorgänge wirken sich nicht auf andere Instanzen aus.

::: info Kontext für Multi-Instancing
Dieses Kapitel geht von einem Multi-Instanz-Deployment-Modell aus, bei dem jede Organisation ihre eigene isolierte AI-Hub-Instanz besitzt. Für Multi-Tenancy (logische Trennung innerhalb einer einzelnen Instanz) siehe [Multi-Tenancy](../../15_multi_tenancy/).
:::

## Backup-Ansätze

Sie können den AI-Hub mithilfe von VM-Snapshots oder komponentenbasierten Backups sichern.

VM-Snapshots erfassen den gesamten Zustand der virtuellen Maschine. Sie stellen das gesamte System auf einmal wieder her. Komponentenbasierten Backups behandeln einzelne Datenspeicher separat, sodass Sie bestimmte Teile wiederherstellen können.

---

## VM-Snapshots

VM-Snapshots erfassen alles: OS, Docker, Daten, Konfiguration. Sie stellen die gesamte VM in einem einzigen Vorgang wieder her. Es werden keine Backup-Skripte benötigt. Alle Services sind zum gleichen Zeitpunkt konsistent.

Backup-Größen sind groß, da Sie die gesamte Festplatte kopieren. Backup-Zeiten sind länger. Sie können einzelne Datenbanken nicht selektiv wiederherstellen. Die VM muss gestoppt werden, oder Sie benötigen einen Snapshot-fähigen Hypervisor.

Stoppen Sie die AI-Hub-Services, bevor Sie einen Snapshot mit `docker compose down` erstellen. Alternativ verwenden Sie anwendungskonsistente Snapshots (Azure mit VM-Agent, VMware mit Quiesce). Erstellen Sie Snapshots vor größeren Updates. Testen Sie Wiederherstellungen regelmäßig.

---

## Komponentenbasierten Backups

### Was gesichert werden muss

PostgreSQL speichert mehrere Datenbanken: OpenWebUI, Phoenix, Dagster und LiteLLM. Eine separate PostgreSQL-Instanz speichert das FerretDB-Backend. Verwenden Sie pg_basebackup für vollständige Backups und WAL-Archivierung für die Point-in-Time-Recovery.

FerretDB speichert Agent-Konfigurationen, Prozessdefinitionen, Chat-Verläufe, Benutzersitzungen und Metadaten der Wissensbasis. Das PostgreSQL-Backup für die FerretDB-Instanz deckt dies ab. Sie können optional Exporte im MongoDB-Format für die Portabilität erstellen.

Milvus speichert Vektoreinbettungen für RAG. Exportieren Sie Sammlungen in S3-kompatiblen Speicher. Einbettungen können bei Bedarf aus Quelldokumenten neu generiert werden.

SeaweedFS speichert vom Benutzer hochgeladene Dokumente, RAG-Wissensbasisdateien und Chat-Anhänge. Der SeaweedFS Filer verwendet etcd für die Metadatenspeicherung (gesichert mit etcd-Snapshots unten). Sichern Sie die eigentlichen Dateidaten mithilfe von S3-kompatiblen Synchronisierungstools.

Valkey speichert Cache-Daten und WebSocket-Sitzungsstatus für OpenWebUI. Valkey persistiert automatisch auf der Festplatte. Sichern Sie das Datenvolumen.

NATS speichert Event-Streams und Nachrichtenpersistenz für die ereignisgesteuerte Architektur. Sichern Sie das Datenvolumen.

etcd speichert Milvus-Koordinationsmetadaten, SeaweedFS-Filer-Metadaten und Service-Discovery-Informationen. Verwenden Sie ein Snapshot-basiertes Backup.

Die Konfiguration umfasst Umgebungsvariablen, SSL-Zertifikate und Docker-Compose-Dateien. Verschlüsseln Sie Backups. Speichern Sie Verschlüsselungsschlüssel separat (HSM, Key Management Services, mehrere sichere Standorte).

---

## Backup-Automatisierung

Automatisieren Sie Backup-Aufgaben mit Cron oder ähnlichen Schedulern. Planen Sie Backups in Zeiten geringer Auslastung, um Leistungseinbußen zu vermeiden. Überprüfen Sie regelmäßig die Backup-Integrität und alarmieren Sie bei Fehlern.
