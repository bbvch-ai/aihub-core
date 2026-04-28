# Continuous Postgres Maintenance via the Backup Dagster Instance

## Context

The platform Postgres grows without bound on long-running deployments. At one customer the `dagster` database had
reached 131 GiB; the bulk was framework-internal noise (`HANDLED_OUTPUT`, `LOADED_INPUT`, `ENGINE_EVENT`, verbose Python
`DEBUG` logs) accumulated over months of pipeline activity. Without intervention the disk would eventually fill and
Dagster would flip into a read-only state. The `retention:` block in `dagster.yaml` only addresses tick history — the
dominant `event_logs` and `runs` tables are not covered.

Operators were therefore left with a one-off manual cleanup recipe (Dagster's official "database tuning" page) that does
not generalise across deployments. Postgres health needs to be a property of the platform, not a runbook the operator
runs once and forgets.

## Decision Drivers

- *Bounded Postgres growth as a platform property* — customers should not need to know about it for the platform to stay
  healthy over months.
- *UI-safe by construction* — pruning must never delete rows the Dagster UI depends on. The cost of a regression (silent
  asset catalog, lost run history) is very hard to debug.
- *Mutually exclusive with backup* — the backup job stops postgres while it runs; cleanup or repack running concurrently
  would fail mid-query.
- *Reuse the existing operations plane* — no new container, no new Dagster instance.

## Decision

Build a maintenance subsystem **inside the existing backup Dagster instance**. Two new jobs run on weekly / monthly
schedules; they share the same daemon, webserver, and operator mental model as backup and restore.

- **Cleanup job** prunes only events the Dagster UI does not need: noisy Python log entries (DEBUG/INFO/WARNING) past
  their retention windows, and curated framework-internal event types (`HANDLED_OUTPUT`, `LOADED_INPUT`, `ENGINE_EVENT`,
  `ASSET_MATERIALIZATION_PLANNED`, `STEP_OUTPUT`). Asset materializations, step success/failure, run rows, asset catalog
  and sensor cursors are never touched.
- **Repack job** runs `pg_repack` on the heavy tables to return disk pages to the OS — `VACUUM` alone marks dead rows
  reusable internally but does not free disk.
- **Serialisation via tag-based concurrency** — every job that touches Postgres (backup, restore, cleanup, repack)
  carries the same mutex tag, and the backup Dagster's run coordinator caps concurrency for that tag at one. Other
  future jobs without the tag run unimpeded. Intra-run parallelism (e.g. parallel per-service backup ops) is unaffected.
- **Postgres image now ships `pg_repack`** — a project-managed image extends `pgvector/pgvector:pg17` with the apt
  package and the extension is registered on the dagster DB at first init. The backup container ships the matching CLI.
  Customer deployments running custom Postgres images without the extension see a clean skip with metadata explaining
  why; nothing fails.
- **First-run safety** — every cleanup `DELETE` is bounded by a per-transaction row cap. On a backlogged DB the first
  weekly tick prunes a fixed fraction; remaining noise drains over subsequent ticks. This protects against WAL flooding
  and the disk-full → read-only failure mode.
- **Failure isolation** — handlers return results; one stuck handler does not block the others. The finalize asset
  aggregates and only fails the run if any handler reported failure.
- **Cluster-wide retention block** — added to both the main and backup `dagster.yaml`s so the daemon prunes tick history
  automatically.

## Consequences

### Positive

- Postgres footprint is bounded by retention windows, regardless of how long a deployment has run. A 5-year-old
  deployment carries roughly the same `event_logs` size as a 3-month-old one.
- Operators get a working solution out of the box. The default configuration is sensible; the kill switch is one env
  var.
- Maintenance runs visible in the same Dagster UI operators already use for backup/restore, with per-handler metadata
  for ops review.
- UI-safety invariants are enforced at three layers: handler logic (curated allow-list), unit tests, and a dedicated
  integration test that runs the full chain against a real Postgres and asserts the load-bearing rows survive.
- Tag-based concurrency is precise: only the postgres-affecting jobs serialise. Future sensors, health checks and ad-hoc
  utilities run unimpeded.

### Trade-offs

- **The backup package now owns two responsibilities** — backup the platform, and maintain the platform's Postgres. The
  package name (`packages/backup`) under-sells the broader scope. We accept this rather than forking a second Dagster
  instance for maintenance only; both responsibilities touch the storage layer and share the same mutex.
- **Custom Postgres image required for repack.** The upstream `pgvector` image does not ship `pg_repack`. The build
  stage builds the custom image locally; other stages reference a project-managed image that an admin mirrors once.
  Deployments using a foreign Postgres image still work — repack reports a clean skip; cleanup works unconditionally.
- **Long-running backups can delay cleanup ticks.** A backup that exceeds its window pushes the next cleanup tick into
  the queue; cleanup runs once backup completes. This is the intended trade-off — correctness over schedule punctuality.
  Operators who care about the gap can alert on tick start_time vs scheduled_time.
- **No notification on maintenance failure today.** The Apprise-based run-failure notifications (ADR
  `2026_04_23_dagster_run_failure_notifications.md`) are wired into the pipeline code locations only. A failed
  maintenance run shows up only in the backup Dagster UI. Extending the notification sensor to the backup code location
  is a tracked follow-up.
- **First-run drain takes weeks.** With a per-tick row cap and a weekly schedule, a heavily backlogged DB needs several
  ticks to fully catch up. Trade-off vs the first-run WAL-flood risk; operators wanting a faster catch-up can manually
  launch the cleanup job through the UI repeatedly.

## Related Decisions

- `2026_04_23_dagster_run_failure_notifications.md` — the existing notification sensor covers pipeline code locations;
  the maintenance subsystem in the backup code location is currently out of scope of that ADR.
