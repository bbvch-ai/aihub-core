# Check 05 — one Document class against two databases

**Gate:** cost input — informs the ADR, does not kill the option\
**Verdict:** not run\
**Environment:** see [`../environment.md`](../environment.md)

## Question

How does Beanie express what MongoEngine's `switch_db` does for us, and what does that cost?

This is expected to be the most awkward finding, which is why it is the first of the cost checks. Beanie binds a
Document class to one database at `init_beanie` time. We route the same class across databases at call time:

- `packages/core/swiss_ai_hub/core/persistence/rag/documents/entities/ref_doc.py:17` imports `switch_db` and uses it
  inside query methods (e.g. line 192, line 366).
- `packages/core/swiss_ai_hub/core/persistence/messaging/entities/persisted_agent_event_entity.py:177` and
  `persisted_process_event_entity.py:46` call `persisted_entity.switch_db(db)` before saving.

So the pattern is not incidental — event persistence and RAG document storage both depend on it.

## What to run

Attempt the equivalent in Beanie and record what it takes. Candidate approaches to try, in order of preference:

1. A per-database initialised copy of the Document class.
2. Dropping to the underlying PyMongo collection for the routed operations, keeping Beanie for everything else.
3. Re-initialising a Document against a different database per call (expected to be unacceptable — measure it anyway so
   the ADR can say why).

*(script + exact code — fill when run)*

## Raw output

```
not run
```

## Interpretation

*not run*

## What to record beyond pass/fail

- Which approach works, and how much code each entity needs compared to `switch_db` today.
- Whether the approach is safe under concurrency — the API serves many requests against many tenant databases.
- Whether the routed path loses anything Beanie otherwise gives us (validation, hooks, typed results). If the answer is
  "we drop to raw PyMongo for these entities", say plainly that those entities gain nothing from the migration.

## Caveats

*not run*
