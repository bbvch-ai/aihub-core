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
    resource = AppriseResource(
        config=AppriseConfig(
            urls=list(urls),
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
                "Apprise failure notification was not accepted by any endpoint for run %s", context.dagster_run.run_id
            )

    return _sensor


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
