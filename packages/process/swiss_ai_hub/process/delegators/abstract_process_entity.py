import abc

from pydantic import BaseModel


class BaseProcessEntity(abc.ABC):
    """
    The process entity is a participant of a workflow, such as a human, agent, program, etc.
    In order to delegate work to it or receive a piece of work from it, we must usually define more context.
    For example, to know from which agent to receive a piece of work as a process step input, we must know its
    agent_id and agent_class. We use the In and Out classes exactly to provide this context.
    """

    class In(BaseModel, abc.ABC):
        """Receive WorkEvent as INPUT to a process step."""

        pass

    class Out(BaseModel, abc.ABC):
        """Delegates a WorkReqeust as an OUTPUT from a process step."""

        pass
