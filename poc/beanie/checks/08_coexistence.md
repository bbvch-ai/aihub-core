# Check 08 — sync and async clients on one collection

**Gate:** cost input — informs the ADR, does not kill the option\
**Verdict:** **PASS** — coexistence works, so incremental migration is viable\
**Run:** 2026-09-22 · beanie 2.2.0 · mongoengine 0.29.3 · FerretDB 2.5.0 ·
[`../environment.md`](../environment.md)\
**Script:** [`check_08_coexistence.py`](check_08_coexistence.py) · **Raw output:**
[`../logs/08_coexistence.log`](../logs/08_coexistence.log)

## Question

Can a synchronous `MongoClient` (MongoEngine) and an `AsyncMongoClient` (Beanie) operate on the same collection in the
same process?

This decides the migration **shape**, not whether Beanie works. If the two cannot coexist, incremental migration is off
the table and only big-bang across 22 `Document` + 13 `EmbeddedDocument` classes and 139 `.objects(` call sites
remains — a materially riskier proposition.

The check also probes the thing the migration is meant to fix, so that it is measured rather than asserted: during
coexistence, the un-migrated half still blocks the event loop.

## Raw output

```
== 1. interleaved writes, read by the other side ==
  Beanie reads MongoEngine's doc      : b value=2
  MongoEngine reads Beanie's doc      : a value=1

== 2. write by one, update by the other, read back by the first ==
  Beanie doc updated by MongoEngine   : value=99 (expect 99)

== 3. connection counts ==
  server reports: {}

== 4. does the SYNC half still block the event loop? ==
  ticks in a free 200ms window                 : 13
  200 blocking MongoEngine reads took          : 447ms
  ticks during that window                     : 0 (expect ~44 if the loop were free)
  200 async Beanie reads took                  : 524ms
  ticks during that window                     : 49 (expect ~52 if the loop stayed free)
```

Full output in [`../logs/08_coexistence.log`](../logs/08_coexistence.log).

## Interpretation

**Coexistence works.** Both clients hold the same collection open in one process; each reads documents written by the
other, and an update applied through MongoEngine is visible to Beanie on re-read. Nothing had to be coordinated between
them. **Incremental, entity-by-entity migration is therefore viable** — which, combined with the identical on-disk
shape from [check 02](02_basic_crud.md), is the strongest structural result of this phase.

**The loop-starvation mechanism is demonstrated, not argued.** A background task ticking every 10 ms recorded:

- **0 ticks** during 447 ms of blocking MongoEngine reads. The loop was not merely slowed, it was completely starved —
  nothing else ran for the whole window. This is exactly the failure described in issue #1634: while a query is in
  flight, the API answers no HTTP request, delivers no WebSocket frame and dispatches no NATS callback.
- **49 ticks** during 524 ms of async Beanie reads, against ~52 expected. The loop stayed alive throughout.

**An honest note on the timings: async was not faster.** 200 sequential Beanie reads took 524 ms against 447 ms for
MongoEngine. Sequential `await`s do not overlap, so per-operation there is nothing to gain — and a small overhead to
pay. The benefit is not throughput, it is that **other work can run at all**. Any argument for the migration that
leans on "it will be faster" is not supported by this evidence, and the ADR should avoid making it.

## Recorded beyond pass/fail

- Two connection pools against one database caused no observable problem at this scale.
- **`serverStatus` returns `{}` on FerretDB** — the connection-count reporting a real MongoDB provides is not
  implemented. Minor, but worth knowing: operational visibility into pool usage is not available here, so "did we
  double the connections" cannot be answered by asking the server.
- MongoEngine's global connection registry and Beanie's `init_beanie` coexisted in one process without conflict.

## Caveats

- **The timings are contaminated and are not the phase-3 measurement.** The full dev stack was running against the same
  FerretDB instance. They demonstrate a mechanism (starved vs alive), not a rate. Phase 3 needs an uncontended
  environment and its own environment section.
- The tick-based probe measures loop availability coarsely. It shows starvation clearly; it does not quantify latency
  distribution, which is what the phase-3 p99 figure is for.
- One collection, one process, one worker. Nothing here covers multiple API workers, or a pool exhausted by
  concurrency.
- Coexistence was tested on a simple document. Entities with embedded documents, or the `strict: False` ones from
  [check 06](06_extra_allow.md), could still interact badly — and the check-06 result means a coexisting pair must
  agree on extra-field handling, or one side's write path can delete what the other preserves.
