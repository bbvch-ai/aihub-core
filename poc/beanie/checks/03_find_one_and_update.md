# Check 03 — `find_one_and_update`

**Gate:** hard — a FAIL ends the Beanie option\
**Verdict:** not run\
**Environment:** see [`../environment.md`](../environment.md)

## Question

Does FerretDB 2.5 support the `findAndModify` path that Beanie uses for its update operations?

This is a hard gate because it is not optional in Beanie: `save_changes()` and the `set`/`update` helpers route through
it. If FerretDB does not implement it with the semantics Beanie expects, every write path would have to be rewritten as
a plain replace — which is exactly the kind of cost that decides the ADR.

Our own code also depends on atomic update semantics today, e.g.
`packages/core/swiss_ai_hub/core/persistence/rag/documents/entities/ref_doc.py:366` uses `update_one` with a set on a
nested field and reads its result as a success flag.

## What to run

Exercise `find_one_and_update` through Beanie: a plain field set, a nested-field set, an upsert, and the
`return_document` before/after behaviour. Then confirm the returned document matches what a subsequent read shows.

*(script + exact code — fill when run)*

## Raw output

```
not run
```

## Interpretation

*not run*

## What to record beyond pass/fail

- Whether the returned document reflects the pre- or post-update state, and whether that matches Beanie's expectation.
- Upsert behaviour, including what `_id` an upserted document receives.
- Whether Beanie's optimistic-concurrency (revision) mechanism works, **if** we would use it — if it doesn't, note
  whether it can be switched off cleanly rather than treating it as a failure.
- Nested-field updates (`a.b.c`), since our config documents are deeply nested.

## Caveats

*not run*
