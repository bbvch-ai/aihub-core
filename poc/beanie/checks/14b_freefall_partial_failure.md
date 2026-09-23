# Check 14b — does the partial-failure guarantee hold for a free-fall migration?

**Phase:** 4\
**Verdict:** **FAIL** — free-fall migrations apply partially, and nothing records it\
**Run:** 2026-09-23 · beanie 2.2.0 · FerretDB 2.5.0 · [`../environment.md`](../environment.md)\
**Scripts:** [`check_14b_freefall_partial_failure.py`](check_14b_freefall_partial_failure.py) ·
[`migrations_freefall/`](migrations_freefall/) · **Raw output:**
[`../logs/14b_freefall_partial_failure.log`](../logs/14b_freefall_partial_failure.log)

## Question

[Check 14](14_migration_robustness.md) Q1 found that an `@iterative_migration` which fails partway writes **nothing**,
because Beanie collects its `replace_many` calls as coroutines and awaits none of them until the whole collection is
transformed (`iterative.py:93-128`). That makes "refuse to start on migration failure" a safe policy for that kind.

`@free_fall_migration` is built differently. `free_fall.py` is four lines long and simply awaits the author's function:

```python
async def run(self, session):
    function_kwargs = {"session": session}
    if "self" in self.function_signature.parameters:
        function_kwargs["self"] = None
    await self.function(**function_kwargs)
```

Nothing is collected and nothing is deferred. Does the guarantee still hold?

Free-fall cannot simply be banned — it is the only kind that can create an index, touch two collections, or rename a
field with `$rename`. So the answer decides whether a rule is needed.

## Raw output

```
== 1. run the free-fall migration that raises on the third document ==
  run_migrate -> FreeFallExploded: deliberate failure partway through a free-fall migration

== 2. what did it leave behind? ==
    a-before   state='migrated'
    b-before   state='migrated'
    boom       state='original'
    z-after    state='original'
  2/4 documents migrated, migrations_log entries: 0
```

Full output in [`../logs/14b_freefall_partial_failure.log`](../logs/14b_freefall_partial_failure.log).

## Interpretation

**The guarantee does not hold.** The same failure that wrote 0/4 documents as an iterative migration wrote **2/4** as a
free-fall one. The collection is left in a mixed state, and `migrations_log` is **empty** — nothing records that a
partial write ever happened.

Three consequences follow, and all three are in the ADR:

1. **A backward run does not recover it.** The runner rolls back the last migration *recorded in the log*, and this one
   never reached the log. See [check 15](15_backward_behaviour.md) T2.
2. **Recovery is a forward re-run**, which is only safe if the migration is idempotent — the reason for rule 6.
3. **"Refuse to start on migration failure" is safe for iterative migrations and not for free-fall ones.** The policy
   has to be stated per kind, not per framework.

## Caveats

- Four documents, one collection, one migration. Where exactly the failure lands relative to the write is what
  determines the ratio; 2/4 is this fixture's answer, not a general one.
- The migration writes document by document with `save()`. A free-fall migration written as a single `update_many` —
  which rule 6 recommends — would be atomic at the server for that one statement, and would not show this failure mode.
  That is precisely why rule 6 recommends it.
- Only the forward direction was exercised. A free-fall `Backward` failing partway was not tested and would presumably
  behave the same way.
