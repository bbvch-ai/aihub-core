# ADR-NEW-037: Authoritative Supported AI Use Cases

**Status**: Proposed (2026-05-25) **Drives**: Architecture Review §1 Strengths claim defensibility, customer pre-sales
scoping, audit readiness

## Context

The architecture review document (§1 Tóm tắt and §3.2 Business core values vs reality) historically claimed that the
aihub agent framework covers "9 of 10 enterprise AI use cases". This claim is:

1. **Not traceable** to any canonical industry taxonomy (McKinsey / Gartner / BCG / Anthropic patterns).
2. **Not documented** in any ADR, scope statement, or positioning page.
3. **Not defensible** under customer audit or due-diligence questioning: "What are the 10? Which 1 is missing? How was
   coverage assessed?"
4. **Source of confusion** for new customers and pre-sales teams scoping deals: unclear what aihub does vs does NOT do
   out of the box.

The team needs an authoritative list of supported use cases to:

- Anchor positioning claims in documentation, marketing, and customer conversations.
- Set explicit out-of-scope boundaries so customers do not assume support that does not exist.
- Track coverage maturity (full / partial / out-of-scope) per use case.
- Update the list as roadmap evolves.

## Decision Drivers

1. **Audit defensibility** — claims in docs must trace to an explicit, reviewed list.
2. **Customer pre-sales clarity** — sales engineering must give a yes/no answer per use case quickly.
3. **Roadmap alignment** — engineering should know which use cases are first-class commitments vs experimental.
4. **Maintainability** — list must be reviewed every release cycle to track drift.
5. **Industry alignment** — list should reference well-known enterprise AI patterns where possible, not invent new
   taxonomy.

## Decision

Adopt the following **authoritative list of supported use cases** for aihub platform. Each use case has explicit
coverage status and links to evidence in the codebase.

### Coverage status legend

- ✅ **Full** — production-ready, documented, customer can rely on it.
- ⚠️ **Partial** — works but with caveats (missing test coverage, dead-code component, weak edge cases).
- ❌ **Out of scope** — explicitly NOT supported; customer must integrate external tools or build their own.

### Supported use cases

| #   | Use case                                      | Status     | Evidence in codebase                                                                                                          | Notes                                                                                                           |
| --- | --------------------------------------------- | ---------- | ----------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| 1   | **Conversational AI / chatbot interfaces**    | ✅ Full    | OpenWebUI integration (port 8080); chat history in FerretDB; streaming responses via NATS Display Events                      | Multi-channel: web UI, Teams, Slack via `packages/bot`                                                          |
| 2   | **Document Q&A (RAG) — single source**        | ✅ Full    | Milvus vector store; BGE-M3 embedding; BGE reranker; document chunks indexed via pipeline                                     | Standard RAG pattern                                                                                            |
| 3   | **Multi-source RAG**                          | ✅ Full    | CTC implementation: Jira + Confluence + SharePoint via 6 Dagster pipelines                                                    | Pattern is customer-specific, not yet extracted to core                                                         |
| 4   | **Document parsing / OCR**                    | ✅ Full    | MinerU service (port 5001); PDF, Word, structural extraction                                                                  | ADR `2026_02_09` standardizes MinerU                                                                            |
| 5   | **Tool calling / function calling (ReAct)**   | ✅ Full    | MCP (Model Context Protocol) integration                                                                                      | Security: MCP args bypass Presidio (concern, see `adr_019`)                                                     |
| 6   | **Human-in-the-loop (HITL) workflows**        | ✅ Full    | `AgentInTheLoopRequestEvent` pattern; `expert_asking` agent (BMD); Process UI for human tasks                                 | Core capability                                                                                                 |
| 7   | **Multi-agent orchestration**                 | ⚠️ Partial | CTC `retrieval_orchestrator` agent — custom built, not yet extracted to core                                                  | Should be lifted to core as first-class pattern                                                                 |
| 8   | **Voice STT/TTS**                             | ✅ Full    | Speaches service (port 8185); both speech-to-text and text-to-speech                                                          | Enterprise features (speaker diarization, custom vocabulary) not validated                                      |
| 9   | **Code execution sandbox**                    | ✅ Full    | Jupyter container (port 8888); used by agents for ad-hoc computation                                                          | Isolation guarantees not formally documented                                                                    |
| 10  | **Browser automation**                        | ✅ Full    | Playwright container (port 3036); agents can drive headless browsers for web scraping / UI automation                         | Security implications of sandboxed browser not documented                                                       |
| 11  | **Workflow / business process orchestration** | ⚠️ Partial | `packages/process` exists but is dead code (0 external imports); Dagster covers data pipeline orchestration only              | See ADR-NEW-013 (Process Package Fate)                                                                          |
| 12  | **Structured output / data extraction**       | ⚠️ Partial | Relies on LLM JSON mode; no native schema validation guarantees; weak models (e.g., gpt-oss-120b) often return malformed JSON | Concern documented in BMD AI output stability; mitigation: `instructor` / `outlines` libraries + fallback chain |

### Out-of-scope use cases (explicit)

| #   | Use case                                                 | Reason out of scope                                                                          | Customer alternative                                                                             |
| --- | -------------------------------------------------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| 13  | **Image understanding / multimodal vision**              | No vision model in stack; MinerU OCR covers document images only, not general image analysis | Customer integrates external vision model (Azure Computer Vision, GPT-4V) via custom MCP tool    |
| 14  | **Predictive analytics / time-series forecasting**       | No ML training pipeline; no forecasting framework; not within agent-platform scope           | Customer uses dedicated ML platform (Databricks, Vertex AI) and exposes results to agent via API |
| 15  | **Custom fine-tuned model serving**                      | No model serving framework for customer-trained models (only foundation models via LiteLLM)  | Customer hosts fine-tuned model behind OpenAI-compatible API; register in LiteLLM config         |
| 16  | **Real-time streaming voice agents** (sub-200ms latency) | Speaches STT/TTS is request-response, not duplex streaming; no Voice Activity Detection      | Customer integrates dedicated voice platform (Deepgram, ElevenLabs) for low-latency requirements |
| 17  | **Translation / localization at content level**          | No translation pipeline; UI i18n (DE/EN/FR/IT) is separate from runtime content translation  | Customer adds translation step via custom agent calling external translation API                 |
| 18  | **Classification / NER with custom-trained models**      | No fine-tuning infrastructure; no model serving for non-foundation models                    | Customer trains externally and exposes inference via API; agent calls it as a tool               |

### Maturity policy

- **Quarterly review** of this list by the architecture team.
- **Coverage change** (promote ⚠️ → ✅ or demote ✅ → ⚠️) requires this ADR to be updated with rationale.
- **Adding a new use case** (in or out of scope) requires PR review by the architecture team plus product owner.
- **Removing an out-of-scope item** (i.e., bringing it into scope) requires a separate implementation ADR.

## Consequences

### Positive

- **Marketing and pre-sales claims** anchored to an explicit list — no more vague "9 of 10" without provenance.
- **Customer scoping conversations** become deterministic: a customer can check the list and immediately know whether
  aihub covers their need.
- **Engineering roadmap** has a clearer prioritization signal: promoting ⚠️ to ✅ is concrete work; bringing ❌ in scope
  is a strategic decision requiring its own ADR.
- **Audit readiness** improves: this ADR is an authoritative source for compliance reviews.

### Negative

- **Maintenance overhead** — quarterly review is real work; without discipline this ADR will drift.
- **Loss of marketing flexibility** — sales cannot claim coverage of use case X if it is explicitly out of scope without
  triggering an ADR update.
- **Risk of premature scoping** — some use cases listed as out of scope may be in scope earlier than planned if a
  customer requests them, requiring an emergency ADR update.

### Neutral

- This ADR replaces the unanchored "9 of 10" claim in the architecture review document (§1 Strengths, §3.2 Business
  values vs reality) with explicit references to this list.
- Future architecture reviews should treat this ADR as the source of truth for the "supported use cases" question.

## Implementation Steps

1. **Update architecture review document** (`01_architecture_review_overview.{vi,en}.md`):
   - §1 Strengths: replace "9 of 10 enterprise AI use cases" claim with reference to this ADR.
   - §3.2 Business values vs reality: same replacement.
   - Add concern in §4.1 Core (if still open): "AI use case scope undefined" — close as resolved once this ADR is
     accepted.
2. **Update customer-facing marketing** to align with this list.
3. **Update pre-sales playbook / scoping doc** with this list as a checklist.
4. **Schedule quarterly review** in team calendar.
5. **Move ADR from Proposed to Accepted**: rename file in `docs/arc42/decisions/` with date prefix (e.g.,
   `2026_06_01_aihub_supported_use_cases.md`).

## References

- [Architecture Review Overview §1 Tóm tắt](../01_architecture_review_overview.vi.md#1-t%C3%B3m-t%E1%BA%AFt)
- [Architecture Review Overview §3.2 Business core values vs thực tế](../01_architecture_review_overview.vi.md#32-business-core-values-vs-th%E1%BB%B1c-t%E1%BA%BF)
- ADR `2026_02_09` — MinerU standardization
- ADR `adr_019_mcp_secure_executor.md` — MCP security
- ADR `adr_020_document_acl_inheritance.md` — RAG ACL
- ADR-NEW-013 — Process Package Fate (related to use case #11)
