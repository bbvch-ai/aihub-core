# Dynamic Container Discovery for Backup Service

## Context

The backup service (`aihub_backup`) needs to stop and restart Docker Compose services during backup and restore
operations. A straightforward approach would be to hardcode container names — maintaining explicit lists of application
containers, infrastructure consumers, database containers, and start-order tuples. However, these lists would need to be
manually synchronized with the main Docker Compose template whenever a service is added, removed, or renamed — a fragile
coupling across two packages.

## Decision Drivers

- **Avoid manual synchronization**\
  Adding a new service to Docker Compose should not require updating container name lists in the backup service. Static
  lists create a coupling that is a predictable source of errors and review friction.

- **Correct backup isolation**\
  Stopping only application containers during backup would leave infrastructure consumers running, allowing potential
  writes during backup windows. Stopping all managed containers provides stronger consistency guarantees.

- **Parallel backup safety**\
  Per-service backup assets run in parallel (Dagster fan-out). Each handler starts only the containers it needs, backs
  up, then stops them. This requires that no two handlers share a container dependency.

## Decision

Use dynamic discovery via Docker Compose's built-in `com.docker.compose.project` label instead of hardcoded container
lists. Every container created by Docker Compose automatically receives this label with the project name.

**Workflow**:

1. `backup_session`: Discover all containers in the compose project, stop all except infrastructure that must stay
   running (`backup-*`, `seaweedfs-*`, `etcd`). Save `previously_running` list.
2. Per-service assets (parallel): Start handler dependencies → backup → stop handler dependencies.
3. `backup_finalize`: Restart all `previously_running` containers.

**Key components**:

- `ContainerDiscovery` class: Uses `com.docker.compose.project` label to find containers, detects own project from
  hostname-based container lookup. Exclusion prefixes: `backup-`, `seaweedfs-`, `etcd`.
- `SERVICE_DEPS` dict: Maps each handler to its required containers and health-check timeout.
- Import-time disjointness assertion: Validates that no two handlers claim the same container, catching parallel-unsafe
  configurations before deployment.

**No custom Docker labels required** — the standard `com.docker.compose.project` label is sufficient. No separate
compose file needed — backup containers live in the main compose project and discover siblings via the shared project
label.

## Consequences

- Adding/removing Docker Compose services requires **zero changes** to backup code
- Stronger backup isolation: all managed containers stopped during backup, not just applications
- Import-time safety assertion prevents future handlers from accidentally sharing container dependencies
- Backup service must run inside Docker Compose (needs Docker socket + project label on own container)
