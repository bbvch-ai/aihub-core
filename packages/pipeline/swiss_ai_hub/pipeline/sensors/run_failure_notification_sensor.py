import logging
from collections.abc import Sequence

from dagster import (
    DefaultSensorStatus,
    GraphDefinition,
    JobDefinition,
    RunFailureSensorContext,
    SensorDefinition,
    run_failure_sensor,
)
from dagster_apprise import AppriseConfig, AppriseResource
from swiss_ai_hub.core.infrastructure import NotificationSettings

logger = logging.getLogger(__name__)

type MonitoredJob = JobDefinition | GraphDefinition

_MAX_ASSET_KEYS_IN_MESSAGE = 5
_MAX_ERROR_PREVIEW_CHARS = 500


def run_failure_notification_sensor(
    *,
    urls: Sequence[str],
    dagster_ui_base_url: str | None = None,
    title_prefix: str = "Swiss AI Hub Pipeline",
    monitored_jobs: Sequence[MonitoredJob] | None = None,
    minimum_interval_seconds: int = 30,
    name: str = "run_failure_notification_sensor",
) -> SensorDefinition:
    """Dispatches a notification via Apprise whenever a run in this code location fails.

    Catches both job-based runs (observe/materialize/remove) and auto-materialize runs spawned by
    ``AutomationConditionSensorDefinition``, because `@run_failure_sensor` fires on any failed run
    in the code location when ``monitored_jobs`` is ``None``.
    """
    url_list = list(urls)
    url_count = len(url_list)
    resource = AppriseResource(
        config=AppriseConfig(
            urls=url_list,
            base_url=dagster_ui_base_url,
            title_prefix=title_prefix,
        ),
    )

    @run_failure_sensor(
        name=name,
        monitored_jobs=list(monitored_jobs) if monitored_jobs else None,
        default_status=DefaultSensorStatus.RUNNING,
        minimum_interval_seconds=minimum_interval_seconds,
    )
    def _sensor(context: RunFailureSensorContext) -> None:
        message = _format_failure_message(context)
        sent = resource.notify_run_status(
            run=context.dagster_run,
            status="FAILURE",
            message=message,
        )
        if not sent:
            logger.error(
                "Apprise failure notification rejected by all %d endpoint(s) for run %s",
                url_count,
                context.dagster_run.run_id,
            )

    return _sensor


def run_failure_notification_sensors_from_settings() -> list[SensorDefinition]:
    """Env-driven variant: returns a single-element list with the configured sensor, or ``[]`` when disabled.

    Reads ``NotificationSettings`` from the environment and, if ``URLS`` is non-empty, constructs a sensor via
    :func:`run_failure_notification_sensor`. Intended to be spread into a ``Definitions(sensors=[...])`` list so that
    builders can opt in to env-driven notifications without importing settings themselves.
    """
    settings = NotificationSettings()
    if not settings.enabled:
        return []
    return [
        run_failure_notification_sensor(
            urls=settings.URLS,
            dagster_ui_base_url=settings.DAGSTER_UI_BASE_URL,
            title_prefix=settings.TITLE_PREFIX,
            minimum_interval_seconds=settings.MIN_INTERVAL_SECONDS,
        ),
    ]


def _format_failure_message(context: RunFailureSensorContext) -> str:
    run = context.dagster_run
    parts: list[str] = []

    asset_selection = run.asset_selection or frozenset()
    if asset_selection:
        keys = sorted(asset_selection, key=lambda key: key.to_user_string())
        preview = [key.to_user_string() for key in keys[:_MAX_ASSET_KEYS_IN_MESSAGE]]
        remainder = len(keys) - len(preview)
        suffix = f" (+{remainder} more)" if remainder > 0 else ""
        parts.append(f"Assets: {', '.join(preview)}{suffix}")

    failure_event = context.failure_event
    error_message = failure_event.message if failure_event is not None else None
    if error_message:
        preview = (
            error_message
            if len(error_message) <= _MAX_ERROR_PREVIEW_CHARS
            else error_message[: _MAX_ERROR_PREVIEW_CHARS - 3] + "..."
        )
        parts.append(f"Error: {preview}")

    return "\n".join(parts)
