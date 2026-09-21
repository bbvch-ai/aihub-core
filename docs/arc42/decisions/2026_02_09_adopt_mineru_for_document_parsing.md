# Adopt MinerU for Document Parsing

## Context

Swiss AI Hub requires robust document parsing capabilities to extract structured content from PDFs, Word documents, and
other file formats for the document ingestion pipeline. The platform must support both GPU-enabled deployments (with
local model inference) and CPU-only environments (with remote model access).

We initially adopted Docling, which offers two operational modes:

- **Pipeline Mode**: Uses multiple specialized models (OCR, table recognition, layout analysis) orchestrated through
  transformers/PyTorch. Provides excellent quality but requires significant compute resources.
- **VLM Pipeline Mode**: Uses a single fine-tuned vision-language model (granite-docling) for unified processing.

While Docling's pipeline mode produced high-quality results, it faced critical scalability challenges:

- **CPU Performance**: Processing took minutes per PDF page on CPU-only infrastructure, making it impractical for
  production use without GPU acceleration.
- **VLM Limitations**: Switching to VLM mode with remotely-hosted granite-docling improved speed but degraded parsing
  quality compared to pipeline mode. The VLM approach still underperformed relative to expectations.
- **Deployment Constraints**: No clear path to serve both GPU and CPU environments with acceptable performance/quality
  trade-offs.

## Decision Drivers

- **Dual Environment Support**: Must work efficiently in both GPU-enabled (local inference) and CPU-only (remote
  inference) deployments
- **Scalability**: Document parsing should complete in seconds, not minutes, regardless of infrastructure
- **Quality**: Maintain high accuracy for OCR, table extraction, and layout preservation
- **Licensing Compliance**: Respect open-source license boundaries while integrating with proprietary code
- **VLM Performance**: VLM mode should be production-ready, not a degraded fallback

## Decision

We adopt **MinerU** as the document parsing engine, replacing Docling entirely. MinerU operates in VLM mode exclusively,
using its custom-trained vision-language model (MinerU2.5-2509-1.2B) for unified document understanding.

**Architecture**:

1. **mineru-api** (CPU-only container): Lightweight API service that handles document parsing requests. Routes VLM
   inference to LiteLLM proxy rather than loading models locally.
2. **mineru-vlm** (GPU container, optional): Hosts MinerU's VLM via vLLM for local inference when GPU is available. Not
   deployed in CPU-only environments.
3. **LiteLLM Integration**: Unified routing layer directs VLM requests to either:
   - Local `mineru-vlm` container (GPU deployments)
   - Partner-hosted cloud endpoint (CPU deployments)

**AGPL Licensing Isolation**: MinerU is AGPL-licensed, requiring strict network isolation to avoid viral licensing
effects:

- MinerU code runs only in dedicated Docker containers (`mineru-api`, `mineru-vlm`)
- Communication exclusively via REST API (HTTP network boundary)
- No direct library imports into proprietary `swiss_ai_hub.core` or other packages
- Containers added to license exclusion list (`licenses.config.json`)

**API Strategy Change**:

- **Removed Docling-Specific API**: The `/api/v1/docling` endpoint was removed as we no longer offer Docling-compatible
  APIs
- **Generic Parsing Endpoint**: `/api/v1/parsing` added exclusively for OpenWebUI integration (OpenWebUI still relies on
  backend parsing)
- **Implementation Agnostic**: The parsing endpoint abstracts away the underlying implementation (MinerU), unlike the
  previous Docling-specific endpoint

**Configuration Changes**:

- Removed: `DOCLING_*` environment variables, `DoclingLoader`, `DoclingSettings`, `DoclingController`
- Added: `MINERU_*` environment variables, `MineruLoader`, `MineruSettings`, `ParsingController`

## Consequences

### Positive

- **Universal Scalability**: CPU environments achieve acceptable performance via remote VLM inference, GPU environments
  get optimal performance via local vLLM
- **Simplified Model Strategy**: Single VLM model handles all document types, eliminating multi-model orchestration
  complexity
- **Superior Quality**: MinerU's VLM produces better parsing quality than Docling's pipeline mode while also being
  significantly faster
- **Flexible Deployment**: GPU/CPU decision made at deployment time via Docker Compose stage, not hardcoded in
  application logic
- **License Safety**: Network isolation prevents AGPL contamination of proprietary codebase

### Negative

- **AGPL License Risk**: Must maintain strict network boundaries; accidental library imports could trigger viral
  licensing
- **Container Proliferation**: Two additional containers (`mineru-api`, `mineru-vlm`) increase deployment complexity
- **Partner Dependency**: CPU deployments rely on partner-hosted VLM endpoint availability and performance
- **Model Lock-in**: Committed to MinerU's VLM model; switching would require rewriting integration
- **Network Overhead**: REST API calls add latency compared to in-process function calls (acceptable trade-off for
  license safety)
- **Image Size**: `mineru-vlm` container includes baked-in models (~4GB) for faster startup at cost of storage

### Trade-offs

- **Performance vs Licensing**: Network isolation adds latency but ensures AGPL compliance
- **Speed Improvement**: MinerU VLM achieves 4-10x speedup over Docling while maintaining superior quality
- **Flexibility vs Complexity**: Supporting both GPU/CPU environments requires additional infrastructure but enables
  broader deployment scenarios
