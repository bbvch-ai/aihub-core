# Migrate from MongoEngine to Beanie

## Context

Swiss AI Hub persists to FerretDB through MongoEngine, a **synchronous** ODM called from `async def` throughout the API.
The API runs one event loop that serves every HTTP request, every WebSocket frame and every NATS callback, so a blocking
query freezes all of it for the duration of the round-trip.

Issue [#1634](https://github.com/bbvch-ai/aihub-core/issues/1634) records two production symptoms this caused: agent
runs failing at start when the config RPC's single 5 s no-retry budget expired while NATS sat idle, and every agent
class flipping offline at once when a stalled discovery round stopped refreshing `last_discovered`.

Those symptoms framed the question as a performance problem, and **as a performance problem the migration does not
justify itself**. The measurements are unambiguous: fully off-loading MongoEngine with `asyncio.to_thread` performs as
well as Beanie at every concurrency the platform will reach. The decisive driver is a different one, and it belongs to a
different issue.

[#1152](https://github.com/bbvch-ai/aihub-core/issues/1152) asks for a versioned migration framework for the platform's
FerretDB collections: a registry that runs migrations automatically on startup, `strict: True` on documents once it
exists, and a CI gate that fails when a schema change ships without one. Today there is none, so every schema change
becomes either a manual operator step or an `if old_shape:` branch in code — which is also why 15 `Document` classes and
3 `EmbeddedDocument` classes run with `strict: False` today.

**Beanie ships a migration framework, and it works on FerretDB.** Choosing Beanie answers #1634 and the bulk of #1152
with one decision instead of two.

The evaluation ran as a throwaway spike on branch `poc/beanie-spike` (head `34055e94`), deliberately never merged.
Fourteen checks against FerretDB 2.5.0 and Beanie 2.2.0 produced the evidence recorded at the end of this document.

## Decision Drivers

- **Beanie's migration framework works on FerretDB, tested end to end**\
  A real iterative migration transformed documents correctly, the run was recorded in `migrations_log`, a second run was
  a **no-op**, and a backward migration rolled the change back. Those four properties are what "runs automatically on
  startup" requires. The platform gets a versioned registry, forward/backward machinery, state tracking and idempotency
  instead of building them.
- **It makes the schema-drift problem tractable**\
  Eighteen persistence classes run with `strict: False` because old document shapes drift and nothing can remove them
  deliberately: every access entity (`BearerToken`, `RoleEntity`, `TenantMetadataEntity`, `UserTenantRoleEntity`), both
  discovery entities (`AgentClassEntity`, `ProcessClassEntity`), all messaging entities (`ThreadEntity`,
  `PersistedAgentEventEntity`, `PersistedProcessEventEntity`), the whole RAG datalake (`BucketEntity`, `IngestorEntity`,
  `NamespaceEntity`, `SourcePipelineEntity`) plus `RefDoc`, `UserDashboardEntity`, and the embedded `ConfigSpecsEntity`,
  `DashboardItem` and `Dashboard`. That is half the entity inventory, not a corner case. A working migration framework
  is what permits normalising that drift and then tightening the models — which is #1152's second acceptance criterion.
- **Pydantic-native persistence closes a long-standing convention gap**\
  Entities are MongoEngine documents converted by hand to Pydantic DTOs. Beanie documents *are* Pydantic models,
  removing the double modelling and aligning persistence with the codebase's Pydantic-first convention.
- **Performance is not a reason to migrate, and this must not be forgotten later**\
  At a production container's thread-pool width of 6, off-loaded MongoEngine and Beanie are indistinguishable up to 400
  concurrent config RPCs — p50 221 ms vs 267 ms, zero timeouts against the 5 s budget. Beanie is also **slower** per
  operation: 524 ms against 447 ms for 200 sequential reads. Any future argument that leans on speed is unsupported by
  this evidence.
- **FerretDB 2.5 is not an obstacle**\
  Every compatibility gate passed: the compound unique index on `agent_configs` is created and genuinely enforced,
  `findAndModify` has correct semantics, and both production aggregation pipelines — including the correlated `$lookup`
  with `let`/`$expr`/`$in` — return rows byte-identical to plain PyMongo.
- **Incremental migration is structurally possible**\
  Beanie and MongoEngine write **identical document shapes**, and a synchronous `MongoClient` coexists with an
  `AsyncMongoClient` on one collection in one process, each reading the other's writes. Entities can move one at a time.
- **The migration surface is smaller than the issue implies**\
  36 entity classes live in `packages/core` (29) and `packages/bot` (7) **only**. `packages/pipeline` holds **zero** —
  its two `Document` classes are LlamaIndex's and its `connect_to_mongo_db` is dead code. There is no synchronous
  context to work around, and no need for Bunnet or a permanent two-ODM split.
- **Beanie 2.x uses PyMongo's supported async driver**\
  `AsyncMongoClient`, with zero references to Motor, which is deprecated upstream.
- **The costs are known and bounded, not discovered mid-migration**\
  A non-incremental test-suite conversion, a per-database routing registry, and five datetime fields to normalise. Each
  is named below with a size.

## Decision

**We migrate persistence from MongoEngine to Beanie, incrementally, and adopt Beanie's migration framework as the answer
to #1152.**

### Six rules that are not optional

Every one of these was found by a check that first appeared to pass. All six failure modes are **silent** — no
exception, no warning, success reported — so none of them would be caught by a reviewer reading a diff.

1. **Never opt in to `use_transaction=True`.** Beanie 2.2 defaults it to `False`; the rule guards the opt-in. FerretDB
   2.5 does not implement `commitTransaction` (`code 59, CommandNotFound`). With the flag on, the migration's writes
   **land**, the commit then fails, the run raises, and `migrations_log` is left **empty** — data changed with nothing
   recording it, so a retry re-applies the migration to already-migrated documents. It is the flag an operator reaches
   for *because they want safety*, and on FerretDB it buys the appearance of atomicity with none of the substance.
   Enforced in CI, not left to a comment.

2. **Every entity ported from a `strict: False` document declares `extra="allow"`**, until its drift has been normalised
   by a migration. Today that is 18 of the 36 classes being ported, so `extra="allow"` is the default posture of this
   migration, not an exception. Without it, a single `replace()` deletes every undeclared field. The other write paths
   survive only because `save()` uses `$set`-style semantics — an implementation property no test of ours asserts.

3. **`switch_db` is never translated by re-initialising a Document per call.** That translation passed a sequential test
   20/20 and then **silently misrouted under concurrency**: a write intended for one tenant's database landed in
   another's. Routing uses a lazy per-database registry of initialised subclasses instead.

4. **Automatic migration on startup holds a leader lease.** Four replicas started together, all reported success, and
   every document was migrated **twice**, with four `migrations_log` entries for one migration. The log is a plain
   collection with no locking, and FerretDB has no transactions to make the check-then-write atomic, so the ordinary
   read-modify-write race applies. The failure is not a failed boot — it is silently corrupted data with the log
   claiming success. `CronScheduler` already holds a Redis leader lease for exactly this reason; migrations follow it.

5. **Migrations across tenant databases run strictly sequentially**, never `asyncio.gather`-ed. Run concurrently in one
   process, one tenant was left entirely unmigrated **with no error raised**, while another received two log entries.

6. **Every `@free_fall_migration` is idempotent**: it can be re-run against a collection it already half-processed and
   produce the same end state. In practice, filter on the pre-migration shape (`{"new_field": {"$exists": False}}`)
   rather than on all documents, and prefer a single `update_many` over a per-document loop. A free-fall migration that
   cannot be written this way is split into an iterative migration for the data and a free-fall migration for the index
   or rename only. Reviewers ask for the re-run test, not the happy-path test.

Rules 3 and 5 share a root cause with the test-infrastructure cost below: **Beanie's database binding is
process-global.** `init_beanie` and `DBHandler` both mutate class-level state, so anything that retargets it must be
serialised or given its own process. Three symptoms — cross-tenant misrouting, dead-loop clients in tests, corrupt
concurrent migrations — one mechanism, worth teaching once rather than three times.

**An `@iterative_migration` that fails partway is safe**, which makes "refuse to start on migration failure" a viable
policy for that kind: a migration that raised mid-run wrote **nothing at all**. Beanie collects its `replace_many` calls
as coroutines and awaits none of them until the whole collection is transformed
(`beanie/migrations/controllers/iterative.py:93-128`), so the database is left in its pre-migration state and the deploy
can be rolled back. This does **not** extend to a failure inside that final `asyncio.gather`, nor is it verified beyond
the 10 000-document default `batch_size`.

**A `@free_fall_migration` has no such property.** The same failure expressed as a free-fall migration, verified against
FerretDB 2.5.0 during review of this ADR, left 2 of 4 documents migrated and `migrations_log` empty. Free-fall is the
only kind that can create an index, touch two collections or rename a field with `$rename`, so it cannot simply be
banned. Hence rule 6.

### Order of work

**Before the first entity moves.** These cannot be done incrementally:

- **The test-suite loop-scope change.** `AsyncMongoClient` is loop-bound. Widening pytest-asyncio's loop scope works but
  **cannot be mixed** with the default per-test scope, so all 913 `@pytest.mark.asyncio` tests move together and lose
  per-test loop isolation. The 183 `@async_test` uses cannot be rescued by loop scope at all, because `asyncio.run()`
  always creates its own loop; `packages/core/swiss_ai_hub/core/testing/asyncio_utils/bdd.py` is rewritten to share one.
  `db_isolation` is unaffected — it drops the test database with a synchronous client.
- **The lazy per-database routing registry** (rule 3).
- **The datetime normalisation.** Five naive-local fields in three collections: `AgentClassEntity.first_discovered` and
  `.last_discovered`, `ProcessClassEntity.first_discovered` and `.last_discovered`, and `ThreadEntity.created_at`.
  Measured on a UTC+7 host, mixing the two conventions in one collection makes a freshly written timestamp read as **7
  hours old — OFFLINE** against a 5-minute threshold. `ThreadEntity.created_at` is the trap: it has no field default and
  is naive only because of two assignment sites, so a migration written from a scan of defaults misses it.

**Then, entity by entity**, ordered by symptom relief: `AgentConfigEntityDocument` → `AgentClassEntity` → `ThreadEntity`
→ the persisted-event entities → access entities → RAG datalake → `packages/bot`.

**Not part of this migration**, tracked separately because they are true regardless of the ODM: the `NCRequester`
single-shot no-retry budget, and the fragility of a 5-minute `last_discovered` window as the definition of liveness.

### The interim fix stays

`AgentService.get_agent_configuration` and both discovery rounds already call MongoEngine through `asyncio.to_thread`
(branch `fix/api-mongo-blocking-loop`, `4722b030`), with regression tests that assert the property rather than the
implementation: a ticker coroutine must keep running while the call is in flight, verified to fail without the fix at 0
ticks against the 15 required.

That work is not wasted. It resolves #1634's symptoms now, months before the migration completes, and each wrapper is
deleted on the line being rewritten when its entity is ported.

One measured caveat makes finishing the migration matter rather than stalling half-way: **partial off-loading measured
worse than none** under a saturated loop (p50 4085 ms vs 3425 ms), because `to_thread` needs a second loop slice to
resume after its worker thread returns. The benefit comes from freeing the loop, not from wrapping one handler.

### Alternatives considered

1. **Keep MongoEngine and finish the `asyncio.to_thread` work.** Rejected. It resolves #1634 completely and costs far
   less — which is why the interim fix shipped — but it leaves #1152 entirely unbuilt and the Pydantic convention broken
   at the persistence boundary. On performance evidence alone this was the better option, and an earlier draft of this
   ADR recommended it; the migration-framework driver is what changed the balance.
2. **Build a versioned migration runner on raw PyMongo, keeping MongoEngine.** Migrations mostly operate on raw
   documents, so they do not strictly need an ODM. Rejected on cost and risk: it means writing and maintaining the
   registry, state tracking, forward/backward machinery and idempotency ourselves, against a battle-tested
   implementation that arrives with the ODM we would want anyway for convention reasons.
3. **ODMantic and Mongoz.** Excluded on paper without testing: both are built on Motor, deprecated upstream.
4. **PyMongo async with hand-written repository classmethods, no ODM.** Not evaluated. It would carry the same
   test-infrastructure and `switch_db` costs as Beanie, without Beanie's Pydantic integration or its migration
   framework.

## Consequences

### Positive

- #1634 and #1152 are answered by one decision. The migration framework arrives with the ODM rather than being built.
- Schema changes stop being manual operator steps or `if old_shape:` branches, and `strict: False` becomes removable
  once drift is normalised.
- Entities become Pydantic models, removing the entity ↔ DTO double modelling and satisfying convention #2 at the
  persistence boundary.
- Blocking database calls leave the event loop permanently, rather than depending on every future author remembering
  `asyncio.to_thread`.
- The migration is incremental: identical document shapes and sync/async coexistence on one collection were both
  verified, so entities move one at a time behind a working test suite.
- The costs were found before committing rather than during. Every one of the five rules exists because a check caught a
  silent failure, and each is reproducible from the spike branch.

### Trade-offs

- **The test-suite conversion is a single large change**, not an incremental one, and it removes per-test loop isolation
  from all 913 async tests including the majority that never touch the database. The `@async_test` rewrite is
  **identified but not built** — it must not be priced as cheap until it is.
- **No performance gain, and a small per-operation loss.** Beanie was slower in every sequential measurement taken.
- **Six silent failure modes to defend against.** CI checks and a routing registry are mitigations, not guarantees; a
  future author who does not know rule 4 exists can still reintroduce a double-applying migration, and one who writes a
  free-fall migration as a plain loop reintroduces partial application.
- **The per-database routing registry is new code** with concurrency requirements that did not exist under MongoEngine,
  replacing a mechanical translation that fails in a cross-tenant direction.
- **Migration effort across 36 entity classes and 144 `.objects(` call sites**, and the surface grows while the decision
  is deliberated — `SourcePipelineEntity` landed on `main` during this evaluation. Every repository classmethod becomes
  `async`, cascading into every service and test that calls it.
- **The evaluation ran on a development host**, not production: 20 cores, Windows, single-node FerretDB, a synthetic
  saturator, no LLM traffic, no agent runners and a warm corpus, exercising only the config RPC path. The 123-second
  cold read that `persisted_agent_event_entity.py:584` blames for the original incident was **not** reproduced — a
  blocking call of that length starves the loop under any variant that still has one.
- **Migration behaviour at scale is untested.** The largest migration exercised three documents in one collection.
  Duration, memory use and how long a leader lease must be held are all unknown, as is the write-stage failure mode
  above the 10 000-document `batch_size`.

## Evidence — the fourteen checks

Recorded here because the spike branch is never merged. Each check on that branch holds its question, the script that
answers it, verbatim unedited output in `poc/beanie/logs/`, an interpretation and its own caveats. This table is the
durable summary; the branch is the reproduction.

Environment for every check: **Beanie 2.2.0**, **FerretDB 2.5.0** (`postgres-documentdb:17.0.106.0-ferretdb-2.5.0`,
reporting MongoDB 7.0.77, wire version 21), MongoEngine 0.29.3, Python 3.13.13, on a 20-core Windows host at **UTC+7**.
The host offset is load-bearing for check 07 — on a UTC host that check proves nothing.

### Phase 1 — compatibility gate (checks 01–08)

Checks 01–04 were hard gates: any failure would have ended the Beanie option and left "extend `asyncio.to_thread`" as
the answer. Checks 05–08 were cost inputs.

| #   | Question                                                    | Verdict            | Key finding                                                                                                                                                                           |
| --- | ----------------------------------------------------------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 01  | Does `init_beanie` create our indexes, and are they real?   | **PASS**           | Compound unique index on `agent_configs` created **and genuinely enforced** — a duplicate insert is rejected, not silently accepted. Idempotent re-init: 103 ms cold, 9 ms warm.      |
| 02  | Do CRUD and the on-disk shape match MongoEngine?            | **PASS**           | **Byte-identical shapes** — zero key-set difference, no Beanie bookkeeping field. Each ODM reads the other's documents. This is what makes incremental migration possible.            |
| 03  | Does FerretDB support the `findAndModify` path Beanie uses? | **PASS**           | Correct BEFORE/AFTER, nested `$set` preserving siblings, upsert, no-match → `None`. Found that `save_changes()` requires `use_state_management = True` per Document.                  |
| 04  | Do our real aggregation pipelines survive?                  | **PASS**           | Both production pipelines return rows **byte-identical to plain PyMongo**, correlated `$lookup` included. `allowDiskUse` is accepted but **not proven honoured** — pre-existing.      |
| 05  | How is `switch_db` expressed, and what does it cost?        | **PASS WITH COST** | The mechanical translation passed a sequential test **20/20**, then **silently misrouted under concurrency**: a write for database A landed in database B. Source of rule 3.          |
| 06  | Do undeclared fields survive a read-modify-write?           | **PASS WITH COST** | A model without `extra="allow"` written back with `replace()` **deleted every drift field**. The other paths survive only by implementation accident. Source of rule 2.               |
| 07  | What is actually stored for a datetime?                     | **PASS**           | Beanie stores datetimes **identically** to MongoEngine — the hazard is pre-existing and ODM-neutral. At UTC+7 a fresh aware-UTC stamp reads **7 hours old → OFFLINE**.                |
| 08  | Can sync and async clients share a collection?              | **PASS**           | They can, each reading the other's writes — the second precondition for incremental migration. Also showed the loop fix: **0 ticks** during 447 ms of blocking reads vs **49 of 52**. |

### Phase 3 — evaluation (checks 09–12)

| #   | Question                                          | Verdict               | Key finding                                                                                                                                                                               |
| --- | ------------------------------------------------- | --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 09  | Does Beanie survive this repo's test suite?       | **PASS WITH COST**    | A module-scoped client fails on the **first** test, not the second. The loop-scope mitigation is all-or-nothing across 913 tests, and the 183 `@async_test` uses need `bdd.py` rewritten. |
| 10  | Where does `asyncio.to_thread` stop holding?      | **`to_thread` holds** | Indistinguishable from Beanie to 400 concurrent RPCs at pool width 6. A gap opens only at pool=2 / 800 concurrent, where neither times out. Partial off-loading measured worse than none. |
| 11  | What do the sync contexts in pipeline and bot do? | **PASS**              | `packages/pipeline` holds **zero** MongoEngine entities. `packages/bot` has 7 call sites and is already async. No Bunnet, no two-ODM split.                                               |
| 12  | How big is the datetime migration?                | **PASS**              | **5 fields in 3 collections.** `ThreadEntity.created_at` is the trap: no field default, naive only via two assignment sites.                                                              |

### Phase 4 — the migration framework (checks 13–14)

| #   | Question                                                                 | Verdict                     | Key finding                                                                                                                                                                                                                                                                                                         |
| --- | ------------------------------------------------------------------------ | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 13  | Does Beanie's migration framework work on FerretDB?                      | **PASS WITH ONE HARD RULE** | Forward transforms documents, the run is recorded, a second run is a **no-op**, backward rolls back. With `use_transaction=True`: writes land, commit fails, log left empty. Source of rule 1.                                                                                                                      |
| 14  | Does it survive partial failure, concurrent replicas and many databases? | **1 PASS, 2 FAIL**          | A failed **iterative** migration writes **nothing**; a failed free-fall migration writes everything up to the raise (added during ADR review, rule 6). Four concurrent replicas **double-applied** every document while all reporting success (rule 4), and concurrent multi-database migration corrupted (rule 5). |

### How the evidence was produced

Five rules governed the spike, and two of them caught mistakes that would otherwise have reached this document:

1. **Raw output is never edited, trimmed or paraphrased.** Summarised tracebacks are not evidence.
2. **Every check cites the pinned environment.** FerretDB's compatibility surface moves between releases, so a version
   number is the scope of every finding.
3. **A check that was not run says "not run"** — never PASS by assumption.
4. **Every report carries a "what this does NOT prove" section.** A green table says these operations worked on this
   version with this data shape, not that Beanie works.
5. **Verdicts are `PASS`, `PASS WITH COST` or `FAIL`.** "Mostly works" is not a verdict.

**Check 10's verdict criteria were written before the first measurement**, including the row "raw MongoEngine and
`to_thread` are indistinguishable → the harness is wrong". That row fired: the first harness saturated the loop with
~400 small writes per second, every variant passed, and the measurement was discarded rather than reported. The source
comment at `persisted_agent_event_entity.py:584` named the real culprit — a *cold read*, not many fast writes — and the
harness was rebuilt around the real spend aggregation over 50 000 documents.

**Check 06 stated that four documents run with `strict: False`.** That was a recollection, not a grep; the code has 18.
The earlier draft of this ADR carried the number forward. It slipped through because the raw-output rule covers script
output, not prose.

**Check 06 initially reported every write path as safe.** That result looked clean and was incomplete: the combination
of a strict model with `replace()` had not been tried, and that is the one that destroys data. It was noticed only
because a model that discards extra fields should not have been able to preserve them. Both runs are kept in the log.
