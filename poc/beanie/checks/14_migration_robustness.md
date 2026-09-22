# Check 14 — the three open questions on automatic migrations

**Phase:** 4 — settles what [check 13](13_migration_framework.md) left open\
**Verdict:** **Q1 PASS · Q2 FAIL — needs a lease · Q3 FAIL — migrations must run sequentially**\
**Run:** 2026-09-22 · beanie 2.2.0 · FerretDB 2.5.0 · [`../environment.md`](../environment.md)\
**Scripts:** [`check_14_migration_robustness.py`](check_14_migration_robustness.py) ·
[`migrations_counter/`](migrations_counter/) · [`migrations_failing/`](migrations_failing/) · **Raw output:**
[`../logs/14_migration_robustness.log`](../logs/14_migration_robustness.log)

## Why this check exists

Check 13 proved the migration framework works when called **once, from a script, against one database**. The ADR's
"Open questions" section named what that did not cover. Each is answered here by an experiment.

A note on method: **Q2 uses separate processes, not asyncio tasks.** Beanie's `DBHandler` is module-global state, so
concurrent tasks in one process would contend on that rather than on the database, and the result would be an artifact
of the harness rather than a fact about replicas. Q3 deliberately tests the in-process case as well, because that is a
real deployment shape (one API migrating many tenant databases).

The counter migration increments a field rather than transforming one, so a double-application is visible as
`applied == 2` instead of as an exception that could be mistaken for something else.

## Q1 — What does a migration that fails partway leave behind? → **PASS**

```
run_migrate -> MigrationExploded: deliberate failure partway through the migration
  a-before   state='original'
  b-before   state='original'
  boom       state='original'
  z-after    state='original'
0/4 documents migrated, migrations_log entries: 0
```

**Nothing was written.** Not a partial application — zero documents changed, despite the failure occurring on the third
of four documents, with one document queued behind it.

The reason is in `beanie/migrations/controllers/iterative.py:93-127`: the `replace_many` calls are **collected as
coroutines and not awaited** until the whole collection has been transformed:

```python
all_migration_ops.append(self.output_document_model.replace_many(...))   # collected, not awaited
...
await asyncio.gather(*all_migration_ops)                                  # nothing happens until here
```

So this is not luck or small-collection behaviour — a failure in the **transform** writes nothing at any collection
size, which is a genuinely good property on a database with no transactions.

**It does not extend to the write stage.** If one of the `replace_many` calls fails inside that final `asyncio.gather`,
other batches may already have applied. `batch_size` defaults to **10 000** (`iterative.py:45`), so a collection under
that size is one batch and effectively all-or-nothing; a larger one is not. This was not tested.

## Q2 — Do concurrent replicas double-apply? → **FAIL**

```
before: applied=[0, 0, 0]
replica 0..3: worker: OK          (four separate processes, all reporting success)
after : applied=[2, 2, 2], migrations_log entries=4
```

**Yes.** Every document was incremented **twice**, and `migrations_log` holds **four** entries for a migration that
should appear once. No runner reported an error — all four believed they had done the right thing.

`migrations_log` is a plain collection with no locking, and FerretDB has no transactions to make the
check-then-write atomic. So the classic read-modify-write race applies: several runners read "not yet applied" before
any of them writes the log.

**This is a blocker for "migrations run automatically on startup" as stated.** The platform runs multiple API replicas,
and they start together on a deploy. The consequence is not a failed boot — it is silently corrupted data from a
migration applied N times, with the log claiming success.

The platform already has the pattern for this. `CronScheduler` holds a **Redis leader lease** precisely so that N
replicas do not all fire the same scheduled run
(`packages/core/swiss_ai_hub/core/scheduling/`, and `packages/api/CLAUDE.md` § Lifetime Manager). Migrations on startup
need the same: one replica takes a lease, runs migrations, releases; the others wait for it to finish before serving.

## Q3 — Migrations across several tenant databases → **FAIL when concurrent**

```
-- sequentially, one database after another --
  tenant_a      OK   applied=[1, 1, 1] log=1
  tenant_b      OK   applied=[1, 1, 1] log=1

-- concurrently, in ONE process --
  tenant_a      OK   applied=[0, 0, 0] log=0   <-- WRONG
  tenant_b      OK   applied=[1, 1, 1] log=2
```

**Sequential is correct. Concurrent in one process is corrupt** — and reports success while being so. `tenant_a` was
never migrated at all yet raised no error, while `tenant_b` received **two** log entries for one migration.

This is the **same root cause** as [check 05](05_multi_db.md)'s cross-tenant misrouting and
[check 09](09_test_infrastructure.md)'s dead-loop client: `DBHandler`, like `init_beanie`, is **process-global state**.
Two concurrent `run_migrate` calls overwrite each other's target database between yields, so one run's work lands
against the other's connection.

Three symptoms, one mechanism. It is worth stating as a single rule rather than three separate ones: **Beanie's
database binding is process-global, so anything that retargets it must be serialised or given its own process.**

## What this changes in the ADR

Two of the three open questions are now answered with a **requirement**, not a reassurance:

1. Automatic migration on startup needs a **leader lease**, following `CronScheduler`'s Redis pattern. Without it,
   multiple replicas silently apply migrations N times.
2. Multi-tenant migrations must run **strictly sequentially** in one process — never `asyncio.gather` across databases.
3. A failed migration writes nothing (for collections under `batch_size`), so "refuse to start on migration failure" is
   a safe policy: the database is left in its pre-migration state and the deploy can be rolled back.

## Caveats

- **Q1's write-stage failure was not tested.** A failure inside the final `asyncio.gather`, or a collection larger than
  the 10 000-document `batch_size`, could still leave a partial application. That needs its own check before a large
  collection is migrated.
- **Q2 used four replicas on one host**, all starting within milliseconds. Real replicas start across machines with
  more jitter, which changes the probability of the race but not its existence. `applied=[2, 2, 2]` rather than `[4,
  4, 4]` shows two runners lost the race and skipped — timing-dependent, so the exact multiple is not meaningful.
- **No lease implementation was built or tested.** The `CronScheduler` pattern is cited as the precedent, not
  demonstrated for migrations.
- Three documents per collection, two tenant databases. Nothing here says anything about migration duration, memory
  use at corpus scale, or how long a lease would need to be held.
