# Docling Serve API Reference

**Version:** 1.9.0
**Base URL:** `https://serve.docling.ai-agents.ch`
**Swagger UI:** `/docs`
**OpenAPI JSON:** `/openapi.json`

## Authentication

All `/v1/*` endpoints require API key authentication via `APIKeyAuth`.

---

## Health Endpoints

### GET /health
Check server health status.

**Response:** `HealthCheckResponse`

```bash
curl https://serve.docling.ai-agents.ch/health
```

### GET /version
Get server version information.

**Response:** Object with version details

```bash
curl https://serve.docling.ai-agents.ch/version
```

---

## Convert Endpoints

### POST /v1/convert/source
Convert document(s) from URL (synchronous).

**Request Body:** `ConvertDocumentsRequest` (JSON)
**Response:** `ConvertDocumentResponse` or `application/zip`

### POST /v1/convert/file
Convert uploaded file(s) (synchronous).

**Request Body:** `multipart/form-data` with `files`
**Response:** `ConvertDocumentResponse` or `application/zip`

### POST /v1/convert/source/async
Convert document(s) from URL (asynchronous).

**Request Body:** `ConvertDocumentsRequest` (JSON)
**Response:** `TaskStatusResponse` with `task_id`

### POST /v1/convert/file/async
Convert uploaded file(s) (asynchronous).

**Request Body:** `multipart/form-data` with `files`
**Response:** `TaskStatusResponse` with `task_id`

---

## Chunk Endpoints

### Hybrid Chunker

| Endpoint | Method | Mode |
|----------|--------|------|
| `/v1/chunk/hybrid/source` | POST | Sync, URL input |
| `/v1/chunk/hybrid/file` | POST | Sync, file upload |
| `/v1/chunk/hybrid/source/async` | POST | Async, URL input |
| `/v1/chunk/hybrid/file/async` | POST | Async, file upload |

### Hierarchical Chunker

| Endpoint | Method | Mode |
|----------|--------|------|
| `/v1/chunk/hierarchical/source` | POST | Sync, URL input |
| `/v1/chunk/hierarchical/file` | POST | Sync, file upload |
| `/v1/chunk/hierarchical/source/async` | POST | Async, URL input |
| `/v1/chunk/hierarchical/file/async` | POST | Async, file upload |

**Response (sync):** `ChunkDocumentResponse` or `application/zip`
**Response (async):** `TaskStatusResponse` with `task_id`

---

## Task Management Endpoints

### GET /v1/status/poll/{task_id}
Poll the status of an asynchronous task.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `task_id` | path | Yes | - | Task identifier |
| `wait` | query | No | 0.0 | Seconds to wait for completion |

**Response:** `TaskStatusResponse`

```bash
curl "https://serve.docling.ai-agents.ch/v1/status/poll/{task_id}?wait=10"
```

### GET /v1/result/{task_id}
Retrieve the result of a completed task.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | path | Yes | Task identifier |

**Response:** `ConvertDocumentResponse`, `ChunkDocumentResponse`, or `application/zip`

```bash
curl "https://serve.docling.ai-agents.ch/v1/result/{task_id}"
```

---

## Clear Endpoints

### GET /v1/clear/converters
Clear converter instances from memory.

**Response:** `ClearResponse`

```bash
curl "https://serve.docling.ai-agents.ch/v1/clear/converters"
```

### GET /v1/clear/results
Clear stored results from memory.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `older_then` | query | No | 3600 | Clear results older than N seconds |

**Response:** `ClearResponse`

```bash
# Clear results older than 1 hour (default)
curl "https://serve.docling.ai-agents.ch/v1/clear/results"

# Clear ALL results
curl "https://serve.docling.ai-agents.ch/v1/clear/results?older_then=0"

# Clear results older than 5 minutes
curl "https://serve.docling.ai-agents.ch/v1/clear/results?older_then=300"
```

---

## Common Convert/Chunk Options

These parameters are available for all convert and chunk endpoints:

### Input Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `convert_from_formats` | array | all | Allowed: docx, pptx, html, image, pdf, asciidoc, md, csv, xlsx, xml_uspto, xml_jats, mets_gbs, json_docling, audio, vtt |
| `convert_page_range` | [int, int] | [1, max] | Page range to convert (1-indexed) |
| `convert_document_timeout` | number | 604800 | Timeout per document (seconds) |
| `convert_abort_on_error` | boolean | false | Abort on error |

### OCR Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `convert_do_ocr` | boolean | true | Enable OCR processing |
| `convert_force_ocr` | boolean | false | Replace existing text with OCR |
| `convert_ocr_engine` | string | "easyocr" | Engine: auto, easyocr, ocrmac, rapidocr, tesserocr, tesseract |
| `convert_ocr_lang` | array | [] | Languages for OCR (engine-specific) |

### Table Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `convert_do_table_structure` | boolean | true | Extract table structure |
| `convert_table_mode` | string | "accurate" | Mode: fast, accurate |
| `convert_table_cell_matching` | boolean | true | Match predictions to PDF cells |

### Image Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `convert_include_images` | boolean | true | Extract images |
| `convert_images_scale` | number | 2.0 | Scale factor for images |
| `convert_image_export_mode` | string | "embedded" | Mode: placeholder, embedded, referenced |

### Enrichment Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `convert_do_code_enrichment` | boolean | false | OCR code enrichment |
| `convert_do_formula_enrichment` | boolean | false | Formula OCR (LaTeX output) |
| `convert_do_picture_classification` | boolean | false | Classify pictures |
| `convert_do_picture_description` | boolean | false | Describe pictures with VLM |

### Pipeline Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `convert_pipeline` | string | "standard" | Pipeline: standard, vlm |
| `convert_pdf_backend` | string | "dlparse_v4" | Backend: pypdfium2, dlparse_v1, dlparse_v2, dlparse_v4 |

### Output Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `target_type` | string | "inbody" | Output target type |
| `convert_md_page_break_placeholder` | string | "" | Page break marker in markdown |

---

## Chunking-Specific Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_converted_doc` | boolean | false | Include converted doc with chunks |
| `chunking_max_tokens` | int | auto | Max tokens per chunk |
| `chunking_tokenizer` | string | "sentence-transformers/all-MiniLM-L6-v2" | HuggingFace tokenizer |
| `chunking_merge_peers` | boolean | true | Merge undersized chunks |
| `chunking_use_markdown_tables` | boolean | false | Use markdown for tables |
| `chunking_include_raw_text` | boolean | false | Include raw_text in response |
