---
title: Sicherung und Wiederherstellung
source_sha: d0d764cec0fa0c21606cbcc4e8e725cb82786da276e095aaf7e47f5df88408b8
---

# Sicherung und Wiederherstellung

## Übersicht

Jede Tenant-Instanz verfügt über unabhängige Backups. Datenisolation zwischen den Tenants. Wiederherstellungsvorgänge
beeinflussen andere Tenants nicht.

## Backup-Ansätze

Sie können den AI-Hub mittels VM-Snapshots oder Komponenten-Backups sichern.

VM-Snapshots erfassen den gesamten Zustand der virtuellen Maschine. Sie stellen das gesamte System auf einmal wieder
her. Komponenten-Backups behandeln einzelne Datenspeicher separat, sodass Sie spezifische Teile wiederherstellen können.

---

## VM-Snapshots

VM-Snapshots erfassen alles: OS, Docker, Daten, Konfiguration. Sie stellen die gesamte VM in einem einzigen Vorgang
wieder her. Es werden keine Backup-Skripte benötigt. Alle Dienste sind zum gleichen Zeitpunkt konsistent.

Backup-Größen sind groß, da Sie die gesamte Festplatte kopieren. Backup-Zeiten sind länger. Sie können einzelne
Datenbanken nicht selektiv wiederherstellen. Die VM muss gestoppt werden, oder Sie benötigen einen Snapshot-fähigen
Hypervisor.

Stoppen Sie AI-Hub-Dienste, bevor Sie einen Snapshot mit `docker compose down` erstellen. Alternativ können Sie
anwendungskonsistente Snapshots verwenden (Azure mit VM-Agent, VMware mit Quiescing). Erstellen Sie Snapshots vor
größeren Updates. Testen Sie Wiederherstellungen regelmäßig.

---

## Komponenten-Backups

### Was gesichert werden soll

PostgreSQL speichert mehrere Datenbanken: OpenWebUI, Phoenix, Dagster und LiteLLM. Eine separate PostgreSQL-Instanz
speichert das FerretDB-Backend. Verwenden Sie pg_basebackup für vollständige Backups und WAL-Archivierung für die
Point-in-Time-Wiederherstellung.

FerretDB speichert Agent-Konfigurationen, Prozessdefinitionen, Chat-Verläufe, Benutzersitzungen und Metadaten der
Wissensdatenbank. Das PostgreSQL-Backup für die FerretDB-Instanz deckt dies ab. Optional können Sie MongoDB-formatige
Exporte für die Portabilität erstellen.

Milvus speichert Vektor-Embeddings für RAG. Exportieren Sie Collections in S3-kompatiblen Speicher. Embeddings können
bei Bedarf aus Quelldokumenten neu generiert werden.

SeaweedFS speichert vom Benutzer hochgeladene Dokumente, RAG-Wissensdatenbankdateien und Chat-Anhänge. Verwenden Sie
S3-kompatible Synchronisierungstools.

Valkey speichert Cache-Daten und den WebSocket-Sitzungsstatus für OpenWebUI. Valkey persistiert automatisch auf der
Festplatte. Sichern Sie das Datenvolume.

NATS speichert Ereignisströme und Nachrichtenpersistenz für die ereignisgesteuerte Architektur. Sichern Sie das
Datenvolume.

etcd speichert Milvus-Metadaten und Service-Discovery-Informationen. Verwenden Sie Snapshot-basierte Backups.

Die Konfiguration umfasst Umgebungsvariablen, SSL-Zertifikate und Docker Compose-Dateien. Verschlüsseln Sie Backups.
Speichern Sie Verschlüsselungsschlüssel separat (HSM, Schlüsselverwaltungsdienste, mehrere sichere Speicherorte).

---

## Backup-Automatisierung

Automatisieren Sie Backup-Aufgaben mit Cron oder ähnlichen Planern. Planen Sie Backups während Perioden geringer
Nutzung, um Leistungseinbußen zu vermeiden. Überprüfen Sie regelmäßig die Backup-Integrität und alarmieren Sie bei
Fehlern.

---
