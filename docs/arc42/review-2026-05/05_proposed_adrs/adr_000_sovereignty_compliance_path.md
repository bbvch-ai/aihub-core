# Sovereignty Compliance Path

**Status**: Proposed (cần stakeholder decision trong tuần) **Severity**: P0+ (values violation, legal risk, marketing
block) **Drives**: SOV-1 trong
[Details §18 Data Sovereignty Violation](../02_architecture_review_details.md#18-data-sovereignty-violation-critical)

## Context

Platform Swiss AI Hub declare Swiss data sovereignty là core value qua ADR
`2026_02_24_swiss_sovereign_dual_mode_inference.md` (Feb 2026):

> "Swiss data sovereignty: All cloud inference must stay within Swiss infrastructure."
>
> "Azure OpenAI is a US-based service. For a Swiss-first platform, routing inference data through US infrastructure
> contradicts the core data sovereignty promise."

Decision: "Swiss LLM Cloud replaces Azure OpenAI and Cohere as the sole cloud provider."

Tuy nhiên review 2026-05 phát hiện cả 2 customer deployments hiện tại đều vi phạm ADR này:

**aihub-bmd** (`configs/litellm/litellm-config.yml`):

- 100% Azure OpenAI cho LLM, embedding, image gen, transcription, TTS
- Endpoint `aihub-aifoundry-swe.openai.azure.com` (Azure Sweden region)
- Cohere reranking (US/Canada vendor)
- Sovereign rate: 1/9 services (chỉ MinerU OCR routed qua Swiss LLM Cloud)

**aihub-ctc** (`configs/litellm/litellm-config.latest.yml`):

- 100% Azure AI Foundry với 13 model bindings
- Endpoints `ctcaihub-foundry-sui.cognitiveservices.azure.com` (Switzerland region) và
  `ctcaihub-foundry-swe.cognitiveservices.azure.com` (Sweden region)
- Azure Document Intelligence cho OCR thay vì MinerU
- Azure VM + Azure Key Vault + Azure AD B2C
- Cohere reranking
- Sovereign rate: 0/13 services

Đặc biệt nguy hiểm: ctc có alias `text-generation/gpt-oss-120b` (tên gợi ý open-source sovereign) trỏ đến
`azure/gpt-5-nano` (proprietary Azure). Application code và audit logs thấy tên sovereign nhưng data thực tế đi qua
Microsoft.

Implications:

- Marketing claim "Swiss Sovereign AI" hiện tại không thể defense trước audit.
- US Cloud Act áp dụng: Microsoft và Cohere là US entities, có thể bị US gov compel disclosure of EU data.
- Schrems II ruling: EU companies dùng US cloud cần additional safeguards.
- Swiss revDSG, GDPR Art. 44 transfer requirements không meet.
- FINMA banking, HIPAA healthcare customers hoàn toàn block.

## Decision Drivers

- **Compliance**: Defense trước GDPR, Swiss revDSG, US Cloud Act, Schrems II, FINMA audit.
- **Reputation**: Tránh media exposure "Swiss AI actually on Azure US".
- **Customer trust**: Existing customers chọn platform vì sovereignty promise.
- **Marketing integrity**: Match claim với reality.
- **Pragmatism**: Model quality của Azure GPT-5 hiện cao hơn Swiss LLM Cloud (Gemma-4-31B-it).
- **Cost**: Self-hosted hardware cost upfront vs cloud opex.
- **Vendor lock-in**: ctc lock-in Azure ở 5 tầng, migration cost cao.
- **Time-to-fix**: Customers đã production, không thể downtime dài.

## Decision

Stakeholder phải chọn 1 trong 3 options trong tuần. Lý do gấp: marketing claim đang nói dối, audit risk hiện hữu,
customer #3 sẽ lại copy pattern nếu không có policy clear.

### Option A: Self-hosted local LLM (full sovereignty, recommended)

Deploy local LLM stack trên hardware tự quản, zero cloud LLM dependency.

**Stack**:

- **vLLM** cho high-throughput production serving (continuous batching, paged attention).
- **Ollama** hoặc **llama.cpp** cho development và test environments.
- **Models open-weight**: Llama 3.1/3.3 (8B/70B), Qwen 2.5 (7B/14B/72B), Mistral Small/Large, Mixtral 8x7B/8x22B, Gemma
  2 (9B/27B). Có thể fine-tune.
- **Embeddings**: BGE-M3 (multilingual, 1024-dim) hoặc bge-multilingual-gemma2.
- **Reranking**: BGE-Reranker-v2-m3 thay Cohere.
- **OCR**: MinerU (đã chuẩn hoá qua ADR 2026_02_09) thay Azure Document Intelligence.

**Hardware**:

- Tối thiểu 1× NVIDIA A100 80GB hoặc H100 cho 7B-13B model serving production.
- Cho 70B model: 2× A100 80GB hoặc tương đương.
- Location: bare-metal trên data center customer hoặc Hetzner CH/EU, Exoscale CH.

**Migration plan**:

- bmd: 1-2 sprints migrate LiteLLM config sang local endpoints.
- ctc: 2-3 sprints, bao gồm migrate Azure VM sang bare-metal, replace Azure Document Intelligence với MinerU, remove
  Azure AD B2C.

**Pros**: True data sovereignty, zero vendor lock-in, predictable cost (CapEx hardware, không OpEx per-token), no Cloud
Act exposure, defense full trước audit.

**Cons**: Hardware procurement upfront cost (1× A100 80GB ~\$15-20K), model quality có thể thấp hơn GPT-5 cho một số
tasks complex, ops complexity cao hơn (managed cloud).

### Option B: Update ADR, accept hybrid (pragmatic)

Update ADR 2026_02_24 thành "Sovereign-preferred, hybrid-allowed". Document explicit tier.

**Changes**:

- ADR text rewrite: "Tier-1 Sovereign self-hosted preferred. Tier-2 Hybrid cloud allowed with customer explicit
  consent."
- Customer agreement explicit về data flow (which LLM calls go through Azure).
- Marketing rebranded: "Swiss-hosted infrastructure with optional hybrid LLM (US cloud)".
- Customer data classification: sensitive data luôn qua sovereign tier, non-sensitive có thể hybrid.

**Pros**: Quick fix (1-2 tuần), giữ model quality, minimum disruption cho bmd/ctc.

**Cons**: Marketing sovereignty claim weakened, vẫn có US Cloud Act exposure cho Tier-2 data, không phù hợp enterprise
customers regulated industries.

### Option C: Per-customer sovereignty tier (best for enterprise mix)

Core platform supports cả 2 modes. Customer chọn tier tại deployment time.

**Implementation**:

- Feature flag `sovereignty_mode = "sovereign-only" | "hybrid"` trong customer config.
- Sovereign-only mode: chỉ allow local LLM endpoints trong LiteLLM config (CI gate kiểm tra).
- Hybrid mode: allow Azure OpenAI/Foundry nhưng emit warning log và audit entry.
- bmd và ctc giữ hybrid (Azure) với clear documentation.
- New customers default sovereign-only.
- Marketing: "Choose your sovereignty level".

**Pros**: Flexible per use-case, high-sensitivity customers có proper isolation, gradual migration path.

**Cons**: 2 code paths trong LiteLLM config validation và deployment scripts, marketing complexity, increased testing
surface.

### Decision matrix

| Aspect                                    | Option A (self-hosted) | Option B (hybrid OK) | Option C (per-customer) |
| ----------------------------------------- | :--------------------: | :------------------: | :---------------------: |
| Marketing "Swiss Sovereign AI" defensible |       Yes (full)       |    No (downgrade)    |      Per-customer       |
| Effort cho team                           |     L (1-3 tháng)      |     S (1-2 tuần)     |       M (1 tháng)       |
| Cost upfront                              |    High (hardware)     |         Low          |         Medium          |
| Model quality                             |  Lower (open-weight)   |    Higher (GPT-5)    |          Mixed          |
| Compliance enterprise (FINMA, HIPAA)      |          Yes           |          No          |  Yes (sovereign tier)   |
| Customer trust                            |          High          |        Medium        |   High (transparent)    |
| Time to migrate bmd/ctc                   |       1-3 tháng        | 1-2 tuần (doc only)  |         Gradual         |

**Recommended**: Option A nếu sovereignty là non-negotiable core value, Option C nếu cần flexibility cho enterprise mix,
Option B chỉ acceptable nếu marketing rebranded đồng bộ.

## Consequences

### Positive (Option A)

- Defense full trước GDPR, revDSG, FINMA, HIPAA, US Cloud Act, Schrems II audits.
- Marketing claim match reality.
- Customer trust high.
- Cost predictable (CapEx hardware, không bị tính per-token spike).
- Zero vendor lock-in cho LLM layer.

### Negative (Option A)

- Hardware procurement upfront cost (\$15-20K per A100 80GB).
- Model quality có thể thấp hơn cho complex reasoning tasks.
- Ops complexity cao hơn (model serving, GPU monitoring).
- Migration time cho bmd/ctc: 1-3 tháng downtime hoặc dual-running.
- Customers cần training cho new operational model.

### Positive (Option B)

- Quick implementation (1-2 tuần).
- Minimum disruption.
- Giữ model quality cao.

### Negative (Option B)

- Marketing claim phải downgrade.
- Existing customer trust risk nếu họ chọn platform vì sovereignty.
- Vẫn có US Cloud Act exposure.
- Block enterprise regulated industries.

### Positive (Option C)

- Flexibility cho customer mix.
- Gradual migration path.
- Transparent customer agreement.

### Negative (Option C)

- 2 code paths increase maintenance.
- Testing complexity tăng.
- Marketing message phức tạp.

## Implementation notes

Sau khi decision:

1. Update ADR `2026_02_24` với reality reconciliation (ADR-NEW-017).
2. Customer LiteLLM config CI gate (ADR-NEW-016).
3. Customer notification về data flow change (legal language).
4. Update marketing materials, website, customer-facing docs.
5. Customer ADRs (bmd, ctc) document migration decision (xem
   [Overview §11.2](../01_architecture_review_overview.vi.md#112-customer-aihub-bmd) và
   [§11.3](../01_architecture_review_overview.vi.md#113-customer-aihub-ctc)).

## References

- ADR `2026_02_24_swiss_sovereign_dual_mode_inference.md`: Original sovereignty decision (đang bị vi phạm).
- [Details §18 Data Sovereignty Violation](../02_architecture_review_details.md#18-data-sovereignty-violation-critical):
  Full evidence và analysis.
- [Overview §1 Tóm tắt một trang](../01_architecture_review_overview.vi.md#1-t%C3%B3m-t%E1%BA%AFt-m%E1%BB%99t-trang):
  Executive context.
- [Overview §7 Go/No-Go Decision Flow](../01_architecture_review_overview.vi.md#7-go-no-go-decision-flow): Sovereignty
  as Q1 block.
