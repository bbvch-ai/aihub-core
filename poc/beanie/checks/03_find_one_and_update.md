# Check 03 — `find_one_and_update`

**Gate:** hard — a FAIL ends the Beanie option\
**Verdict:** **PASS** (with one Beanie configuration prerequisite discovered)\
**Run:** 2026-09-22 · beanie 2.2.0 · FerretDB 2.5.0 · [`../environment.md`](../environment.md)\
**Script:** [`check_03_find_one_and_update.py`](check_03_find_one_and_update.py) · **Raw output:**
[`../logs/03_find_one_and_update.log`](../logs/03_find_one_and_update.log)

## Question

Does FerretDB 2.5 support the `findAndModify` path that Beanie uses for its update operations?

A hard gate because it is not optional in Beanie: the `set`/`update` helpers and `save_changes()` route through it. If
FerretDB did not implement it with the semantics Beanie expects, every write path would have to be rewritten as a plain
replace.

Our own code depends on the same primitive today, e.g.
`packages/core/swiss_ai_hub/core/persistence/rag/documents/entities/ref_doc.py:366`, which sets a deeply nested field
(`set__data__metadata__is_ingested=True`) and reads the result as a success flag.

## What was run

Driver-level `find_one_and_update` for the four semantics we rely on (plain set, nested-field set, upsert, no-match),
then the three Beanie-level write APIs (`.set()`, `save_changes()`, query-level `.update(Set(...))`).

## Raw output

```
== 1. driver-level find_one_and_update, plain field set ==
returned (AFTER) : counter=1
returned (BEFORE): counter=1
stored now       : counter=2  -> BEFORE/AFTER semantics correct

== 2. nested-field set (the ref_doc.py:366 shape) ==
data.metadata    : {'is_ingested': True, 'source': 'spike'}
siblings intact  : text='hello'

== 3. upsert ==
upserted _id=ObjectId('6ab2233f1e01f34c9f07ccc1') type=ObjectId counter=99

== 4. no-match without upsert returns None ==
returned: None

== 5. Beanie API: .set() ==
after .set()     : counter=42

== 6a. save_changes() WITHOUT state management ==
refused by Beanie: StateManagementIsTurnedOff: State management is turned off for this document
-> save_changes() is NOT available by default; it is opt-in per Document

== 6b. save_changes() WITH use_state_management = True ==
after save_changes: counter=7 metadata={'is_ingested': True, 'source': 'changed'}

== 6c. does state management change the stored shape? ==
keys: ['_id', 'counter', 'data', 'ref_doc_id']

== 7. Beanie API: query-level update with Set ==
after query update: counter=100
```

Full output, including the first run's unhandled traceback, in
[`../logs/03_find_one_and_update.log`](../logs/03_find_one_and_update.log).

## Interpretation

**FerretDB implements `findAndModify` correctly for every semantic we depend on.** `ReturnDocument.BEFORE` and
`.AFTER` return the pre- and post-update document respectively and the stored value confirms both; a nested-field
`$set` reaches `data.metadata.is_ingested` and leaves the sibling keys untouched, which is precisely the `ref_doc.py`
shape; an upsert creates the document with a server-generated `ObjectId`; and a no-match without upsert returns `None`
rather than raising. All three Beanie write APIs work on top of it.

**The one thing this check found is a Beanie prerequisite, not a FerretDB limitation.** `save_changes()` is *not*
available by default — it raises `StateManagementIsTurnedOff` unless the Document sets `use_state_management = True`.
This surfaced as an unhandled exception on the first run, which is why the script now tests both configurations
side by side. It matters for the migration because `save_changes()` (write only the changed fields) is the natural
replacement for MongoEngine's `save()`, and every ported Document that wants it must opt in explicitly. A port that
forgets the flag fails at runtime, not at import — so it is a per-entity checklist item, not something a reviewer will
catch by reading a diff.

**Turning state management on does not change the stored document.** The keys after a `save_changes()` are exactly
`['_id', 'counter', 'data', 'ref_doc_id']` — no bookkeeping field appears. So the shape-equality result from
[check 02](02_basic_crud.md) survives enabling it, and the incremental-migration precondition is not weakened by this
setting.

## Recorded beyond pass/fail

- `ReturnDocument` before/after semantics verified against the stored value, not just against the returned document.
- Upsert generates a standard `ObjectId`; no client-side id generation was needed.
- Nested `$set` is genuinely partial — sibling keys under the same parent survived.
- `use_state_management` is client-side only: it adds no field to the document.

## Caveats

- **`use_revision` was not tested.** Beanie's optimistic-concurrency mechanism adds a revision field and a
  compare-and-set to every write, which is a different wire operation and would invalidate check 02's shape equality.
  If the migration would use it, it needs its own check.
- Single-document, single-client updates only. No concurrent writers, so this says nothing about whether FerretDB's
  `findAndModify` is genuinely atomic under contention — worth a separate check if any ported entity relies on
  atomicity for correctness.
- `save_changes()` was exercised on a document loaded in the same process moments earlier. Long-lived documents, or
  ones mutated in ways the state tracker may not observe (in-place mutation of a nested `dict` did work here), are not
  covered.
- Array update operators (`$push`, `$pull`, `$addToSet`) were not tested; several of our entities hold lists.
