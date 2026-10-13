from collections.abc import Sequence
from typing import Annotated

from dagster import AssetsDefinition, AutomationConditionSensorDefinition, DefaultSensorStatus
from dagster._core.storage.tags import MAX_RETRIES_TAG


def default_automation_sensor(
    assets: Sequence[AssetsDefinition],
    minimum_interval_seconds=60,
    max_retries: Annotated[int, "Run re-executions per failed automation run; 0 leaves runs untagged"] = 0,
) -> AutomationConditionSensorDefinition:
    """Sensor required to enable auto asset materialization.

    A retry budget is opt-in because `eager()` treats a failed launch as handled: a pipeline whose failures are mostly
    transient (the rclone data-lake write) wants its partitions re-executed, while one whose failures are mostly
    deterministic (parsing) would only repeat the same expensive failure.
    """
    return AutomationConditionSensorDefinition(
        "AutomaterializeSensor",
        target=assets,
        default_status=DefaultSensorStatus.RUNNING,
        minimum_interval_seconds=minimum_interval_seconds,
        run_tags={MAX_RETRIES_TAG: str(max_retries)} if max_retries else None,
    )
