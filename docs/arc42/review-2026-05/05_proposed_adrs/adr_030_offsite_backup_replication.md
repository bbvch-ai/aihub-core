# Off-site Backup Replication and 3-2-1 Compliance

**Status**: Proposed **Severity**: P0 (catastrophic disaster scenario, business continuity block) **Drives**: DR-1 in
[Details §21.1 Backup Disaster Recovery](../02_architecture_review_details.md#211-backup-disaster-recovery-fatal-flaw)

## Context

Review 2026-05 found a fatal disaster-recovery flaw: **the backup destination and primary data both sit on the SAME
SeaweedFS instance on the SAME VM**.

Evidence:

| Evidence                                    | File:Line                                                                                                  |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Backup S3 endpoint hardcoded SeaweedFS      | `packages/backup/swiss_ai_hub/backup/settings.py:54`: `AWS_ENDPOINT_URL: str = "http://seaweedfs-s3:9000"` |
| Backup bucket on same instance              | `packages/backup/swiss_ai_hub/backup/settings.py:55`: `S3_BUCKET: str = "backups"`                         |
| Milvus backup source and dest same instance | `packages/backup/milvus-backup.yaml:15-31`: Source `seaweedfs-s3`, Dest `seaweedfs-s3`                     |
| SeaweedFS no replication                    | `infra/docker-compose.dev.yml`: `replication="000"`                                                        |
| SeaweedFS topology single-node              | 1 master + 1 volume server + 1 filer (no HA)                                                               |
| README confirms                             | `packages/backup/README.md:13`: "Daily backup ... to S3 (SeaweedFS)"                                       |

Disaster scenario (100% applicable):

```
VM compromise / disk failure / power outage / human error / ransomware
    SeaweedFS volume (holds primary data: documents, Milvus vectors,
                      Mongo dumps, backup tarballs) is lost or corrupt
    NO RESTORE PATH
    Primary data and backups die together
```

Compared to the industry-standard 3-2-1 backup rule:

| Rule                  | Best practice                      | Swiss AI Hub today                                                  |
| --------------------- | ---------------------------------- | ------------------------------------------------------------------- |
| **3** copies of data  | Primary + 2 backups                | 1 copy (primary), 1 backup ON SAME storage = effectively **1 copy** |
| **2** different media | Disk + tape/cloud/different region | Only 1 medium (same SeaweedFS volume)                               |
| **1** off-site copy   | Geographic separation              | **0 off-site copies**                                               |

Violates 3/3 rules.

Existing risks doc admit (`docs/arc42/chapters/11_risks_and_technical_debt.md:20-32`):

> "Off-site replication via SeaweedFS are both tracked as P0 items and are in progress... Off-site replication and
> application-consistent cross-store snapshots remain open."

The platform team knows, but hasn't shipped after several months.

## Decision Drivers

- **Business continuity**: Recover from hardware failure, ransomware, datacenter outage.
- **RPO (Recovery Point Objective)**: Acceptable data loss window (target 24h initially).
- **RTO (Recovery Time Objective)**: Acceptable downtime (target 4h initially).
- **Sovereignty**: Off-site target must be Swiss-jurisdiction if there is a data-sovereignty mandate.
- **Cost**: Cross-region replication has cost (egress bandwidth, storage).
- **Operational simplicity**: Automate; no dependence on manual ops.
- **Verifiability**: Periodic restore drill to confirm backups are usable.
- **Encryption**: Backup data encrypted at rest and in transit.

## Decision

3-tier implementation, deploy incrementally.

### Tier 1: Emergency mitigation (1-2 days, deploy immediately)

Push backups to an off-site target via a cron job on the host (outside the Docker stack).

```bash
# /etc/cron.daily/aihub-offsite-sync
#!/bin/bash
set -euo pipefail

REGION="${AIHUB_REGION:-ch-central-1}"
OFFSITE_ENDPOINT="${OFFSITE_S3_ENDPOINT:-https://s3.exoscale.ch}"
OFFSITE_BUCKET="${OFFSITE_S3_BUCKET:-aihub-offsite-backup}"

# Wait for the daily backup to finish (Dagster job finishes ~3 AM Europe/Zurich)
sleep 7200  # 2 hours buffer after 1 AM daily backup

# Sync with encryption
docker exec backup-dagster bash -c "
  aws s3 sync s3://backups/ s3://${OFFSITE_BUCKET}/ \
    --endpoint-url ${OFFSITE_ENDPOINT} \
    --sse aws:kms \
    --sse-kms-key-id ${OFFSITE_KMS_KEY_ID} \
    --storage-class STANDARD_IA \
    --delete-removed
"

# Verify offsite integrity
docker exec backup-dagster bash -c "
  aws s3 ls s3://${OFFSITE_BUCKET}/ \
    --endpoint-url ${OFFSITE_ENDPOINT} \
    --recursive --summarize
"
```

**Off-site target options (Swiss-sovereign preferred)**:

| Provider                       | Region                       | Pros                              | Cons                 |
| ------------------------------ | ---------------------------- | --------------------------------- | -------------------- |
| **Infomaniak Public Cloud S3** | Switzerland                  | Swiss jurisdiction, GDPR-friendly | API throughput limit |
| **Exoscale SOS**               | Switzerland (Geneva, Zurich) | Swiss sovereign, S3-compatible    | Smaller scale        |
| **Hetzner Storage Box**        | DE/FI                        | EU jurisdiction, low cost         | Not Swiss            |
| **Bare-metal secondary VM**    | Customer-controlled          | Full sovereignty                  | Higher ops effort    |
| **OVHcloud Object Storage**    | EU regions                   | EU sovereign                      | French law applies   |

Recommended: Infomaniak or Exoscale for Swiss sovereignty.

### Tier 2: Configurable backup target (1 sprint)

Refactor `BackupSettings` to support a separate target endpoint:

```python
# packages/backup/swiss_ai_hub/backup/settings.py
class BackupSettings(BaseSettings):
    # Existing primary storage (local SeaweedFS for fast access)
    AWS_ENDPOINT_URL: str = "http://seaweedfs-s3:9000"  # Local primary
    S3_BUCKET: str = "backups"
    S3_STORAGE_ACCESS_KEY: str = "admin"
    S3_STORAGE_SECRET_KEY: SecretStr

    # NEW: Off-site target (separate endpoint)
    BACKUP_OFFSITE_ENDPOINT_URL: str = ""  # Empty disables
    BACKUP_OFFSITE_BUCKET: str = ""
    BACKUP_OFFSITE_ACCESS_KEY: str = ""
    BACKUP_OFFSITE_SECRET_KEY: SecretStr = SecretStr("")
    BACKUP_OFFSITE_REGION: str = "ch-central-1"
    BACKUP_OFFSITE_STORAGE_CLASS: str = "STANDARD_IA"  # Cost optimization
    BACKUP_OFFSITE_KMS_KEY_ID: str = ""  # Encryption key

    # NEW: Replication policy
    BACKUP_REPLICATE_ENABLED: bool = False
    BACKUP_REPLICATE_DELAY_HOURS: int = 1  # Wait after primary backup
    BACKUP_REPLICATE_RETENTION_DAYS: int = 90  # Cold storage retention
    BACKUP_REPLICATE_PARALLEL_TRANSFERS: int = 4
```

Startup validation warns if offsite is disabled for production:

```python
@model_validator
def warn_no_offsite(self):
    if not self.BACKUP_OFFSITE_ENDPOINT_URL and self.is_production:
        logger.error(
            "⚠️ CRITICAL: Backup target is local SeaweedFS only, no disaster protection! "
            "Set BACKUP_OFFSITE_ENDPOINT_URL for off-site replication."
        )
        # Optionally raise on prod
```

### Tier 3: Cross-region Dagster job (1-2 sprints)

Replace the shell script with a proper Dagster asset for observability + retries.

```python
# packages/backup/swiss_ai_hub/backup/dagster/assets/offsite_replication.py
@asset(
    name="offsite_replication",
    description="Replicate primary backup S3 to off-site target.",
    deps=["backup_finalize"],  # Run after backup completes
    automation_condition=AutomationCondition.eager(),
    retry_policy=RetryPolicy(max_retries=3, delay=300, backoff=Backoff.EXPONENTIAL),
)
async def offsite_replication(
    context: AssetExecutionContext,
    settings: BackupSettings,
    primary_s3: S3Manager,
    offsite_s3: OffsiteS3Manager,
) -> OffsiteReplicationResult:
    """
    Replicate today's backup to the off-site target.

    Steps:
    1. List objects in the primary bucket for today's partition.
    2. Stream-copy each object to offsite with encryption.
    3. Verify checksums match (SHA-256).
    4. Apply retention policy (delete old offsite backups).
    5. Emit metric for monitoring.
    """
    today = datetime.utcnow().date()
    primary_prefix = f"daily/{today.isoformat()}/"

    objects = await primary_s3.list_objects(prefix=primary_prefix)
    context.log.info(f"Replicating {len(objects)} objects to offsite")

    replicated = 0
    errors = []

    for obj in objects:
        try:
            data = await primary_s3.get_object(obj.key)
            checksum = hashlib.sha256(data).hexdigest()

            await offsite_s3.put_object(
                key=obj.key,
                data=data,
                sse="aws:kms",
                sse_kms_key_id=settings.BACKUP_OFFSITE_KMS_KEY_ID,
                metadata={
                    "source_checksum": checksum,
                    "replicated_at": datetime.utcnow().isoformat(),
                },
                storage_class=settings.BACKUP_OFFSITE_STORAGE_CLASS,
            )

            # Verify
            offsite_obj = await offsite_s3.head_object(obj.key)
            assert offsite_obj.metadata["source_checksum"] == checksum

            replicated += 1
        except Exception as e:
            errors.append({"key": obj.key, "error": str(e)})
            context.log.error(f"Failed replicating {obj.key}: {e}")

    # Apply retention
    await offsite_s3.apply_retention(days=settings.BACKUP_REPLICATE_RETENTION_DAYS)

    return OffsiteReplicationResult(
        replicated_count=replicated,
        error_count=len(errors),
        errors=errors,
        timestamp=datetime.utcnow(),
    )


@schedule(
    cron_schedule="0 4 * * *",  # 4 AM (1h after daily_backup_job at 3 AM)
    job=offsite_replication_job,
    execution_timezone="Europe/Zurich",
)
def daily_offsite_replication_schedule():
    return {}
```

### Tier 4 (future): Cross-region with continuous replication

For SaaS scale, consider:

- SeaweedFS async replication (built-in cross-region).
- Real-time event streaming to offsite (NATS → offsite NATS).
- Read-replica for disaster failover.

### DR Drill (monthly)

Document procedure:

1. Pick random offsite backup.
2. Spin up isolated test VM.
3. Restore PostgreSQL, Mongo, Milvus, Valkey, NATS from offsite.
4. Verify data integrity (sample queries).
5. Document restore time → update RTO baseline.
6. Document data loss → update RPO baseline.

### Monitoring and alerting

Cross-ref ADR-NEW-032 (AlertManager). Critical alerts:

```yaml
- alert: BackupOffsiteStale
  expr: time() - aihub_offsite_last_sync_timestamp > 90000  # 25 hours
  for: 5m
  labels: {severity: critical}
  annotations:
    summary: "Off-site backup replication stale > 25h"
    runbook: "https://docs.aihub.ch/runbook/backup-offsite-stale"

- alert: BackupOffsiteFailureRate
  expr: rate(aihub_offsite_replication_errors_total[1h]) > 0.1
  for: 10m
  labels: {severity: warning}

- alert: OffsiteStorageNearLimit
  expr: aihub_offsite_storage_used_bytes / aihub_offsite_storage_quota_bytes > 0.85
  for: 30m
  labels: {severity: warning}
```

## Consequences

### Positive

- 3-2-1 backup rule compliance.
- Disaster recovery feasible (hardware failure, ransomware, datacenter outage).
- Sovereignty maintained (off-site target in Swiss jurisdiction).
- RTO/RPO measurable and verifiable via the monthly drill.
- Encryption end-to-end (transit and rest).
- Audit trail for every replication operation.

### Negative

- Cost: Off-site storage + egress bandwidth (~\$50-200/month per TB depending provider).
- Network bandwidth utilization: backup sync time depends on data size (10 TB backup ~ 2-8 hours over 100 Mbps).
- Initial setup: KMS keys, IAM roles, network config.
- Stale window: between primary and offsite (acceptable RPO 24h).
- Restore time increases: pulling from offsite is slower than local SeaweedFS.

### Implementation timeline

- **Week 1**: Tier 1 cron script deployed now (emergency mitigation for production).
- **Sprint 1 (week 2-3)**: Tier 2 configurable target in code.
- **Sprint 2 (week 4-5)**: Tier 3 Dagster job with observability.
- **Sprint 3 (week 6-7)**: Monitoring + alerting + first DR drill.
- **Quarterly**: DR drill documented.

### Customer notification

Before rollout:

- Notify customers about the data-flow change (off-site target).
- Update the GDPR transfer assessment if the off-site has a cross-border element.
- Add to the DPA (Data Processing Agreement) if a third-party provider is used.

## References

- [Details §21.1 Backup Disaster Recovery](../02_architecture_review_details.md#211-backup-disaster-recovery-fatal-flaw):
  Full evidence and disaster scenario.
- [Existing risks doc](../../chapters/11_risks_and_technical_debt.md): Lines 20-32 admit gap.
- 3-2-1 Backup Rule: Industry standard.
- Infomaniak Public Cloud: https://www.infomaniak.com/en/hosting/public-cloud
- Exoscale SOS: https://www.exoscale.com/object-storage/
- ADR-NEW-031 (Configurable Backup Target Endpoint): Detailed config schema.
- ADR-NEW-032 (Prometheus + AlertManager): Monitoring integration.
