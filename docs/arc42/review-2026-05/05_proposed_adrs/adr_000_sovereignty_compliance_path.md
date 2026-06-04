# Sovereignty Compliance Path

**Status**: Proposed (needs a stakeholder decision this week) **Severity**: P0+ (values violation, legal risk, marketing
block) **Drives**: SOV-1 in
[Details §18 Data Sovereignty Violation](../02_architecture_review_details.md#18-data-sovereignty-violation-critical)

## Context

Swiss AI Hub declares Swiss data sovereignty as a core value via ADR `2026_02_24_swiss_sovereign_dual_mode_inference.md`
(Feb 2026):

> "Swiss data sovereignty: All cloud inference must stay within Swiss infrastructure."
>
> "Azure OpenAI is a US-based service. For a Swiss-first platform, routing inference data through US infrastructure
> contradicts the core data sovereignty promise."

Decision: "Swiss LLM Cloud replaces Azure OpenAI and Cohere as the sole cloud provider."

However, review 2026-05 found that all 5 current production customer deployments violate or deviate from this ADR:

**aihub-bmd** (`configs/litellm/litellm-config.yml`):

- 100% Azure OpenAI for LLM, embedding, image gen, transcription, TTS
- Endpoint `aihub-aifoundry-swe.openai.azure.com` (Azure Sweden region)
- Cohere reranking (US/Canada vendor)
- Sovereign rate: 1/9 services (only MinerU OCR routed through Swiss LLM Cloud)

**aihub-ctc** (`configs/litellm/litellm-config.latest.yml`):

- 100% Azure AI Foundry with 13 model bindings
- Endpoints `ctcaihub-foundry-sui.cognitiveservices.azure.com` (Switzerland region) and
  `ctcaihub-foundry-swe.cognitiveservices.azure.com` (Sweden region)
- Azure Document Intelligence for OCR instead of MinerU
- Azure VM + Azure Key Vault + Azure AD B2C
- Cohere reranking
- Sovereign rate: 0/13 services

Especially dangerous: ctc has an alias `text-generation/gpt-oss-120b` (a name suggesting open-source sovereign) pointing
to `azure/gpt-5-nano` (proprietary Azure). Application code and audit logs see the sovereign name, but the data actually
goes through Microsoft.

**aihub-demoscope** (`configs/litellm/...`):

- Mixed sovereignty: Azure OpenAI Switzerland (`demoscopeaihub-oai-sui.openai.azure.com`) + local vLLM (Gemma-3 12b/27b,
  gte-Qwen2 embedding, bge-reranker)
- Sovereign rate: partial — the only customer with on-prem inference for some workloads
- The Azure vs vLLM workload split is not documented

**aihub-wpe** (`configs/litellm/config.latest.yaml`):

- 100% Azure OpenAI; region not in the repo (only the env var `AZURE_OPENAI_BASE_URL` in `.env.prod` —
  sensitive-file-guarded). Sovereignty status cannot be verified from git
- Azure AD / Entra identity
- TLS private key `wpe.ai-agents.ch+1-key.pem` committed to git (see proposed `adr_041`)

**aihub-fmh** (`infra/...` + Pulumi `iac_azure/`):

- Azure OpenAI Switzerland North (`*-openai-sui`) — defensible for the Swiss-only TARDOC/TARMED data
- Uses **Azure AI Search** instead of Milvus (double inference cost; vendor lock-in; see proposed `adr_039`)
- LlamaIndex monkey-patch to register GPT-5 model names (`lib/common/register_openai_models.py`)
- Azure AD identity; Pulumi state in an Azure storage account (SPOF)

Implications:

- The "Swiss Sovereign AI" marketing claim currently cannot be defended in an audit.
- US Cloud Act applies: Microsoft and Cohere are US entities and can be compelled by the US gov to disclose EU data.
- Schrems II ruling: EU companies using US cloud need additional safeguards.
- Swiss revDSG and GDPR Art. 44 transfer requirements are not met.
- FINMA banking and HIPAA healthcare customers are fully blocked.

## Decision Drivers

- **Compliance**: Defensible in GDPR, Swiss revDSG, US Cloud Act, Schrems II, and FINMA audits.
- **Reputation**: Avoid media exposure of "Swiss AI actually on Azure US".
- **Customer trust**: Existing customers chose the platform for its sovereignty promise.
- **Marketing integrity**: Match the claim with reality.
- **Pragmatism**: Azure GPT-5 model quality is currently higher than Swiss LLM Cloud (Gemma-4-31B-it).
- **Cost**: Self-hosted hardware upfront cost vs cloud opex.
- **Vendor lock-in**: ctc is locked into Azure across 5 layers; migration cost is high.
- **Time-to-fix**: Customers are already in production; long downtime is not acceptable.

## Decision

Stakeholders must choose 1 of 3 options this week. Why urgent: the marketing claim is currently false, the audit risk is
real, and customer #3 will copy the pattern again if there is no clear policy.

### Option A: Self-hosted local LLM (full sovereignty, recommended)

Deploy a local LLM stack on self-managed hardware, with zero cloud LLM dependency.

**Stack**:

- **vLLM** for high-throughput production serving (continuous batching, paged attention).
- **Ollama** or **llama.cpp** for development and test environments.
- **Open-weight models**: Llama 3.1/3.3 (8B/70B), Qwen 2.5 (7B/14B/72B), Mistral Small/Large, Mixtral 8x7B/8x22B, Gemma
  2 (9B/27B). Can be fine-tuned.
- **Embeddings**: BGE-M3 (multilingual, 1024-dim) or bge-multilingual-gemma2.
- **Reranking**: BGE-Reranker-v2-m3 instead of Cohere.
- **OCR**: MinerU (standardized via ADR 2026_02_09) instead of Azure Document Intelligence.

**Hardware**:

- At minimum 1× NVIDIA A100 80GB or H100 for 7B-13B model serving in production.
- For a 70B model: 2× A100 80GB or equivalent.
- Location: bare-metal in the customer's data center, or Hetzner CH/EU, Exoscale CH.

**Migration plan**:

- bmd: 1-2 sprints to migrate the LiteLLM config to local endpoints.
- ctc: 2-3 sprints, including migrating the Azure VM to bare-metal, replacing Azure Document Intelligence with MinerU,
  and removing Azure AD B2C.

**Pros**: True data sovereignty, zero vendor lock-in, predictable cost (CapEx hardware, no per-token OpEx), no Cloud Act
exposure, fully defensible in audit.

**Cons**: Hardware procurement upfront cost (1× A100 80GB ~\$15-20K), model quality may be lower than GPT-5 for some
complex tasks, higher ops complexity (vs managed cloud).

### Option B: Update ADR, accept hybrid (pragmatic)

Update ADR 2026_02_24 to "Sovereign-preferred, hybrid-allowed". Document explicit tiers.

**Changes**:

- ADR text rewrite: "Tier-1 Sovereign self-hosted preferred. Tier-2 Hybrid cloud allowed with customer explicit
  consent."
- Explicit customer agreement on data flow (which LLM calls go through Azure).
- Marketing rebranded: "Swiss-hosted infrastructure with optional hybrid LLM (US cloud)".
- Customer data classification: sensitive data always via the sovereign tier, non-sensitive data may use hybrid.

**Pros**: Quick fix (1-2 weeks), keeps model quality, minimum disruption for bmd/ctc.

**Cons**: Marketing sovereignty claim weakened, still has US Cloud Act exposure for Tier-2 data, not suitable for
enterprise customers in regulated industries.

### Option C: Per-customer sovereignty tier (best for enterprise mix)

The core platform supports both modes. The customer chooses a tier at deployment time.

**Implementation**:

- Feature flag `sovereignty_mode = "sovereign-only" | "hybrid"` in the customer config.
- Sovereign-only mode: only allow local LLM endpoints in the LiteLLM config (CI gate enforces this).
- Hybrid mode: allow Azure OpenAI/Foundry but emit a warning log and an audit entry.
- bmd and ctc keep hybrid (Azure) with clear documentation.
- New customers default to sovereign-only.
- Marketing: "Choose your sovereignty level".

**Pros**: Flexible per use-case, high-sensitivity customers get proper isolation, gradual migration path.

**Cons**: 2 code paths in LiteLLM config validation and deployment scripts, marketing complexity, increased testing
surface.

### Decision matrix

| Aspect                                    | Option A (self-hosted) | Option B (hybrid OK) | Option C (per-customer) |
| ----------------------------------------- | :--------------------: | :------------------: | :---------------------: |
| Marketing "Swiss Sovereign AI" defensible |       Yes (full)       |    No (downgrade)    |      Per-customer       |
| Effort for the team                       |     L (1-3 months)     |    S (1-2 weeks)     |       M (1 month)       |
| Cost upfront                              |    High (hardware)     |         Low          |         Medium          |
| Model quality                             |  Lower (open-weight)   |    Higher (GPT-5)    |          Mixed          |
| Compliance enterprise (FINMA, HIPAA)      |          Yes           |          No          |  Yes (sovereign tier)   |
| Customer trust                            |          High          |        Medium        |   High (transparent)    |
| Time to migrate bmd/ctc                   |       1-3 months       | 1-2 weeks (doc only) |         Gradual         |

**Recommended**: Option A if sovereignty is a non-negotiable core value, Option C if flexibility is needed for an
enterprise mix, Option B only acceptable if marketing is rebranded in sync.

## Consequences

### Positive (Option A)

- Fully defensible in GDPR, revDSG, FINMA, HIPAA, US Cloud Act, Schrems II audits.
- Marketing claim matches reality.
- High customer trust.
- Predictable cost (CapEx hardware, no per-token spikes).
- Zero vendor lock-in for the LLM layer.

### Negative (Option A)

- Hardware procurement upfront cost (\$15-20K per A100 80GB).
- Model quality may be lower for complex reasoning tasks.
- Higher ops complexity (model serving, GPU monitoring).
- Migration time for bmd/ctc: 1-3 months of downtime or dual-running.
- Customers need training for the new operational model.

### Positive (Option B)

- Quick implementation (1-2 weeks).
- Minimum disruption.
- Keeps high model quality.

### Negative (Option B)

- Marketing claim must be downgraded.
- Existing customer trust at risk if they chose the platform for sovereignty.
- Still has US Cloud Act exposure.
- Blocks enterprise regulated industries.

### Positive (Option C)

- Flexibility for a customer mix.
- Gradual migration path.
- Transparent customer agreement.

### Negative (Option C)

- 2 code paths increase maintenance.
- Testing complexity increases.
- Marketing message is more complex.

## Implementation notes

After the decision:

1. Update ADR `2026_02_24` with reality reconciliation (ADR-NEW-017).
2. Customer LiteLLM config CI gate (ADR-NEW-016).
3. Customer notification about the data-flow change (legal language).
4. Update marketing materials, website, customer-facing docs.
5. Customer ADRs (bmd, ctc, demoscope, wpe, fmh) document the migration decision (see Overview §3.2-§3.6 and the
   per-customer C4 in `c4/`).

## References

- ADR `2026_02_24_swiss_sovereign_dual_mode_inference.md`: Original sovereignty decision (currently being violated).
- [Details §18 Data Sovereignty Violation](../02_architecture_review_details.md#18-data-sovereignty-violation-critical):
  Full evidence and analysis.
- [Overview §1 Summary](../01_architecture_review_overview.en.md#1-summary): Executive context.
- [Overview Recommendations](../01_architecture_review_overview.en.md#6-recommendations): Sovereignty decision as the
  first immediate item.
