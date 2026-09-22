# Check 13 — does Beanie's migration framework work on FerretDB 2.5?

**Phase:** 4 — run after the ADR draft, because this driver was not in the issue text\
**Verdict:** **PASS WITH ONE HARD RULE** — the framework works; `use_transaction=True` must never be used on FerretDB\
**Run:** 2026-09-22 · beanie 2.2.0 · FerretDB 2.5.0 · [`../environment.md`](../environment.md)\
**Scripts:** [`check_13_migration_framework.py`](check_13_migration_framework.py) ·
[`migrations/20260922000001_split_name_field.py`](migrations/20260922000001_split_name_field.py) · **Raw output:**
[`../logs/13_migration_framework.log`](../logs/13_migration_framework.log)

## Why this check exists, late

Phases 1–3 answered the question **issue #1634 framed**: two production symptoms, both performance. On that evidence
the ADR recommended not migrating, because `asyncio.to_thread` matched Beanie everywhere it was measured.

The actual driver for choosing Beanie turned out to be different and was never written in the issue: **Beanie ships a
migration framework**, and the platform wants automatic migrations — which is
[#1152](https://github.com/bbvch-ai/aihub-core/issues/1152), a separate open issue asking for a versioned migration
registry that runs on startup.

That is not a performance question, so no load measurement could answer it. This check does.

## What the framework is, read from the installed package

| Fact                                                          | Source                            |
| ------------------------------------------------------------- | --------------------------------- |
| Always opens `client.start_session()`                         | `migrations/runner.py:167`        |
| Wraps the run in `start_transaction()` **only** when asked    | `migrations/runner.py:168-169`    |
| `use_transaction` defaults to **False**                       | `executors/migrate.py:58`         |
| State tracked as `MigrationLog` docs in `migrations_log`      | `migrations/models.py`            |

A real iterative migration was written in Beanie's own format (one field becomes two, including a row with no surname
as the awkward case) so this exercises the framework rather than a simulation of it.

## Raw output

```
== 1. can FerretDB open a session at all? ==
  write+read inside a session: OK
  start_session() -> OK

== 2. does FerretDB support start_transaction()? ==
  start_transaction() -> OperationFailure: no such command: 'commitTransaction'
                         {'ok': 0.0, 'code': 59, 'codeName': 'CommandNotFound'}

== 3. forward migration, use_transaction=False (the default) ==
  before: {'full_name': 'Ada Lovelace'} {'full_name': 'Alan Turing'} {'full_name': 'Grace'}
  run_migrate FORWARD -> OK
  after:  {'first_name': 'Ada', 'last_name': 'Lovelace'}
          {'first_name': 'Alan', 'last_name': 'Turing'}
          {'first_name': 'Grace', 'last_name': ''}

== 4. was the run recorded? ==
  migrations_log: name='20260922000001_split_name_field.py' is_current=True ts=2026-09-22 16:07:15

== 5. is a second forward run a no-op? ==
  second run -> OK, documents unchanged

== 6. backward migration (rollback) ==
  run_migrate BACKWARD -> OK
  after rollback: {'full_name': 'Ada Lovelace'} {'full_name': 'Alan Turing'} {'full_name': 'Grace'}

== 7. forward migration WITH use_transaction=True ==
  run_migrate FORWARD (transactional) -> OperationFailure: no such command: 'commitTransaction'
  after: documents ARE migrated

FOLLOW-UP PROBE -- state after the FAILED transactional run:
   data  : migrated (first_name / last_name present)
   log entries: 0
```

Full output in [`../logs/13_migration_framework.log`](../logs/13_migration_framework.log).

## Interpretation

**The framework works on FerretDB, in the default configuration, end to end.** Every property that "automatic
migration" requires is present:

- Forward migration transforms documents correctly, including the awkward row (`Grace` → `last_name: ''`).
- The run is **recorded** in `migrations_log` with `is_current=True`.
- A second forward run is a **no-op** — which is what makes it safe to call on every startup.
- Backward migration **rolls the change back** cleanly.

So the answer to the driver is yes: Beanie would supply the versioned registry, the forward/backward machinery, the
state tracking and the idempotency that #1152 asks for, rather than the platform building them.

### The hard rule: never set `use_transaction=True` on FerretDB

FerretDB 2.5 does not implement `commitTransaction` at all (`code: 59, CommandNotFound`). That alone would be a cost,
not a blocker, since the flag is off by default. What makes it a **rule** rather than a caveat is what happens when it
is set:

- the migration's writes **land** — the documents come out migrated;
- `commitTransaction` then fails, so the run **raises**;
- and `migrations_log` is left **empty**.

The data is changed and nothing records that it changed. An operator seeing the error would retry — re-applying a
migration to already-migrated data. For this migration, the retry would find no `full_name` field to split.

The trap is that `use_transaction=True` is exactly the flag someone reaches for *because they want safety*. On
FerretDB it buys the appearance of atomicity with none of the substance, and is strictly worse than leaving it off. If
the migration framework is adopted, this belongs in the ADR as a rule and in CI as a check, not in a comment.

### It also makes check 06's cost tractable

[Check 06](06_extra_allow.md) found that `extra="allow"` is mandatory on the four `strict: False` entities, or a
`replace()` silently deletes drift fields. That requirement exists *because* there is no way to remove drift
deliberately. With a working migration framework, drift can be normalised and the models tightened — which is
precisely what #1152's second acceptance criterion (`strict: True` once the framework exists) asks for. The two
findings are the same problem from opposite ends.

## What this does NOT prove

- **One migration, three documents, one collection.** Nothing about performance on a large corpus, or about a
  migration that must run across many tenant databases — which is where [check 05](05_multi_db.md)'s `switch_db`
  finding would apply, and it was not combined with this.
- **The startup hook was not built.** `run_migrate` was called directly from a script. Wiring it into the API's
  lifespan, and deciding what happens when a migration fails at boot, is unexamined.
- **No CI gate.** #1152's third criterion — CI fails when a schema change ships without a migration — is still custom
  work under either ODM.
- **`free_fall_migration` was not tested**, only `iterative_migration`.
- **No concurrent-startup test.** Several API replicas booting together would all call the migration runner; whether
  `migrations_log` prevents a double-apply under that race is untested, and FerretDB's lack of transactions makes it a
  fair question.
