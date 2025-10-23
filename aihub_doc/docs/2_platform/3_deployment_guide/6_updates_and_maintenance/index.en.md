---
title: 'Updates & Maintenance'
index: 6
---

# Updates and Maintenance

## Overview

This guide covers update and maintenance procedures for AI-Hub deployments. The AI-Hub architecture separates **core platform components** (this repository) from **customer-specific code** (separate private repositories), allowing independent versioning and update schedules while maintaining compatibility.

### Architecture Overview

**Core Platform** (`aihub-core` - this repository):
- Shared foundation components: API, Web, Dagster, Bot
- Public repository visible to all
- Semantic versioning (e.g., `v0.13.0`)
- All customers' tenants use these core components

**Customer Code** (`aihub-<customer>` - separate repositories):
- Custom agents, pipelines, processes
- Private customer repositories (under BBV or customer control)
- Independent versioning pinned to specific core version
- Customer controls update schedule

## Definitions

- **Core Version**: Version of `aihub-core` platform components (e.g., `v0.13.0`)
- **Customer Version**: Version of customer-specific code (e.g., `v1.2.3`)
- **Version Pinning**: Customer code explicitly depends on specific core version
- **RTO (Recovery Time Objective)**: Maximum acceptable time to restore services after an update failure
- **Rollback**: Reverting to the previous version after a failed update

---

# Part 1: Core Platform Updates

## Core Version Management

### Versioning Strategy

The core platform uses **semantic versioning** (`major.minor.patch`):

- **Major** (X.0.0): Breaking changes, significant architectural updates
- **Minor** (0.X.0): New features, backward-compatible changes
- **Patch** (0.0.X): Bug fixes, security patches

**Current version**: `v0.13.0`

### Available Core Version Tags

| Tag | Description | Stability | Use Case |
|-----|-------------|-----------|----------|
| `latest` | Latest stable production release | High | Production deployments |
| `nightly` | Latest development build | Medium | Testing, staging environments |
| `v0.13.0` | Specific version tag | Highest | Production with version pinning |

### Core Release Process

1. **PR Merge**: Developer merges PR to `main` with version label (`major`, `minor`, `patch`)
2. **Automated Tagging**: CI/CD computes new version and creates Git tag
3. **Component Builds**: Triggers builds for affected components (api, dagster, web, etc.)
4. **Image Publishing**: Docker images published to `ghcr.io/bbvch-ai/aihub-core/*`
5. **Changelog Generation**: Automated changelog created

**Example Core Images**:
```
ghcr.io/bbvch-ai/aihub-core/api:v0.13.0
ghcr.io/bbvch-ai/aihub-core/dagster:v0.13.0
ghcr.io/bbvch-ai/aihub-core/web:v0.13.0
```

---

## Core Update Types

### 1. Core Patch Updates (Low Risk)

**Scope**: Bug fixes, security patches in core components

**Downtime**: Minimal (5-15 minutes)

**Impact**: All tenants using this core version

**Process**: Rolling restart of core services

### 2. Core Minor Updates (Medium Risk)

**Scope**: New core features, backward-compatible API changes

**Downtime**: Short (15-30 minutes)

**Impact**: Customer code remains compatible

**Process**: Full service restart with health checks

### 3. Core Major Updates (High Risk)

**Scope**: Breaking changes in core APIs or architecture

**Downtime**: Extended (30-120 minutes)

**Impact**: **Requires customer code updates** for compatibility

**Process**: Coordinated update with customer code testing

---

## Core Update Procedures

### Standard Core Update (Patch/Minor)

For backward-compatible core updates that don't affect customer code.

#### Pre-Update Checklist

- [ ] Review core changelog and release notes
- [ ] Verify customer code compatibility (if breaking changes)
- [ ] Backup all tenant data (per-tenant backups)
- [ ] Create pre-update VM snapshot
- [ ] Schedule maintenance window
- [ ] Notify affected tenants

#### Update Steps

1. **Backup Current State**: Create VM snapshot or component backups
2. **Update Core Image Tags**: Modify `docker-compose.yml` to use new core version tags
3. **Pull New Core Images**: Download updated core containers
4. **Restart Core Services**: Stop and restart services with health check verification
5. **Verify Core Services**: Check health endpoints, verify critical functionality
6. **Monitor**: Watch logs and metrics for 24-48 hours

#### Post-Update Verification

- [ ] All core services healthy
- [ ] Core APIs responding correctly
- [ ] Customer agents/pipelines still functional
- [ ] Observability dashboards operational
- [ ] No errors in service logs

### Major Core Update with Breaking Changes

For core updates that require customer code changes.

#### Pre-Update Requirements

- [ ] Review breaking changes in core changelog
- [ ] Notify customers of required code updates
- [ ] Test customer code against new core version in staging
- [ ] Update customer code to support new core version
- [ ] Plan coordinated update schedule

#### Update Strategy

**Option A: Update Core, Then Customer Code** (Recommended)
1. Update core platform to new major version
2. Verify core services healthy
3. Update customer code separately (see Part 2)
4. Test integration between new core and new customer code

**Option B: Coordinated Update**
1. Prepare both core and customer code updates
2. Schedule single maintenance window
3. Update core and customer code together
4. Verify complete system integration

---

## Core Rollback Procedures

### When to Rollback Core

Initiate a core rollback if:
- Core services fail to start or remain unhealthy
- Critical core APIs broken
- Performance degradation in core components
- Security vulnerabilities introduced in core
- Unable to resolve core issues within RTO window

### Core Rollback from VM Snapshot

Fastest method for complete core rollback:

1. Stop all services (core + customer)
2. Restore VM from pre-update snapshot
3. Start services and verify health
4. Notify stakeholders of rollback

**RTO**: 15-30 minutes

### Core Rollback by Version Tag

If data is compatible:

1. Update `docker-compose.yml` to previous core version tags
2. Pull previous core images
3. Restart core services
4. Verify health
5. Customer code continues running (unchanged)

**RTO**: 10-20 minutes

**Note**: Customer code may need rollback if it depends on new core features.

---

# Part 2: Customer Code Updates

## Customer Code Architecture

### Repository Structure

Each customer has a separate private repository:

```
aihub-<customer>/
├── aihub_agents/          # Custom agent implementations
├── aihub_pipeline/        # Custom data pipelines
├── aihub_process/         # Custom business processes
├── pyproject.toml         # Dependencies + core version pinning
├── docker-compose.yml     # Deployment configuration
└── .github/workflows/     # CI/CD pipelines
```

### Customer Code Versioning

Customer code uses **independent semantic versioning**:

- **Version**: `v1.2.3` (separate from core version)
- **Core Dependency**: Pinned in `pyproject.toml`

**Example**:
```toml
[tool.poetry.dependencies]
aihub-core = { git = "https://github.com/bbvch-ai/aihub-core.git", tag = "v0.13.0" }
```

### Customer Image Publishing

Customer code follows same CI/CD pattern as core:

```
ghcr.io/bbvch-ai/aihub-<customer>/agent:v1.2.3
ghcr.io/bbvch-ai/aihub-<customer>/pipeline:v1.2.3
ghcr.io/bbvch-ai/aihub-<customer>/process:v1.2.3
```

---

## Customer Code Update Types

### 1. Customer Code Updates (No Core Change)

**Scope**: Bug fixes or features in customer agents/pipelines

**Core Version**: Unchanged (still pinned to same core version)

**Downtime**: Minimal (5-15 minutes)

**Process**: Update customer images only

### 2. Customer Code + Core Version Bump

**Scope**: Customer code updated to use newer core version

**Core Version**: Updated (e.g., `v0.13.0` → `v0.14.0`)

**Downtime**: Medium (15-30 minutes)

**Process**: Update core dependency, rebuild customer code, deploy both

---

## Customer Code Update Procedures

### Standard Customer Code Update

For customer code changes without core version change.

#### Pre-Update Checklist

- [ ] Review customer code changelog
- [ ] Verify core version compatibility (unchanged)
- [ ] Test in staging environment
- [ ] Backup tenant data
- [ ] Schedule maintenance window

#### Update Steps

1. **Backup Current State**: Create snapshot
2. **Update Customer Image Tags**: Modify `docker-compose.yml` for customer services only
3. **Pull New Customer Images**: Download updated customer containers
4. **Restart Customer Services**: Stop and restart agents/pipelines/processes
5. **Verify Functionality**: Test custom agents and pipelines
6. **Monitor**: Watch for errors in customer service logs

#### Post-Update Verification

- [ ] Customer agents responding correctly
- [ ] Custom pipelines executing successfully
- [ ] Custom processes functioning
- [ ] Integration with core APIs working
- [ ] No errors in customer service logs

### Customer Code Update with Core Version Bump

For updating customer code to use a newer core version.

#### Pre-Update Requirements

- [ ] Test customer code against new core version in staging
- [ ] Update core version pin in `pyproject.toml`
- [ ] Rebuild and test customer images
- [ ] Review core breaking changes affecting customer code
- [ ] Update customer code for compatibility

#### Update Steps

1. **Backup Current State**: Complete system backup
2. **Update Core Components First**: Follow core update procedure (Part 1)
3. **Verify Core Health**: Ensure core services healthy
4. **Update Customer Code Images**: Deploy customer code built against new core
5. **Restart Customer Services**: Start updated customer services
6. **Verify Integration**: Test customer code with new core
7. **Monitor**: Close monitoring for 24-48 hours

---

## Customer Code Rollback Procedures

### When to Rollback Customer Code

Rollback customer code if:
- Custom agents/pipelines fail to start
- Customer-specific functionality broken
- Performance issues in customer services
- Integration issues with core (after core update)

### Customer Code Rollback

1. **Identify Scope**: Customer code only, or customer + core?
2. **Rollback Customer Images**: Revert `docker-compose.yml` to previous customer tags
3. **Pull Previous Customer Images**: Download previous versions
4. **Restart Customer Services**: Stop and start with previous versions
5. **Verify**: Check custom functionality

**RTO**: 10-20 minutes

### Combined Core + Customer Rollback

If customer code was updated alongside core:

1. **Rollback Core First**: Follow core rollback procedure
2. **Rollback Customer Code**: Revert customer image tags
3. **Restart All Services**: Core + customer services
4. **Verify Complete System**: Test full stack

**RTO**: 20-40 minutes

---

# Part 3: Update Coordination

## Core and Customer Version Compatibility

### Version Pinning Strategy

Customer code explicitly pins to specific core version:

```toml
# pyproject.toml in customer repo
[tool.poetry.dependencies]
aihub-core = { git = "https://github.com/bbvch-ai/aihub-core.git", tag = "v0.13.0" }
```

**Benefits**:
- Customer controls when to adopt new core versions
- Core updates don't break customer code unexpectedly
- Customer can test compatibility before updating

### Compatibility Matrix Example

| Customer Version | Core Version | Status | Notes |
|-----------------|--------------|--------|-------|
| v1.0.0 | v0.12.0 | Legacy | End of life |
| v1.1.0 | v0.13.0 | Supported | Current production |
| v1.2.0 | v0.13.0 | Supported | Latest features |
| v2.0.0 | v0.14.0 | Testing | Next major release |

---

## Update Strategies

### Strategy 1: Update Core First (Recommended)

For backward-compatible core updates.

**Workflow**:
1. Update core platform (v0.13.0 → v0.13.1)
2. Verify customer code still works (no changes needed)
3. Customer code continues using updated core
4. Optional: Update customer code later for new core features

**Advantages**:
- Lower risk (customer code unchanged)
- Faster update cycle
- Can update core and customer independently

### Strategy 2: Coordinated Update

For breaking core changes requiring customer code updates.

**Workflow**:
1. Core releases new major version (v0.13.0 → v0.14.0)
2. Customer tests their code against v0.14.0 in staging
3. Customer updates code for compatibility
4. Schedule coordinated update:
   - Update core to v0.14.0
   - Update customer code to v2.0.0 (built against v0.14.0)
5. Deploy both together

**Advantages**:
- Single maintenance window
- Guaranteed compatibility
- Controlled migration

### Strategy 3: Gradual Migration

For large customer codebases with many custom components.

**Workflow**:
1. Update core to new version (backward-compatible mode)
2. Migrate customer components incrementally:
   - Update and deploy Agent A
   - Test and verify
   - Update and deploy Pipeline B
   - Test and verify
   - Continue until all components updated
3. Disable backward-compatible mode in core

**Advantages**:
- Lowest risk
- Incremental testing
- Easier rollback of individual components

---

## Testing Compatibility

### Staging Environment Setup

Maintain staging environment with:
- Latest core version (or release candidate)
- Copy of customer code
- Representative dataset
- Same infrastructure configuration

### Compatibility Testing Checklist

Before updating production:

**Core Testing**:
- [ ] Core services start and pass health checks
- [ ] Core APIs respond correctly
- [ ] Core database migrations successful
- [ ] Core performance acceptable

**Customer Code Testing**:
- [ ] Custom agents execute successfully
- [ ] Custom pipelines process data correctly
- [ ] Custom processes complete workflows
- [ ] Integration with core APIs working

**Integration Testing**:
- [ ] End-to-end user workflows functional
- [ ] Chat interface with custom agents
- [ ] Document upload to custom pipelines
- [ ] External integrations (MS Teams, Slack)

---

## Multi-Tenant Update Strategy

### Per-Tenant Deployment Model

Each tenant operates isolated instance with:
- Shared core components (same core version across tenants)
- Tenant-specific customer code (can differ per tenant)

### Phased Rollout Strategy

**Phase 1: Pilot Tenant** (Week 1)
- Select low-risk tenant
- Update core and customer code
- Monitor for 3-5 days
- Collect feedback

**Phase 2: Staged Rollout** (Week 2-3)
- Update 25% of tenants
- Monitor for issues
- Update another 25%
- Continue to 75%

**Phase 3: Final Deployment** (Week 4)
- Update remaining 25%
- Monitor all tenants
- Document lessons learned

**Alternative: Customer-Controlled Updates**

If customer controls their repository:
- Customer decides update schedule
- Customer tests in their staging
- Customer deploys to their tenants
- BBV provides core updates and support

---

## Configuration Management

### Core Configuration

Version-controlled in `aihub-core` repository:
- `configs/nats/nats.latest.conf`
- `configs/litellm/config.latest.yaml`
- `configs/milvus/milvus.latest.yaml`
- `configs/dagster/dagster.latest.yaml`

### Customer Configuration

Version-controlled in customer repository:
- `configs/custom-agent-config.yaml`
- `configs/custom-pipeline-config.yaml`
- `.env` (tenant-specific environment variables)

### Configuration Updates

**Core Configuration Changes**:
1. Update configuration in `aihub-core`
2. Test in staging
3. Deploy with core update
4. Customer code inherits new configuration

**Customer Configuration Changes**:
1. Update configuration in customer repo
2. Test in staging
3. Deploy with customer code update
4. Core remains unchanged

---

## Monitoring During Updates

### Core Health Monitoring

Monitor core service health:
- API response time and error rate
- Dagster pipeline execution
- Web interface availability
- Database connection health

### Customer Code Monitoring

Monitor customer service health:
- Custom agent execution success rate
- Custom pipeline processing time
- Custom process completion rate
- Integration with core APIs

### Observability Tools

Use built-in observability stack:
- **SigNoz**: Metrics, logs, traces (core + customer)
- **Phoenix**: AI-specific tracing (agent workflows)
- **OpenTelemetry**: Distributed tracing across all services

---

## Maintenance Tasks

### Core Maintenance (BBV Responsibility)

**Weekly**:
- [ ] Review core security advisories
- [ ] Check for core dependency updates
- [ ] Monitor core performance metrics

**Monthly**:
- [ ] Apply core patch updates
- [ ] Review core capacity planning
- [ ] Test core backup restoration

**Quarterly**:
- [ ] Evaluate core minor version updates
- [ ] Core security audit
- [ ] Core disaster recovery drill

### Customer Code Maintenance (Customer or BBV)

**Weekly**:
- [ ] Review customer code logs
- [ ] Monitor custom service performance
- [ ] Verify customer backups

**Monthly**:
- [ ] Update customer code dependencies (non-core)
- [ ] Review custom service resource usage
- [ ] Test customer code in staging

**Quarterly**:
- [ ] Evaluate core version bump
- [ ] Review custom code architecture
- [ ] Customer-specific disaster recovery test

---

## Troubleshooting Update Issues

### Core Service Fails After Update

**Symptoms**: Core API, Web, or Dagster fails to start

**Diagnosis**:
- Check core service logs
- Verify core configuration syntax
- Confirm database migrations completed

**Resolution**:
- Review core changelog for breaking changes
- Rollback core to previous version
- Contact BBV support for core issues

### Customer Service Fails After Update

**Symptoms**: Custom agents or pipelines fail to start or execute

**Diagnosis**:
- Check customer service logs
- Verify customer code compatibility with core version
- Test customer code in isolation

**Resolution**:
- Review customer code changes
- Verify core API compatibility
- Rollback customer code if needed
- Update customer code for new core version

### Integration Issues Between Core and Customer

**Symptoms**: Customer code runs but fails to interact with core APIs

**Diagnosis**:
- Check API version compatibility
- Review core API changes in changelog
- Verify network connectivity between containers

**Resolution**:
- Update customer code to use new core API patterns
- Verify environment variables for core API endpoints
- Check authentication/authorization configuration

---

## Emergency Update Procedures

### Critical Core Security Patch

For urgent vulnerabilities in core platform:

1. **Assess Impact**: Determine which customers/tenants affected
2. **Notify Customers**: Emergency maintenance notice
3. **Backup**: Quick snapshot across tenants
4. **Apply Core Patch**: Update core images to patched version
5. **Verify**: Test core security fix
6. **Monitor**: Close monitoring for 24 hours

**RTO Target**: 2-4 hours

### Critical Customer Code Patch

For urgent vulnerabilities in customer-specific code:

1. **Assess Scope**: Identify affected customer repositories
2. **Notify Customer**: Emergency patch notification
3. **Backup**: Snapshot affected tenants
4. **Apply Patch**: Update customer images
5. **Verify**: Test customer code fix
6. **Monitor**: Close monitoring for 24 hours

**RTO Target**: 2-4 hours

---

## Best Practices

### For Core Updates

- **Pin Versions in Production**: Use explicit core tags (v0.13.0), not `latest`
- **Test Before Deploy**: Always test core updates in staging first
- **Communicate Breaking Changes**: Notify customers well in advance of major core updates
- **Maintain Backward Compatibility**: Strive for backward-compatible core APIs

### For Customer Code Updates

- **Pin Core Version**: Always pin to specific core version in `pyproject.toml`
- **Test Against Multiple Core Versions**: Ensure compatibility with core N and N-1
- **Independent Versioning**: Version customer code independently from core
- **Follow Same CI/CD Patterns**: Use same container registry and automation as core

### For Update Coordination

- **Update Core First**: For backward-compatible changes, update core before customer code
- **Test Compatibility**: Always test customer code against new core in staging
- **Staged Rollouts**: Use pilot tenants before full deployment
- **Document Dependencies**: Maintain clear compatibility matrix

---

## Summary Checklist

### Core Update Checklist

- [ ] Review core changelog
- [ ] Notify affected customers of core update
- [ ] Test core update in staging
- [ ] Backup all tenant data
- [ ] Update core image tags
- [ ] Deploy core update
- [ ] Verify core services healthy
- [ ] Test customer code compatibility
- [ ] Monitor for 48 hours

### Customer Code Update Checklist

- [ ] Review customer code changes
- [ ] Verify core version compatibility
- [ ] Test customer code in staging
- [ ] Backup tenant data
- [ ] Update customer image tags
- [ ] Deploy customer code update
- [ ] Verify customer services healthy
- [ ] Test integration with core
- [ ] Monitor for 48 hours

### Combined Update Checklist

- [ ] Plan coordinated update schedule
- [ ] Test both core and customer code together
- [ ] Backup complete system
- [ ] Update core first, verify health
- [ ] Update customer code, verify health
- [ ] Test end-to-end functionality
- [ ] Monitor for 48 hours
- [ ] Document update results

---

## Next Steps

- [Production Configuration](../2_production_configuration/) — Configure production environment
- [Scaling Considerations](../3_scaling_considerations/) — Plan for capacity growth
- [Backup and Recovery](../4_backup_and_recovery/) — Backup before updates
- [Monitoring and Alerting](../5_monitoring_and_alerting/) — Update monitoring

---

## Related Documentation

- **Deployment**: [Deployment Options](../1_deployment_options/) — Per-tenant architecture
- **Architecture**: [Core Components](../../2_architecture/1_core_components/) — Core component dependencies
- **Development**: [README.md](/README.md) — Repository structure and customer code patterns
