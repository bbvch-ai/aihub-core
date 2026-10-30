# Count Embedding and Reranker Tokens with the Model's Own Tokenizer

## Context

Embedding and reranking models reject an input past their window with a 400 instead of truncating it (#1856). Every site
that sizes such an input counted it with tiktoken `cl100k_base`, the OpenAI tokenizer, not the model's:

- **Ingestion:** the largest nodes (figures, the table-parse fallback) were capped at 0.85 × 8192 = 6963 cl100k tokens,
  counted with the chat model's configuration, and without the metadata that `embed_nodes` prepends. bge-m3 rejected the
  ones that ran over, and `embed_nodes` skipped them, so the document was indexed with a hole. Reproduced on 2026-10-29
  with a code `<figure>`.
- **Attached files** counted `len // 4`.
- **Query clamps** kept 50% of the window in cl100k, and the reranker ignored the document side of each query/document
  pair, so one oversized pair dropped reranking for the whole turn.

#1662 had already removed the earlier remote counter (LiteLLM's `/utils/token_counter`): it was blocking HTTP that
loaded the gateway, and it counted with tiktoken anyway.

A spike on 2026-10-29 measured each configured model's own tokenizer file against the usage the providers bill, on 24
samples (English, German and French prose, Python, tables, numbers, emoji and CJK, whitespace-heavy text, three sizes
each):

| Model (provider)              | Tokenizer file               | Matches provider | Provider tokens / cl100k |
| ----------------------------- | ---------------------------- | ---------------- | ------------------------ |
| bge-m3 (Phoeniqs)             | `BAAI/bge-m3@5617a9f`        | 24/24            | 0.54–1.45                |
| bge-m3 (stoney)               | `BAAI/bge-m3@5617a9f`        | 23/24, over by 1 | 0.54–1.45                |
| bge-reranker (both providers) | `BAAI/bge-m3@5617a9f`        | 23/24, over by 1 | 0.54–1.45                |
| gemma-4-31B-it (both)         | `google/gemma-4-31B-it`      | 24/24            | 0.54–1.64                |
| Kimi-K2.6                     | `moonshotai/Kimi-K2.6`       | 24/24            | 0.79–1.11                |
| Ministral-3-14B, Apertus      | shared Mistral BPE           | 24/24            | 0.85–1.65                |
| Qwen3.5-122B                  | `Qwen/Qwen3.5-122B-A10B-FP8` | 24/24            | 0.75–1.64                |

No provider exposes a `/tokenize` endpoint. On bge-m3, cl100k undercounts code by 1.32–1.45× (1.54× in production),
whitespace-heavy text by 1.31× and markdown by 1.15×, and overcounts German by up to 1.5×.

## Decision Drivers

- **A count that matches the window**\
  A safety factor only moves the failure: 0.85 still let 1.45× code through, and a factor large enough for code wastes a
  third of the window on German.
- **No network call per count**\
  #1662 showed what a remote counter costs the gateway, and budget sites run on every chunk and every turn.
- **Nothing breaks for a model nobody declared**\
  Chat models and any embedder a deployment adds must keep working exactly as before.
- **No re-ingest**\
  Existing indexes keep their chunk boundaries; nodes indexed under the old ceiling stay where they are.

## Decision

**Each embedding and reranking model declares its tokenizer in the LiteLLM config.** Two curated `model_info` keys, in
the style of ADR `2026_10_16_model_aware_llm_parameters`:

- `aihub_tokenizer`: the id of a vendored tokenizer (`bge-m3` for both `embedding/bge-m3` and `reranker/bge`).
- `aihub_input_overhead_tokens`: the special tokens the model adds, 2 per input for the embedder (`<s> text </s>`) and 4
  per pair for the reranker (`<s> query </s></s> document </s>`). They are a fact about the model, not the file: one
  file serves both.

Our own keys, not LiteLLM's `custom_tokenizer`, so LiteLLM never reaches out to Hugging Face. A unit test checks that
every `mode: embedding|rerank` entry of every generated config declares both, and that the id is vendored.

**The tokenizer file is vendored in `packages/core`.** `generative_ai/resources/tokenizers/vendored/bge_m3/` holds
`sentencepiece.bpe.model` (5.1 MB, byte-identical in bge-m3 and bge-reranker-v2-m3), its MIT `LICENSE` (FlagEmbedding,
and XLM-R from which the model originates) and a `SOURCE.json` with repository, revision, file, sha256 and format. Every
image installs core from source, so no image or compose change is needed.

**sentencepiece, with a margin of one.** The `.model` loads in 0.31 s and +38–59 MiB per process, against 0.5–0.7 s and
+282 MiB for `tokenizer.json`, and encodes about 4× faster. It drops trailing whitespace that `tokenizer.json` keeps, so
on such input it counts exactly one token fewer (20,000 repository snippets, never two). `ModelTokenizer.count` adds 1
for this format everywhere, so it never undercounts and overcounts by at most 1.

**Counted in-process at the budget sites only.** `ModelTokenBudget.for_model(name, model_info)` is built from the
`model_info` the caller already fetched, loads the tokenizer lazily and once per process. `LiteLLMBase.token_counter`
stays tiktoken, so chat budgets, cost tracking and #1662's no-network guarantee are untouched. The sites:

- **Ingestion node ceiling:** content is capped at `MAX_NODE_TOKENS = 2048` exact tokens. Every built node is then
  checked as `embed_nodes` sends it, metadata included; a node over the window has its content split again to the room
  its metadata leaves, and metadata leaving under 256 tokens raises, naming the document, the node and its largest keys.
  Summary nodes get the same check before embedding.
- **Splitting:** `SentenceSplitter` sums separately encoded pieces and overshoots (2113 tokens for 2048 on Python), so
  every piece is counted again and split smaller while over, then cut by a measured binary search over characters. Token
  ids are never decoded back to text. The 512-token text splitter and table splitting stay in tiktoken, so chunk
  boundaries do not move.
- **Query clamp:** the whole window minus the overhead for a declared model.
- **Reranker:** per request, each document is counted as sent; the query gets the room the longest document leaves. If
  that is under 256 tokens, the longest documents are cut for this request only, which handles nodes indexed under the
  old ceiling (up to ~8.2k tokens).

**A model without `aihub_tokenizer` keeps today's behaviour:** tiktoken `cl100k_base`, the 0.85 node factor and
character caps, and the 0.5 query factor. Each process logs one warning per undeclared embedding or reranking model;
chat models stay quiet.

**The fallback stays on `cl100k_base`, not `o200k_base`.** Measured on the same 24 samples against the exact counts:

| Model                   | cl100k worst undercount | o200k worst undercount | Mean error cl100k → o200k |
| ----------------------- | ----------------------- | ---------------------- | ------------------------- |
| bge-m3 (embed + rerank) | 1.45× (Python)          | 1.45× (Python)         | 19.4% → 16.5%             |
| gemma-4                 | 1.64× (numbers)         | 1.66× (numbers)        | 21.6% → 18.6%             |
| Qwen3.5                 | 1.64× (numbers)         | 1.66× (numbers)        | 16.9% → 15.0%             |
| Ministral / Apertus     | 1.65× (numbers)         | 1.67× (numbers)        | 16.5% → 23.1%             |
| Kimi-K2.6               | 1.11× (German)          | **1.38×** (German)     | 4.7% → 11.4%              |

o200k is closer on average for three families, but only because it overcounts less on German, French and CJK. A budget's
safety depends on the worst undercount, and there o200k is equal or worse everywhere and adds new ones (German
1.04–1.38× instead of 0.86–1.11×).

### Rejected options

- **Counting at the gateway** (LiteLLM's token counter or a custom endpoint): the blocking round trip per count #1662
  removed, and LiteLLM would fetch tokenizers from Hugging Face.
- **Downloading tokenizers in an init container or at start:** a network dependency at start for a 5 MB file that
  changes when the model does, which is when the config changes too.
- **Per-model ratios on top of tiktoken:** the ratio varies 0.54–1.45× by content on bge-m3 alone, so it is still a
  guess with a safety factor.
- **Letting the provider truncate:** neither provider truncates embeddings or rerank pairs; they answer 400.
- **A shared tokenizer service:** worth it only if chat models' ~62 MB of files and up to ~8.6 GiB worst-case memory
  move in-process. That is decided with the chat models, behind the same `ModelTokenBudget` interface.

## Consequences

- **Memory:** each process that counts loads sentencepiece once, +38–59 MiB and 0.31 s on first use; worst case ~19
  processes across a stack, about 1.1 GiB. A rerank of 20–50 documents costs under 25 ms of counting, run off the event
  loop.
- **Vendored files in an Apache-2.0 package:** the MIT files carry their own `LICENSE`, listed in `LICENSES.md`,
  `NOTICE` and core's `license-files`, and are excluded from the whitespace pre-commit hooks.
- **Adding an embedding or reranking model** means vendoring its tokenizer and declaring both keys, or accepting the
  fallback and its warning.
- **Deploy order:** apps cache `model_info` per process, and ansible does not restart LiteLLM when its mounted config
  changes. Force-recreate LiteLLM first, then restart the apps; otherwise they run on the fallback (correct as before,
  just not exact) until their next restart. The k8s LiteLLM config needs the same keys.
- **New ingestion splits large figures and tables into more, smaller nodes** (2048 instead of ~7k tokens). Ordinary text
  chunks are unchanged, and nothing is re-ingested; legacy oversized nodes are handled per rerank request.
- **Chat models stay on tiktoken.** Number-heavy text undercounts 1.62–1.65× on gemma, Qwen, Ministral and Apertus, so a
  chat budget at 85% can reach ~140% of the window. That is a separate issue: whether `token_counter` becomes
  model-aware, how to ship ~62 MB of files, the gated Apertus repository and Kimi's licence clause.
