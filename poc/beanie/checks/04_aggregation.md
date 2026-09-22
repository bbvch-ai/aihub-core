# Check 04 — aggregation: `$group`, `$lookup`, `allowDiskUse`

**Gate:** hard — a FAIL ends the Beanie option\
**Verdict:** not run\
**Environment:** see [`../environment.md`](../environment.md)

## Question

Are our existing aggregation pipelines reachable and correct through Beanie's aggregation API?

The pipelines themselves are ODM-independent — they are raw stage dictionaries sent over the wire, so FerretDB either
supports them today (it must, they are in production) or it doesn't. What this check actually tests is whether **Beanie
can pass them through unchanged**, including the options, and whether results come back in the same shape.

Two real pipelines to reproduce:

1. **LLM spend**, `packages/core/swiss_ai_hub/core/persistence/messaging/entities/persisted_agent_event_entity.py:578` —
   `$match` → `$project` → `$group` (dedup by `event_id`) → `$group` (sum) → `$sort`, executed with
   `allowDiskUse=True` (line 599). The comment there records the reason: without the time bound the dedup stage trips
   Mongo's 100 MB `$group` limit, and `allowDiskUse` is what keeps that from being a hard failure.

2. **Unanswered work requests**,
   `packages/core/swiss_ai_hub/core/persistence/messaging/entities/persisted_process_event_entity.py:74` — a `$lookup`
   sub-query joining work events to work requests.

## What to run

Seed enough documents to make both pipelines meaningful, run each through Beanie's aggregation, and compare the result
set against the same pipeline run through MongoEngine and through a raw PyMongo client on the same data.

*(script + exact code — fill when run)*

## Raw output

```
not run
```

## Interpretation

*not run*

## What to record beyond pass/fail

- Whether `allowDiskUse=True` is accepted by FerretDB at all, and whether Beanie forwards it. If FerretDB ignores it
  silently, the spend query keeps working until a deployment gets large enough to hit the limit — a latent failure, not
  a current one. Say so explicitly.
- Result-shape differences: Beanie can project aggregation output into a Pydantic model; confirm raw dicts are also
  available, since our code reads `row["_id"]` directly.
- Whether `$lookup` behaves identically, especially the empty-match case.

## Caveats

*not run*
