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

- Full Backup (Daily)
- Continuous WAL Archiving

---

### 2. FerretDB (MongoDB-Compatible) Backup

FerretDB stores documents in PostgreSQL, so it's covered by PostgreSQL backups. However, for compliance and portability, also create MongoDB-format exports.

**What's Backed Up**:
- Agent configurations
- Process definitions
- Chat histories
- User sessions
- Knowledge base metadata

---

### 3. Milvus Vector Database Backup

Milvus stores vector embeddings for RAG. Backups export collections to S3-compatible storage.

**Important**: Vector embeddings can be **regenerated** from source documents. If backup storage is limited, prioritize PostgreSQL and SeaweedFS over Milvus.

---

### 4. SeaweedFS (File Storage) Backup

SeaweedFS stores user-uploaded documents, RAG knowledge base files, and chat attachments.

**Alternative: rsync from volumes**:

---

### 5. etcd (Distributed Configuration) Backup

etcd stores Milvus metadata and service discovery information.

---

### 6. Configuration and Secrets Backup

Configuration files, environment variables, and SSL certificates must be backed up securely.

**Encryption Key Management**:
- Store encryption key in a **secure, separate location**
- Consider using hardware security modules (HSM) or key management services
- Maintain key backups in multiple secure locations (safe, off-site)

---

### 7. Docker Volumes Backup (Alternative Method)

If using Docker volumes directly without application-level backups:

**Note**: Application-level backups (PostgreSQL, Milvus, etc.) are **preferred** over volume backups for consistency and portability.

---

## Backup Automation

- Cron Schedule: Create a centralized cron schedule for all backup tasks:
- Backup Verification Script

---

## Recovery Procedures

### Full Disaster Recovery

Complete system restoration from backups after catastrophic failure.

#### Prerequisites

- Clean VM or bare-metal server with supported OS
- Docker and Docker Compose installed
- Network access to backup storage
- Decryption keys for encrypted backups

---

### Partial Recovery (Single Service)

Restore only a specific component without full system recovery.

---

### Point-in-Time Recovery (PITR)

Restore PostgreSQL to a specific point in time using WAL archives.

#### Prerequisites

- WAL archiving must be enabled
- WAL archives available from the target recovery point

---

## Off-Site Backup Strategy

### 3-2-1 Backup Rule

For production deployments, implement the 3-2-1 rule:

- **3 copies** of data: 1 production + 2 backups
- **2 different media types**: Local disk + remote storage/tape
- **1 off-site copy**: Different physical location

---

## Monitoring and Alerts

### Backup Health Monitoring

Monitor backup operations and alert on failures:

### Integration with Monitoring Systems

- **Prometheus Metrics**
- **Alert Rules** (Prometheus AlertManager)

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

Restrict backup access to authorized personnel only

### Audit Logging

Log all backup operations for compliance:

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

**Monthly Restore Test**

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

- **PostgreSQL backup fails**
- **SeaweedFS backup incomplete**

### Recovery Issues

- **PostgreSQL restore fails**
- **Milvus collection not found after restore**

---

## Summary Checklist

### Daily Operations

- [ ] Verify backup cron jobs executed successfully
- [ ] Check backup log for errors
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

- [ ] Conduct a full disaster recovery drill
- [ ] Review and update backup procedures
- [ ] Test recovery from off-site backup
- [ ] Update RTO/RPO metrics based on actual tests

---

## Next Steps

- [Production Configuration](../2_production_configuration/) — Configure production environment variables
- [Scaling Considerations](../3_scaling_considerations/) — Plan for growth
- [Monitoring and Alerting](../5_monitoring_and_alerting/) — Set up backup monitoring
- [Updates and Maintenance](../6_updates_and_maintenance/) — Update procedures

---

## Related Documentation

- **Deployment**: [Deployment Options](../1_deployment_options/) — Understand per-tenant architecture
- **Security**: [Authentication & Authorization](../../11_access_management/1_authentication_setup/) — Secure backup access
- **Compliance**: [Swiss Data Protection](../../19_compliance/3_dsg/) — revDSG compliance for backups
