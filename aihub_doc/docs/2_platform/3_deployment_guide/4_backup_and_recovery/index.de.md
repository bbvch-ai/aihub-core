---
title: Backup und Wiederherstellung
source_sha: 9961b32561a83f20d16be4b3f5c7292087a562c61a13f144c17b11f7f3b94409
---

# Backup und Wiederherstellung

## Übersicht

Jede Instanz verfügt über unabhängige Backups. Die Datenisolation zwischen Instanzen ist gewährleistet.
Wiederherstellungsvorgänge beeinflussen andere Instanzen nicht.

::: info Kontext Multi-Instancing
Dieses Kapitel geht von einem Multi-Instancing-Deployment-Modell aus, bei dem jede Organisation ihre eigene isolierte
AI-Hub-Instanz hat. Für Multi-Tenancy (logische Trennung innerhalb einer einzelnen Instanz) siehe
[Multi-Tenancy](../../16_multi_tenancy/).
:::

## Backup-Ansätze

Sie können den AI-Hub mit VM-Snapshots oder komponentenbasierten Backups sichern.

VM-Snapshots erfassen den gesamten Zustand der virtuellen Maschine. Sie stellen das gesamte System auf einmal wieder
her. Komponentenbasierten Backups handhaben individuelle Datenspeicher separat, sodass Sie bestimmte Teile
wiederherstellen können.

---

## VM-Snapshots

VM-Snapshots erfassen alles: OS, Docker, Daten, Konfiguration. Sie stellen die gesamte VM in einem Vorgang wieder her.
Es werden keine Backup-Skripte benötigt. Alle Services sind zum gleichen Zeitpunkt konsistent.

Die Backup-Größen sind groß, da Sie die gesamte Festplatte kopieren. Backup-Zeiten sind länger. Sie können einzelne
Datenbanken nicht selektiv wiederherstellen. Die VM muss gestoppt werden, oder Sie benötigen einen Snapshot-fähigen
Hypervisor.

Stoppen Sie AI-Hub-Services, bevor Sie einen Snapshot mit `docker compose down` erstellen. Alternativ verwenden Sie
anwendungskonsistente Snapshots (Azure mit VM-Agent, VMware mit Quiesce). Erstellen Sie Snapshots vor größeren Updates.
Testen Sie Wiederherstellungen regelmäßig.

---

## Komponentenbasierten Backups

### Was zu sichern ist

PostgreSQL speichert mehrere Datenbanken: OpenWebUI, Phoenix, Dagster und LiteLLM. Eine separate PostgreSQL-Instanz
speichert das FerretDB-Backend. Verwenden Sie pg_basebackup für vollständige Backups und WAL-Archivierung für
Point-in-Time Recovery.

FerretDB speichert Agent-Konfigurationen, Prozessdefinitionen, Chat-Historien, Benutzersitzungen und
Knowledge-Base-Metadaten. Das PostgreSQL-Backup für die FerretDB-Instanz deckt dies ab. Sie können optional
MongoDB-formatierte Exporte für die Portabilität erstellen.

Milvus speichert Vektor-Embeddings für RAG. Exportieren Sie Kollektionen in S3-kompatiblen Speicher. Embeddings können
bei Bedarf aus Quelldokumenten regeneriert werden.

SeaweedFS speichert vom Benutzer hochgeladene Dokumente, RAG Knowledge-Base-Dateien und Chat-Anhänge. Der SeaweedFS
Filer verwendet etcd für die Metadatenspeicherung (gesichert mit etcd-Snapshots unten). Sichern Sie die eigentlichen
Dateidaten mit S3-kompatiblen Synchronisierungstools.

Valkey speichert Cache-Daten und den WebSocket-Sitzungsstatus für OpenWebUI. Valkey persistiert automatisch auf der
Festplatte. Sichern Sie das Datenvolumen.

NATS speichert Event-Streams und Message Persistence für die Event-driven Architektur. Sichern Sie das Datenvolumen.

etcd speichert Milvus-Koordinationsmetadaten, SeaweedFS-Filer-Metadaten und Service Discovery Informationen. Verwenden
Sie Snapshot-basierte Backups.

Die Konfiguration umfasst Umgebungsvariablen, SSL-Zertifikate und Docker Compose-Dateien. Verschlüsseln Sie Backups.
Speichern Sie Verschlüsselungsschlüssel separat (HSM, Key Management Services, mehrere sichere Standorte).

---

## Backup-Automatisierung

Automatisieren Sie Backup-Aufgaben mit Cron oder ähnlichen Schedulern. Planen Sie Backups während Perioden geringer
Auslastung, um Leistungseinbußen zu vermeiden. Überprüfen Sie regelmäßig die Backup-Integrität und alarmieren Sie bei
Fehlern.
