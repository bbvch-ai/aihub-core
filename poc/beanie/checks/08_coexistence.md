# Check 08 — sync and async clients on one collection

**Gate:** cost input — informs the ADR, does not kill the option\
**Verdict:** not run\
**Environment:** see [`../environment.md`](../environment.md)

## Question

Can a synchronous `MongoClient` (MongoEngine) and an `AsyncMongoClient` (Beanie) operate on the same collection in the
same process, correctly and at the same time?

This decides whether an **incremental** migration is possible. If the two cannot coexist, the only remaining shape is
big-bang across 22 `Document` and 13 `EmbeddedDocument` classes and 139 `.objects(` call sites — a materially different,
and much riskier, proposition. So this check does not gate Beanie; it gates the *migration shape*.

It also matters for the parts of the codebase that are synchronous and gain nothing from an async ODM: Dagster ops in
`packages/pipeline` and parts of `packages/bot`.

## What to run

In one process, open both clients against the same spike database and interleave operations on one collection: write
via MongoEngine, read via Beanie, and the reverse. Then run both concurrently under an event loop and check for
correctness, not just absence of errors.

*(script + exact code — fill when run)*

## Raw output

```
not run
```

## Interpretation

*not run*

## What to record beyond pass/fail

- Two connection pools now exist against the same database — record the total connection count and whether FerretDB's
  limits are a concern.
- Whether a document written by one ODM reads back identically through the other (the shape question from check 02,
  now under concurrency).
- Whether MongoEngine's global connection registry conflicts with Beanie's init in the same process.
- What happens when a sync call blocks the loop while an async call is in flight — this is the very bug the migration
  is meant to fix, and during coexistence it still exists in the un-migrated half.

## Caveats

*not run*
