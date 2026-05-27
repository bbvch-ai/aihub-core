# Proposed ADRs (Architecture Decision Records)

Folder này chứa các ADRs đề xuất từ Architecture Review 2026-05 cho các gaps critical đã identify.

**Trạng thái**: Proposed (chưa accepted). Mỗi ADR cần stakeholder review và acceptance trước khi implement.

**Tham chiếu**: Toàn bộ 36 ADRs proposed liệt kê trong
[Details §24](../02_architecture_review_details.md#24-proposed-adrs-36-total).

## ADRs đã viết detailed (priority P0)

| #           | File                                                                               | Topic                                           | Drives             |
| ----------- | ---------------------------------------------------------------------------------- | ----------------------------------------------- | ------------------ |
| ADR-NEW-000 | [`adr_000_sovereignty_compliance_path.md`](adr_000_sovereignty_compliance_path.md) | Sovereignty compliance path (Option A/B/C)      | §18 SOV-1          |
| ADR-NEW-011 | [`adr_011_audit_log_entity.md`](adr_011_audit_log_entity.md)                       | Audit log entity và compliance                  | DTC-2, BR-4        |
| ADR-NEW-012 | [`adr_012_usage_limits_enforcement.md`](adr_012_usage_limits_enforcement.md)       | LLM cost cap và UsageLimits enforcement         | DTC-1              |
| ADR-NEW-019 | [`adr_019_mcp_secure_executor.md`](adr_019_mcp_secure_executor.md)                 | MCP secure executor và tool authorization       | §19.2              |
| ADR-NEW-020 | [`adr_020_document_acl_inheritance.md`](adr_020_document_acl_inheritance.md)       | Document ACL inheritance trong vector DB        | §19.3              |
| ADR-NEW-030 | [`adr_030_offsite_backup_replication.md`](adr_030_offsite_backup_replication.md)   | Off-site backup replication và 3-2-1 compliance | §21.1              |
| ADR-NEW-037 | [`adr_037_aihub_supported_use_cases.md`](adr_037_aihub_supported_use_cases.md)     | Authoritative supported AI use cases            | §1 Strengths, §3.2 |

## ADRs chưa viết detailed (30 còn lại)

Liệt kê trong [Details §24](../02_architecture_review_details.md#24-proposed-adrs-36-total). Khi nào team commit
implement, viết detailed ADR theo template trong
[`../../decisions/0000_00_00_template.md`](../../decisions/0000_00_00_template.md).

| #           | Title                                             | Drives           | Priority |
| ----------- | ------------------------------------------------- | ---------------- | :------: |
| ADR-NEW-001 | SDK Versioning và Deprecation Policy              | G2.1, G2.4       |    P1    |
| ADR-NEW-002 | Tenant Data Isolation Strategy                    | G1.1             |    P0    |
| ADR-NEW-003 | Database Migration Framework                      | G4.1             |    P0    |
| ADR-NEW-004 | Customer Extension Configuration Schema           | G1.2, G2.7, G3.6 |    P1    |
| ADR-NEW-005 | Secrets Management và Rotation                    | G3.7             |    P1    |
| ADR-NEW-006 | SDK Public API Contract (import discipline)       | G2.6             |    P2    |
| ADR-NEW-007 | Operations Guide và On-Call Playbook              | G5.1, G5.2       |    P1    |
| ADR-NEW-008 | Tenant Provisioning Automation                    | G1.3             |    P1    |
| ADR-NEW-009 | SDK Downstream Integration Testing                | G2.5, G8.2       |    P1    |
| ADR-NEW-010 | SLI/SLO Definition for Production                 | G6.3, G7.2       |    P1    |
| ADR-NEW-013 | Process Package Fate                              | DTC-8            |    P0    |
| ADR-NEW-014 | Pipeline Executor Strategy (Multiprocess)         | DTC-6            |    P0    |
| ADR-NEW-015 | Milvus Cluster Mode và Index Selection            | DTC-7            |    P0    |
| ADR-NEW-016 | Customer LiteLLM Config Compliance Gate           | SOV-1            |    P0    |
| ADR-NEW-017 | Update 2026_02_24 ADR with Reality Reconciliation | SOV-1            |    P0    |
| ADR-NEW-018 | Per-language Presidio Routing                     | §19.1            |    P1    |
| ADR-NEW-021 | Source-System Authentication Strategy             | §19.4            |    P0    |
| ADR-NEW-022 | AITL Recursion Depth Limit                        | §20.1.1          |    P0    |
| ADR-NEW-023 | Pre-flight Cost Estimation và Hard Cap            | §20.1.2          |    P1    |
| ADR-NEW-024 | Citation Verification Guard                       | §20.1.3          |    P1    |
| ADR-NEW-025 | Document Upload Pipeline Validation               | §20.1.5, §20.2.4 |    P1    |
| ADR-NEW-026 | User và Tenant Deletion API (GDPR Art. 17)        | §20.2.1          |    P0    |
| ADR-NEW-027 | MongoDB Collection TTL Strategy                   | §20.2.2          |    P1    |
| ADR-NEW-028 | Embedding Model Versioning và Migration           | §20.2.5          |    P1    |
| ADR-NEW-029 | Container Supply Chain Security                   | §20.3            |    P2    |
| ADR-NEW-031 | Configurable Backup Target Endpoint               | §21.1            |    P0    |
| ADR-NEW-032 | Prometheus và AlertManager và On-call Routing     | §21.2            |    P0    |
| ADR-NEW-033 | SLI/SLO Definitions và Business Metrics           | §21.2            |    P1    |
| ADR-NEW-034 | Circuit Breaker for External Dependencies         | §21.3            |    P1    |
| ADR-NEW-035 | Per-tenant Bulkhead Isolation                     | §21.3            |    P1    |
| ADR-NEW-036 | Graceful Degradation for RAG/LLM Failures         | §21.3            |    P1    |

## Workflow accept ADR

1. Stakeholder review draft ADR.
2. Discussion trong team meeting hoặc PR review.
3. Update ADR với feedback nếu cần.
4. Sau acceptance, move ADR vào [`../../decisions/`](../../decisions/) với prefix date thực tế (vd
   `2026_06_01_audit_log_entity.md`).
5. Update Details §24 đổi status từ "Proposed" sang "Accepted [link]".
6. Update Roadmap (Details §23) nếu cần điều chỉnh timeline.

## Template

Mỗi ADR follow template: Context → Decision Drivers → Decision → Consequences. Xem
[`../../decisions/0000_00_00_template.md`](../../decisions/0000_00_00_template.md).
