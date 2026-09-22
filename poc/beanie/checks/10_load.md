# Check 10 — the load measurement that decides the ADR

**Phase:** 3, step 2\
**Verdict:** **`to_thread` holds. Beanie is not justified on performance grounds.**\
**Run:** 2026-09-22 · beanie 2.2.0 · FerretDB 2.5.0 + NATS 2.11.4 **only** (rest of the dev stack stopped) ·
20-core Windows host · [`../environment.md`](../environment.md)\
**Script:** [`check_10_load.py`](check_10_load.py) · **Raw output:** [`../logs/10_load.log`](../logs/10_load.log)

## Question, pre-registered before the first measurement

Check 08 already showed Beanie is **not faster** (524 ms vs 447 ms for 200 sequential reads), so throughput was never
the question. The question was:

> At what concurrency does `asyncio.to_thread` stop holding the line, and is that above or below our real load?

`to_thread` does not remove blocking, it relocates it into a bounded pool (`min(32, cpu_count + 4)`; nothing in this
repo configures it — a 2-core container gets 6 workers, this host gets 24). Past the pool width, work queues and the
5 s `NCRequester` budget comes back into play.

### The pre-registered verdict table

| Outcome                                                                               | Reading                                                    |
| ------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| `to_thread` shows no timeouts at ≥ 3× peak concurrency, at production pool width      | **Beanie not justified. Recommend not migrating.**         |
| `to_thread` degrades at or below peak, and a wider executor does not fix it            | Beanie justified. Recommend migrating.                     |
| `to_thread` degrades but a wider executor fixes it                                     | Configure the executor, do not migrate.                    |
| Raw MongoEngine and `to_thread` are indistinguishable                                  | **The harness is wrong.** Fix it before drawing anything.  |

## Four variants, because the shipped fix is partial

| Variant          | Responder | Saturator | Models                                                  |
| ---------------- | --------- | --------- | ------------------------------------------------------- |
| `raw`            | blocks    | blocks    | before the interim fix                                  |
| `to_thread_part` | off-loop  | blocks    | **today** — the fix touched 2 call sites; ~137 still block |
| `to_thread_full` | off-loop  | off-loop  | the "keep patching" end state                           |
| `beanie`         | async     | async     | the migration end state                                 |

`to_thread_full` vs `beanie` is the decision. `raw` is the control.

## The first harness was wrong, and the control caught it

The first attempt saturated the loop with ~400 small writes/second, standing in for `EventPersister`. **Every variant
passed**, including `raw` — the pre-registered "harness is wrong" outcome. Many small writes do not starve a loop.

The source comment at `persisted_agent_event_entity.py:584` names the real culprit:

> It is not what took the event loop down, though — that was a 123s cold read of 30 days off disk, which no pipeline
> shape avoids and only the threadpool hand-off contains.

The starver is **one slow read**, not many fast writes. The saturator was rebuilt around the real spend-aggregation
shape over a seeded 50 000-document corpus (one pass ≈ 512–570 ms), run repeatedly, with a `gap` parameter as the
contention dial.

## Results

**Contention sweep, default pool (24 workers).** `gap` = idle seconds between saturator passes; `gap=0` is a 100%
blocking duty cycle, which no real API sustains.

| variant          | gap  | conc | p50 ms   | p99 ms   | timeouts |
| ---------------- | ---- | ---- | -------- | -------- | -------- |
| `raw`            | 0.00 | 50   | **3425** | **3425** | 0        |
| `to_thread_part` | 0.00 | 50   | **4085** | **4085** | 0        |
| `to_thread_full` | 0.00 | 50   | 57       | 74       | 0        |
| `beanie`         | 0.00 | 50   | 62       | 82       | 0        |
| `raw`            | 0.25 | 50   | 161      | 162      | 0        |
| `to_thread_full` | 0.25 | 50   | 55       | 71       | 0        |
| `beanie`         | 0.25 | 50   | 43       | 61       | 0        |

**Pool width and concurrency sweep**, `gap=0`:

| variant          | pool | conc | p50 ms | p99 ms | timeouts |
| ---------------- | ---- | ---- | ------ | ------ | -------- |
| `to_thread_full` | 6    | 400  | 221    | 396    | 0        |
| `beanie`         | 6    | 400  | 267    | 401    | 0        |
| `to_thread_full` | 2    | 800  | 974    | 1536   | 0        |
| `beanie`         | 2    | 800  | 582    | 885    | 0        |

Full matrix in [`../logs/10_load.log`](../logs/10_load.log).

## Interpretation

**The harness reproduces the symptom.** `raw` at a saturated loop runs at a p50 of **3425 ms** against a 5 s budget,
versus tens of milliseconds when the loop is free — an 80× difference. The control passes, so the rest can be read.

**`to_thread_full` and `beanie` are equivalent across the entire realistic range.** At the default pool they sit within
noise of each other (57 vs 62 ms p50 at 50 concurrent). At a production container's pool width of 6 they are still
indistinguishable at 400 concurrent (221 vs 267 ms p50, 396 vs 401 ms p99). **No variant timed out anywhere in this
matrix.**

**The thread-pool knee exists but is at an unreachable operating point.** Only at a 2-thread pool with 800 concurrent
config RPCs and a 100% blocking duty cycle does a gap open: 974 ms vs 582 ms p50, Beanie ~1.7× better. Both remain far
under the 5 s budget. For scale: config RPCs fire **once per agent run start**, so 800 concurrent means 800 agent runs
beginning in the same instant against a 1-core container.

Measured against the pre-registered table, this is row 1: **no timeouts at far beyond 3× any realistic peak, at
production pool width. Beanie is not justified on performance grounds.**

### The finding I did not expect: partial `to_thread` is *worse* than none

`to_thread_part` — which is **production today** — is consistently worse than `raw` under a saturated loop: 4085 ms vs
3425 ms p50. The diagnostic explains it:

```
raw        queued 1071 ms (waiting for the loop) + lookup  35 ms
to_thread  queued 1014 ms (same wait)            + lookup 516 ms
```

Both wait the same time for the loop. The difference comes *after* the handler is entered: `to_thread` needs a
**second loop slice** to resume once the worker thread finishes, and on a contended loop that second slice costs
another blocking cycle. A blocking call needs one slice; the off-loaded one needs two.

This is a real mechanism, not an artifact — but note its condition. At `gap=0.25` and `gap=1.0` the effect disappears
(`to_thread_part` matches or beats `raw`), leaving only intermittent p95 spikes of 586–702 ms at `gap=1.0`. It requires
a **continuously** blocked loop.

The consequence for strategy is the useful part: **wrapping a few hot call sites while leaving the rest blocking does
not simply help less — under heavy contention it can hurt.** The benefit arrives when the *loop* is freed, not when one
handler is. That argues against "patch only the sites that hurt" as an end state, and for either finishing the job or
migrating. It does not argue against the interim fix, which was always framed as buying time.

## What this does NOT prove

- **Not a production prediction.** A 20-core Windows dev box, single-node FerretDB, a synthetic saturator, no LLM
  traffic, no agent runners, no WebSocket fan-out, one API worker. It shows the *shape* of each variant's curve, not
  absolute latency.
- **The 123 s incident was not reproduced.** The saturator blocks for ~0.5 s per pass. A single 123 s blocking call
  starves the loop for 123 s under **every** variant that still has one — which is precisely why the real fix is
  removing blocking calls, by any means, rather than choosing an ODM.
- **No cold-cache measurement.** The corpus was warm. The source comment attributes the incident to a *cold* read.
- **Only the config RPC path.** HTTP endpoint latency, WebSocket delivery and event persistence throughput were not
  measured.
- **`to_thread_part` is a model of today, not today.** It uses one blocking saturator; production has ~137 unfixed
  call sites of varying cost.

## Caveats

- `gap=0` is pathological. No real API blocks its loop 100% of the time. The realistic rows are `gap=0.25` and
  `gap=1.0`, where every variant is comfortable.
- Latencies are medians of 3 runs. Spread within a run is not reported beyond p95/p99.
- The `passes` column shows the saturator completing 9–12 aggregations per window under `raw`/`to_thread_part` but only
  3–4 under `to_thread_full`/`beanie` — the off-loaded variants trade saturator throughput for responsiveness. Not
  analysed further; it does not affect the verdict, but it means the variants were not doing identical total work.
- Thread-pool width was pinned with `set_default_executor`. Production sets nothing, so the real width is whatever
  `cpu_count + 4` yields in the container.
