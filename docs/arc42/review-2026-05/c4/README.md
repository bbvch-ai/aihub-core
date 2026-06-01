# Per-Customer C4 Diagrams

This folder contains C4 Level 1 (System Context) and Level 2 (Container) diagrams for each scope in the Swiss AI
Hub ecosystem. Created as part of architecture review refresh 2026-05-28.

## Files

| Scope                                | File                                | Status                 | Highlights                                                                                                |
| ------------------------------------ | ----------------------------------- | ---------------------- | --------------------------------------------------------------------------------------------------------- |
| aihub-core (Platform)                | [`platform.md`](platform.md)        | Extracted from §1, §2.1 of [`../03_c4_diagrams.md`](../03_c4_diagrams.md) | 30+ containers; reference architecture |
| aihub-bmd (v0.279.2)                 | [`bmd.md`](bmd.md)                  | Extracted from §2.2 of [`../03_c4_diagrams.md`](../03_c4_diagrams.md)     | SMB source; Azure Sweden + Cohere     |
| aihub-ctc (v0.274.3)                 | [`ctc.md`](ctc.md)                  | Extracted from §2.3 of [`../03_c4_diagrams.md`](../03_c4_diagrams.md)     | Jira/Confluence/SharePoint + custom API + Azure Foundry SUI+SWE |
| aihub-demoscope (v0.246.4*)          | [`demoscope.md`](demoscope.md)      | **NEW** in this review | Mixed Azure SUI + local vLLM; Mongo+Redis+Phoenix divergence                                              |
| aihub-wpe (v0.255.6)                 | [`wpe.md`](wpe.md)                  | **NEW** in this review | Deploy-only manual VM; TLS-key-in-git incident (see [`adr_041`](../05_proposed_adrs/adr_041_tls_key_committed_remediation.md)) |
| aihub-fmh (v0.186.0)                 | [`fmh.md`](fmh.md)                  | **NEW** in this review | Azure SUI + Azure AI Search (not Milvus); Pulumi committed; bot; evaluation framework                     |
| Deployment generations               | [`deployment_generations.md`](deployment_generations.md) | **NEW** 2026-05-29 refresh | Gen 1 (manual VM + docker-compose) · Gen 2 (Ansible Pull + OpenStack Infomaniak) · Gen 3 (K8s `aihub-k8s`) |

> *Demoscope SDK pin unverifiable from `pyproject.toml`; figure carried over from prior snapshot — see footnote in
> Overview Component-versions table.

## How to read these files

Each file follows the same structure:

1. **Level 0 — High-Level Solution Architecture.** Boundary-first `flowchart` (added in the 2026-05-29 refresh):
   custom code, core touchpoints, Azure services, LLM (local vs Foundry), observability, and backup in one
   colour-coded view. Less text, more wiring — the fastest way to read a customer.

1. **Level 1 — System Context.** Who uses the customer system and what external systems it integrates with.
   Mermaid `C4Context` block. Trust boundary annotation below the diagram.

2. **Level 2 — Container.** Deployable units inside the customer scope and their dependencies. Mermaid
   `C4Container` block. Container-vs-scaling-readiness table for the customer.

3. **Cross-reference.** Links back to:
   - The aggregated [`../03_c4_diagrams.md`](../03_c4_diagrams.md) for L3 components + dynamic sequences + deployment
     + cross-customer topology.
   - The customer-specific concerns in [`../01_architecture_review_overview.en.md`](../01_architecture_review_overview.en.md)
     §3.2-§3.6 and §5.2-§5.6.
   - Any proposed ADRs in [`../05_proposed_adrs/`](../05_proposed_adrs/) that target this customer.

The aggregated Multi-Customer Topology View (cross-customer aggregate) stays in [`../03_c4_diagrams.md`](../03_c4_diagrams.md)
to avoid duplication; each per-customer file links to it.

## C4 reference

- [Simon Brown — The C4 model for visualising software architecture](https://c4model.com/)
- [Mermaid C4 syntax](https://mermaid.js.org/syntax/c4.html) — rendered by VitePress, GitHub markdown preview, and
  VS Code's Markdown Preview Mermaid Support extension.

## Update policy

These files are part of the review snapshot. When the underlying code changes:

- Customer version pins → update the L1/L2 system box label.
- Customer adds/removes a service → update the Container diagram and the scaling-readiness table.
- New customer onboarded → add a new file here following the same pattern; update this README's table.

Snapshot date: **2026-05-28** (aihub-core v0.290.4, 47 ADRs, 5 production customers).
