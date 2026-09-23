# Check 17 — does a fresh deployment have to replay migration history?

**Phase:** 4\
**Verdict:** **GAP** — a fresh database cannot run the migration history, and Beanie has no baseline mechanism\
**Run:** 2026-09-23 · beanie 2.2.0 · FerretDB 2.5.0 · [`../environment.md`](../environment.md)\
**Script:** [`check_17_fresh_deployment.py`](check_17_fresh_deployment.py) · **Raw output:**
[`../logs/17_fresh_deployment.log`](../logs/17_fresh_deployment.log)

## Question

EF Core has an `InitialCreate` migration: a fresh database is bootstrapped by running migrations from #1, and
`Database.Migrate()` at startup handles it. What is Beanie's equivalent?

**There isn't one, and it does not need one** — MongoDB has no schema to create. Collections appear on first write and
indexes come from `init_beanie`, not from a migration. A fresh deployment is fully usable with **zero** migrations run.

That inverts the problem. A fresh deployment writes data in the **current** shape, but its `migrations_log` is empty, so
the runner believes nothing has been applied. Running `beanie migrate` therefore applies *historical* migrations to data
that is already post-migration.

## Raw output

```
== 0. simulate a FRESH deployment ==
    {'first_name': 'Ada', 'last_name': 'Lovelace', 'tenant': 't1'}
    {'first_name': 'Alan', 'last_name': 'Turing', 'tenant': 't1'}
  migrations_log entries: 0  (empty -- nothing applied)

== 1. deploy runs `beanie migrate` ==
  run_migrate -> ValidationError: 1 validation error for OldPerson
  full_name  Field required [type=missing, ...]

== 2. what happened to the already-current data? ==
    {'first_name': 'Ada', 'last_name': 'Lovelace', 'tenant': 't1'}
    {'first_name': 'Alan', 'last_name': 'Turing', 'tenant': 't1'}
  migrations_log entries: 0
```

Full output in [`../logs/17_fresh_deployment.log`](../logs/17_fresh_deployment.log).

## Interpretation

**A fresh deployment cannot run the migration history.** The historical migration expects `full_name`, which a fresh
database never had, and Pydantic rejects the document before any transform runs.

It **failed safely** — data intact, `migrations_log` still empty — which is [check 14](14_migration_robustness.md) Q1's
deferred-write property holding again. An equivalent free-fall migration would not have been so clean.

**Beanie has no baseline mechanism.** Verified against `beanie migrate --help`: the options are
`--forward`/`--backward`, `--distance`, `--connection-uri`, `--database_name`, `--path`, `--allow-index-dropping`,
`--use-transaction`. There is no `--fake` (Django), no `stamp` (Alembic), no equivalent of manipulating
`__EFMigrationsHistory`. The only skip mechanism in the source is `runner.py:207` — *"Skip migrations that start with an
underscore"* — which is global to the migrations directory, so it cannot baseline one database while leaving others to
migrate.

## Why this matters more here than in a single-database application

Swiss AI Hub is **multi-tenant with per-tenant databases**. Tenants are provisioned continuously, so this is not a
one-off bootstrap concern — **every new tenant database starts with an empty `migrations_log` and current-shape data**.

Combined with rule 5 (migrations across tenant databases run strictly sequentially), the runner would walk every tenant
database and hit this on each newly provisioned one.

## Options

1. **Stamp the log at provisioning time.** When the platform creates a tenant database, insert a `MigrationLog` document
   naming the newest migration with `is_current=True`. This is what `--fake` would do, and it is a few lines. **This is
   the right answer for this platform** — it belongs in tenant provisioning, next to the code that creates the database.
2. **Write every migration to tolerate already-current data.** Natural for free-fall (`update_many` filtered on the
   pre-migration shape, which rule 6 already recommends); awkward for iterative, because the input model *requires* the
   old field, which is exactly what failed here.
3. **Track migrations per tenant rather than globally.** More correct, more work, and not something Beanie offers —
   `migrations_log` lives in whichever database the runner is pointed at, which does give per-database tracking for
   free, provided each database is stamped correctly when created.

Option 1 plus rule 6 covers it. Neither is provided by the framework.

## Caveats

- One migration, two documents, one database. The multi-tenant interaction with rule 5 is reasoned, not measured.
- The failure mode shown is for an **iterative** migration. A free-fall migration expecting the old shape would more
  likely apply partially, or silently do nothing, rather than raising — and would not be as safe.
- Stamping was not implemented or tested here, only identified.
