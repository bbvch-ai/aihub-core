# Phase 3 report — evaluation

**Verdict: `to_thread` holds. On this evidence, Beanie is not justified — recommend NOT migrating.**

**Run:** 2026-09-22 · `poc/beanie-spike` · beanie 2.2.0 · FerretDB 2.5.0 + NATS 2.11.4 **only** (rest of the dev stack
stopped for check 10) · 20-core Windows host at UTC+7\
**Environment:** [`environment.md`](environment.md) · **Raw output:** [`logs/`](logs/)

## Result table

| #  | Check                                                    | Verdict                                             |
| -- | -------------------------------------------------------- | --------------------------------------------------- |
| 09 | [Test infrastructure](checks/09_test_infrastructure.md)  | **PASS WITH COST** — suite conversion is not incremental |
| 10 | [Load measurement](checks/10_load.md)                    | **`to_thread` holds** — Beanie not justified on performance |
| 11 | [Sync contexts](checks/11_sync_contexts.md)              | **PASS** — the concern evaporates; pipeline has no MongoEngine |
| 12 | [Datetime inventory](checks/12_datetime_inventory.md)    | **PASS** — 5 fields in 3 collections                |

## The decision, against the pre-registered criteria

Check 10's verdict table was written **before** the first measurement. The result is row 1:

> `to_thread` shows no timeouts at ≥ 3× peak concurrency, at production pool width → **Beanie is not justified on this
> evidence. Recommend not migrating.**

The numbers, at a 100% blocking duty cycle — the pathological case no real API sustains:

| Variant          | pool | conc | p50 ms | p99 ms | timeouts |
| ---------------- | ---- | ---- | ------ | ------ | -------- |
| `to_thread_full` | 6    | 400  | 221    | 396    | 0        |
| `beanie`         | 6    | 400  | 267    | 401    | 0        |
| `to_thread_full` | 2    | 800  | 974    | 1536   | 0        |
| `beanie`         | 2    | 800  | 582    | 885    | 0        |

`to_thread_full` and `beanie` are indistinguishable up to 400 concurrent config RPCs at a production container's pool
width. A gap opens only at a 2-thread pool with 800 concurrent requests — where Beanie is ~1.7× better and **neither
times out**, both remaining far under the 5 s budget. Config RPCs fire once per agent run start, so 800 concurrent
means 800 runs beginning in the same instant against a 1-core container.

Combined with check 08's finding that Beanie is **slower** per operation (524 ms vs 447 ms for 200 sequential reads),
there is no performance case to make.

## What phase 3 adds that phase 1 could not

**The harness had to be rebuilt once, and the control caught it.** The first attempt saturated the loop with ~400 small
writes/second. Every variant passed, including `raw` — the pre-registered "the harness is wrong" outcome. The source
comment at `persisted_agent_event_entity.py:584` names the real culprit: *"a 123s cold read of 30 days off disk"*. The
starver is one slow read, not many fast writes. Rebuilt around the real spend-aggregation shape over 50 000 documents,
the control behaves: `raw` runs at a p50 of 3425 ms against tens of milliseconds for the off-loop variants.

**Partial `to_thread` can be worse than none.** `to_thread_part` — production today, two call sites fixed and ~137
still blocking — measured *worse* than `raw` under a saturated loop (4085 ms vs 3425 ms p50). The diagnostic explains
it: both wait ~1 s for the loop, but `to_thread` needs a **second loop slice** to resume after the worker thread
finishes, and on a contended loop that costs another blocking cycle. The effect disappears at `gap≥0.25`, so it needs a
continuously blocked loop — but the strategic reading holds: **the benefit comes from freeing the loop, not from
wrapping one handler.** That argues against "patch only the hot sites" as an end state. It does not argue against the
interim fix, which was always framed as buying time.

**The sync-context worry was based on a false premise.** `packages/pipeline` holds **zero** MongoEngine entities: its
two `Document` classes are LlamaIndex's, its `connect_to_mongo_db` is dead code, and its document store runs on
LlamaIndex's `MongoDocumentStore` over raw PyMongo. `packages/bot` has seven production call sites and is already a
FastAPI service. No Bunnet, no permanent two-ODM split.

**The datetime migration is small.** Five fields in three collections, not a programme. One of them
(`ThreadEntity.created_at`) has no field default and is naive only because of two assignment sites — a trap for any
migration written from a scan of defaults.

## Corrections to phase 1

| Figure                | Phase 1 said                | Correct                                           |
| --------------------- | --------------------------- | ------------------------------------------------- |
| Entity split          | 22 Document + 13 Embedded   | **20 Document-like + 15 Embedded** (35 total, unchanged) |
| Packages with entities| core / api / bot / pipeline | **core (28) + bot (7) only**                      |
| `packages/pipeline`   | 2 entities                  | **0** — both are LlamaIndex `Document` subclasses  |

The phase-1 count matched `^class X(Document)` without checking which `Document` was imported.

## The case for migrating, stated fairly

Nothing here says Beanie is bad. It passed every compatibility gate in phase 1, is Pydantic-native (convention #2),
uses PyMongo's supported async driver rather than deprecated Motor, and produces byte-identical documents. At the
extreme operating point it is measurably better. If the platform's concurrency profile changes by two orders of
magnitude, this measurement should be re-run.

What the evidence does not support is migrating **now, for performance**. The cost side is concrete: a non-incremental
test-suite conversion (check 09), a lazy per-database registry to replace `switch_db` whose absence silently misroutes
across tenants (check 05), `extra="allow"` mandatory on four entities or `replace()` deletes drift data (check 06), and
a datetime normalisation with no framework to run it (check 12, issue #1152).

## What this does NOT prove

- **Not a production prediction.** A 20-core Windows dev box, single-node FerretDB, a synthetic saturator, no LLM
  traffic, no agent runners, no WebSocket fan-out, one API worker. It shows the *shape* of each curve, not absolute
  latency.
- **The 123 s incident was not reproduced.** The saturator blocks ~0.5 s per pass. A single 123 s blocking call starves
  the loop for 123 s under every variant that still has one — which is why the real fix is removing blocking calls by
  any means, not choosing an ODM.
- **No cold-cache measurement.** The corpus was warm; the incident was cold.
- **Only the config RPC path.** HTTP endpoint latency, WebSocket delivery and event-persistence throughput unmeasured.
- **Checks 11 and 12 are static analysis.** Nothing was executed; reflective or indirect usage would not appear.
- **The `@async_test` rewrite (check 09) was identified, not built.** The ADR must not price it as cheap until someone
  builds it.

## Recommendation for the ADR

1. **Do not migrate now.** Record Beanie as evaluated, viable and rejected on cost-versus-benefit — not as unsuitable.
2. **Finish the `to_thread` work instead**, driven by measurement rather than by wrapping everything: `to_thread_full`
   matched Beanie everywhere it was tested, and partial adoption is the configuration that measured worst.
3. **Set a revisit trigger** rather than leaving it open: re-run check 10 if concurrent agent-run starts rise by an
   order of magnitude, or if the API moves to a container with fewer cores.
4. **Keep the findings that stand alone**, independent of the ODM decision: the `NCRequester` no-retry gap, the
   datetime normalisation (5 fields), and the `is_online` 5-minute-window fragility.
5. **Drop** the planned follow-up issue for a pipeline/bot sync-context strategy — check 11 shows there is nothing to
   decide.
