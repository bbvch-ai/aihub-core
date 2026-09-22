# Check 07 — datetime storage shape

**Gate:** cost input — informs the ADR, does not kill the option\
**Verdict:** not run\
**Environment:** see [`../environment.md`](../environment.md)

## Question

What exactly is stored for a datetime today, what would Beanie store, and how far apart are they?

This check sizes a data migration, and the codebase is already inconsistent with itself — which is the point:

- `AgentClassEntity.last_discovered` defaults to **naive local time** (`default=datetime.now`,
  `.../agents/agent_class_entity.py:107`). The class documents why this matters at `:257`: comparing it against an
  aware UTC `now` misclassifies every agent class by the host's UTC offset — on a host ahead of UTC every dead class
  reads online, on a host behind UTC nothing fires.
- `AgentConfigEntityDocument.created_at` / `updated_at` default to **aware UTC** (`datetime.now(UTC)`,
  `.../agents/agent_config_entity_document.py:28`).

A Pydantic-native ODM will normalise toward aware UTC. During any coexistence window, mixed rows in one collection are
the failure mode — and `is_online` is exactly the comparison that breaks.

## What to run

Write the same logical timestamp through MongoEngine (both the naive and the aware entity) and through Beanie, then
read the raw BSON with a plain PyMongo client and compare the stored values and their types. Then read each document
back through the *other* ODM and check what Python object comes out.

*(script + exact code — fill when run)*

## Raw output

```
not run
```

## Interpretation

*not run*

## What to record beyond pass/fail

- The raw BSON value for each write path — BSON has no timezone, so the question is which instant was stored.
- The size of the discrepancy in a non-UTC timezone. Run this on a host that is not on UTC, or the check proves
  nothing: the bug it is looking for is invisible at offset zero.
- Whether Beanie returns aware or naive datetimes on read, and what happens when that value is compared against
  `ONLINE_THRESHOLD`.
- How many collections hold a naive-local datetime — that count is the data migration this decision implies.

## Caveats

*not run*
