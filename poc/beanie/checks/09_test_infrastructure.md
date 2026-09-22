# Check 09 — does Beanie survive this repo's test infrastructure?

**Phase:** 3, step 1 — run first as a gate, because it could still kill the option and costs a day\
**Gate:** hard for the migration's feasibility, not for FerretDB compatibility\
**Verdict:** **PASS WITH COST** — no blocker, but a suite-wide change that cannot be adopted incrementally\
**Run:** 2026-09-22 · beanie 2.2.0 · pytest 9.0.3 · pytest-asyncio 1.3.0 · [`../environment.md`](../environment.md)\
**Scripts:** [`check_09_test_infrastructure.py`](check_09_test_infrastructure.py) ·
[`check_09b_loop_scope_mitigation.py`](check_09b_loop_scope_mitigation.py) · **Raw output:**
[`../logs/09_test_infrastructure.log`](../logs/09_test_infrastructure.log)

## Question

`AsyncMongoClient` is loop-bound. Three patterns in this repo treat the event loop differently — do any of them
survive?

| Pattern                | Uses | Loop behaviour                                                              |
| ---------------------- | ---- | --------------------------------------------------------------------------- |
| `@pytest.mark.asyncio` | 913  | No `asyncio_mode` configured anywhere → strict, **a fresh loop per test**   |
| `@async_test`          | 183  | Wraps each step in `asyncio.run()` → **a new loop per BDD step**            |
| `db_isolation`         | all  | Session-autouse fixture, **sync** `MongoClient`, drops the test DB          |

## Raw output

```
[A]  reuse across asyncio.run() boundaries -> RuntimeError: Cannot use AsyncMongoClient in different
     event loop. AsyncMongoClient uses low-level asyncio APIs that bind it to the event loop it was created on.
[A2] re-init inside every asyncio.run() -> OK; 5 steps, 46 ms each
[B1] first test, module-scoped client -> RuntimeError: Cannot use AsyncMongoClient in different event loop.
[B2] second test, SAME module-scoped client, new loop -> RuntimeError: (same)
[B3] per-test init -> OK; 46 ms
[C]  sync drop_database (the db_isolation mechanism) -> OK
[D]  Document class still holds a collection handle after its loop closed: True
     handle: AsyncCollection
```

Mitigation probe (09b):

```
[E1] session-scoped loop + session-scoped client, test 1 -> OK      loop id: 1513267287760
[E2] session-scoped loop + session-scoped client, test 2 -> OK      loop id: 1513267287760  (same loop)
[E3] DEFAULT per-test loop + session-scoped client -> RuntimeError  loop id: 1513267297680  (mismatch)
[E4] asyncio.run() (the @async_test shape) against the session client -> RuntimeError
```

Full output in [`../logs/09_test_infrastructure.log`](../logs/09_test_infrastructure.log).

## Interpretation

**The naive patterns all fail, and one fails worse than predicted.** `[B1]` breaks on the *first* test, not the
second: the module-scoped fixture ran `init_beanie` inside its own `asyncio.run()`, which closed immediately, so every
test using that fixture already holds a client bound to a dead loop. There is no grace period.

**`[D]` confirms the same root cause as [check 05](05_multi_db.md):** `init_beanie` mutates process-wide class state.
After the loop that created it has closed, the Document class still holds an `AsyncCollection` handle pointing at it.
Nothing invalidates it; the next loop just gets a `RuntimeError`. One mechanism, two symptoms — cross-tenant misrouting
in production, dead-loop clients in tests.

**`db_isolation` is unaffected** (`[C]`). It drops the test database with a synchronous client, which has no loop
affinity. The one piece of shared test infrastructure that could have been expensive is free.

### The mitigation works, but it is all-or-nothing

Widening pytest-asyncio's loop scope to `session` and making the client session-scoped **does work** (`[E1]`, `[E2]` —
same loop id, both inserts fine). But `[E3]` is the finding that matters: a test left on the **default** per-test loop,
using that same session client, still fails. **The two scopes cannot be mixed**, so this is not a change that can be
rolled out file by file — all 913 `@pytest.mark.asyncio` tests move together or none do.

And widening the loop scope is a real trade, not a free win: tests stop getting a clean loop each, so state leaks
between them by design. That applies to **all** 913 tests, including the large majority that never touch Mongo and
gain nothing from the change.

### `@async_test` cannot be rescued by loop scope at all

`[E4]`: `asyncio.run()` always creates its own loop, so a session-scoped client is unreachable from it *by
construction*. The 183 `@async_test` uses therefore need one of:

- **Per-step re-init** — works (`[A2]`), 46 ms per step. Across 183 uses that is ≈8 s of added suite time, which is
  affordable. But every BDD step that touches Mongo needs the init added, and a step that forgets it fails at runtime
  with a `RuntimeError`, not at import.
- **Rewrite `@async_test`** to run on a shared loop (`loop.run_until_complete`) instead of `asyncio.run()`. This is a
  change to **one function** in `packages/core/swiss_ai_hub/core/testing/asyncio_utils/bdd.py:11` and is the cheaper
  fix by far. It changes isolation semantics for 183 tests — though for steps *within one BDD scenario*, sharing a loop
  is arguably more faithful to what a scenario represents than tearing the loop down between steps.

## What this means for the decision

This does **not** kill the Beanie option — which is what the gate was asking. But it adds a cost that was not in the
issue's framing and that no amount of entity-by-entity care avoids: **the test suite conversion is not incremental.**
A migration plan that ports entities one at a time still needs the loop-scope change landed in one piece, up front,
before the first entity moves.

The ADR should carry this as its own line item with a size, not as a footnote. The three components are: a one-line
config change (`asyncio_default_fixture_loop_scope`/per-test markers across 913 tests), a one-function rewrite of
`@async_test`, and the loss of per-test loop isolation across the whole suite.

## Recorded beyond pass/fail

- Per-init cost is **46 ms**, consistent across both patterns (`[A2]`, `[B3]`). For reference,
  [check 01](01_init_beanie.md) measured a cold `init_beanie` at 103 ms and a warm one at 9 ms for a single model
  against an existing collection; the 46 ms here includes constructing a fresh `AsyncMongoClient` each time.
- The error is always the same and is explicit rather than silent: `Cannot use AsyncMongoClient in different event
  loop`. Unlike [check 06](06_extra_allow.md)'s data loss, this failure is loud — a test that gets it wrong fails,
  it does not quietly pass.
- `pytest-asyncio` is **1.3.0**, which supports `loop_scope` on both `@pytest.mark.asyncio` and
  `@pytest_asyncio.fixture`. An older version would not have had this mitigation at all.

## Caveats

- **The rewrite of `@async_test` was not built or tested** — only identified. Its feasibility is inferred from
  `[E1]`/`[E2]` working, not demonstrated. It should be built before the ADR claims it as the cheap path.
- The 913 and 183 figures are raw occurrence counts, not counts of tests that touch Mongo. The number needing the
  per-test init is smaller and was **not** inventoried; the loop-scope change, being all-or-nothing, applies to all 913
  regardless.
- Session-scoped loops were tested with four tests in one file. Whether a full suite run stays stable on one shared
  loop — ordering, leakage, teardown — is a different question and untested.
- No parallel runner (`pytest-xdist`) was involved. If the suite ever runs distributed, loop scoping interacts with
  worker processes in ways not examined here.
