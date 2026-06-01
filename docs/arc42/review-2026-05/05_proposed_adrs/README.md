# Proposed ADRs (Architecture Decision Records)

This folder contains proposed ADRs from Architecture Review 2026-05 for the critical gaps identified.

**Status**: Proposed (not yet accepted). Each ADR needs stakeholder review and acceptance before implementation.

**Reference**: All 40 proposed ADRs are listed in
[Details §24](../02_architecture_review_details.md#24-proposed-adrs-36-total) (36 original entries + 4 added in the
2026-05-28 review refresh: ADR-NEW-038 to ADR-NEW-041).

**Added in the 2026-05-29 review refresh**: ADR-NEW-042 to ADR-NEW-046 (pluggable parser/Docling, continuous
component-update strategy, RAG/vector-design gate, C\*C tenant-schema migration, load-test baselines). These items are
**not yet reflected in Details §24** because the Details file is out of scope for this refresh; the corresponding phasing
lives in [PO deck §7](../04_po_presentation_deck.md).

## ADRs already written in detail (priority P0)

| #           | File                                                                               | Topic                                           | Drives             |
| ----------- | ---------------------------------------------------------------------------------- | ----------------------------------------------- | ------------------ |
| ADR-NEW-000 | [`adr_000_sovereignty_compliance_path.md`](adr_000_sovereignty_compliance_path.md) | Sovereignty compliance path (Option A/B/C)      | §18 SOV-1          |
| ADR-NEW-011 | [`adr_011_audit_log_entity.md`](adr_011_audit_log_entity.md)                       | Audit log entity and compliance                 | DTC-2, BR-4        |
| ADR-NEW-012 | [`adr_012_usage_limits_enforcement.md`](adr_012_usage_limits_enforcement.md)       | LLM cost cap and UsageLimits enforcement        | DTC-1              |
| ADR-NEW-019 | [`adr_019_mcp_secure_executor.md`](adr_019_mcp_secure_executor.md)                 | MCP secure executor and tool authorization      | §19.2              |
| ADR-NEW-020 | [`adr_020_document_acl_inheritance.md`](adr_020_document_acl_inheritance.md)       | Document ACL inheritance in the vector DB       | §19.3              |
| ADR-NEW-030 | [`adr_030_offsite_backup_replication.md`](adr_030_offsite_backup_replication.md)   | Off-site backup replication and 3-2-1 compliance | §21.1             |
| ADR-NEW-037 | [`adr_037_aihub_supported_use_cases.md`](adr_037_aihub_supported_use_cases.md)     | Authoritative supported AI use cases            | §1 Strengths, §3.2 |
| ADR-NEW-038 | [`adr_038_sdk_import_discipline.md`](adr_038_sdk_import_discipline.md)             | SDK import discipline — public API only         | §3.2 #10, §3.3 #17 |
| ADR-NEW-039 | [`adr_039_fmh_azure_ai_search_vs_milvus.md`](adr_039_fmh_azure_ai_search_vs_milvus.md) | F*H: Azure AI Search vs core Milvus         | §3.6 #3            |
| ADR-NEW-040 | [`adr_040_k8s_chart_core_version_pinning.md`](adr_040_k8s_chart_core_version_pinning.md) | aihub-k8s chart core-version pin policy   | §3.1 #20, §3.5 #5  |
| ADR-NEW-041 | [`adr_041_tls_key_committed_remediation.md`](adr_041_tls_key_committed_remediation.md) | W*P TLS key in git — remediation procedure | §3.5 #1            |
| ADR-NEW-042 | [`adr_042_pluggable_document_parser_docling.md`](adr_042_pluggable_document_parser_docling.md) | Pluggable document parser — open loader registry + Docling (MinerU CPU) | §5.1, §5.8 |
| ADR-NEW-043 | [`adr_043_continuous_component_update_strategy.md`](adr_043_continuous_component_update_strategy.md) | Continuous component-update strategy (ports/adapters + Renovate + eval gate) | §5.1, §6.2 |
| ADR-NEW-044 | [`adr_044_rag_vector_design_gate.md`](adr_044_rag_vector_design_gate.md) | RAG/vector-DB design gate (design before implement) | §5.4, §5.5, §5.6, §6.4 |
| ADR-NEW-045 | [`adr_045_ctc_tenant_schema_migration.md`](adr_045_ctc_tenant_schema_migration.md) | C\*C MongoDB tenant-entry schema migration (upgrade blocker) | §3.3 #18, §5.3 |
| ADR-NEW-046 | [`adr_046_load_test_baselines.md`](adr_046_load_test_baselines.md) | Load-test baselines (per project + core) | §3.5 #11, §5.8 |
| ADR-NEW-047 | [`adr_047_gen3_tenant_isolation_hardening.md`](adr_047_gen3_tenant_isolation_hardening.md) | Gen 3 (aihub-k8s) tenant isolation hardening — NetworkPolicy, ResourceQuota, per-tenant Milvus credential, HA | ADR-NEW-002, c4/deployment_generations |

## ADRs not yet written in detail (30 remaining)

Listed in [Details §24](../02_architecture_review_details.md#24-proposed-adrs-36-total). When the team commits to
implementing one, write the detailed ADR following the template in
[`../../decisions/0000_00_00_template.md`](../../decisions/0000_00_00_template.md).

| #           | Title                                             | Drives           | Priority |
| ----------- | ------------------------------------------------- | ---------------- | :------: |
| ADR-NEW-001 | SDK Versioning and Deprecation Policy             | G2.1, G2.4       |    P1    |
| ADR-NEW-002 | Tenant Data Isolation Strategy                    | G1.1             |    P0    |
| ADR-NEW-003 | Database Migration Framework                      | G4.1             |    P0    |
| ADR-NEW-004 | Customer Extension Configuration Schema           | G1.2, G2.7, G3.6 |    P1    |
| ADR-NEW-005 | Secrets Management and Rotation                   | G3.7             |    P1    |
| ADR-NEW-006 | SDK Public API Contract (import discipline)       | G2.6             |    P2    |
| ADR-NEW-007 | Operations Guide and On-Call Playbook             | G5.1, G5.2       |    P1    |
| ADR-NEW-008 | Tenant Provisioning Automation                    | G1.3             |    P1    |
| ADR-NEW-009 | SDK Downstream Integration Testing                | G2.5, G8.2       |    P1    |
| ADR-NEW-010 | SLI/SLO Definition for Production                 | G6.3, G7.2       |    P1    |
| ADR-NEW-013 | Process Package Fate                              | DTC-8            |    P0    |
| ADR-NEW-014 | Pipeline Executor Strategy (Multiprocess)         | DTC-6            |    P0    |
| ADR-NEW-015 | Milvus Cluster Mode and Index Selection           | DTC-7            |    P0    |
| ADR-NEW-016 | Customer LiteLLM Config Compliance Gate           | SOV-1            |    P0    |
| ADR-NEW-017 | Update 2026_02_24 ADR with Reality Reconciliation | SOV-1            |    P0    |
| ADR-NEW-018 | Per-language Presidio Routing                     | §19.1            |    P1    |
| ADR-NEW-021 | Source-System Authentication Strategy             | §19.4            |    P0    |
| ADR-NEW-022 | AITL Recursion Depth Limit                        | §20.1.1          |    P0    |
| ADR-NEW-023 | Pre-flight Cost Estimation and Hard Cap           | §20.1.2          |    P1    |
| ADR-NEW-024 | Citation Verification Guard                       | §20.1.3          |    P1    |
| ADR-NEW-025 | Document Upload Pipeline Validation               | §20.1.5, §20.2.4 |    P1    |
| ADR-NEW-026 | User and Tenant Deletion API (GDPR Art. 17)       | §20.2.1          |    P0    |
| ADR-NEW-027 | MongoDB Collection TTL Strategy                   | §20.2.2          |    P1    |
| ADR-NEW-028 | Embedding Model Versioning and Migration          | §20.2.5          |    P1    |
| ADR-NEW-029 | Container Supply Chain Security                   | §20.3            |    P2    |
| ADR-NEW-031 | Configurable Backup Target Endpoint               | §21.1            |    P0    |
| ADR-NEW-032 | Prometheus + AlertManager + On-call Routing       | §21.2            |    P0    |
| ADR-NEW-033 | SLI/SLO Definitions and Business Metrics          | §21.2            |    P1    |
| ADR-NEW-034 | Circuit Breaker for External Dependencies         | §21.3            |    P1    |
| ADR-NEW-035 | Per-tenant Bulkhead Isolation                     | §21.3            |    P1    |
| ADR-NEW-036 | Graceful Degradation for RAG/LLM Failures         | §21.3            |    P1    |

## ADR acceptance workflow

1. Stakeholder reviews the draft ADR.
2. Discussion in a team meeting or PR review.
3. Update the ADR with feedback if needed.
4. After acceptance, move the ADR into [`../../decisions/`](../../decisions/) with the actual date prefix (e.g.
   `2026_06_01_audit_log_entity.md`).
5. Update Details §24, changing the status from "Proposed" to "Accepted [link]".
6. Update the Roadmap (Details §23) if the timeline needs adjusting.

## Template

Each ADR follows the template: Context → Decision Drivers → Decision → Consequences. See
[`../../decisions/0000_00_00_template.md`](../../decisions/0000_00_00_template.md).
