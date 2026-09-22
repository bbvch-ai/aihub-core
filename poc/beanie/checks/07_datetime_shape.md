# Check 07 — datetime storage shape

**Gate:** cost input — informs the ADR, does not kill the option\
**Verdict:** **PASS** — Beanie is byte-for-byte identical to MongoEngine here. The hazard is real but **pre-existing
and ODM-neutral**\
**Run:** 2026-09-22 · beanie 2.2.0 · mongoengine 0.29.3 · FerretDB 2.5.0 · host at **UTC+7** ·
[`../environment.md`](../environment.md)\
**Script:** [`check_07_datetime_shape.py`](check_07_datetime_shape.py) · **Raw output:**
[`../logs/07_datetime_shape.log`](../logs/07_datetime_shape.log)

## Question

What exactly is stored for a datetime today, what would Beanie store, and how far apart are they?

The codebase is already inconsistent with itself:

- `AgentClassEntity.last_discovered` defaults to **naive local** (`default=datetime.now`, `agent_class_entity.py:107`).
- `AgentConfigEntityDocument.created_at` defaults to **aware UTC** (`datetime.now(UTC)`,
  `agent_config_entity_document.py:28`).

`is_online` compares `datetime.now() - last_discovered < ONLINE_THRESHOLD` (`agent_class_entity.py:110`). The docstring
at `:257` states the consequence of getting the zone wrong: on a host ahead of UTC every dead class reads online, on a
host behind UTC nothing ever fires.

**This host is UTC+7**, so the check can actually see the discrepancy. On a UTC host it would have proven nothing.

## Raw output

```
== 0. the two values, in Python ==
  datetime.now()     -> datetime.datetime(2026, 9, 22, 13, 59, 26, 712182)
  datetime.now(UTC)  -> datetime.datetime(2026, 9, 22, 6, 59, 26, 712184, tzinfo=utc)
  difference         -> 7.0h

== 3. raw BSON, read with a plain PyMongo client ==
  beanie_aware_utc           datetime.datetime(2026, 9, 22, 6, 59, 26, 712000)  tzinfo=None
  beanie_naive_local         datetime.datetime(2026, 9, 22, 13, 59, 26, 712000) tzinfo=None
  mongoengine_aware_utc      datetime.datetime(2026, 9, 22, 6, 59, 26, 712000)  tzinfo=None
  mongoengine_naive_local    datetime.datetime(2026, 9, 22, 13, 59, 26, 712000) tzinfo=None

== 6. the is_online comparison, as agent_class_entity.py:110 performs it ==
  beanie_naive_local         age=0:00:00.148751   ONLINE (correct)
  beanie_aware_utc           age=7:00:00.148813   OFFLINE (WRONG)
  mongoengine_naive_local    age=0:00:00.148855   ONLINE (correct)
  mongoengine_aware_utc      age=7:00:00.148891   OFFLINE (WRONG)

== 7. and the reverse error: comparing against an aware UTC now ==
  beanie_naive_local         age=-1 day, 17:00:00  ONLINE
  mongoengine_naive_local    age=-1 day, 17:00:00  ONLINE
```

Full output in [`../logs/07_datetime_shape.log`](../logs/07_datetime_shape.log).

## Interpretation

**Beanie stores datetimes exactly as MongoEngine does.** A naive-local value is written as its wall-clock reading
(13:59) — BSON carries no zone, so it is stored *as if* it were UTC. An aware-UTC value is written as 06:59. The four
stored values are identical across the two ODMs, field for field. **Beanie neither introduces nor fixes this problem.**

Both ODMs also return **naive** datetimes on read (`tzinfo=None`), because the client is not `tz_aware`. Beanie does
not re-attach UTC — a Pydantic `datetime` field accepts what PyMongo hands it. The same documents read through a
`tz_aware=True` client come back labelled UTC, including the naive-local one, which is the clearest statement of the
problem: **the database cannot tell the two conventions apart.** `13:59` is stored as "13:59 UTC" whether or not that
is what anyone meant.

The consequences are quantified rather than argued:

- A **freshly written** aware-UTC timestamp, read by the naive-local comparison, computes an age of **7 hours** and is
  classified **OFFLINE** against a 5-minute threshold. A live agent class would read as dead.
- The reverse error computes a **negative** age (`-1 day, 17:00:00`) and reads **ONLINE**. A class dead for hours would
  read as alive — and, per the source docstring, runs would fire into NATS with no consumer and vanish.

## What this means for the migration

This is a **pre-existing data hazard, not a Beanie cost**, and the ADR should classify it that way. But it is the
migration that would trigger it, for a specific reason: a Pydantic-native port naturally reaches for
`default_factory=lambda: datetime.now(UTC)` — as `AgentConfigEntityDocument` already does — and the moment one process
writes aware-UTC into `agent_classes` while another still writes naive-local, the collection holds both conventions and
`is_online` is wrong for half its rows.

So the sequencing requirement is concrete: **normalise the naive-local columns to UTC before, or as part of, porting
the entity that owns them** — never after. That is a data migration with no framework to run it (issue #1152), which
makes the dependency between the two issues sharper than "worth sequencing".

## Recorded beyond pass/fail

- The stored values are **identical** across ODMs for both input conventions — no conversion is applied by either.
- Neither ODM returns aware datetimes by default; `tz_aware=True` on the client is what changes that, and it would
  change it for *all* reads at once, which is itself a breaking change for any code doing naive arithmetic.
- Sub-millisecond precision is truncated by BSON (`712182` → `712000`) identically for both. Not relevant to a
  5-minute threshold, but recorded for anything relying on microseconds.

## Caveats

- One host, one offset (+7). Behaviour at a negative offset is inferred from the arithmetic, not measured.
- No DST transition was exercised. A host in a DST-observing zone has a second, seasonal source of the same error;
  UTC+7 does not observe DST.
- The `is_online` logic was reproduced in the check rather than imported from `AgentClassEntity`, so this tests the
  comparison shape, not that exact code path.
- How many collections hold naive-local datetimes was **not** inventoried here. That count is the size of the
  migration and still needs doing.
