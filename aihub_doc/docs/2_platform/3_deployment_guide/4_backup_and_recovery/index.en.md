---
title: Backup and Recovery
index: 4
---

# Backup and Recovery

## Overview

This guide describes backup and recovery procedures for AI-Hub deployments. The platform supports per-tenant instance isolation with independent backup strategies, ensuring complete data sovereignty and compliance with Swiss data protection regulations.

## Recovery Objectives

### Definitions

- **RTO (Recovery Time Objective)**: Maximum acceptable time to restore services after a disaster
- **RPO (Recovery Point Objective)**: Maximum acceptable data loss measured in time
- **WAL (Write-Ahead Log)**: PostgreSQL transaction log that records all database changes before they are written to data files, enabling point-in-time recovery

### Target Metrics

| Deployment Type | RTO | RPO | Backup Frequency |
|----------------|-----|-----|------------------|
| Production (VM/On-Premise) | 8 hours | 15 minutes | Automated/Daily |

---

## Backup Architecture

### Per-Tenant Backup Isolation

Each tenant instance maintains **independent backups** with no cross-tenant dependencies:

**Benefits**:
- Complete data isolation between tenants
- Tenant-specific compliance requirements (retention periods)
- Independent recovery without affecting other tenants
- Granular cost tracking per tenant

---

## Production Backup Strategy (VM/On-Premise)

### Overview

Production deployments require comprehensive backup across all data layers with automation, monitoring, and regular testing.

### Backup Approaches

There are two primary approaches to backing up production AI-Hub deployments:

1. **VM Snapshots (Simple)**: Capture the entire virtual machine state
2. **Component-Level Backups (Granular)**: Back up individual data stores separately

**VM snapshots** provide the simplest backup strategy with instant recovery, while **component-level backups** offer more flexibility, smaller backup sizes, and selective recovery.

---

## Approach 1: VM Snapshot (Simple Full Backup)

### Overview

VM snapshots provide the **simplest backup method** by capturing the entire virtual machine state, including all data, configuration, and system files. This is ideal for smaller deployments or when simplicity is prioritized over granular control.

### When to Use VM Snapshots

**Advantages**:
- ✅ Simple to implement and automate
- ✅ Captures everything (OS, Docker, data, configuration)
- ✅ Fastest disaster recovery (restore entire VM)
- ✅ No complex backup scripts needed
- ✅ Point-in-time consistency across all services

**Disadvantages**:
- ❌ Larger backup size (entire disk)
- ❌ Longer backup time
- ❌ Cannot selectively restore individual databases
- ❌ Requires VM to be stopped or snapshot-capable hypervisor

### Creating VM Snapshots

#### Swiss Cloud Providers

**Exoscale**:
```bash
# Create snapshot via CLI
exo compute instance snapshot create <instance-name> \
    --zone ch-gva-2

# Schedule automated snapshots
# (Configure via Exoscale console: Compute > Instances > Snapshots)
```

**Cloudscale.ch**:
```bash
# Create snapshot via API
curl -X POST https://api.cloudscale.ch/v1/servers/<server-uuid>/snapshots \
    -H "Authorization: Bearer <API_TOKEN>" \
    -H "Content-Type: application/json" \
    -d '{"name": "aihub-backup-2025-10-23"}'

# Automate with cron
0 2 * * * /usr/local/bin/cloudscale-snapshot.sh
```

**Azure VMs**:
```bash
# Create VM snapshot
az snapshot create \
    --resource-group aihub-prod \
    --name aihub-snapshot-$(date +%Y%m%d) \
    --source /subscriptions/<sub-id>/resourceGroups/aihub-prod/providers/Microsoft.Compute/disks/aihub-vm-disk

# Or create managed image (includes all disks)
az image create \
    --resource-group aihub-prod \
    --name aihub-image-$(date +%Y%m%d) \
    --source aihub-vm
```

#### On-Premise Hypervisors

**Proxmox VE**:
```bash
# Create snapshot
qm snapshot <vmid> <snapshot-name>

# Example: Daily automated snapshot
0 2 * * * qm snapshot 100 daily-backup-$(date +%Y%m%d)

# Cleanup old snapshots (keep 7 days)
qm listsnapshot 100 | grep daily-backup | tail -n +8 | xargs -I {} qm delsnapshot 100 {}
```

**VMware vSphere/ESXi**:
```bash
# Create snapshot via govc CLI
govc snapshot.create -vm aihub-prod "Backup $(date +%Y%m%d_%H%M%S)"

# Automated via PowerCLI
New-Snapshot -VM "aihub-prod" -Name "Backup-$(Get-Date -Format 'yyyyMMdd')" -Quiesce
```

**KVM/libvirt**:
```bash
# Create external snapshot (recommended for production)
virsh snapshot-create-as aihub-prod \
    snapshot-$(date +%Y%m%d) \
    "Daily backup" \
    --disk-only \
    --atomic

# Backup snapshot to separate storage
rsync -avz /var/lib/libvirt/images/aihub-prod.snapshot \
    /backups/vm-snapshots/
```

### Snapshot Retention Policy

```bash
# Example retention script for automated cleanup
#!/bin/bash
# File: /backups/scripts/cleanup-vm-snapshots.sh

RETENTION_DAYS=35

# Exoscale example
exo compute instance snapshot list | grep aihub | \
    awk -v date="$(date -d "-${RETENTION_DAYS} days" +%Y-%m-%d)" \
    '$2 < date {print $1}' | \
    xargs -I {} exo compute instance snapshot delete {}

# Azure example
az snapshot list --resource-group aihub-prod --query \
    "[?timeCreated < '$(date -d "-${RETENTION_DAYS} days" -u +%Y-%m-%dT%H:%M:%SZ)'].id" \
    -o tsv | xargs -I {} az snapshot delete --ids {}
```

### Recovery from VM Snapshot

**Full VM Restore**:

1. **Stop the current VM** (if it exists and is corrupted)
2. **Restore from snapshot**:
   - **Exoscale/Cloudscale**: Create new instance from snapshot via console
   - **Azure**: Create new VM from snapshot or managed image
   - **Proxmox**: `qm rollback <vmid> <snapshot-name>`
   - **VMware**: Right-click VM → Snapshots → Revert to Snapshot
   - **KVM**: `virsh snapshot-revert aihub-prod snapshot-name`
3. **Start the restored VM**
4. **Verify services**: `docker compose ps` and test endpoints

**Recovery Time**: Typically 15-30 minutes depending on VM size and cloud provider.

### Snapshot Best Practices

**Consistency**:
- Stop AI-Hub services before snapshot for consistency: `docker compose down`
- Or use application-consistent snapshots (e.g., Azure with VM agent, VMware with quiesce)

**Frequency**:
- **Daily snapshots**: Suitable for most production deployments
- **Pre-update snapshots**: Always snapshot before major updates
- **Weekly/monthly archives**: Keep long-term snapshots for compliance

**Testing**:
- Monthly: Restore snapshot to test environment and verify functionality
- Document actual RTO achieved during test restores

---

## Approach 2: Component-Level Backups (Granular)

### Overview

Component-level backups provide granular control by backing up individual data stores separately. This approach offers flexibility for selective recovery and smaller backup sizes.

### Data Stores to Back Up

| Component | Criticality | Backup Method | Frequency | Retention |
|-----------|-------------|---------------|-----------|-----------|
| PostgreSQL | CRITICAL | pg_basebackup + WAL | Full: Daily, WAL: Continuous | 35 days |
| FerretDB Documents | CRITICAL | PostgreSQL + mongodump | Daily + Monthly | 35 days |
| Milvus Vectors | HIGH | Collection export | Daily | 30 days |
| SeaweedFS Files | CRITICAL | S3 sync | Daily | 90 days |
| etcd Metadata | MEDIUM | Snapshot | Every 6 hours | 7 days |
| Configuration | CRITICAL | File backup | Daily | 90 days |
| SSL Certificates | CRITICAL | Encrypted backup | Weekly | 1 year |
| Docker Volumes | HIGH | Volume snapshot | Daily | 30 days |

---

## Backup Procedures (Component-Level)

### 1. PostgreSQL Database Backup

PostgreSQL stores multiple databases: OpenWebUI, Phoenix, Dagster, LiteLLM, and the FerretDB backend.

#### Full Backup (Daily)

**Method 1: pg_basebackup (Recommended)**

```bash
#!/bin/bash
# File: /backups/scripts/backup-postgres.sh

BACKUP_DIR="/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="${BACKUP_DIR}/${TIMESTAMP}"

# Create backup directory
mkdir -p "${BACKUP_PATH}"

# Perform base backup
pg_basebackup -h localhost -U postgres \
    -D "${BACKUP_PATH}" \
    -Ft -z -P \
    --wal-method=stream

# Verify backup
if [ $? -eq 0 ]; then
    echo "$(date): Backup successful: ${BACKUP_PATH}" >> /var/log/aihub-backup.log

    # Create a restore info file
    cat > "${BACKUP_PATH}/backup_info.txt" <<EOF
Backup Date: $(date)
PostgreSQL Version: $(psql -U postgres -t -c "SELECT version();")
Backup Method: pg_basebackup
EOF

    # Apply retention policy (keep last 35 days)
    find "${BACKUP_DIR}" -type d -mtime +35 -exec rm -rf {} \;
else
    echo "$(date): Backup FAILED" >> /var/log/aihub-backup.log
    exit 1
fi
```

**Method 2: pg_dump (Logical Backup)**

```bash
#!/bin/bash
# File: /backups/scripts/backup-postgres-logical.sh

BACKUP_DIR="/backups/postgres-logical"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATABASES=("openwebui" "phoenix" "dagster" "litellm" "ferretdb")

mkdir -p "${BACKUP_DIR}"

for DB in "${DATABASES[@]}"; do
    pg_dump -h localhost -U postgres -Fc \
        "${DB}" > "${BACKUP_DIR}/${DB}_${TIMESTAMP}.dump"

    if [ $? -eq 0 ]; then
        echo "$(date): ${DB} backup successful" >> /var/log/aihub-backup.log
    else
        echo "$(date): ${DB} backup FAILED" >> /var/log/aihub-backup.log
    fi
done

# Retention: 35 days
find "${BACKUP_DIR}" -name "*.dump" -mtime +35 -delete
```

#### Continuous WAL Archiving

**Setup WAL archiving** in PostgreSQL configuration:

```bash
# File: /var/lib/postgresql/data/postgresql.conf (or via docker volume)

# Enable WAL archiving
wal_level = replica
archive_mode = on
archive_command = 'rsync -a %p /backups/postgres-wal/%f'
archive_timeout = 300  # Force WAL segment switch every 5 minutes

# Retention
wal_keep_size = 1GB
```

**WAL Archive Management**:

```bash
#!/bin/bash
# File: /backups/scripts/cleanup-wal.sh

WAL_ARCHIVE="/backups/postgres-wal"
RETENTION_DAYS=7

# Clean up old WAL files (keep 7 days)
find "${WAL_ARCHIVE}" -name "*.gz" -mtime +${RETENTION_DAYS} -delete

echo "$(date): WAL cleanup complete" >> /var/log/aihub-backup.log
```

---

### 2. FerretDB (MongoDB-Compatible) Backup

FerretDB stores documents in PostgreSQL, so it's covered by PostgreSQL backups. However, for compliance and portability, also create MongoDB-format exports.

```bash
#!/bin/bash
# File: /backups/scripts/backup-ferretdb.sh

BACKUP_DIR="/backups/ferretdb"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="${BACKUP_DIR}/${TIMESTAMP}"

mkdir -p "${BACKUP_PATH}"

# MongoDB-style dump via FerretDB
mongodump \
    --uri="mongodb://admin:admin@localhost:27017/aihub?authSource=admin" \
    --out="${BACKUP_PATH}" \
    --gzip

if [ $? -eq 0 ]; then
    echo "$(date): FerretDB backup successful: ${BACKUP_PATH}" >> /var/log/aihub-backup.log

    # Retention: 35 days
    find "${BACKUP_DIR}" -type d -mtime +35 -exec rm -rf {} \;
else
    echo "$(date): FerretDB backup FAILED" >> /var/log/aihub-backup.log
    exit 1
fi
```

**What's Backed Up**:
- Agent configurations
- Process definitions
- Chat histories
- User sessions
- Knowledge base metadata

---

### 3. Milvus Vector Database Backup

Milvus stores vector embeddings for RAG. Backups export collections to S3-compatible storage.

```bash
#!/bin/bash
# File: /backups/scripts/backup-milvus.sh

BACKUP_DIR="/backups/milvus"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
MILVUS_HOST="localhost:19530"

mkdir -p "${BACKUP_DIR}"

# Export collections (requires Milvus backup tool or API)
# Option 1: Using Milvus Backup utility
milvus-backup create \
    --milvus-address="${MILVUS_HOST}" \
    --backup-name="backup_${TIMESTAMP}" \
    --collections="*" \
    --backup-dir="${BACKUP_DIR}"

# Option 2: Using Python API
python3 << 'EOF'
from pymilvus import connections, utility, Collection
import json
from datetime import datetime

connections.connect(host="localhost", port="19530")

collections = utility.list_collections()
backup_data = {
    "timestamp": datetime.now().isoformat(),
    "collections": collections
}

# Save collection metadata
with open("/backups/milvus/collections_metadata.json", "w") as f:
    json.dump(backup_data, f, indent=2)

print(f"Backed up {len(collections)} collections")
EOF

if [ $? -eq 0 ]; then
    echo "$(date): Milvus backup successful" >> /var/log/aihub-backup.log

    # Retention: 30 days
    find "${BACKUP_DIR}" -name "backup_*" -mtime +30 -exec rm -rf {} \;
else
    echo "$(date): Milvus backup FAILED" >> /var/log/aihub-backup.log
    exit 1
fi
```

**Important**: Vector embeddings can be **regenerated** from source documents. If backup storage is limited, prioritize PostgreSQL and SeaweedFS over Milvus.

---

### 4. SeaweedFS (File Storage) Backup

SeaweedFS stores user-uploaded documents, RAG knowledge base files, and chat attachments.

```bash
#!/bin/bash
# File: /backups/scripts/backup-seaweedfs.sh

BACKUP_DIR="/backups/seaweedfs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
S3_ENDPOINT="http://localhost:8333"
BUCKETS=("open-webui" "milvus" "playground")

mkdir -p "${BACKUP_DIR}/${TIMESTAMP}"

# Sync each bucket to backup directory
for BUCKET in "${BUCKETS[@]}"; do
    echo "Backing up bucket: ${BUCKET}"

    s3cmd sync \
        --host="${S3_ENDPOINT}" \
        --host-bucket="${S3_ENDPOINT}" \
        s3://${BUCKET}/ \
        "${BACKUP_DIR}/${TIMESTAMP}/${BUCKET}/"

    if [ $? -eq 0 ]; then
        echo "$(date): SeaweedFS bucket ${BUCKET} backup successful" >> /var/log/aihub-backup.log
    else
        echo "$(date): SeaweedFS bucket ${BUCKET} backup FAILED" >> /var/log/aihub-backup.log
    fi
done

# Retention: 90 days
find "${BACKUP_DIR}" -type d -mtime +90 -exec rm -rf {} \;
```

**Alternative: rsync from volumes**:

```bash
# Direct volume backup
rsync -av --delete \
    /var/lib/docker/volumes/seaweedfs-volume/_data/ \
    /backups/seaweedfs/${TIMESTAMP}/
```

---

### 5. etcd (Distributed Configuration) Backup

etcd stores Milvus metadata and service discovery information.

```bash
#!/bin/bash
# File: /backups/scripts/backup-etcd.sh

BACKUP_DIR="/backups/etcd"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ETCD_ENDPOINT="http://localhost:2379"

mkdir -p "${BACKUP_DIR}"

# Create etcd snapshot
etcdctl snapshot save "${BACKUP_DIR}/etcd-snapshot-${TIMESTAMP}.db" \
    --endpoints="${ETCD_ENDPOINT}"

if [ $? -eq 0 ]; then
    echo "$(date): etcd snapshot successful" >> /var/log/aihub-backup.log

    # Retention: 7 days
    find "${BACKUP_DIR}" -name "etcd-snapshot-*.db" -mtime +7 -delete
else
    echo "$(date): etcd snapshot FAILED" >> /var/log/aihub-backup.log
    exit 1
fi
```

---

### 6. Configuration and Secrets Backup

Configuration files, environment variables, and SSL certificates must be backed up securely.

```bash
#!/bin/bash
# File: /backups/scripts/backup-config.sh

BACKUP_DIR="/backups/config"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/config-${TIMESTAMP}.tar.gz.enc"
PROJECT_DIR="/opt/aihub"

mkdir -p "${BACKUP_DIR}"

# Create encrypted backup of configuration
tar -czf - \
    "${PROJECT_DIR}/.env" \
    "${PROJECT_DIR}/configs/" \
    "${PROJECT_DIR}/docker-compose*.yml" \
    "${PROJECT_DIR}/certs/" \
    | openssl enc -aes-256-cbc -salt -pbkdf2 -pass file:/root/.backup-key > "${BACKUP_FILE}"

if [ $? -eq 0 ]; then
    echo "$(date): Configuration backup successful" >> /var/log/aihub-backup.log

    # Retention: 90 days
    find "${BACKUP_DIR}" -name "config-*.tar.gz.enc" -mtime +90 -delete
else
    echo "$(date): Configuration backup FAILED" >> /var/log/aihub-backup.log
    exit 1
fi

# Backup encryption key to separate secure location
# IMPORTANT: Store /root/.backup-key in a safe, separate location!
```

**Encryption Key Management**:
- Store encryption key (`/root/.backup-key`) in a **secure, separate location**
- Consider using hardware security modules (HSM) or key management services
- Maintain key backups in multiple secure locations (safe, off-site)

---

### 7. Docker Volumes Backup (Alternative Method)

If using Docker volumes directly without application-level backups:

```bash
#!/bin/bash
# File: /backups/scripts/backup-docker-volumes.sh

BACKUP_DIR="/backups/docker-volumes"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
VOLUME_ROOT="${VOLUME_ROOT:-./.docker-volumes}"

mkdir -p "${BACKUP_DIR}"

# Stop services (optional, for consistent backup)
# docker compose down

# Backup all volumes
tar -czf "${BACKUP_DIR}/volumes-${TIMESTAMP}.tar.gz" \
    "${VOLUME_ROOT}"

if [ $? -eq 0 ]; then
    echo "$(date): Docker volumes backup successful" >> /var/log/aihub-backup.log

    # Retention: 30 days
    find "${BACKUP_DIR}" -name "volumes-*.tar.gz" -mtime +30 -delete
else
    echo "$(date): Docker volumes backup FAILED" >> /var/log/aihub-backup.log
    exit 1
fi

# Restart services
# docker compose up -d
```

**Note**: Application-level backups (PostgreSQL, Milvus, etc.) are **preferred** over volume backups for consistency and portability.

---

## Backup Automation

### Cron Schedule

Create a centralized cron schedule for all backup tasks:

```bash
# File: /etc/cron.d/aihub-backup

# PostgreSQL full backup (daily at 2:00 AM)
0 2 * * * root /backups/scripts/backup-postgres.sh

# FerretDB export (daily at 2:30 AM)
30 2 * * * root /backups/scripts/backup-ferretdb.sh

# Milvus backup (daily at 3:00 AM)
0 3 * * * root /backups/scripts/backup-milvus.sh

# SeaweedFS sync (daily at 4:00 AM)
0 4 * * * root /backups/scripts/backup-seaweedfs.sh

# Configuration backup (daily at 5:00 AM)
0 5 * * * root /backups/scripts/backup-config.sh

# etcd snapshot (every 6 hours)
0 */6 * * * root /backups/scripts/backup-etcd.sh

# WAL cleanup (daily at 6:00 AM)
0 6 * * * root /backups/scripts/cleanup-wal.sh

# Backup verification (weekly, Sunday 1:00 AM)
0 1 * * 0 root /backups/scripts/verify-backups.sh
```

### Backup Verification Script

```bash
#!/bin/bash
# File: /backups/scripts/verify-backups.sh

BACKUP_ROOT="/backups"
LOG_FILE="/var/log/aihub-backup-verification.log"

echo "=== Backup Verification: $(date) ===" >> "${LOG_FILE}"

# Check PostgreSQL backup age
LATEST_PG=$(find "${BACKUP_ROOT}/postgres" -type d -name "2*" | sort -r | head -1)
if [ -n "${LATEST_PG}" ]; then
    AGE=$(( ($(date +%s) - $(stat -c %Y "${LATEST_PG}")) / 86400 ))
    echo "PostgreSQL: Latest backup is ${AGE} days old" >> "${LOG_FILE}"
    if [ ${AGE} -gt 2 ]; then
        echo "WARNING: PostgreSQL backup is older than 2 days!" >> "${LOG_FILE}"
    fi
else
    echo "ERROR: No PostgreSQL backups found!" >> "${LOG_FILE}"
fi

# Check SeaweedFS backup age
LATEST_SWF=$(find "${BACKUP_ROOT}/seaweedfs" -type d -name "2*" | sort -r | head -1)
if [ -n "${LATEST_SWF}" ]; then
    AGE=$(( ($(date +%s) - $(stat -c %Y "${LATEST_SWF}")) / 86400 ))
    echo "SeaweedFS: Latest backup is ${AGE} days old" >> "${LOG_FILE}"
    if [ ${AGE} -gt 2 ]; then
        echo "WARNING: SeaweedFS backup is older than 2 days!" >> "${LOG_FILE}"
    fi
else
    echo "ERROR: No SeaweedFS backups found!" >> "${LOG_FILE}"
fi

# Check backup sizes
echo "=== Backup Sizes ===" >> "${LOG_FILE}"
du -sh "${BACKUP_ROOT}"/* >> "${LOG_FILE}"

echo "" >> "${LOG_FILE}"
```

---

## Recovery Procedures

### Full Disaster Recovery

Complete system restoration from backups after catastrophic failure.

#### Prerequisites

- Clean VM or bare-metal server with supported OS
- Docker and Docker Compose installed
- Network access to backup storage
- Decryption keys for encrypted backups

#### Recovery Steps

**Step 1: Restore Configuration**

```bash
# Restore encrypted configuration
openssl enc -aes-256-cbc -d -pbkdf2 -pass file:/root/.backup-key \
    -in /backups/config/config-YYYYMMDD_HHMMSS.tar.gz.enc \
    | tar -xzf - -C /opt/aihub

# Verify configuration files
ls -la /opt/aihub/.env /opt/aihub/configs/
```

**Step 2: Restore PostgreSQL**

```bash
# Stop existing PostgreSQL (if running)
docker compose down postgres

# Remove old data
rm -rf .docker-volumes/postgres-data/*

# Restore from pg_basebackup
tar -xzf /backups/postgres/YYYYMMDD_HHMMSS/base.tar.gz \
    -C .docker-volumes/postgres-data/

# Restore WAL files if needed
cp /backups/postgres-wal/* .docker-volumes/postgres-data/pg_wal/

# Start PostgreSQL
docker compose up -d postgres

# Wait for PostgreSQL to start
sleep 10

# Verify databases
docker compose exec postgres psql -U postgres -c "\l"
```

**Alternative: Restore from pg_dump**

```bash
# Start PostgreSQL with empty database
docker compose up -d postgres

# Restore each database
for DB in openwebui phoenix dagster litellm ferretdb; do
    docker compose exec -T postgres pg_restore -U postgres \
        -d ${DB} < /backups/postgres-logical/${DB}_YYYYMMDD_HHMMSS.dump
done
```

**Step 3: Restore SeaweedFS**

```bash
# Stop SeaweedFS services
docker compose down seaweedfs-master seaweedfs-volume seaweedfs-filer

# Restore volumes
rsync -av /backups/seaweedfs/YYYYMMDD_HHMMSS/ \
    .docker-volumes/seaweedfs-volume/

# Start SeaweedFS
docker compose up -d seaweedfs-master seaweedfs-volume seaweedfs-filer

# Verify buckets
s3cmd ls s3://
```

**Step 4: Restore Milvus**

```bash
# Stop Milvus
docker compose down milvus-standalone etcd

# Restore etcd snapshot
docker compose up -d etcd
sleep 5

etcdctl snapshot restore /backups/etcd/etcd-snapshot-YYYYMMDD_HHMMSS.db \
    --data-dir=.docker-volumes/etcd-data

# Restore Milvus collections
milvus-backup restore \
    --backup-name="backup_YYYYMMDD_HHMMSS" \
    --backup-dir="/backups/milvus" \
    --milvus-address="localhost:19530"

# Start Milvus
docker compose up -d milvus-standalone

# Verify collections
python3 -c "from pymilvus import connections, utility; \
    connections.connect(); \
    print(utility.list_collections())"
```

**Step 5: Start All Services**

```bash
# Start remaining services
docker compose up -d

# Verify all containers are running
docker compose ps

# Check logs for errors
docker compose logs --tail=50
```

**Step 6: Validate Recovery**

```bash
# Test API endpoint
curl -k https://localhost/api/health

# Test OpenWebUI
curl -k https://localhost/

# Test agent execution
# (Manual: Log in and run a test agent workflow)

# Check data integrity
docker compose exec postgres psql -U postgres -d openwebui \
    -c "SELECT COUNT(*) FROM chats;"
```

---

### Partial Recovery (Single Service)

Restore only a specific component without full system recovery.

#### Recover PostgreSQL Database Only

```bash
# Identify the database to restore
TARGET_DB="openwebui"

# Drop existing database (WARNING: Data loss!)
docker compose exec postgres psql -U postgres -c "DROP DATABASE ${TARGET_DB};"
docker compose exec postgres psql -U postgres -c "CREATE DATABASE ${TARGET_DB};"

# Restore from dump
docker compose exec -T postgres pg_restore -U postgres \
    -d ${TARGET_DB} < /backups/postgres-logical/${TARGET_DB}_YYYYMMDD_HHMMSS.dump

# Verify restoration
docker compose exec postgres psql -U postgres -d ${TARGET_DB} -c "\dt"
```

#### Recover User Files Only

```bash
# Restore specific bucket from SeaweedFS backup
s3cmd sync /backups/seaweedfs/YYYYMMDD_HHMMSS/open-webui/ \
    s3://open-webui/

# Verify files
s3cmd ls s3://open-webui/
```

---

### Point-in-Time Recovery (PITR)

Restore PostgreSQL to a specific point in time using WAL archives.

#### Prerequisites

- WAL archiving must be enabled
- WAL archives available from the target recovery point

#### Recovery Steps

```bash
# Stop PostgreSQL
docker compose down postgres

# Restore base backup
rm -rf .docker-volumes/postgres-data/*
tar -xzf /backups/postgres/YYYYMMDD_HHMMSS/base.tar.gz \
    -C .docker-volumes/postgres-data/

# Create recovery.conf (PostgreSQL < 12) or recovery.signal (>= 12)
cat > .docker-volumes/postgres-data/recovery.signal << 'EOF'
restore_command = 'cp /backups/postgres-wal/%f %p'
recovery_target_time = '2025-10-23 14:30:00 UTC'
recovery_target_action = 'promote'
EOF

# Start PostgreSQL (will replay WAL to target time)
docker compose up -d postgres

# Monitor recovery
docker compose logs -f postgres

# Once recovery completes, PostgreSQL will promote to primary
# Verify data at target time
docker compose exec postgres psql -U postgres -c "SELECT NOW();"
```

---

## Off-Site Backup Strategy

### 3-2-1 Backup Rule

For production deployments, implement the 3-2-1 rule:

- **3 copies** of data: 1 production + 2 backups
- **2 different media types**: Local disk + remote storage/tape
- **1 off-site copy**: Different physical location

### Remote Backup Options

#### Option 1: Swiss Cloud Storage

```bash
#!/bin/bash
# File: /backups/scripts/sync-offsite-cloud.sh

# Sync to Swiss cloud provider (e.g., Exoscale Object Storage)
s3cmd sync --delete-removed \
    /backups/ \
    s3://aihub-backups-tenant-zug/

echo "$(date): Off-site sync to cloud complete" >> /var/log/aihub-backup.log
```

#### Option 2: Secondary Data Center

```bash
#!/bin/bash
# File: /backups/scripts/sync-offsite-datacenter.sh

# Rsync to DR site over SSH
rsync -avz --delete \
    -e "ssh -i /root/.ssh/backup_key" \
    /backups/ \
    backup@dr-site.example.ch:/backups/tenant-zug/

echo "$(date): Off-site sync to DR site complete" >> /var/log/aihub-backup.log
```

#### Option 3: Tape Backup (Long-Term Archive)

```bash
#!/bin/bash
# File: /backups/scripts/backup-to-tape.sh

# Monthly tape backup for long-term retention
TAPE_DEVICE="/dev/nst0"
BACKUP_DATE=$(date +%Y%m)

tar -czf - /backups/ | dd of=${TAPE_DEVICE} bs=1M

echo "$(date): Tape backup ${BACKUP_DATE} complete" >> /var/log/aihub-backup.log
```

### Off-Site Backup Schedule

```bash
# Sync to cloud (daily at 6:00 AM)
0 6 * * * root /backups/scripts/sync-offsite-cloud.sh

# Sync to DR site (daily at 7:00 AM)
0 7 * * * root /backups/scripts/sync-offsite-datacenter.sh

# Tape backup (1st of each month at 8:00 AM)
0 8 1 * * root /backups/scripts/backup-to-tape.sh
```

---

## Monitoring and Alerts

### Backup Health Monitoring

Monitor backup operations and alert on failures:

```bash
#!/bin/bash
# File: /backups/scripts/monitor-backups.sh

# Check if backups completed successfully today
EXPECTED_BACKUPS=("postgres" "ferretdb" "milvus" "seaweedfs" "config")
ALERT=0

for BACKUP in "${EXPECTED_BACKUPS[@]}"; do
    LATEST=$(find /backups/${BACKUP} -type f -o -type d -mtime -1 | wc -l)

    if [ ${LATEST} -eq 0 ]; then
        echo "ALERT: No recent ${BACKUP} backup found!" | \
            mail -s "Backup Alert: ${BACKUP}" admin@example.ch
        ALERT=1
    fi
done

if [ ${ALERT} -eq 0 ]; then
    echo "$(date): All backups current" >> /var/log/aihub-backup.log
fi
```

### Integration with Monitoring Systems

**Prometheus Metrics**:

```bash
# Export backup metrics for Prometheus
cat > /var/lib/node_exporter/textfile_collector/backup_metrics.prom << EOF
# HELP aihub_backup_age_seconds Age of latest backup in seconds
# TYPE aihub_backup_age_seconds gauge
aihub_backup_age_seconds{component="postgres"} $(( $(date +%s) - $(stat -c %Y /backups/postgres/latest) ))
aihub_backup_age_seconds{component="seaweedfs"} $(( $(date +%s) - $(stat -c %Y /backups/seaweedfs/latest) ))

# HELP aihub_backup_size_bytes Size of latest backup in bytes
# TYPE aihub_backup_size_bytes gauge
aihub_backup_size_bytes{component="postgres"} $(du -sb /backups/postgres/latest | cut -f1)
aihub_backup_size_bytes{component="seaweedfs"} $(du -sb /backups/seaweedfs/latest | cut -f1)
EOF
```

**Alert Rules** (Prometheus AlertManager):

```yaml
# Alert if backup is older than 48 hours
- alert: BackupTooOld
  expr: aihub_backup_age_seconds > 172800
  labels:
    severity: critical
  annotations:
    summary: "Backup for {{ $labels.component }} is too old"
    description: "Last backup is {{ $value }} seconds old"
```

---

## Security Considerations

### Backup Encryption

All backups containing sensitive data must be encrypted:

**At Rest**:
- Configuration backups: Encrypted with AES-256
- Database dumps: Optionally encrypted
- File storage: Consider volume-level encryption (LUKS)

**In Transit**:
- Use SSH/SCP for remote transfers
- Use TLS for cloud storage uploads
- Use VPN for DR site replication

### Access Control

Restrict backup access to authorized personnel only:

```bash
# Set restrictive permissions on backup directory
chmod 700 /backups
chown root:root /backups

# Limit SSH key access for remote backups
chmod 600 /root/.ssh/backup_key

# Secure encryption key
chmod 400 /root/.backup-key
```

### Audit Logging

Log all backup operations for compliance:

```bash
# Backup operations logged to syslog
logger -t aihub-backup "PostgreSQL backup completed: /backups/postgres/${TIMESTAMP}"

# Centralized logging
# Ship /var/log/aihub-backup.log to SIEM or log aggregation system
```

---

## Compliance and Retention

### Swiss Data Protection (revDSG) Requirements

**Retention Periods**:
- **Operational backups**: 30-35 days minimum
- **Compliance archives**: 90 days to 10 years (depending on data type)
- **Audit logs**: 1 year minimum

**Data Deletion**:
- Implement secure deletion when backups exceed retention period
- Use `shred` or `secure-delete` for sensitive data
- Document deletion procedures for audits

```bash
# Secure deletion after retention period
find /backups/postgres -type d -mtime +35 -exec shred -vfz -n 3 {} \;
```

### Backup Retention Policy

| Backup Type | Retention | Storage Location | Compliance Reason |
|-------------|-----------|------------------|-------------------|
| Daily full backups | 35 days | Local + Cloud | Operational recovery |
| Weekly archives | 90 days | Cloud + Tape | Short-term compliance |
| Monthly archives | 1 year | Tape | Long-term compliance |
| Annual archives | 10 years | Secure tape vault | Legal/regulatory requirements |

---

## Testing and Validation

### Regular Restore Testing

**Monthly Restore Test**:

```bash
#!/bin/bash
# File: /backups/scripts/test-restore.sh

# Restore to a separate test environment
TEST_DIR="/opt/aihub-test"

# Restore latest backup
# ... (perform full recovery to test environment)

# Run validation queries
docker compose -f ${TEST_DIR}/docker-compose.yml exec postgres \
    psql -U postgres -c "SELECT COUNT(*) FROM openwebui.chats;"

# Cleanup test environment
docker compose -f ${TEST_DIR}/docker-compose.yml down -v

echo "$(date): Restore test completed successfully" >> /var/log/aihub-backup.log
```

### Disaster Recovery Drills

Conduct full disaster recovery drills quarterly:

1. **Simulate failure**: Power down production system
2. **Restore from backups**: Follow full recovery procedures
3. **Validate functionality**: Test all agents, pipelines, and user access
4. **Document findings**: Record RTO/RPO achieved, identify improvements
5. **Update procedures**: Incorporate lessons learned

---

## Troubleshooting

### Backup Failures

**PostgreSQL backup fails**:
```bash
# Check PostgreSQL is running
docker compose ps postgres

# Check disk space
df -h /backups

# Check permissions
ls -la /backups/postgres

# Check PostgreSQL logs
docker compose logs postgres
```

**SeaweedFS backup incomplete**:
```bash
# Verify S3 endpoint is reachable
curl http://localhost:8333

# Check SeaweedFS logs
docker compose logs seaweedfs-filer

# Manually test S3 sync
s3cmd --host=localhost:8333 ls s3://
```

### Recovery Issues

**PostgreSQL restore fails**:
```bash
# Check backup file integrity
tar -tzf /backups/postgres/YYYYMMDD_HHMMSS/base.tar.gz

# Verify PostgreSQL version compatibility
docker compose exec postgres psql -U postgres -c "SELECT version();"

# Check WAL files availability
ls -la /backups/postgres-wal/
```

**Milvus collection not found after restore**:
```bash
# List available collections
python3 -c "from pymilvus import connections, utility; \
    connections.connect(); \
    print(utility.list_collections())"

# Re-index from source documents if needed
# (Trigger RAG pipeline re-ingestion)
```

---

## Summary Checklist

### Daily Operations

- [ ] Verify backup cron jobs executed successfully
- [ ] Check backup log for errors (`/var/log/aihub-backup.log`)
- [ ] Monitor backup disk space usage
- [ ] Confirm off-site sync completed

### Weekly Operations

- [ ] Review backup sizes and retention
- [ ] Test backup file integrity (random sampling)
- [ ] Verify encryption keys are securely stored
- [ ] Check backup monitoring alerts

### Monthly Operations

- [ ] Perform restore test to staging environment
- [ ] Review and update retention policies
- [ ] Audit access logs for backup directories
- [ ] Verify tape backups (if applicable)

### Quarterly Operations

- [ ] Conduct full disaster recovery drill
- [ ] Review and update backup procedures
- [ ] Test recovery from off-site backup
- [ ] Update RTO/RPO metrics based on actual tests

---

## Next Steps

- [Production Configuration](../2_production_configuration/) - Configure production environment variables
- [Scaling Considerations](../3_scaling_considerations/) - Plan for growth
- [Monitoring and Alerting](../5_monitoring_and_alerting/) - Set up backup monitoring
- [Updates and Maintenance](../6_updates_and_maintenance/) - Update procedures

---

## Related Documentation

- **Deployment**: [Deployment Options](../1_deployment_options/) - Understand per-tenant architecture
- **Security**: [Authentication & Authorization](../../11_access_management/1_authentication_setup/) - Secure backup access
- **Compliance**: [Swiss Data Protection](../../13_compliance/2_swiss_dsg/) - revDSG compliance for backups
