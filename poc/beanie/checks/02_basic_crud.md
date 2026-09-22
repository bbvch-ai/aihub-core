# Check 02 — insert, `find_one`, replace/save

**Gate:** hard — a FAIL ends the Beanie option\
**Verdict:** not run\
**Environment:** see [`../environment.md`](../environment.md)

## Question

Do Beanie's basic document operations work against FerretDB 2.5, and does the stored document have the same on-disk
shape MongoEngine produces?

The floor. If this fails nothing else matters. But the second half of the question is the interesting one: an
incremental migration means both ODMs read and write the same collections for a period, so a shape difference is not
cosmetic — it decides whether incremental migration is possible at all.

## What to run

Round-trip a document through Beanie: insert, read back by `find_one`, modify, save, read again. Then write an
equivalent document through MongoEngine into the same collection and compare the two raw BSON documents field by
field, reading them with a plain PyMongo client so neither ODM's deserialization hides a difference.

*(script + exact code — fill when run)*

## Raw output

```
not run
```

## Interpretation

*not run*

## What to record beyond pass/fail

- `_id` type and generation: both should be `ObjectId`, but confirm rather than assume.
- Whether Beanie writes any bookkeeping field of its own (e.g. a revision field) that MongoEngine would then see as an
  unknown field — relevant to check 06.
- Whether MongoEngine's `_cls` discriminator appears on any of our documents and, if so, what Beanie does with it.
- Field-name and type mapping for nested documents (`EmbeddedDocument` → nested Pydantic model).

## Caveats

*not run*
