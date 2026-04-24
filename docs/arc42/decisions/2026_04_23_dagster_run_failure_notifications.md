# Pipeline Run-Failure Notifications via dagster-apprise

## Context

Swiss AI Hub's observability philosophy, documented in
`docs/docs/2_platform/3_deployment_guide/5_monitoring_and_alerting/`, delegates alerting to whatever external
observability platform the operator uses (SigNoz by default, also Datadog, Splunk, PagerDuty): the platform emits
OpenTelemetry metrics, logs, and traces, and the backend decides when to page somebody. That model covers request-path
failures well because the relevant signals do reach the OTEL collector — but it has an operational gap at the pipeline
edge. Dagster pipelines fail silently from the operator's perspective: a failed asset materialization or a
crashed-observation job shows up in the Dagster UI, not in SigNoz, and nobody gets woken up. Several recent
SharePoint-to-datalake stalls were noticed only when downstream agents started returning empty results.

`@run_failure_sensor` is the correct Dagster primitive for this: it fires on every failed run in a code location and,
crucially, does *not* need to be wired per-asset. That matters because our pipelines are asset-centric and most
materializations are triggered indirectly by `AutomationConditionSensorDefinition` — which produces runs, which the
failure sensor still catches. One sensor per code location covers both explicit jobs (observe/materialize/remove) and
auto-materialize runs.

The remaining question was how to deliver the notification. Operators want Slack today, Teams later, and in some
deployments email or PagerDuty. Rolling our own multi-channel dispatcher would mean maintaining Slack webhook code, SMTP
code, retries, message formatting — a small project on its own. `dagster-apprise` already wraps the Apprise library,
which abstracts 80+ notification services behind a single URL format (`slack://...`, `mailto://...`, `msteams://...`,
`pagerduty://...`). Reusing it is consistent with how we use `dagster-aws` and `dagster-postgres` for their respective
domains: take the well-maintained integration instead of hand-rolling.

## Decision Drivers

- **Coverage of asset-centric runs**: the mechanism must catch auto-materialize failures, not only explicit-job
  failures, because most of our pipelines rely on `AutomationCondition.eager()` under an
  `AutomationConditionSensorDefinition`.
- **Minimal custom code**: pipelines are domain infrastructure, not a notifications product. Every line of delivery code
  we own is a line we maintain.
- **Broad channel support**: operators across deployments need Slack, Teams, email, or PagerDuty without us adding a new
  codepath per channel.
- **Opt-in and invisible when unused**: if no URLs are configured, the sensor must not exist and must produce no
  warnings, so the dev stack and anyone not operating production stays quiet.
- **Inheritable by default pipelines**: `app/default_rag_pipeline/__init__.py` and friends should pick up the sensor
  without code changes — operators turn it on by setting env vars, not by redeploying new Python.
- **Consistent with repo conventions**: use `EnvironmentSettings` for config, keep settings in `packages/core`, keep
  Dagster wiring in `packages/pipeline/util/definitions_util.py`, no new abstraction layers (conv. #16).

## Decision

Add a thin library wrapper around `dagster_apprise.AppriseResource.notify_run_status` and wire it into every
`Definitions` builder in `packages/pipeline/swiss_ai_hub/pipeline/util/definitions_util.py`.

- **`NotificationSettings`** (in
  `packages/core/swiss_ai_hub/core/infrastructure/notification/notification_settings.py`): `EnvironmentSettings`
  subclass with `NOTIFICATION_` prefix. Fields: `URLS: list[str]` (comma-separated Apprise URIs),
  `DAGSTER_UI_BASE_URL: str | None`, `TITLE_PREFIX: str`, `MIN_INTERVAL_SECONDS: int`. `enabled` is true when `URLS` is
  non-empty.
- **`run_failure_notification_sensor()`** (in
  `packages/pipeline/swiss_ai_hub/pipeline/sensors/run_failure_notification_sensor.py`): decorates a
  `@run_failure_sensor` with `default_status=RUNNING`, instantiates an `AppriseResource`, and on each failed run
  dispatches a message containing the run's asset keys (truncated to 5), the error preview (truncated to 500 chars), and
  a deep link to `{DAGSTER_UI_BASE_URL}/runs/{run_id}`. `AppriseResource.notify_run_status` supplies run_id, job_name,
  and the deep-link format; our custom body adds the asset/error context.
- **Automatic wiring**: a private helper `_failure_notification_sensors()` in `definitions_util.py` reads
  `NotificationSettings()` on each call and returns `[]` when disabled or `[sensor]` when enabled. Each of the four
  builders — `default_definitions`, `default_sharepoint_to_datalake_definitions`,
  `default_local_filesystem_to_datalake_definitions`, `default_rclone_to_datalake_definitions` — spreads the result into
  its `sensors=[...]` list. `app/default_rag_pipeline/__init__.py`, `app/shared_rag_pipeline/__init__.py`, and
  `playground/__init__.py` are not modified; they inherit the sensor by calling the library.
- **Consumer escape hatch**: consumers that compose `Definitions` manually (e.g.,
  `playground/quick_start/my_document_pipeline.py`) can import `run_failure_notification_sensor` directly and pass
  `monitored_jobs=[my_job]` or custom URLs when they want more than the default env-driven behaviour.
- **Env propagation — three-way split to minimize operator-facing env vars**. The four `NOTIFICATION_*` env vars the
  `NotificationSettings` Pydantic class consumes are sourced from three places depending on what kind of value they
  carry:
  - **`.env.dev`/`.env.prod` (operator-supplied)** — only `NOTIFICATION_URLS`, because it carries secrets (Slack tokens,
    SMTP credentials). `.env.dev` additionally keeps `NOTIFICATION_DAGSTER_UI_BASE_URL='http://localhost:3000'` for
    developers running pipelines locally outside Docker via `make playground` (the Python process reads env directly
    there, not through the compose template).
  - **`infra/deployment/templates/docker-compose.yml.j2` (stage-derived)** — `NOTIFICATION_DAGSTER_UI_BASE_URL` is
    computed by a Jinja `{% set %}` at the top of the template:
    `"http://localhost:3000" if stage == 'dev' else "https://dagster.${DOMAIN}"`. The non-dev branch relies on the same
    `${DOMAIN}`-based Traefik host used by the Dagster webserver itself, so the link always points where the operator
    actually reaches Dagster.
  - **`infra/deployment/compose-config.yml` (platform defaults)** — `NOTIFICATION_TITLE_PREFIX` and
    `NOTIFICATION_MIN_INTERVAL_SECONDS` live under a `notifications:` block and are baked into the generated compose
    files at render time. Changing them means editing one value and running `make generate-compose`, not updating every
    operator's `.env`. Empty `NOTIFICATION_URLS` means "disabled"; no compose regeneration needed to toggle the feature
    on/off.

## Consequences

- **New runtime dependencies** in `packages/pipeline`: `dagster-apprise` (0.0.2+) and `apprise` (1.9.9+). Both are small
  and under active maintenance. Adds ~2 MB to the image.
- **Operators learn one URL format** (`slack://...`, `mailto://...`, `msteams://...`). This is a known Apprise
  convention; trade-off is better than maintaining N per-channel env vars in our settings.
- **Custom message body lives in the library** — consistent with where we own formatting for NATS events and Dagster
  asset metadata. Future wording/i18n tweaks happen in one place.
- **Sensor runs in the code location**, not the daemon. That's where Dagster evaluates sensors anyway, and it means the
  `default_rag_pipeline` / `shared_rag_pipeline` containers — not `dagster-daemon` — need the env vars (already handled
  in the compose template).
- **Complementary to OTEL alerting, not a replacement**: this covers Dagster run outcomes specifically. Request-path
  failures, LLM failures, and infra-level problems continue to be alerted through the OTEL/SigNoz pipeline. We keep the
  platform-docs statement that alerting is configured externally; this ADR is the documented exception for Dagster run
  lifecycle signals.
