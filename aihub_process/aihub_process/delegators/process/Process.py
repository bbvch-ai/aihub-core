from aihub_process.delegators.AbstractProcessEntity import BaseProcessEntity


class Process(BaseProcessEntity):
    """
    A process can itself be a participating entity in another process!
    In any process, at some point, the process finished, in which case we use the Process.Out in combination
    with a ProcessStopEvent to indicate that this process successfully completed.
    However! The completion of one process can also trigger the start of another, allowing us for
    process chaining!
    Hence, using Process.In, the completion of one process can trigger the start of another.
    """

    class In(BaseProcessEntity.In):
        """Receive ProcessWorkEvent as INPUT to a process step from another process with class and id."""

        process_class: str
        process_id: str

    class Out(BaseProcessEntity.Out):
        """Does NOT further delegate the work, instead, acts like a sink, terinating the process."""

        pass
