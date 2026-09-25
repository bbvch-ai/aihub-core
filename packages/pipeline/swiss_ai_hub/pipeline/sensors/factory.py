from collections.abc import Sequence

from dagster import AssetsDefinition, AutomationConditionSensorDefinition, DefaultSensorStatus
from dagster._core.storage.tags import MAX_RETRIES_TAG

AUTOMATION_RUN_MAX_RETRIES = 2


def default_automation_sensor(
    assets: Sequence[AssetsDefinition], minimum_interval_seconds=60
) -> AutomationConditionSensorDefinition:
    """Sensor required to enable auto asset materialization.

    Its runs carry a retry budget because `eager()` treats a failed launch as handled: without a re-execution, a
    partition that failed on a transient outage stays failed until its upstream data version changes.
    """
    return AutomationConditionSensorDefinition(
        "AutomaterializeSensor",
        target=assets,
        default_status=DefaultSensorStatus.RUNNING,
        minimum_interval_seconds=minimum_interval_seconds,
        run_tags={MAX_RETRIES_TAG: str(AUTOMATION_RUN_MAX_RETRIES)},
    )
