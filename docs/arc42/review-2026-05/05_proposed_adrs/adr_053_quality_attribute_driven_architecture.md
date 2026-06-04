# Quality-Attribute-Driven Architecture — Define NFR Scenarios Before Deciding Architecture

**Status**: Proposed (2026-05-29) **Severity**: P1 (architecture governance; root cause of deferred multi-tenancy)
**Drives**: Overview §3.1 #35 (no quality-attribute/NFR scenarios), §3.1 #3 (multi-tenant data layer not isolated),
§3.3 #18 (C\*C tenant-schema migration); relates to `adr_002` (tenant isolation), `adr_003` (DB migration), `adr_044`
(design-before-implement gate)

## Context

The review keeps hitting the same shape: an architecturally significant decision was **made implicitly or deferred**
because no measurable quality attribute forced it early, and the bill arrives later as a customer-impacting migration.

The clearest case is **multi-tenancy**:

- The platform advertises tenant-scoped URLs/roles, but the **data layer is not isolated** (§3.1 #3 / §4.0): entities
  lack `tenant_id`, NATS/Milvus/Valkey/Neo4j are not namespaced.
- Because "tenant isolation" was never written as a **required quality scenario with a target** up front, it was
  deferred — and retrofitting it now means a **tenant data migration** across MongoDB/Milvus/NATS subjects/keys with
  large blast radius. C\*C already faces a tenant-schema migration as an upgrade blocker (§3.3 #18).
- The same pattern recurs for portability (OSS lock-in, §3.1 #24), scalability (single-node ceilings, §3.1 #10/#17),
  and observability (§3.1 #18/#19): all are "discovered" as gaps rather than stated as targets.

arc42 chapter 10 (Quality Requirements) is the canonical home for **quality scenarios** (measurable
stimulus→response statements), but the platform has **no agreed set driving the architecture**. Decisions are made
functionally; non-functional targets are reconstructed after the fact during this review.

## Decision Drivers

- **NFRs must drive architecture, not follow it.** A deferred isolation requirement becomes a migration, not a config
  change.
- **Customer impact.** Retrofitting cross-cutting attributes (tenancy, isolation) forces data migrations that affect
  live customers (C\*C is the proof).
- **Decidability.** Without targets, there is no objective basis to choose between architectures or to know when an
  attribute is "good enough".
- **Auditability.** ISO 27001 / SOC2 and enterprise customers expect documented quality requirements.

## Decision

1. **Author arc42 ch10 quality scenarios** for the platform: a prioritised set of measurable scenarios across
   Multi-Tenancy/Isolation, Scalability, Availability/HA, Portability (anti-lock-in), Security, Performance, and
   Observability — each as stimulus → measurable response.
2. **Make them architecture gates.** Architecturally significant decisions (ADRs) must state which quality scenario(s)
   they satisfy and the target; a design that defers a P0 scenario must say so explicitly with the migration cost it
   incurs.
3. **Sequence cross-cutting attributes early.** Specifically, decide tenant-isolation strategy (`adr_002`) and the DB
   migration framework (`adr_003`) **before** onboarding more tenants, so isolation is built-in rather than migrated-in
   (avoids repeating the C\*C tenant migration `adr_045`).
4. **Re-use the design-before-implement gate** (`adr_044`) as the per-feature enforcement mechanism, extended from
   RAG/vector design to any decision touching a P0 quality scenario.
5. **Review cadence.** Re-validate quality scenarios at each major release and on new-customer onboarding.

## Consequences

**Positive**

- Architecture decisions become defensible against explicit, measurable targets.
- Cross-cutting attributes (esp. multi-tenancy) are built-in early, avoiding forced customer migrations.
- Gives the team an objective "good enough" line per attribute, and auditors a documented quality baseline.

**Negative**

- Upfront effort to author and prioritise quality scenarios; risk of over-specifying.
- Gating ADRs against quality scenarios adds a step to the decision process.

**Open items**

- Owner of the quality-scenario catalogue (architects) and its priority ranking.
- Whether to retrofit isolation now (migration) or hold until the scenarios + `adr_002`/`adr_003` land — this ADR makes
  that trade-off explicit rather than implicit.

## References

- Overview §3.1 #35, §3.1 #3 / §4.0 (multi-tenancy not isolated), §3.3 #18 (C\*C tenant migration), §3.1 #24
  (portability/lock-in).
- arc42 chapter 10 (Quality Requirements) — `docs/arc42/chapters/10_quality_requirements.md`.
- Related: `adr_002` (Tenant Data Isolation Strategy), `adr_003` (Database Migration Framework), `adr_045` (C\*C
  tenant-schema migration), `adr_044` (RAG/vector-design gate — design before implement).
