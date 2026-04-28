---
title: Data Retention Policies
---

## Data retention strategy

The platform implements a tiered retention strategy:

**Ephemeral data (30-day automatic deletion)**: High-performance working memory stored in Redis expires automatically.
Execution-specific data provides a fixed 30-day window for debugging. Conversational memory uses a sliding 30-day
expiration that resets with each access.

**Workflow events (dual constraints)**: NATS JetStream manages workflow events with both time-based (30 days) and
capacity-based (10 million messages) limits. In high-throughput deployments, events may be deleted before the 30-day
limit when capacity is reached.

**Permanent storage (manual lifecycle management)**: NoSQL storage retains conversation history indefinitely without
automatic expiration. Organizations must implement explicit data lifecycle policies aligned with regulatory requirements
and business needs.

**Operational implications**: Organizations have a 30-day window for forensic analysis of workflow execution details.
Critical execution information should be persisted to permanent storage before the 30-day threshold for long-term
retention. Compliance investigations requiring workflow reconstruction are limited to the available retention window.

**Dagster operational logs (separate retention track)**: Verbose Python logger entries (`DEBUG`, `INFO`, `WARNING`)
emitted by pipelines and agents and transient framework-internal events (`HANDLED_OUTPUT`, `LOADED_INPUT`,
`ENGINE_EVENT`, `ASSET_MATERIALIZATION_PLANNED`, `STEP_OUTPUT`) are pruned automatically by the platform's continuous
maintenance subsystem to prevent unbounded Postgres growth. Default retention windows are 7 days for `DEBUG`, 60 days
for `INFO`/`WARNING`, and 30 days for transient framework events; configurable per deployment via
`DAGSTER_*_LOG_RETENTION_DAYS` environment variables. Asset materializations, step success/failure, and run records are
**never** pruned by this subsystem — they remain available for the lifetime of the deployment unless deleted explicitly.
See [Backup and Recovery](../../3_deployment_guide/4_backup_and_recovery/#continuous-postgres-maintenance) for details.
