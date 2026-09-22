# Check 06 — `extra="allow"` round-trip (the `strict: False` equivalent)

**Gate:** cost input — informs the ADR, does not kill the option\
**Verdict:** **PASS WITH COST** — safe *only* if every ported `strict: False` entity declares `extra="allow"`; one
combination silently destroys data\
**Run:** 2026-09-22 · beanie 2.2.0 · FerretDB 2.5.0 · [`../environment.md`](../environment.md)\
**Script:** [`check_06_extra_allow.py`](check_06_extra_allow.py) · **Raw output:**
[`../logs/06_extra_allow.log`](../logs/06_extra_allow.log)

## Question

Does a document carrying fields the model does not declare survive a read-modify-write through Beanie **without losing
those fields**?

Four of our documents run with `strict: False` precisely because old shapes drift: `ThreadEntity`,
`PersistedAgentEventEntity`, `PersistedProcessEventEntity`, `UserDashboardEntity`. Loading such a document is the easy
half; writing it back is the half that matters. If Beanie drops undeclared fields on save, a single read-modify-write
silently deletes production data that no code knew about — and there is no migration framework in place to have
removed it deliberately (that is issue #1152).

## What was run

A document with three extra fields (including a nested one) was inserted via raw PyMongo, then read, modified and
written back through every combination of **model configuration** (default vs `extra="allow"`) and **write path**
(`save()`, `save_changes()`, `replace()`). The stored BSON was re-read with a plain client after each.

## Raw output

```
== 7. summary ==
  StrictDoc.save()               safe
  StrictDoc.replace()            DATA LOSS  ['legacy_owner', 'nested_legacy', 'removed_in_v2']
  LenientDoc.save()              safe
  LenientDoc.save_changes()      safe
  LenientDoc.replace()           safe
```

```
== 6b. THE DANGEROUS COMBINATION: strict model + replace() ==
  model_extra on strict model: None
  after StrictDoc.replace()
    keys stored : ['thread_id', 'title']
    extras kept : NONE
    extras LOST : ['legacy_owner', 'nested_legacy', 'removed_in_v2']
```

Full output in [`../logs/06_extra_allow.log`](../logs/06_extra_allow.log).

## Interpretation

**One combination destroys data: a model without `extra="allow"` written back with `replace()`.** The document came
out of that write holding only its two declared fields; all three drift fields were gone, with no error and no
warning.

The other four combinations are safe, but **their safety is incidental, not a guarantee**, and the distinction matters:

- `LenientDoc` is safe because `extra="allow"` keeps the extras *on the model* (`model_extra` showed all three), so
  whatever the write path does, the data is there to write back.
- `StrictDoc.save()` is safe for a different and weaker reason: the extras are **not** on the model
  (`model_extra` is `None`), so its survival depends entirely on `save()` using `$set`-style semantics that leave
  untouched fields alone. Nothing about the model protects it. Change the write path — as `replace()` does — and the
  data is gone.

So the rule for the migration is unambiguous and belongs in the ADR as a hard requirement, not a recommendation:
**every Document ported from a `strict: False` entity must declare `extra="allow"`.** Relying on "we only ever call
`save()`" is relying on a property of Beanie's implementation that no test in our suite asserts.

This is also worth noting about the failure mode: it is silent, it is a *deletion*, and it would only manifest on
documents old enough to have drifted — which are exactly the documents least likely to appear in a test fixture and
most likely to matter in a long-running customer deployment.

## Process note

An earlier run of this script omitted the strict-model + `replace()` case and reported **every** path as "safe". That
result was misleading, and it looked clean. The gap was noticed only because `StrictDoc.save()` surviving was
surprising — a model that discards extras should not have been able to preserve them, which pointed at `save()` not
being a full replace and therefore at an untested combination. The script was extended and re-run; both runs are in
the log.

## Recorded beyond pass/fail

- Beanie does **not** reject unknown fields on read by default — a strict model loads a drifted document without
  error. So there is no natural tripwire: nothing fails loudly before the data is lost.
- `model_extra` exposes the extras on a lenient model, so code that needs to read drift fields can.
- Nested extra structures (`{'a': {'b': [1, 2, 3]}}`) round-trip intact on the safe paths.

## Caveats

- Only top-level extras were tested. Drift *inside* a declared nested field (e.g. an unknown key within an embedded
  document) is a different case and was not covered.
- `save_changes()` was tested only on the lenient model, because it requires `use_state_management` (see
  [check 03](03_find_one_and_update.md)); the strict + `save_changes()` combination is untested.
- Our four `strict: False` documents were not themselves ported — this used a stand-in with the same shape. The real
  entities carry embedded documents and lists, where drift behaviour could differ.
- No test of bulk write paths (`insert_many`, query-level `.update()`), which may have their own semantics.
