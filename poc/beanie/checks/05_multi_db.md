# Check 05 — one Document class against two databases

**Gate:** cost input — informs the ADR, does not kill the option\
**Verdict:** **PASS WITH COST** — a safe approach exists, and the obvious translation of `switch_db` is **unsafe**\
**Run:** 2026-09-22 · beanie 2.2.0 · FerretDB 2.5.0 · [`../environment.md`](../environment.md)\
**Script:** [`check_05_multi_db.py`](check_05_multi_db.py) · **Raw output:**
[`../logs/05_multi_db.log`](../logs/05_multi_db.log)

## Question

How does Beanie express what MongoEngine's `switch_db` does for us, and what does that cost?

Beanie binds a Document class to one database at `init_beanie` time. We retarget at **call** time:

- `persisted_agent_event_entity.py:177` and `persisted_process_event_entity.py:46` — `persisted_entity.switch_db(db)`
  before saving.
- `ref_doc.py:17`, `:192`, `:366` — `with switch_db(RefDoc, DB_ALIAS) as SwitchedRefDoc`.

Event persistence and RAG document storage both depend on it, so this is not incidental.

## What was run

The three candidate approaches from the plan, each writing to two databases, plus a concurrency probe on the one that
looked most like a drop-in replacement.

## Raw output

```
== approach 1: one initialised Document subclass per database ==
  db A contains: ['in-a']
  db B contains: ['in-b']
  isolated correctly: True

== approach 2: one class, route by dropping to the raw collection ==
  wrote to db B via raw collection: raw-to-b
  read back and rehydrated: raw-to-b payload={'db': 'B'}
  leaked into db A: False

== approach 3: re-init the Document per call ==
  20 routed writes via re-init: 0.202s (10.1 ms/write)
  landed in A: 10, in B: 10 (expect 10 / 10)

== approach 3 under concurrency: two routed writes on one event loop ==
  race-to-a: intended=aihub_beanie_spike landed=aihub_beanie_spike_tenant_b -> MISROUTED
  race-to-b: intended=aihub_beanie_spike_tenant_b landed=aihub_beanie_spike_tenant_b -> OK
```

Full output in [`../logs/05_multi_db.log`](../logs/05_multi_db.log).

## Interpretation

**The headline result is the concurrency probe.** Approach 3 — re-initialise the Document against the target database
before each call, which is the mechanical translation of `switch_db` — works perfectly in a sequential loop (20/20
writes landed in the right database) and then **silently misroutes** the moment two routed writes interleave on one
event loop. `race-to-a` was written into tenant B's database.

That is not a performance problem, it is a **cross-tenant data-leak shape**, and it is exactly the condition the API
runs under: one event loop, many concurrent requests, many tenant databases. `init_beanie` mutates process-wide class
state, so any yield between binding and writing lets another task rebind underneath. The failure is silent — no
exception, no warning, the write simply lands in the wrong place.

It matters that this was reproduced rather than reasoned about: sequential testing gives it a clean bill of health, so
a port that only ran unit tests would ship it.

**Approach 1 is correct and cheap.** A separate Document subclass per database, each initialised once, isolates
correctly. The cost is structural rather than per-call: one subclass and one `init_beanie` per database.

**Approach 2 is correct but gives up the ODM.** Routing by dropping to the raw PyMongo collection works and does not
leak, but the write goes out with a hand-rolled `model_dump` and comes back through a hand-rolled `model_validate` —
no Beanie validation on write, no event hooks, no typed query API. Entities routed this way would gain essentially
nothing from the migration beyond the async driver.

## What this means for the migration plan

The affected entities — `RefDoc`, `PersistedAgentEventEntity`, `PersistedProcessEventEntity` — cannot be ported by
mechanically replacing `switch_db`. Each needs an explicit routing design, and the ADR should say so rather than
leaving it as an implementation detail:

- Approach 1 requires the set of databases to be **known when the process initialises**. Ours is not fully: knowledge
  databases are created at runtime. So it needs extending into a **lazy registry** — build and cache an initialised
  subclass the first time a database is seen. That registry is new code with its own concurrency requirements, and it
  did not exist in the MongoEngine version.
- Approach 3 must be explicitly ruled out in writing, with this evidence attached, or someone will reach for it later
  because it reads as the natural translation.

## Recorded beyond pass/fail

- Approach 3 sequential throughput: 10.1 ms per routed write, dominated by the re-init round-trip. Even if it were
  safe, that is a poor per-write cost for the event-persistence path, which writes every agent event.
- Approach 2's round-trip preserved the payload exactly (`payload={'db': 'B'}` came back intact) and did not leak into
  the other database.

## Caveats

- Two databases, one collection, one process. Real deployments have many tenant databases and multiple API workers.
- The concurrency probe used an explicit `await asyncio.sleep(0.01)` between binding and writing to make the race
  deterministic. A real interleaving depends on where the event loop happens to yield — which makes the bug
  *intermittent* in production, not absent. The probe demonstrates the mechanism; it does not measure how often it
  would fire.
- The lazy-registry extension of approach 1 was **not built or tested here**. Its feasibility is inferred from
  approach 1 working, not demonstrated.
- No test of what happens when a database is dropped or recreated underneath an initialised subclass.
