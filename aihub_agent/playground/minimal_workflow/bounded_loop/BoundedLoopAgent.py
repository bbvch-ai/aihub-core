from aihub_lib.nats.context.run.RunContext import RunContext
from aihub_lib.nats.events import StopEvent, UserMessageEvent

from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from playground.minimal_workflow.bounded_loop.BoundedLoopAgentConfig import BoundedLoopAgentConfig
from playground.minimal_workflow.bounded_loop.events.BeginEvent import BeginEvent
from playground.minimal_workflow.bounded_loop.events.DecisionEvent import DecisionEvent
from playground.minimal_workflow.bounded_loop.events.ProcessAEvent import ProcessAEvent


class BoundedLoopAgent(Agent):
    @step()
    async def start_step(self, event: UserMessageEvent, run_context: RunContext) -> BeginEvent:
        print("[SimpleAgent.start_step]")
        await run_context.set("loop_count", 0)
        return BeginEvent(count=0)

    @step()
    async def process_a_step(self, event: BeginEvent) -> ProcessAEvent:
        print("[SimpleAgent.process_a_step]")
        return ProcessAEvent()

    @step()
    async def decision_step(
        self, event: ProcessAEvent, agent_config: BoundedLoopAgentConfig, run_context: RunContext
    ) -> DecisionEvent | BeginEvent:
        loop_count = await run_context.get("loop_count")
        print("[SimpleAgent.decision_step]", loop_count)
        if loop_count < agent_config.loop_max:
            await run_context.set("loop_count", loop_count + 1)
            return BeginEvent(count=loop_count + 1)

        return DecisionEvent()

    @step()
    async def end_step(self, event: DecisionEvent) -> StopEvent:
        print("[SimpleAgent.end_step]")
        return StopEvent()
