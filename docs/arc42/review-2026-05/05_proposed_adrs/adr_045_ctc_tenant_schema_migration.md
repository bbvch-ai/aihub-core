# C\*C MongoDB Tenant-Entry Schema Migration (Upgrade Blocker)

**Status**: Proposed (2026-05-29) **Severity**: P0 (blocks the C*C SDK upgrade) **Drives**: Overview §3.3, §5.3 (c*c);
depends on ADR-NEW-003 (Database Migration Framework)

## Context

C*C is pinned at core **v0.274.3** (16 minors behind v0.290.4). The **biggest upgrade risk identified in review
2026-05** is that the **MongoDB schema for tenant entries changed** between the pinned version and current core.
Upgrading the SDK without migrating the existing tenant documents will leave C*C with data that no longer matches the
entity model — a correctness and availability risk, not a cosmetic one.

This is the concrete instance of a platform-wide gap: there is **no database migration framework** (tracked as
ADR-NEW-003). Today an SDK bump that changes a persisted schema has no safe, repeatable, reversible path — exactly the
situation C\*C is in. Tenant data is high-value (access rules, membership, metadata), so an ad-hoc one-off script is the
wrong tool.

Relevant core entities live under `packages/core/swiss_ai_hub/core/persistence/access/` (e.g. `TenantMetadataEntity`,
`UserTenantRoleEntity`, `RoleEntity`). Note also that **Keycloak — not Mongo — is the source of truth for tenant
existence** (`KeycloakAdminService.tenant_exists()`), so the migration must reconcile Mongo tenant documents against
Keycloak groups rather than trusting Mongo alone.

## Decision Drivers

- **No data loss / no downtime surprise**: tenant data must survive the upgrade intact.
- **Reversible**: a failed migration must roll back cleanly (backup + dry-run first).
- **Repeatable**: other customers will hit schema changes too — solve it with the framework, not a bespoke script.
- **Source-of-truth correctness**: reconcile against Keycloak, which owns tenant existence.
- **Sequenced**: the migration must run as a gated step in the C\*C upgrade, not opportunistically.

## Decision

1. **Build the migration on top of ADR-NEW-003** (the database migration framework) rather than a throwaway script —
   C\*C is the first real consumer and validates the framework.

2. **Author a forward migration** that transforms v0.274.3-era tenant-entry documents to the current
   `TenantMetadataEntity` / `UserTenantRoleEntity` shape, with an explicit **down/rollback** path.

3. **Reconcile against Keycloak**: during migration, validate each Mongo tenant document against
   `KeycloakAdminService.tenant_exists()` / `get_all_tenant_groups()`; drop/flag orphans rather than carrying stale rows
   forward.

4. **Gated rollout for C\*C**: (a) full backup; (b) **dry-run on a restored copy** with row-count and spot-check
   assertions; (c) run in a maintenance window; (d) post-migration verification (entity loads, auth/permission smoke
   test) before un-gating traffic. This is the migration step in the C\*C upgrade track in the PO roadmap (§7, Q4).

## Consequences

**Positive**

- C\*C can upgrade safely; the highest-risk blocker is removed.
- The migration framework (ADR-NEW-003) gets a real, validated first use.
- Tenant data is reconciled with its Keycloak source of truth as a side benefit.

**Negative**

- Requires a maintenance window and a tested rollback — real coordination with the customer.
- Depends on ADR-NEW-003 landing first (or a minimal version of it).
- Verification surface is non-trivial (auth/permission behaviour must be re-checked post-migration).

**Open items**

- Exact field-level diff between v0.274.3 and current tenant-entry schema (to be extracted before authoring).
- Whether to bundle this with other pending C\*C schema changes in the 16-minor gap, or migrate incrementally.
- Maintenance-window scheduling with the customer.

## References

- `packages/core/swiss_ai_hub/core/persistence/access/` — `TenantMetadataEntity`, `UserTenantRoleEntity`, `RoleEntity`.
- `KeycloakAdminService` (core auth) — authoritative tenant-existence checks.
- Depends on: ADR-NEW-003 (Database Migration Framework).
- Related: [`adr_040`](adr_040_k8s_chart_core_version_pinning.md) (version-pin policy),
  [`adr_038`](adr_038_sdk_import_discipline.md) (SDK upgrade hygiene).
