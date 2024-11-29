from dagster import ExecutorDefinition, in_process_executor


def default_process_executor() -> ExecutorDefinition:
    """We usually use the in-process executor for our pipelines, as we want consecutive steps / ops
    to run in the same process and use multi-processing only for parallel runs.
    """
    return in_process_executor
