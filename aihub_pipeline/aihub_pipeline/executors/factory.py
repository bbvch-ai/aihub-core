import yaml
from dagster import ExecutorDefinition, in_process_executor
from dagster._core.execution.retries import RetryMode
from dagster_celery.executor import CeleryExecutor

from aihub_lib.infrastructure.celery.CeleryConfig import CeleryConfig


def default_process_executor() -> ExecutorDefinition:
    """We usually use the in-process executor for our pipelines, as we want consecutive steps / ops
    to run in the same process and use multi-processing only for parallel runs.
    """
    return in_process_executor


def scalable_celery_executor() -> CeleryExecutor:
    """Defines an executor that runs Dagster ops in a Celery worker cluster.
    Ideal when deployed to azure in a horizontally scalable container app."""
    return CeleryExecutor(
        retries=RetryMode.ENABLED,
        broker=CeleryConfig().CELERY_BROKER,
        backend=CeleryConfig().CELERY_BACKEND,
    )
