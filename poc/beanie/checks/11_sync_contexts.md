# Check 11 — sync contexts in `packages/pipeline` and `packages/bot`

**Phase:** 3, step 3 — code inventory, no runtime measurement\
**Verdict:** **PASS — the concern largely evaporates.** `packages/pipeline` holds **zero** MongoEngine entities, and
`packages/bot` is already async.\
**Run:** 2026-09-22 · static analysis of the working tree at `poc/beanie-spike`

## Question

Beanie has no synchronous mode. The plan flagged Dagster ops in `packages/pipeline` and parts of `packages/bot` as
code that cannot `await`, and therefore as a potential blocker or a forced split (keep MongoEngine there, or adopt
Bunnet). How much code is actually affected?

## What was found

### `packages/pipeline` — not affected at all

| Measure                                        | Count |
| ---------------------------------------------- | ----- |
| MongoEngine entity classes                     | **0** |
| `.objects(` queries in `swiss_ai_hub/pipeline` | **0** |
| `mongoengine.connect()` call sites reached     | **0** |

Three things explain it:

1. **`RefDocDocument` and `DocumentWithFigureInfo` are LlamaIndex documents, not MongoEngine ones.** Both do
   `from llama_index.core import Document`. They were counted as MongoEngine entities in the phase-1 inventory — see
   the correction below.
2. **`connect_to_mongo_db` is dead code.** `packages/pipeline/swiss_ai_hub/pipeline/util/connection_utils.py:5` defines
   it and **nothing in the repository calls it**.
3. **Document-store access does not go through MongoEngine.** It goes through LlamaIndex's `MongoDocumentStore`
   (`pipeline/resources/doc_store/mongo_document_store_resource.py`, `core/persistence/rag/documents/stores/docstore.py`),
   which sits on raw PyMongo. An ODM swap does not touch it.

The only MongoEngine use anywhere under `packages/pipeline` is `playground/__init__.py`, which creates a `BucketEntity`
row so the quick-start example has a database to ingest into. Playground scaffolding, not the pipeline runtime.

### `packages/bot` — affected, but it is already async

| Measure                                         | Count |
| ----------------------------------------------- | ----- |
| MongoEngine entity classes                      | 7     |
| `.objects(` call sites in production code       | **7** |
| `.objects(` call sites in tests                 | 24    |
| `async def` in production code                  | 45    |
| FastAPI / uvicorn / APIRouter references        | 16    |

The seven production call sites live in exactly two files — `persistence/entities/conversation_entity.py` (4) and
`persistence/entities/path_entity.py` (3) — and every one is inside a plain `@classmethod`, not an `async def`. The bot
itself is a FastAPI service with 45 async functions, so those classmethods are called *from* async code. They are
ordinary blocking-call-in-async-context sites, the same shape as the API's, not a genuine sync context.

## Interpretation

**There is no sync-context problem to solve.** The plan carried "what do `packages/pipeline` and `packages/bot` do,
given they cannot `await`?" as an open question and a possible forced split in the migration. The answer is that the
premise was wrong for both:

- `packages/pipeline` **has no MongoEngine to migrate.** Its Dagster ops being synchronous is irrelevant, because they
  never touch the ODM.
- `packages/bot` is an async service. Its seven call sites convert exactly like the API's — `async` classmethods
  awaited from already-async callers.

Two consequences for the plan:

1. **Drop the follow-up issue** for a pipeline/bot sync-context strategy. Bunnet is not needed, and neither is a
   permanent two-ODM split by package.
2. **The migration surface is smaller than stated.** It is `packages/core` (28 classes) plus seven call sites in
   `packages/bot`, and nothing else.

## Correction to the phase-1 inventory

The phase-1 report and several check files state **"22 `Document` + 13 `EmbeddedDocument` = 35 classes … across
core/api/bot/pipeline"**. Two figures in that are wrong:

| Figure                | Phase 1 said                    | Correct                                            |
| --------------------- | ------------------------------- | -------------------------------------------------- |
| Total classes         | 35                              | **35** (coincidentally unchanged)                  |
| Split                 | 22 Document + 13 Embedded       | **20 Document-like + 15 Embedded**                 |
| Packages              | core / api / bot / pipeline     | **core (28) + bot (7) only**                       |
| `packages/pipeline`   | 2 entities                      | **0** — both are LlamaIndex `Document` subclasses  |

The original count regex matched `^class X(Document)` without checking which `Document` was imported, so two
LlamaIndex classes were swept in. The total survived because the stricter count found two additional embedded classes
the first pass missed. `packages/api` declares no entities of its own; it imports them from `packages/core`.

## Caveats

- Static analysis only. Nothing was executed, so a dynamic or reflective use of an entity would not appear.
- The `.objects(` pattern misses other query entry points (`Entity(...)` construction followed by `.save()`,
  `switch_db`, aggregation via `.objects.aggregate`). The bot figure is therefore a floor, not an exact total.
- "Already async" describes the bot's call sites, not that they are correct — they are blocking calls inside an async
  service, i.e. the same defect class as issue #1634 names for the API. That is a separate finding, not a migration
  blocker.
