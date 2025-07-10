from aihub_process.delegators.AbstractProcessEntity import BaseProcessEntity


class Agent(BaseProcessEntity):
    """
    The agent entity defines an agent that participates in a process. To know from which agent to receive a piece
    of work as a process step input, we must know its agent_id and agent_class.
    Same holds true for the output: In order to know where to send a work request as a process step output, we must
    know the agent_id and agent_class.
    """

    class In(BaseProcessEntity.In):
        """Receive AgentWorkEvent as INPUT to a process step from an agent with class and id."""

        agent_class: str
        agent_id: str

    class Out(BaseProcessEntity.Out):
        """Delegates a AgentWorkReqeust as an OUTPUT from a process step to an agent with class and id."""

        agent_class: str
        agent_id: str

