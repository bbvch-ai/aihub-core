---
title: Backup und Wiederherstellung
source_sha: "5f5edc4d994e8ac0a8ec7f01a10f9ca081f820a36eb89d8d606b019fa2563a46"
---

# Backup und Wiederherstellung

## Übersicht

Jede Instanz verfügt über unabhängige Backups. Die Daten sind zwischen den Instanzen isoliert. Wiederherstellungsvorgänge beeinträchtigen andere Instanzen nicht.

::: info Multi-Instancing-Kontext
Dieses Kapitel setzt ein Multi-Instancing-Deployment-Modell voraus, bei dem jede Organisation ihre eigene isolierte AI-Hub-Instanz besitzt.
Für Multi-Tenancy (logische Trennung innerhalb einer Einzelinstanz) siehe [Multi-Tenancy](../../15_multi_tenancy/).
:::

## Backup-Ansätze

Sie können den AI-Hub entweder mit VM-Snapshots oder mit komponentenspezifischen Backups sichern.

VM-Snapshots erfassen den gesamten Zustand der virtuellen Maschine. Sie stellen das gesamte System auf einmal wieder her. Komponentenspezifische Backups behandeln einzelne Datenspeicher separat, sodass Sie bestimmte Teile wiederherstellen können.

---

## VM-Snapshots

VM-Snapshots erfassen alles: OS, Docker, Daten, Konfiguration. Sie stellen die gesamte VM in einem einzigen Vorgang wieder her. Es sind keine Backup-Skripte erforderlich. Alle Services sind zum gleichen Zeitpunkt konsistent.

Die Backup-Größen sind groß, da Sie die gesamte Festplatte kopieren. Die Backup-Zeiten sind länger. Sie können einzelne Datenbanken nicht selektiv wiederherstellen. Die VM muss gestoppt werden, oder Sie benötigen einen Snapshot-fähigen Hypervisor.

Stoppen Sie die AI-Hub-Services, bevor Sie einen Snapshot mit `docker compose down` erstellen. Alternativ können Sie anwendungskonsistente Snapshots verwenden (Azure mit VM-Agent, VMware mit Quiesce). Erstellen Sie Snapshots vor größeren Updates. Testen Sie Wiederherstellungen regelmäßig.

---

## Komponentenspezifische Backups

### Was gesichert werden muss

PostgreSQL speichert mehrere Datenbanken: OpenWebUI, Phoenix, Dagster und LiteLLM. Eine separate PostgreSQL-Instanz speichert das FerretDB-Backend. Verwenden Sie `pg_basebackup` für vollständige Backups und WAL-Archivierung für die Point-in-Time-Recovery.

FerretDB speichert Agent-Konfigurationen, Prozessdefinitionen, Chat-Verläufe, Benutzersitzungen und Metadaten der Wissensbasis. Das PostgreSQL-Backup für die FerretDB-Instanz deckt dies ab. Optional können Sie Exporte im MongoDB-Format für die Portabilität erstellen.

Milvus speichert Vector Embeddings für RAG. Exportieren Sie Sammlungen in S3-kompatiblen Speicher. Embeddings können bei Bedarf aus Quelldokumenten neu generiert werden.

SeaweedFS speichert vom Benutzer hochgeladene Dokumente, RAG-Wissensbasisdateien und Chat-Anhänge. Verwenden Sie S3-kompatible Synchronisationstools.

Valkey speichert Cache-Daten und WebSocket-Sitzungsstatus für OpenWebUI. Valkey persistiert automatisch auf der Festplatte. Sichern Sie das Datenvolume.

NATS speichert Ereignisströme und Nachrichtenpersistenz für die ereignisgesteuerte Architektur. Sichern Sie das Datenvolume.

etcd speichert Milvus-Metadaten und Service-Discovery-Informationen. Verwenden Sie Snapshot-basierte Backups.

Die Konfiguration umfasst Umgebungsvariablen, SSL-Zertifikate und Docker-Compose-Dateien. Verschlüsseln Sie Backups. Speichern Sie Verschlüsselungsschlüssel separat (HSM, Key Management Services, mehrere sichere Orte).

---

## Backup-Automatisierung

Automatisieren Sie Backup-Aufgaben mit Cron oder ähnlichen Schedulern. Planen Sie Backups in Perioden geringer Auslastung, um Leistungseinbußen zu vermeiden. Überprüfen Sie regelmäßig die Backup-Integrität und alarmieren Sie bei Fehlern.
