from dagster import AssetsDefinition, AutomationConditionSensorDefinition, DefaultSensorStatus
from typing import Sequence


def default_automation_sensor(
    assets: Sequence[AssetsDefinition], minimum_interval_seconds=60
) -> AutomationConditionSensorDefinition:
    """Sensor required to enable auto asset materialization"""
    return AutomationConditionSensorDefinition(
        "AutomaterializeSensor",
        target=assets,
        default_status=DefaultSensorStatus.RUNNING,
        minimum_interval_seconds=minimum_interval_seconds,
    )
