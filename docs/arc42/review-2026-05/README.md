# Architecture Review 2026-05

Tài liệu architecture review cho Swiss AI Hub Platform (`aihub-core`) và các customer deployments (`aihub-bmd`,
`aihub-ctc`).

**Phiên bản assessment**: 3.5 trên 2026-05-25.

## Cấu trúc folder

```
docs/arc42/review-2026-05/
├── README.md                                 ← bạn đang ở đây (index)
├── 01_architecture_review_overview.vi.md     ← Executive Summary (tiếng Việt)
├── 01_architecture_review_overview.en.md     ← Executive Summary (English)
├── 02_architecture_review_details.md         ← Technical deep-dive cho dev team
├── 03_c4_diagrams.md                         ← C4 Model diagrams
└── 05_proposed_adrs/                         ← Detailed ADRs (6 P0 critical done, 30 planned)
```

**Locale variants**: Overview có 2 phiên bản song hành — `.vi.md` (tiếng Việt) và `.en.md` (English). Cùng content, cùng
phiên bản, sync khi update. Details và C4 diagrams hiện chỉ có 1 phiên bản (mixed Vietnamese-English).

## Đọc theo đối tượng

### C-level, Product, Business

Chỉ đọc Overview. Khoảng 30 phút.

- [`01_architecture_review_overview.vi.md`](01_architecture_review_overview.vi.md)

Trọng tâm:

- §1 Tóm tắt một trang: verdict + 3 blockers + bottom-line recommendations.
- §6 Top 10 Critical Findings: executive-level findings với block scenarios.
- §7 Go/No-Go Decision Flow: decision tree cho khách hàng mới.

### Compliance, Legal, Audit

Đọc Overview + Details sections về compliance.

- [`01_architecture_review_overview.vi.md`](01_architecture_review_overview.vi.md) toàn bộ.
- [`02_architecture_review_details.md`](02_architecture_review_details.md) §17 STRIDE Threat Model, §18 Data Sovereignty
  Violation, §19 Security Layer Critical Gaps, §20.2 Data Lifecycle và GDPR Reality.

Trọng tâm: sovereignty violation (Azure OpenAI/Foundry), GDPR right-to-erasure unimplementable, audit log entity không
tồn tại (docs false claim).

### Architects, Technical Leads

Đọc cả 3 documents chính.

- [`01_architecture_review_overview.vi.md`](01_architecture_review_overview.vi.md): toàn bộ.
- [`02_architecture_review_details.md`](02_architecture_review_details.md): toàn bộ §2-§25.
- [`03_c4_diagrams.md`](03_c4_diagrams.md): toàn bộ.

Trọng tâm: §22 WAF detailed status, §23 Roadmap đề xuất, §24 Proposed 36 ADRs.

### Dev team

- [`02_architecture_review_details.md`](02_architecture_review_details.md): code skeletons giải pháp trong §15.3, §19,
  §21.
- [`03_c4_diagrams.md`](03_c4_diagrams.md): component diagrams.

### Security engineer

Trọng tâm Details:

- §17 STRIDE Threat Model.
- §18 Data Sovereignty Violation.
- §19 Security Layer Critical Gaps (Presidio multilingual, MCP PII bypass, Document ACL inheritance, Service account
  auth).
- §20.1 AI Safety (7 sub-concerns).
- §20.2 Data Lifecycle và GDPR Reality.
- §21 Backup DR + Alerting + Resilience.

### SRE / DevOps

Trọng tâm Details:

- §7 Reliability and Data Integrity.
- §8 Operational Excellence.
- §9 Performance and Scalability.
- §10 Observability.
- §21 Backup DR + Alerting + Resilience.
- §22.7 CNCF Cloud-Native Maturity Model.

### Customer team owners (bmd, ctc, customer mới)

Đọc Overview §11 Documentation Backlog:

- §11.1 Platform docs.
- §11.2 Customer aihub-bmd: arc42 12 chapters, C4 L1/L2, 10 ADRs cần trả lời.
- §11.3 Customer aihub-ctc: arc42 12 chapters, C4 L1/L2, 13 ADRs cần trả lời, 10 câu hỏi technical.

## Sync giữa 2 documents

Overview và Details được giữ sync qua:

- **Bảng "Mapping Overview ↔ Details"** ở đầu Details doc.
- **Blockquote `> Chi tiết kỹ thuật:`** sau mỗi section header trong Overview, link sâu đến Details.
- **Footer cross-references** ở cả 2 files.
- **Version đồng bộ**: cả 2 cùng bump version khi có thay đổi (hiện tại v3.5).

## Phương pháp đánh giá

Khung tiêu chuẩn áp dụng:

- AWS Well-Architected Framework (6 pillars: OpEx, Security, Reliability, Performance, Cost, Sustainability).
- 8 trụ cột kiến trúc nội bộ (Multi-tenancy, SDK, Security, Reliability, OpEx, Performance, Observability, QA).
- STRIDE threat modeling.
- OWASP LLM Top 10.
- CNCF Cloud-Native Maturity Model.
- 3-2-1 Backup Rule.
- GDPR + Swiss revDSG compliance check.

Chi tiết phương pháp trong
[Details §2](02_architecture_review_details.md#2-ph%C6%B0%C6%A1ng-ph%C3%A1p-%C4%91%C3%A1nh-gi%C3%A1-checklist).

## Phạm vi và extensibility

Hiện tại assessment cover:

- 1 platform: `aihub-core` v0.289.10.
- 2 customers: `aihub-bmd` v0.279.2, `aihub-ctc` v0.274.3.

Document được thiết kế **extensible cho customer projects bổ sung** ở các phiên bản kế tiếp:

- Customer Registry table (Overview §2) có placeholder rows cho Customer #3, #4.
- Customer Pattern Matrix (Overview §3) có cột `?` sẵn cho customers mới.
- Finding mindmap (Overview §9) phân loại theo Platform-level / Customer-level / Cross-cutting, dễ classify finding mới.
- Risk Heatmap quadrant chart (Overview §4) có thể thêm risks customer-specific.

Khi onboard customer mới (vd Customer #3):

1. Thêm row vào Customer Registry (Overview §2).
2. Fill cột vào Customer Pattern Matrix (Overview §3).
3. Plot customer-specific risks lên Risk Heatmap (Overview §4).
4. Yêu cầu customer team cung cấp docs theo template (Overview §11.2 hoặc §11.3 làm reference).

## Trạng thái deliverables

| Phase | Deliverable                                       |                                                     Status                                                      |
| ----- | ------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------: |
| 1     | Deep exploration 3 projects (parallel agents)     |                                                      Done                                                       |
| 2     | Production-Readiness Assessment (Vietnamese)      |                                            Done (merged vào Details)                                            |
| 2b    | Deep technical concerns analysis                  |                                            Done (merged vào Details)                                            |
| 2c    | Security deep concerns (Presidio, MCP, RAG, auth) |                                               Done (Details §19)                                                |
| 2d    | Brainstorm additional concerns                    |                                               Done (Details §20)                                                |
| 2e    | Backup DR, Alerting, Resilience                   |                                               Done (Details §21)                                                |
| 3     | C4 Model diagrams (Context/Container/Component)   |                                 Done ([`03_c4_diagrams.md`](03_c4_diagrams.md))                                 |
| 4     | arc42 multi-customer view                         | Replaced by Overview §11 Documentation Backlog (customer-specific arc42 docs là deliverable của customer teams) |
| 5     | 36 Proposed ADRs (detailed)                       |       Planned (titles trong Details §24, detailed ADRs sẽ trong [`05_proposed_adrs/`](05_proposed_adrs/))       |
| 6     | Executive Summary + Index page                    |                            Done (Overview là Executive Summary, README này là Index)                            |

## Changelog versions

- **v3.5** (current): Overview header cleanup, thêm §11 Documentation Backlog với 3 subsections (platform, bmd, ctc
  deliverables).
- **v3.4**: Self-hosted local LLM recommendation (thay Swiss LLM Cloud), bỏ Roadmap khỏi Overview, pillar-based
  evaluation thành Section 5.
- **v3.3**: Split single doc thành Overview + Details + C4 với cross-references.
- **v3.2**: Executive Summary section với diagrams (ecosystem, risk heatmap, decision flow, mindmap, roadmap Gantt).
- **v3.1**: TOC, methodology checklist, customer docs gap, WAF detailed status.
- **v3.0**: Consolidated single doc, no unicode icons, no em dash, no effort column.
- **v2.4**: Backup DR + Alerting + Resilience addendum.
- **v2.3**: Brainstormed concerns (AI safety, GDPR, container, supply chain).
- **v2.2**: Security layer 4 concerns (Presidio, MCP, ACL, service auth).
- **v2.1**: Data sovereignty violation findings.
- **v2.0**: Initial consolidated production-readiness assessment.

## Tài liệu liên quan ngoài folder

- [`docs/arc42/chapters/`](../chapters/): Existing arc42 chapters cho platform (12 chapters, 1794 lines, EN).
- [`docs/arc42/decisions/`](../decisions/): 45 existing ADRs.
- [Sovereignty ADR 2026_02_24](../decisions/2026_02_24_swiss_sovereign_dual_mode_inference.md): ADR mà bmd và ctc đang
  vi phạm.
- [Existing risks doc](../chapters/11_risks_and_technical_debt.md): Risks platform team đã track.
- [Tenant ADRs](../decisions/2026_03_30_tenant_path_parameter.md),
  [Keycloak tenant assignment](../decisions/2026_02_20_keycloak_tenant_assignment_via_groups.md),
  [Active tenant](../decisions/2026_04_07_active_tenant_as_keycloak_user_attribute.md).

## Cách contribute

Khi cập nhật assessment:

1. Sửa cả 2 files (Overview và Details) cho consistent.
2. Update Mapping table trong Details nếu thay đổi structure.
3. Update blockquote cross-references trong Overview nếu thay đổi section numbering trong Details.
4. Bump version trong cả 2 footer.
5. Add entry vào Changelog.
6. Update README này nếu thêm/bỏ file.
