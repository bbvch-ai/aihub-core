# Architecture Review 2026-05

Architecture review documentation for the Swiss AI Hub Platform (`aihub-core`) and the customer deployments
(`aihub-bmd`, `aihub-ctc`).

**Assessment version**: 3.6 on 2026-05-28 (refresh: v0.290.4 + 47 ADRs + 5 customer coverage + per-customer C4

- PO presentation deck).

## Folder structure

```
docs/arc42/review-2026-05/
├── README.md                                 ← you are here (index)
├── 01_architecture_review_overview.en.md     ← Executive Summary (English)
├── 02_architecture_review_details.md         ← Technical deep-dive for the dev team
├── 03_c4_diagrams.md                         ← C4 Model diagrams (Platform + bmd + ctc, cross-customer view)
├── 04_po_presentation_deck.md                ← PO/Leadership slide deck (Marp markdown, 1-1.5h session)
├── 05_proposed_adrs/                         ← Detailed ADRs (11 detailed, 29 listed — 40 total)
└── c4/                                       ← Per-customer C4 diagrams (Platform / bmd / ctc / demoscope / wpe / fmh)
```

**Locale variants**: the Overview has 2 parallel versions — `.vi.md` (Vietnamese) and `.en.md` (English). Same content,
same version, kept in sync on update. Details and C4 diagrams currently have only 1 version (English).

## Reading by audience

### C-level, Product, Business

Two options depending on available time:

**Option 1 — Slide deck for a 1-1.5h session** (recommended for a leadership briefing):

- [`04_po_presentation_deck.md`](04_po_presentation_deck.md) — Marp markdown, ~40 slides, 8 sections (TL;DR → Project
  snapshot → CRITICAL risks → Per-customer status → Strategic items → Decisions needed → Roadmap & resources → Recap).
  Export to PDF/PPTX via Marp CLI or VS Code Marp extension.

**Option 2 — Self-read Overview, ~30-45 min**:

- [`01_architecture_review_overview.vi.md`](01_architecture_review_overview.vi.md) (Vietnamese) or
  [`01_architecture_review_overview.en.md`](01_architecture_review_overview.en.md) (English)

Focus on:

- §1 Summary: strengths/weaknesses 1-page overview.
- §3 Priority items for go-live (CRITICAL + HIGH per scope).
- §6 Recommendations: Immediate / Strategic / Documentation / Process.

### Compliance, Legal, Audit

Read the Overview + the Details compliance sections.

- [`01_architecture_review_overview.en.md`](01_architecture_review_overview.en.md) in full.
- [`02_architecture_review_details.md`](02_architecture_review_details.md) §17 STRIDE Threat Model, §18 Data Sovereignty
  Violation, §19 Security Layer Critical Gaps, §20.2 Data Lifecycle and GDPR Reality.

Focus on: sovereignty violation (Azure OpenAI/Foundry), GDPR right-to-erasure unimplementable, audit log entity does not
exist (docs false claim).

### Architects, Technical Leads

Read all 3 main documents.

- [`01_architecture_review_overview.en.md`](01_architecture_review_overview.en.md): in full.
- [`02_architecture_review_details.md`](02_architecture_review_details.md): all of §2-§25.
- [`03_c4_diagrams.md`](03_c4_diagrams.md): in full.

Focus on: §22 WAF detailed status, §23 Proposed Roadmap, §24 Proposed 36 ADRs.

### Dev team

- [`02_architecture_review_details.md`](02_architecture_review_details.md): solution code skeletons in §15.3, §19, §21.
- [`03_c4_diagrams.md`](03_c4_diagrams.md): component diagrams.

### Security engineer

Focus in Details:

- §17 STRIDE Threat Model.
- §18 Data Sovereignty Violation.
- §19 Security Layer Critical Gaps (Presidio multilingual, MCP PII bypass, Document ACL inheritance, Service account
  auth).
- §20.1 AI Safety (7 sub-concerns).
- §20.2 Data Lifecycle and GDPR Reality.
- §21 Backup DR + Alerting + Resilience.

### SRE / DevOps

Focus in Details:

- §7 Reliability and Data Integrity.
- §8 Operational Excellence.
- §9 Performance and Scalability.
- §10 Observability.
- §21 Backup DR + Alerting + Resilience.
- §22.7 CNCF Cloud-Native Maturity Model.

### Customer team owners (bmd, ctc, new customer)

Read Overview §11 Documentation Backlog:

- §11.1 Platform docs.
- §11.2 Customer aihub-bmd: arc42 12 chapters, C4 L1/L2, 10 ADRs to answer.
- §11.3 Customer aihub-ctc: arc42 12 chapters, C4 L1/L2, 13 ADRs to answer, 10 technical questions.

## Sync between the 2 documents

The Overview and Details are kept in sync via:

- **The "Mapping Overview ↔ Details" table** at the top of the Details doc.
- **A blockquote `> Technical detail:`** after each section header in the Overview, deep-linking to Details.
- **Footer cross-references** in both files.
- **Synchronized version**: both bump their version on any change (currently v3.5).

## Assessment method

Standard frameworks applied:

- AWS Well-Architected Framework (6 pillars: OpEx, Security, Reliability, Performance, Cost, Sustainability).
- 8 internal architecture pillars (Multi-tenancy, SDK, Security, Reliability, OpEx, Performance, Observability, QA).
- STRIDE threat modeling.
- OWASP LLM Top 10.
- CNCF Cloud-Native Maturity Model.
- 3-2-1 Backup Rule.
- GDPR + Swiss revDSG compliance check.

Method detail in
[Details §2](02_architecture_review_details.md#2-ph%C6%B0%C6%A1ng-ph%C3%A1p-%C4%91%C3%A1nh-gi%C3%A1-checklist).

## Scope and extensibility

The assessment currently covers:

- 1 platform: `aihub-core` v0.290.4 (47 ADRs).
- 5 production customers: `aihub-bmd` v0.279.2, `aihub-ctc` v0.274.3, `aihub-demoscope` v0.246.4\*, `aihub-wpe`
  v0.255.6, `aihub-fmh` v0.186.0.
- 3 infrastructure repos (Gen 2): `aihub-playbook`, `aihub-ops`, `aihub-{customer_id}` (template).
- 1 Kubernetes deployment (Gen 3, emerging): `aihub-k8s` — `appVersion: "0.1.0"`, images via `${CORE_VERSION}`.

(\*Demoscope SDK pin not in repo `pyproject.toml`; see footnote in Overview Component-versions table.)

The document is designed to be **extensible for additional customer projects** in future versions:

- The Customer Registry table (Overview §2) has placeholder rows for Customer #3, #4.
- The Customer Pattern Matrix (Overview §3) has a `?` column ready for new customers.
- The finding mindmap (Overview §9) classifies by Platform-level / Customer-level / Cross-cutting, making new findings
  easy to classify.
- The Risk Heatmap quadrant chart (Overview §4) can add customer-specific risks.

When onboarding a new customer (e.g. Customer #3):

1. Add a row to the Customer Registry (Overview §2).
2. Fill the columns in the Customer Pattern Matrix (Overview §3).
3. Plot customer-specific risks on the Risk Heatmap (Overview §4).
4. Ask the customer team to provide docs from the template (use Overview §11.2 or §11.3 as a reference).

## Deliverables status

| Phase | Deliverable                                                         |                                                      Status                                                       |
| ----- | ------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------: |
| 1     | Deep exploration 3 projects (parallel agents)                       |                                                       Done                                                        |
| 2     | Production-Readiness Assessment (Vietnamese)                        |                                            Done (merged into Details)                                             |
| 2b    | Deep technical concerns analysis                                    |                                            Done (merged into Details)                                             |
| 2c    | Security deep concerns (Presidio, MCP, RAG, auth)                   |                                                Done (Details §19)                                                 |
| 2d    | Brainstorm additional concerns                                      |                                                Done (Details §20)                                                 |
| 2e    | Backup DR, Alerting, Resilience                                     |                                                Done (Details §21)                                                 |
| 3     | C4 Model diagrams (Context/Container/Component)                     |                                  Done ([`03_c4_diagrams.md`](03_c4_diagrams.md))                                  |
| 4     | arc42 multi-customer view                                           | Replaced by Overview §11 Documentation Backlog (customer-specific arc42 docs are a deliverable of customer teams) |
| 5     | 36 Proposed ADRs (detailed)                                         |        Planned (titles in Details §24, detailed ADRs to live in [`05_proposed_adrs/`](05_proposed_adrs/))         |
| 6     | Executive Summary + Index page                                      |                        Done (Overview is the Executive Summary, this README is the Index)                         |
| 7     | Refresh 2026-05 customer update (5 ADRs, Level 0 diagrams, phasing) |                      Done (PO §7 + [`c4/`](c4/) + [`05_proposed_adrs/`](05_proposed_adrs/))                       |

## Changelog versions

- **v3.7** (current, 2026-05-29): Refresh from the customer update — added 5 new ADRs (042–046: pluggable
  parser/Docling, continuous component-update strategy, RAG/vector-design gate, C\*C tenant-schema migration, load-test
  baselines); added the "Level 0 — High-Level Solution Architecture" diagram for the 5 customers in [`c4/`](c4/); folded
  new findings into the Overview §3/§6 (EN+VI) and the phasing into [PO deck §7](04_po_presentation_deck.md) (Q3/Q4).
  The Details file was left unchanged (out of scope for this refresh).
- **v3.5**: Overview header cleanup, added §11 Documentation Backlog with 3 subsections (platform, bmd, ctc
  deliverables).
- **v3.4**: Self-hosted local LLM recommendation (replacing Swiss LLM Cloud), removed the Roadmap from the Overview,
  pillar-based evaluation became Section 5.
- **v3.3**: Split the single doc into Overview + Details + C4 with cross-references.
- **v3.2**: Executive Summary section with diagrams (ecosystem, risk heatmap, decision flow, mindmap, roadmap Gantt).
- **v3.1**: TOC, methodology checklist, customer docs gap, WAF detailed status.
- **v3.0**: Consolidated single doc, no unicode icons, no em dash, no effort column.
- **v2.4**: Backup DR + Alerting + Resilience addendum.
- **v2.3**: Brainstormed concerns (AI safety, GDPR, container, supply chain).
- **v2.2**: Security layer 4 concerns (Presidio, MCP, ACL, service auth).
- **v2.1**: Data sovereignty violation findings.
- **v2.0**: Initial consolidated production-readiness assessment.

## Related documents outside this folder

- [`docs/arc42/chapters/`](../chapters/): Existing arc42 chapters for the platform (12 chapters, 1794 lines, EN).
- [`docs/arc42/decisions/`](../decisions/): 45 existing ADRs.
- [Sovereignty ADR 2026_02_24](../decisions/2026_02_24_swiss_sovereign_dual_mode_inference.md): the ADR that bmd and ctc
  are violating.
- [Existing risks doc](../chapters/11_risks_and_technical_debt.md): Risks the platform team already tracks.
- [Tenant ADRs](../decisions/2026_03_30_tenant_path_parameter.md),
  [Keycloak tenant assignment](../decisions/2026_02_20_keycloak_tenant_assignment_via_groups.md),
  [Active tenant](../decisions/2026_04_07_active_tenant_as_keycloak_user_attribute.md).

## How to contribute

When updating the assessment:

1. Edit both files (Overview and Details) to keep them consistent.
2. Update the Mapping table in Details if the structure changes.
3. Update the blockquote cross-references in the Overview if section numbering in Details changes.
4. Bump the version in both footers.
5. Add an entry to the Changelog.
6. Update this README if you add/remove a file.
