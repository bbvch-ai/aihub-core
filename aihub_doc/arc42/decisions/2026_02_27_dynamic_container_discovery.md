# Dynamic Container Discovery for Backup Service

## Context

The backup service (`aihub_backup`) needs to stop and restart Docker Compose services during backup and restore
operations. The initial implementation used ~50 hardcoded container names across 6 tuples in `container_lifecycle.py`
(`APP_CONTAINERS`, `INFRA_CONSUMERS`, `DATABASE_CONTAINERS`, `START_ORDER_APPS`, `START_ORDER_INFRA`,
`START_ORDER_SERVICES`). These had to be manually synchronized with the main Docker Compose template whenever a service
was added, removed, or renamed — a fragile coupling across two packages.

## Decision Drivers

- **Eliminate manual synchronization**\
  Adding a new service to Docker Compose should not require updating container name lists in the backup service. The
  coupling was a recurring source of errors and review friction.

- **Correct backup isolation**\
  The old approach only stopped application containers during backup, leaving infrastructure consumers running. This
  meant potential writes during backup windows. Stopping all managed containers provides stronger consistency
  guarantees.

- **Parallel backup safety**\
  Per-service backup assets run in parallel (Dagster fan-out). Each handler starts only the containers it needs, backs
  up, then stops them. This requires that no two handlers share a container dependency.

## Decision

Replace hardcoded container lists with dynamic discovery using Docker Compose's built-in `com.docker.compose.project`
label. Every container created by Docker Compose automatically receives this label with the project name.

**New workflow**:

1. `backup_session`: Discover all containers in the compose project, stop all except infrastructure that must stay
   running (`backup-*`, `seaweedfs-*`, `etcd`). Save `previously_running` list.
2. Per-service assets (parallel): Start handler dependencies → backup → stop handler dependencies.
3. `backup_finalize`: Restart all `previously_running` containers.

**Key components**:

- `ContainerDiscovery` class: Uses `com.docker.compose.project` label to find containers, detects own project from
  hostname-based container lookup. Exclusion prefixes: `backup-`, `seaweedfs-`, `etcd`.
- `SERVICE_DEPS` dict: Maps each handler to its required containers and health-check timeout. Replaces the old
  `RESTORE_STEPS` (used for both backup and restore).
- Import-time disjointness assertion: Validates that no two handlers claim the same container, catching parallel-unsafe
  configurations before deployment.

**No custom Docker labels required** — the standard `com.docker.compose.project` label is sufficient. No separate
compose file needed — backup containers live in the main compose project and discover siblings via the shared project
label.

## Consequences

- Adding/removing Docker Compose services requires **zero changes** to backup code
- ~50 hardcoded container names and 3 consistency assertions eliminated
- Stronger backup isolation: all managed containers stopped during backup, not just applications
- Import-time safety assertion prevents future handlers from accidentally sharing container dependencies
- Backup service must run inside Docker Compose (needs Docker socket + project label on own container)
