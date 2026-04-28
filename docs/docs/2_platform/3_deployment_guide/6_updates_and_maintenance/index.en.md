---
title: Updates & Maintenance
---

# Updates and maintenance

## Architecture

The Swiss AI Hub separates core platform components from customer-specific code. The core platform (this repository)
contains shared foundation components like API, Web, Dagster, and Bot. Customer repositories contain custom agents,
pipelines, and processes. Both use independent semantic versioning and can be updated separately.

Customer code pins to a specific core version through `pyproject.toml`:

```toml
[project.dependencies]
swiss-ai-hub = { git = "https://github.com/bbvch-ai/aihub-core.git", tag = "v1.2.3" }
```

This means core updates don't automatically affect customer deployments. Customers control when they adopt new core
versions.

______________________________________________________________________

## Versioning

The core platform uses semantic versioning:

- Major (X.0.0): Breaking changes and architectural updates
- Minor (0.X.0): New features, backward-compatible changes
- Patch (0.0.X): Bug fixes and security patches

Three version tags are available:

| Tag       | Description              | Stability |
| --------- | ------------------------ | --------- |
| `latest`  | Latest stable release    | High      |
| `nightly` | Latest development build | Medium    |
| `v1.2.3`  | Specific version tag     | Highest   |

Customer code uses its own independent version numbers.

### Release process

When a PR merges to `main` with a version label (`major`, `minor`, or `patch`), CI/CD computes the new version, creates
a Git tag, and builds all affected services. Docker images are published to `ghcr.io/bbvch-ai/aihub-core/*` with the
version tag. A changelog is generated automatically.

Each release also publishes self-contained deployment bundles as GitHub Release assets:

- `swissaihub-<version>.tar.gz` — CPU-only deployment bundle
- `swissaihub-<version>-gpu.tar.gz` — GPU-enabled deployment bundle

These bundles contain everything needed to deploy: `docker-compose.yml` with version-pinned image tags, all service
configuration files, an `.env.template` with placeholder secrets, and a `setup-env.sh` script that generates a `.env`
file with cryptographically secure random values for all passwords, tokens, and signing keys.

Example core images:

```
ghcr.io/bbvch-ai/aihub-core/api:v1.2.3
ghcr.io/bbvch-ai/aihub-core/dagster:v1.2.3
ghcr.io/bbvch-ai/aihub-core/web:v1.2.3
```

Customer code follows the same CI/CD pattern:

```
ghcr.io/bbvch-ai/aihub-core-<customer>/agent:v1.2.3
ghcr.io/bbvch-ai/aihub-core-<customer>/pipeline:v1.2.3
```

Browse all releases at [github.com/bbvch-ai/aihub-core/releases](https://github.com/bbvch-ai/aihub-core/releases).

______________________________________________________________________

## Updates

### Core platform updates

Download the new release bundle from [GitHub Releases](https://github.com/bbvch-ai/aihub-core/releases) and extract it
alongside your current deployment:

```bash
# Download the new version
VERSION="v1.3.0"
curl -L "https://github.com/bbvch-ai/aihub-core/releases/download/${VERSION}/swissaihub-${VERSION}.tar.gz" \
  | tar -xz -C /tmp/swissaihub-update

# Copy your existing .env into the new bundle
cp .env /tmp/swissaihub-update/.env

# Review any new environment variables added in the release
diff <(grep -oP '^[A-Z_]+=' .env.template) <(grep -oP '^[A-Z_]+=' /tmp/swissaihub-update/.env.template)

# Replace the deployment files
cp -r /tmp/swissaihub-update/* .

# Pull new images and restart
docker compose pull
docker compose up -d
```

Backward-compatible updates (patch and minor versions) only require pulling new images and restarting. The release
bundle's `docker-compose.yml` already references the correct version-pinned image tags. Customer code continues running
unchanged.

Major core updates with breaking changes require coordinated updates. Customer code must be updated to work with the new
core version. Both core and customer code are updated together during a maintenance window.

### Customer code updates

Customer code can be updated independently when the core version pin remains unchanged. Update the customer image tags
in `docker-compose.yml`, pull the new images, and restart the customer services.

When customer code adopts a new core version, update the core version pin in `pyproject.toml`, rebuild the customer
images, then deploy both core and customer updates together.

______________________________________________________________________

## Rollbacks

### VM snapshots

VM snapshots capture the entire system state. Rollback restores the complete VM from a pre-update snapshot, returning
all services to their previous state at once.

### Version tags

If data remains compatible with the previous version, rollback by downloading the previous release bundle, restoring
your `.env` file, and restarting:

```bash
# Download the previous version's bundle
PREVIOUS="v1.2.3"
curl -L "https://github.com/bbvch-ai/aihub-core/releases/download/${PREVIOUS}/swissaihub-${PREVIOUS}.tar.gz" \
  | tar -xz -C /tmp/swissaihub-rollback

# Restore previous compose and configs, keep your .env
cp .env /tmp/swissaihub-rollback/.env
cp -r /tmp/swissaihub-rollback/* .

# Roll back
docker compose pull
docker compose up -d
```

Core and customer code can be rolled back independently if they were updated separately. If both were updated together,
roll back core first, then customer code.

______________________________________________________________________

## Compatibility

Customer code pins to specific core versions to maintain stability. A compatibility matrix tracks which customer
versions work with which core versions:

| Customer Version | Core Version | Status    | Notes              |
| ---------------- | ------------ | --------- | ------------------ |
| v1.0.0           | v0.1.2       | Legacy    | End of life        |
| v1.1.0           | v1.2.3       | Supported | Current production |
| v1.2.0           | v1.2.3       | Supported | Latest features    |
| v2.0.0           | v2.3.4       | Testing   | Next major release |

Staging environments should match production infrastructure and use representative datasets for testing compatibility
before production updates.

______________________________________________________________________

## Monitoring

The observability stack includes Langfuse for AI-specific tracing, OpenTelemetry for distributed tracing, and optional
SigNoz Cloud for external metrics and logs. Monitor core services (API, Web, Dagster) and customer services (agents,
pipelines, processes) during and after updates.

______________________________________________________________________

## Continuous Postgres maintenance

The platform includes automated database maintenance that operators do not need to schedule manually. Two jobs run in
the same Dagster instance as backup (UI at `http://localhost:3004`) and keep the `dagster` database bounded over time:
weekly `dagster_cleanup_job` prunes verbose log entries and transient framework events from `event_logs`, and monthly
`postgres_repack_job` reclaims disk pages via `pg_repack`. Both are mutually exclusive with backup via Dagster's
run-coordinator tag concurrency.

This is what keeps a 5-year-old deployment's Postgres footprint comparable to a 3-month-old one. See
[Backup and Recovery](../4_backup_and_recovery/#continuous-postgres-maintenance) for retention windows and the
`MAINTENANCE_DISABLED` kill switch.

______________________________________________________________________

## Related documentation

- [Deployment Options](../1_deployment_options/) - Per-instance architecture
- [Multi-tenancy](../../16_multi_tenancy/) - Logical separation within instances
- [Backup and Recovery](../4_backup_and_recovery/) - Backup strategies
- [Core Components](../../2_architecture/1_core_components/) - Component dependencies
