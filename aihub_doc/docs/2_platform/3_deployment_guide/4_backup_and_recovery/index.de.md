---
title: Sicherung und Wiederherstellung
source_sha: 29cc0d310537befad9daa7d4dfeec7f77fe31909c030554fb787a86fb86c9b8b
---

# Sicherung und Wiederherstellung

## Übersicht

Jede Tenant-Instanz verfügt über unabhängige Backups. Die Datenisolation zwischen den Tenants ist gewährleistet.
Wiederherstellungsvorgänge beeinflussen andere Tenants nicht.

## Sicherungsansätze

Sie können den AI-Hub entweder mithilfe von VM-Snapshots oder komponentenbasierten Backups sichern.

VM-Snapshots erfassen den gesamten Zustand der virtuellen Maschine. Sie stellen das gesamte System auf einmal wieder
her. Komponentenbasiertes Backup behandelt individuelle Datenspeicher separat, sodass Sie spezifische Teile
wiederherstellen können.

---

## VM-Snapshots

VM-Snapshots erfassen alles: Betriebssystem, Docker, Daten, Konfiguration. Sie stellen die gesamte VM in einem einzigen
Vorgang wieder her. Es sind keine Backup-Skripte erforderlich. Alle Dienste sind zum gleichen Zeitpunkt konsistent.

Die Backup-Größen sind groß, da Sie die gesamte Festplatte kopieren. Backup-Zeiten sind länger. Sie können einzelne
Datenbanken nicht selektiv wiederherstellen. Die VM muss gestoppt werden, oder Sie benötigen einen Snapshot-fähigen
Hypervisor.

Stoppen Sie AI-Hub-Dienste vor dem Erstellen eines Snapshots mit `docker compose down`. Alternativ verwenden Sie
anwendungskonsistente Snapshots (Azure mit VM-Agent, VMware mit Quiesce). Erstellen Sie Snapshots vor größeren Updates.
Testen Sie Wiederherstellungen regelmäßig.

---

## Komponentenbasiertes Backup

### Was gesichert werden muss

PostgreSQL speichert mehrere Datenbanken: OpenWebUI, Phoenix, Dagster und LiteLLM. Eine separate PostgreSQL-Instanz
speichert das FerretDB-Backend. Verwenden Sie `pg_basebackup` für vollständige Backups und WAL-Archivierung für
Point-in-Time-Recovery.

FerretDB speichert Agentenkonfigurationen, Prozessdefinitionen, Chat-Verläufe, Benutzersitzungen und Metadaten der
Wissensdatenbank. Das PostgreSQL-Backup für die FerretDB-Instanz deckt dies ab. Optional können Sie MongoDB-formatierte
Exporte für die Portabilität erstellen.

Milvus speichert Vektor-Embeddings für RAG. Exportieren Sie Sammlungen in S3-kompatiblen Speicher. Embeddings können bei
Bedarf aus Quelldokumenten neu generiert werden.

SeaweedFS speichert vom Benutzer hochgeladene Dokumente, RAG-Wissensdatenbankdateien und Chat-Anhänge. Verwenden Sie
S3-kompatible Sync-Tools.

Valkey speichert Cache-Daten und WebSocket-Sitzungsstatus für OpenWebUI. Valkey persistiert automatisch auf der
Festplatte. Sichern Sie das Datenvolume.

NATS speichert Ereignis-Streams und Nachrichtenpersistenz für die ereignisgesteuerte Architektur. Sichern Sie das
Datenvolume.

etcd speichert Milvus-Metadaten und Service-Discovery-Informationen. Verwenden Sie ein Snapshot-basiertes Backup.

Die Konfiguration umfasst Umgebungsvariablen, SSL-Zertifikate und Docker-Compose-Dateien. Verschlüsseln Sie Backups.
Speichern Sie Verschlüsselungsschlüssel separat (HSM, Schlüsselverwaltungsdienste, mehrere sichere Orte).

---

## Backup-Automatisierung

Automatisieren Sie Backup-Aufgaben mit Cron oder ähnlichen Scheduler-Tools. Planen Sie Backups in Zeiten geringer
Auslastung, um Leistungseinbußen zu vermeiden. Überprüfen Sie regelmäßig die Integrität der Backups und lassen Sie sich
bei Fehlern benachrichtigen.

---
