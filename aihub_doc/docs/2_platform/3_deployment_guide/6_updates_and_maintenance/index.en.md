---
title: Updates & Maintenance
---

# Updates and maintenance

## Architecture

The AI-Hub separates core platform components from customer-specific code. The core platform (this repository) contains
shared foundation components like API, Web, Dagster, and Bot. Customer repositories contain custom agents, pipelines,
and processes. Both use independent semantic versioning and can be updated separately.

Customer code pins to a specific core version through `pyproject.toml`:

```toml
[tool.poetry.dependencies]
aihub-core = { git = "https://github.com/bbvch-ai/aihub-core.git", tag = "v1.2.3" }
```

This means core updates don't automatically affect customer deployments. Customers control when they adopt new core
versions.

---

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

When a PR merges to `main` with a version label (`major`, `minor`, or `patch`), CI/CD computes the new version and
creates a Git tag. This triggers component builds for affected services. Docker images are published to
`ghcr.io/bbvch-ai/aihub-core/*` with the version tag. A changelog is generated automatically.

Example core images:

```
ghcr.io/bbvch-ai/aihub-core/api:v1.2.3
ghcr.io/bbvch-ai/aihub-core/dagster:v1.2.3
ghcr.io/bbvch-ai/aihub-core/web:v1.2.3
```

Customer code follows the same CI/CD pattern:

```
ghcr.io/bbvch-ai/aihub-<customer>/agent:v1.2.3
ghcr.io/bbvch-ai/aihub-<customer>/pipeline:v1.2.3
```

---

## Updates

### Core platform updates

Backward-compatible core updates (patch and minor versions) can be deployed by updating image tags in
`docker-compose.yml`, pulling new images, and restarting services. Customer code continues running unchanged.

Major core updates with breaking changes require coordinated updates. Customer code must be updated to work with the new
core version. Both core and customer code are updated together during a maintenance window.

### Customer code updates

Customer code can be updated independently when the core version pin remains unchanged. Update the customer image tags
in `docker-compose.yml`, pull the new images, and restart the customer services.

When customer code adopts a new core version, update the core version pin in `pyproject.toml`, rebuild the customer
images, then deploy both core and customer updates together.

---

## Rollbacks

### VM snapshots

VM snapshots capture the entire system state. Rollback restores the complete VM from a pre-update snapshot, returning
all services to their previous state at once.

### Version tags

If data remains compatible with the previous version, rollback by reverting image tags in `docker-compose.yml` to the
previous versions, pulling those images, and restarting services.

Core and customer code can be rolled back independently if they were updated separately. If both were updated together,
roll back core first, then customer code.

---

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

---

## Monitoring

The observability stack includes Langfuse for AI-specific tracing, OpenTelemetry for distributed tracing, and optional
SigNoz Cloud for external metrics and logs. Monitor core services (API, Web, Dagster) and customer services (agents,
pipelines, processes) during and after updates.

---

## Related documentation

- [Deployment Options](../1_deployment_options/) - Per-instance architecture
- [Multi-tenancy](../../16_multi_tenancy/) - Logical separation within instances
- [Backup and Recovery](../4_backup_and_recovery/) - Backup strategies
- [Core Components](../../2_architecture/1_core_components/) - Component dependencies
