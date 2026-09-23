# Check 15 — what does a backward run actually do?

**Phase:** 4\
**Verdict:** **3 SILENT BEHAVIOURS** — all three confirmed; T2 is worse than the ADR stated\
**Run:** 2026-09-23 · beanie 2.2.0 · FerretDB 2.5.0 · [`../environment.md`](../environment.md)\
**Scripts:** [`check_15_backward_behaviour.py`](check_15_backward_behaviour.py) ·
[`migrations_no_backward/`](migrations_no_backward/) ·
[`migrations_healthy_then_failing/`](migrations_healthy_then_failing/) · [`migrations_chain/`](migrations_chain/) ·
**Raw output:** [`../logs/15_backward_behaviour.log`](../logs/15_backward_behaviour.log)

## Question

[Check 13](13_migration_framework.md) ran one backward migration and it reverted correctly. That is the happy path.
Three behaviours the Rollback section depends on are silent in Beanie's source and needed measuring.

## T1 — a migration with no `Backward` class

```
forward  -> OK    data=['migrated', 'migrated', 'migrated']  log=['..._forward_only.py']
backward -> OK    data=['migrated', 'migrated', 'migrated']  log=['..._forward_only.py', 'root']
```

**The backward run reported success, moved the log pointer to `root`, and left every document migrated.** Nothing
raised, nothing warned.

The mechanism is `runner.py:133-144`:

```python
async def run_backward(self, allow_index_dropping, use_transaction):
    if self.backward_class is not None:        # ← optional
        await self.run_migration_class(...)
    if self.prev_migration is not None:        # ← runs REGARDLESS
        await self.prev_migration.update_current_migration()
```

The body is guarded; the pointer move is not. So an operator who rolls back a release containing a migration with no
`Backward` gets a clean exit code, a log that says the migration is no longer applied, and a database that is still
migrated. **Source of rule 7.**

## T2 — a failed migration, then a backward run

```
forward (A healthy, then B raises)
  data=['after-B', 'after-B', 'after-A']   log=['..._healthy.py']      ← B absent; it never completed
backward distance 1 -> OK
  data=['original', 'original', 'original'] log=['..._healthy.py', 'root']
```

**The backward run undid A — the healthy migration — because B never reached the log.** The runner's idea of "the last
migration" is whatever the log says, and a migration that raised is not in it.

### This is worse than the ADR stated, and the ADR needs correcting

The ADR says the backward run *"leaves the failed one's partial writes in place"*. **It did not.** Before the backward
run two rows held `after-B`; afterwards all three held `original`. A's `Backward` sets the field unconditionally, so it
**overwrote** rows that B had partially migrated — rows A's `Backward` was never designed to see.

Here that happened to be benign: everything normalised to `original`. It is benign by luck. A `Backward` that inverts a
specific transformation — subtract what was added, split what was joined — applied to rows in a *different* state than
it expects, produces corruption rather than a clean revert.

So the accurate statement is: **a backward run after a failed migration undoes the wrong migration, and what happens to
the failed migration's partial writes depends entirely on what the previous migration's `Backward` does to rows it
never wrote.** That is a stronger argument for the ADR's actual conclusion — recovery is a forward re-run — not a
weaker one.

## T3 — a bare backward run

```
forward all three  -> data=[3, 3, 3]
backward, distance=0 (the CLI default) -> data=[0, 0, 0]
```

**All three migrations were undone by a run that named no distance.** `distance=0` logs *"Running migrations backward
without limit"* (`runner.py:102`) and is what the CLI falls back to (`executors/migrate.py:31-34`). An operator
intending to step back one release steps back to the beginning of history. **Source of rule 8.**

## An observation the ADR does not mention

`migrations_log` is **append-only**. After T3's three forward and three backward runs it held:

```
[step_1, step_2, step_3, step_2, step_1, root]
```

Duplicated names, no direction recorded, `is_current` the only pointer. **The log is a cursor with history attached,
not an audit trail of what is applied.** Anything built on it — a CI gate, an operator dashboard, a "which migrations
have run" query — must read `is_current` and the ordering, never the set of names.

## Caveats

- Three documents per collection, one or three migrations per scenario. Nothing here about behaviour at corpus scale.
- T2's outcome is fixture-dependent by its nature: A's `Backward` here is unconditional. The finding is precisely that
  the outcome depends on the previous `Backward`, so a different fixture giving a different result would confirm rather
  than contradict it.
- Backward runs under concurrent replicas were not tested. Rule 4's leader lease presumably applies in both directions,
  but that is inference, not measurement.
- `free_fall` backward migrations were exercised in T2 but not isolated; a free-fall `Backward` failing partway is
  untested.
