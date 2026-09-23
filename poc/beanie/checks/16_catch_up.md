# Check 16 — can an environment several migrations behind catch up in one command?

**Phase:** 4\
**Verdict:** **PASS** — `beanie migrate` is the direct equivalent of `dotnet ef database update`\
**Run:** 2026-09-23 · beanie 2.2.0 · FerretDB 2.5.0 · [`../environment.md`](../environment.md)\
**Scripts:** [`check_16_catch_up.py`](check_16_catch_up.py) · [`migrations_chain/`](migrations_chain/) · **Raw output:**
[`../logs/16_catch_up.log`](../logs/16_catch_up.log)

## Question

Asked from an EF Core background: an environment is 6–8 migrations behind, and `dotnet ef database update` brings it
current in one command. Does `beanie migrate`?

`runner.py:75-97` suggests it should — a FORWARD run with `distance=0` logs *"Running migrations forward without limit"*
and walks `next_migration` until the list is exhausted, starting from wherever `migrations_log`'s `is_current` pointer
sits. But the interesting case is not a fresh database. It is **resuming from the middle**, which is where a wrong
pointer would surface as either a skipped migration or a re-applied one.

The chain increments a counter, so the stored value is an unambiguous record of how many migrations actually ran — a
re-application shows up as `4` rather than as silence.

## Raw output

```
== S1: fresh database, bare `migrate` ==
    applied=[3, 3, 3]  current=..._chain_step_3.py  log_entries=3

== S2: THE EF CORE CASE -- one applied, then bare `migrate` ==
  migrate --distance 1   applied=[1, 1, 1]  current=..._chain_step_1.py
  migrate                applied=[3, 3, 3]  current=..._chain_step_3.py  log_entries=3
  PASS: caught up to 3. Migration 1 did NOT re-run -- it would read 4.

== S3: all applied, then a new migration arrives ==
  release N   (2 migrations)   applied=[2, 2, 2]
  release N+1 (3 migrations)   applied=[3, 3, 3]
  PASS: only the new migration ran.
```

Full output in [`../logs/16_catch_up.log`](../logs/16_catch_up.log).

## Interpretation

**Catch-up works, and it is the default behaviour.** `beanie migrate` with no `--distance` applies every pending
migration in order from the log pointer, and applies none of them twice. An environment N releases behind is brought
current in one command, exactly as `dotnet ef database update` would.

S2 is the load-bearing result: the counter reads **3, not 4**, so migration 1 was correctly recognised as already
applied and skipped. The pointer resumes from the middle of the chain rather than replaying it.

S3 confirms the ordinary deploy case — a release that adds one migration to an already-current database runs only the
new one.

### The asymmetry worth remembering

`distance=0` means *"without limit"* in **both** directions. Forward that is exactly what you want, and is why catch-up
is the default. Backward it means "undo every migration ever applied", which is why the ADR's rule 8 requires an
explicit `--distance` on backward runs, and why [check 15](15_backward_behaviour.md) T3 measured what happens without
one.

**The same default is correct forward and catastrophic backward.**

## Where this is weaker than EF Core

Catching up works; the operational envelope around it is thinner.

- **No preview.** EF Core has `dotnet ef migrations script`, which produces reviewable SQL for the pending set — you can
  hand a DBA "here is what these 8 migrations will do". Beanie has no equivalent. The only way to know what will run is
  to read the migration files.
- **No transaction per migration.** FerretDB has none at all (check 13). If migration 5 of 8 fails, 1–4 are applied, 5
  is partially applied if it is free-fall ([check 14b](14b_freefall_partial_failure.md)) or not at all if it is
  iterative ([check 14](14_migration_robustness.md) Q1), and 6–8 have not run. The database is then in a state **no
  release has ever been in**, and no single command recovers it — a backward run makes it worse rather than better
  ([check 15](15_backward_behaviour.md) T2).
- **The longer the gap, the worse that is.** An environment 8 migrations behind has 8 chances to land in that state, and
  the further behind it is, the less likely anyone has tested that exact sequence.

The mitigation is procedural rather than technical: for an environment far behind, apply in smaller explicit steps
(`--distance 1`) with a check between them, rather than one bare `migrate`. That trades the single-command convenience
for a known position after every step.

## Caveats

- Three migrations, three documents. A realistic 6–8 migration catch-up over a large corpus was not exercised — nothing
  here says anything about duration, or how long a leader lease (rule 4) would need to be held.
- All three migrations are iterative and idempotent by construction. A chain mixing free-fall migrations carries the
  partial-failure exposure described above; that combination was not tested.
- Single process. Catch-up under concurrent replica startup is rule 4's territory and was measured in
  [check 14](14_migration_robustness.md) Q2, not here.
