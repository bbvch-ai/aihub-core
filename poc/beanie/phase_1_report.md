# Phase 1 report — Beanie / FerretDB 2.5 compatibility gate

**Verdict: GO.** All four hard gates pass. The Beanie option survives; proceed to phase 2.

**Run:** 2026-09-22 · `poc/beanie-spike` · beanie **2.2.0** · FerretDB **2.5.0** (reports MongoDB 7.0.77, wire
version 21) · mongoengine 0.29.3 · Python 3.13.13 · host at **UTC+7**\
**Environment:** [`environment.md`](environment.md) · **Raw output:** [`logs/`](logs/)

## Result table

| #  | Check                                                     | Gate | Verdict            | Note                                                              |
| -- | --------------------------------------------------------- | ---- | ------------------ | ----------------------------------------------------------------- |
| 01 | [`init_beanie` + index creation](checks/01_init_beanie.md) | hard | **PASS**           | Compound unique index created **and genuinely enforced**           |
| 02 | [CRUD + on-disk shape](checks/02_basic_crud.md)            | hard | **PASS**           | Byte-identical shape to MongoEngine; both ODMs cross-read          |
| 03 | [`find_one_and_update`](checks/03_find_one_and_update.md)  | hard | **PASS**           | Correct semantics; `save_changes()` needs `use_state_management`   |
| 04 | [`$group`, `$lookup`, `allowDiskUse`](checks/04_aggregation.md) | hard | **PASS**      | Both real pipelines identical to raw PyMongo; correlated `$lookup` works |
| 05 | [One class, two databases](checks/05_multi_db.md)          | cost | **PASS WITH COST** | The obvious `switch_db` translation **misroutes across tenants**   |
| 06 | [`extra="allow"` round-trip](checks/06_extra_allow.md)     | cost | **PASS WITH COST** | Strict model + `replace()` **silently deletes** drift fields       |
| 07 | [Datetime storage shape](checks/07_datetime_shape.md)      | cost | **PASS**           | Beanie identical to MongoEngine; hazard is pre-existing            |
| 08 | [Sync + async, one collection](checks/08_coexistence.md)   | cost | **PASS**           | Coexistence works → incremental migration viable                   |

**Decision rule applied:** any hard-gate FAIL → NO-GO. None failed. → **GO.**

## What this proves

**FerretDB 2.5 is not the obstacle.** Every operation Beanie needs works, including the ones most likely to be
missing: a compound unique index that is actually enforced (not silently accepted), `findAndModify` with correct
BEFORE/AFTER and nested-`$set` semantics, and a **correlated `$lookup`** using `let`/`$expr`/`$in` over the same
collection. Both production pipelines return rows byte-identical to plain PyMongo.

**Incremental migration is structurally viable.** Two independent results support this, and it was not a given:

1. Beanie and MongoEngine write **identical document shapes** — same key set, no Beanie bookkeeping field, `_id` as a
   plain `ObjectId`, embedded documents as the same nested dicts.
2. A sync `MongoClient` and an `AsyncMongoClient` **coexist in one process on one collection**, each reading and
   updating the other's documents.

**The event-loop fix is real, and it is not a speed-up.** With a 10 ms ticker running: 200 blocking MongoEngine reads
produced **0 ticks** in 447 ms — total starvation — while 200 async Beanie reads produced **49 of ~52 expected** ticks.
But async was *slower* in wall-clock (524 ms vs 447 ms). The benefit is that other work can run at all, not throughput.
The ADR must not argue performance.

## What this does NOT prove

A GO verdict says: these operations worked, on these versions, with this data shape, at this scale, on this host. It
does not say Beanie works for this platform. Phase 1 measured **nothing** about:

- **Performance under load.** No concurrent RPC, no p99, no event-loop latency distribution. The timings above are
  contaminated — the full dev stack shared this FerretDB instance — and demonstrate a mechanism, not a rate. That is
  phase 3, on an uncontended environment.
- **The 139 `.objects(` call sites and 35 document classes.** Four stand-in models were used. Query-operator parity
  across the real surface is untested.
- **Test infrastructure.** `AsyncMongoClient` is loop-bound; `@async_test` runs `asyncio.run()` per BDD step, and
  `db_isolation` plus per-module `connect()/disconnect()` were not exercised at all. This remains a live risk to the
  whole option.
- **Sync contexts.** Dagster ops in `packages/pipeline` and parts of `packages/bot` cannot `await`. Untouched here.
- **Scale.** Six documents in the largest seed. Nothing approaches the 100 MB `$group` limit or the 33k-event staging
  figures the source comments cite.
- **Other FerretDB versions.** Findings are scoped to 2.5.0 exactly.
- **`use_revision`.** Not tested; enabling it would invalidate the check-02 shape equality.

## Findings that change the migration plan

Three results are not "Beanie works" — they are requirements the plan must carry.

### 1. `switch_db` has no safe mechanical translation (check 05)

Re-initialising a Document per call — the natural reading of `switch_db` — passed a sequential test 20/20 and then
**misrouted under concurrency**: a write intended for database A landed in database B. `init_beanie` mutates
process-wide class state, so any yield between binding and writing lets another task rebind underneath. Silent, no
exception. That is a **cross-tenant data-leak shape** on exactly the workload the API runs (one loop, many concurrent
requests, many tenant databases).

The safe approach is one initialised Document subclass per database. But our databases are not all known at startup —
knowledge databases are created at runtime — so it needs a **lazy registry** that builds and caches subclasses on
first sight. That is new code with its own concurrency requirements, and it did not exist in the MongoEngine version.
Affects `RefDoc`, `PersistedAgentEventEntity`, `PersistedProcessEventEntity`.

**The ADR must rule out the re-init approach in writing, with this evidence attached** — otherwise someone reaches for
it later because it reads as the obvious translation.

### 2. Every `strict: False` entity must declare `extra="allow"` (check 06)

A model without `extra="allow"`, written back with `replace()`, **silently deleted all undeclared fields**. The other
write paths survive for an incidental reason — `save()` uses `$set`-style semantics, so untouched fields persist —
which is a property of Beanie's implementation that no test of ours asserts. Affects `ThreadEntity`,
`PersistedAgentEventEntity`, `PersistedProcessEventEntity`, `UserDashboardEntity`.

Failure mode: silent, a deletion, and only on documents old enough to have drifted — precisely the ones absent from
test fixtures and present in long-running customer deployments.

### 3. Naive-local datetimes must be normalised *before* their entity is ported (check 07)

Beanie stores datetimes identically to MongoEngine, so this is **pre-existing and ODM-neutral**. But the migration is
what triggers it: a Pydantic-native port naturally reaches for `datetime.now(UTC)`, and the moment one writer uses
aware-UTC while another still uses naive-local in the same collection, `is_online` is wrong for half the rows.
Measured on this UTC+7 host: a freshly written aware-UTC timestamp reads as **7 hours old → OFFLINE** against a
5-minute threshold; the reverse error yields a **negative age** and reads ONLINE for a class dead for hours.

This sharpens the dependency on issue #1152 (migration framework): there is no mechanism to run the normalisation.

## Smaller findings worth carrying

- **Beanie 2.2.0 uses PyMongo's `AsyncMongoClient`, not Motor** (0 Motor references in the installed package). Motor is
  deprecated upstream, so this removes a standing objection.
- **`save_changes()` is opt-in** per Document via `use_state_management`. A port that forgets it fails at runtime, not
  at import — a per-entity checklist item, not something a reviewer catches in a diff. The flag adds no field to the
  stored document.
- **`allowDiskUse=True` is accepted but not proven honoured.** If FerretDB ignores it, the spend query works until a
  deployment crosses the 100 MB `$group` limit. **Not a regression** — MongoEngine passes the identical flag to the
  identical server today. Belongs in the ADR as a pre-existing FerretDB question.
- **`serverStatus` returns `{}` on FerretDB.** Connection-pool visibility is unavailable, so "did coexistence double
  our connections" cannot be answered by asking the server.

## Open questions carried into phase 3

1. Does the test infrastructure survive a loop-bound client? (`@async_test`'s per-step `asyncio.run()`, `db_isolation`,
   per-module `connect()/disconnect()`.) **Highest-risk open item** — it could still sink the option.
2. What is the p99 and timeout rate for the config RPC under concurrent load, across all three variants — raw
   MongoEngine, MongoEngine + `asyncio.to_thread`, Beanie — on an **uncontended** stack?
3. What do `packages/pipeline` (Dagster ops) and `packages/bot` do, given they cannot `await`?
4. How many collections hold naive-local datetimes? That count is the size of the migration implied by finding 3.
5. Does the lazy-registry approach to multi-DB routing actually work? Inferred from check 05 approach 1, **not built**.

## How to reproduce

1. Start the dev stack (FerretDB 2.5.0 + postgres-documentdb); confirm versions with
   [`probe_environment.py`](probe_environment.py).
2. `uv add beanie` in `packages/core` (on this branch only).
3. From the repo root, with `MONGO_*` loaded from `.env` and `PYTHONPATH=packages/core`, run each
   `checks/check_0N_*.py`.
4. Compare output against `logs/0N_*.log`. All checks write only to `aihub_beanie_spike` and
   `aihub_beanie_spike_tenant_b`, and drop their own collections first.

**Note on check 06:** an earlier run omitted the strict-model + `replace()` case and reported every path as "safe".
Both runs are preserved in the log. The gap was found only because `StrictDoc.save()` surviving was surprising enough
to question — a reminder that a clean table is not the same as a complete one.
