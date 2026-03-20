from typing import Annotated

from pydantic import Field

from swiss_ai_hub.process.delegators.abstract_process_entity import BaseProcessEntity


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

        process_class: Annotated[str, Field(description="The class of the process that completed.")]
        process_id: Annotated[str, Field(description="The ID of the process that completed.")]

    class Out(BaseProcessEntity.Out):
        """Does NOT further delegate the work, instead, acts like a sink, terminating the process."""

        pass
