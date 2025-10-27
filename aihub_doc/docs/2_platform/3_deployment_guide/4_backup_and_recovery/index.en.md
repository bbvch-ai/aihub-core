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

## Backup architecture

### Per-tenant backup isolation

Each tenant instance maintains independent backups with no cross-tenant dependencies.

This provides complete data isolation between tenants, tenant-specific compliance requirements (retention periods), independent recovery without affecting other tenants, and granular cost tracking per tenant.

---

## Production backup strategy (VM/on-premise)

### Overview

Production deployments require comprehensive backup across all data layers with automation, monitoring, and regular testing.

### Backup approaches

There are two primary approaches to backing up production AI-Hub deployments: VM snapshots (simple) and component-level backups (granular).

VM snapshots provide the simplest backup strategy with instant recovery. Component-level backups offer more flexibility, smaller backup sizes, and selective recovery.

---

## Approach 1: VM snapshot (simple full backup)

### Overview

VM snapshots capture the entire virtual machine state, including all data, configuration, and system files. This works well for smaller deployments or when simplicity is prioritized over granular control.

### When to use VM snapshots

VM snapshots are simple to implement and automate. They capture everything (OS, Docker, data, configuration) and provide the fastest disaster recovery by restoring the entire VM. No complex backup scripts are needed. They provide point-in-time consistency across all services.

However, they have larger backup sizes (entire disk), longer backup times, cannot selectively restore individual databases, and require the VM to be stopped or a snapshot-capable hypervisor.

### Snapshot best practices

For consistency, stop AI-Hub services before snapshot using `docker compose down`, or use application-consistent snapshots (e.g., Azure with VM agent, VMware with quiesce).

For frequency, daily snapshots are suitable for most production deployments. Always snapshot before major updates. Keep long-term weekly or monthly snapshots for compliance.

For testing, restore snapshots to a test environment monthly and verify functionality. Document actual RTO achieved during test restores.

---

## Approach 2: Component-level backups (granular)

### Overview

Component-level backups provide granular control by backing up individual data stores separately. This approach offers flexibility for selective recovery and smaller backup sizes.

### Data stores to back up

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

## Backup procedures (component-level)

### 1. PostgreSQL Database Backup

PostgreSQL stores multiple databases: OpenWebUI, Phoenix, Dagster, LiteLLM, and the FerretDB backend.

- Full Backup (Daily)
- Continuous WAL Archiving

---

### 2. FerretDB (MongoDB-Compatible) Backup

FerretDB stores documents in PostgreSQL, so it's covered by PostgreSQL backups. However, for compliance and portability, also create MongoDB-format exports.

What's backed up:
- Agent configurations
- Process definitions
- Chat histories
- User sessions
- Knowledge base metadata

---

### 3. Milvus Vector Database Backup

Milvus stores vector embeddings for RAG. Backups export collections to S3-compatible storage.

Vector embeddings can be regenerated from source documents. If backup storage is limited, prioritize PostgreSQL and SeaweedFS over Milvus.

---

### 4. SeaweedFS (File Storage) Backup

SeaweedFS stores user-uploaded documents, RAG knowledge base files, and chat attachments. Backups can be performed using S3-compatible sync tools or direct volume synchronization.

---

### 5. etcd (Distributed Configuration) Backup

etcd stores Milvus metadata and service discovery information.

---

### 6. Configuration and Secrets Backup

Configuration files, environment variables, and SSL certificates must be backed up securely.

Encryption key management: Store encryption keys in a secure, separate location. Consider using hardware security modules (HSM) or key management services. Maintain key backups in multiple secure locations (safe, off-site).

---

### 7. Docker Volumes Backup (Alternative Method)

If using Docker volumes directly without application-level backups:

Note: Application-level backups (PostgreSQL, Milvus, etc.) are preferred over volume backups for consistency and portability.

---

## Backup automation

### Cron schedule

Create a centralized cron schedule for all backup tasks to automate daily, hourly, and weekly backup operations. Schedule backups during low-usage periods to minimize performance impact.

### Backup verification script

Implement automated verification scripts that run weekly to check backup integrity, age, and sizes. Alert administrators if backups are older than expected or missing.

---

## Recovery procedures

### Full disaster recovery

Complete system restoration from backups after catastrophic failure.

#### Prerequisites

- Clean VM or bare-metal server with supported OS
- Docker and Docker Compose installed
- Network access to backup storage
- Decryption keys for encrypted backups

---

### Partial recovery (single service)

Restore only a specific component without full system recovery.

---

### Point-in-time recovery (PITR)

Restore PostgreSQL to a specific point in time using WAL archives.

#### Prerequisites

- WAL archiving must be enabled
- WAL archives available from the target recovery point

---

## Off-site backup strategy

### 3-2-1 backup rule

For production deployments, implement the 3-2-1 rule:

- 3 copies of data: 1 production + 2 backups
- 2 different media types: Local disk + remote storage/tape
- 1 off-site copy: Different physical location

---

## Monitoring and alerts

### Backup health monitoring

Monitor backup operations and alert on failures. Implement checks for backup completion, age, and size to detect issues early.

### Integration with monitoring systems

Integrate backup monitoring with existing observability infrastructure. Export backup age and size metrics for Prometheus monitoring. Configure AlertManager rules to notify on backup failures or old backups.

---

## Security considerations

### Backup encryption

All backups containing sensitive data must be encrypted.

At rest: Configuration backups are encrypted with AES-256. Database dumps are optionally encrypted. File storage can use volume-level encryption (LUKS).

In transit: Use SSH/SCP for remote transfers, TLS for cloud storage uploads, and VPN for DR site replication.

### Access control

Restrict backup access to authorized personnel only. Set restrictive permissions on backup directories, limit SSH key access, and secure encryption keys.

### Audit logging

Log all backup operations for compliance. Backup operations should be logged to syslog and shipped to centralized log aggregation systems for audit trails.

---

## Compliance and retention

### Swiss data protection (revDSG) requirements

Retention periods: Operational backups need 30-35 days minimum. Compliance archives range from 90 days to 10 years depending on data type. Audit logs need 1 year minimum.

Data deletion: Implement secure deletion when backups exceed retention period. Use `shred` or `secure-delete` for sensitive data. Document deletion procedures for audits.

### Backup retention policy

| Backup Type | Retention | Storage Location | Compliance Reason |
|-------------|-----------|------------------|-------------------|
| Daily full backups | 35 days | Local + Cloud | Operational recovery |
| Weekly archives | 90 days | Cloud + Tape | Short-term compliance |
| Monthly archives | 1 year | Tape | Long-term compliance |
| Annual archives | 10 years | Secure tape vault | Legal/regulatory requirements |

---

## Testing and validation

### Regular restore testing

Perform monthly restore tests to a separate test environment to verify backup integrity and practice recovery procedures. Validate that restored data is accessible and services function correctly.

### Disaster recovery drills

Conduct full disaster recovery drills quarterly:

1. Simulate failure: Power down production system
2. Restore from backups: Follow full recovery procedures
3. Validate functionality: Test all agents, pipelines, and user access
4. Document findings: Record RTO/RPO achieved, identify improvements
5. Update procedures: Incorporate lessons learned

---

## Troubleshooting

### Backup failures

Common backup issues and their resolutions:

- PostgreSQL backup fails: Check PostgreSQL is running, verify disk space, check permissions, and review PostgreSQL logs
- SeaweedFS backup incomplete: Verify S3 endpoint is reachable, check SeaweedFS logs, and manually test S3 sync

### Recovery issues

Common recovery problems and solutions:

- PostgreSQL restore fails: Check backup file integrity, verify PostgreSQL version compatibility, and ensure WAL files are available
- Milvus collection not found after restore: List available collections and re-index from source documents if needed

---

## Summary checklist

### Daily operations

- [ ] Verify backup cron jobs executed successfully
- [ ] Check backup log for errors
- [ ] Monitor backup disk space usage
- [ ] Confirm off-site sync completed

### Weekly operations

- [ ] Review backup sizes and retention
- [ ] Test backup file integrity (random sampling)
- [ ] Verify encryption keys are securely stored
- [ ] Check backup monitoring alerts

### Monthly operations

- [ ] Perform restore test to staging environment
- [ ] Review and update retention policies
- [ ] Audit access logs for backup directories
- [ ] Verify tape backups (if applicable)

### Quarterly operations

- [ ] Conduct a full disaster recovery drill
- [ ] Review and update backup procedures
- [ ] Test recovery from off-site backup
- [ ] Update RTO/RPO metrics based on actual tests

---

## Next steps

- [Production Configuration](../2_production_configuration/) - Configure production environment variables
- [Scaling Considerations](../3_scaling_considerations/) - Plan for growth
- [Monitoring and Alerting](../5_monitoring_and_alerting/) - Set up backup monitoring
- [Updates and Maintenance](../6_updates_and_maintenance/) - Update procedures

---

## Related documentation

- [Deployment Options](../1_deployment_options/) - Per-tenant architecture
- [Authentication & Authorization](../../11_access_management/1_authentication_setup/) - Secure backup access
- [Swiss Data Protection](../../19_compliance/3_dsg/) - revDSG compliance for backups
