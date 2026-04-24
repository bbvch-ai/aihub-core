# Pipeline Run-Failure Notifications via dagster-apprise

## Context

Platform alerting (`docs/docs/2_platform/3_deployment_guide/5_monitoring_and_alerting/`) delegates to external
observability (SigNoz/PagerDuty/etc.) via OpenTelemetry. That path doesn't reliably surface Dagster run failures:
crashed observation jobs and failed asset materializations show up in the Dagster UI but nobody gets notified. We need a
direct, pipeline-native failure signal that also covers asset-centric pipelines, where most runs are spawned indirectly
by `AutomationConditionSensorDefinition`.

## Decision Drivers

- **Coverage of asset-centric runs**\
  Must catch auto-materialize failures, not only explicit-job failures.
- **Minimal custom code**\
  Pipelines aren't a notifications product; every line of delivery code is a line we maintain.
- **Broad channel support**\
  Slack today, Teams/email/PagerDuty on demand, without a new codepath per channel.
- **Opt-in**\
  No URLs configured → no sensor, no runtime noise.
- **Inheritable by default pipelines**\
  Operators turn notifications on by setting config, not by redeploying code.

## Decision

Use `dagster-apprise` behind a thin library wrapper and wire it into every `Definitions` builder.

- **Primitive**: `@run_failure_sensor` without `monitored_jobs` — one sensor per code location catches every failed run,
  including the ones auto-materialize spawns.
- **Factory**: `run_failure_notification_sensor()` in
  `packages/pipeline/swiss_ai_hub/pipeline/sensors/run_failure_notification_sensor.py` wraps
  `AppriseResource.notify_run_status`. Message body adds asset keys (truncated to 5), error preview (truncated to 500
  chars), and a deep link to `{base_url}/runs/{run_id}`.
- **Automatic wiring**: `run_failure_notification_sensors_from_settings()` lives in the same module and reads
  `NotificationSettings`; each `default_*_definitions()` builder spreads it into its `sensors=[...]`. Apps in
  `app/default_rag_pipeline/`, `app/shared_rag_pipeline/`, and `playground/` inherit the sensor unchanged.
- **Consumer escape hatch**: manual compositions import `run_failure_notification_sensor` directly and pass custom
  `urls` / `monitored_jobs`.
- **Env propagation** — three-way split so only secrets live in operator env files:
  - **Operator env (secrets)**: `NOTIFICATION_URLS` only; empty = disabled.
  - **Compose template (stage-derived)**: `NOTIFICATION_DAGSTER_UI_BASE_URL` computed from `stage`/`${DOMAIN}`. To
    override when Dagster is hosted on a non-standard subdomain, edit the `NOTIFICATION_DAGSTER_UI_BASE_URL` line in the
    generated `infra/docker-compose.<stage>.yml`.
  - **`compose-config.yml` (platform defaults)**: `NOTIFICATION_TITLE_PREFIX` and `NOTIFICATION_MIN_INTERVAL_SECONDS`
    baked into the generated compose files.

## Consequences

### Positive

- One sensor catches both explicit-job and auto-materialize failures across the whole code location; no per-asset wiring
  as pipelines grow.
- Adding a notification channel = setting a URL, not writing code. 80+ services via Apprise.
- Opt-in via env: dev stacks and anyone not operating production stay quiet.
- Default pipelines (`default_rag_pipeline`, `shared_rag_pipeline`) inherit the behaviour — enabling it is a config
  change, not a redeploy.
- Operator env surface is minimal: only `NOTIFICATION_URLS` (which carries secrets) is operator-visible; UI URL is
  stage-derived, other defaults live in `compose-config.yml`.

### Trade-offs

- Adds `dagster-apprise` and `apprise` as `packages/pipeline` dependencies (~2 MB).
- Operators learn the Apprise URL format instead of N per-channel env vars.
- Sensor runs inside the code-location containers, not the daemon — the notification config must reach those containers
  (already handled by the compose template).
- Complementary to OTEL alerting, not a replacement: covers Dagster run lifecycle only. Request-path, LLM, and infra
  failures still flow through OTEL/SigNoz.

## Related Decisions

- `docs/docs/2_platform/3_deployment_guide/5_monitoring_and_alerting/index.en.md` — Establishes that alerting is
  externalised via OpenTelemetry/SigNoz. This ADR is the documented exception for Dagster run-lifecycle signals, which
  don't reliably surface through that path.
