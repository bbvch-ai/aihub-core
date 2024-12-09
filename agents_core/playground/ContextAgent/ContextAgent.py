from agents_core.agents.abstract.Agent import Agent
from agents_core.workflow.decorators.step import step
from lib_core.nats.context.run.RunContext import RunContext
from lib_core.nats.context.thread.ThreadContext import ThreadContext
from lib_core.nats.events import StopEvent
from playground.ContextAgent.Events.CustomStartEvent import CustomStartEvent
from playground.ContextAgent.Events.EventA import EventA


class ContextAgent(Agent):

    @step()
    async def start_step(self, event: CustomStartEvent, thread_context: ThreadContext, run_context: RunContext) -> EventA:
        thread_count = await thread_context.get("count", 0)
        run_count = await run_context.get("count", 0)
        print(f"[SimpleAgent.start_step] Payload is '{event.payload}'")
        print(f"[SimpleAgent.start_step] Called {thread_count} times in thread, {run_count} times in run")
        await thread_context.set("count", thread_count + 1)
        await run_context.set("count", run_count + 1)
        return EventA()

    @step()
    async def end_step(self, event: EventA, thread_context: ThreadContext, run_context: RunContext) -> StopEvent:
        payload = await run_context.get("payload", [])
        print(f"[SimpleAgent.end_step] Payload is '{payload}'")

        thread_count = await thread_context.get("count", 0)
        run_count = await run_context.get("count", 0)
        print(f"[SimpleAgent.end_step] Called {thread_count} times in thread, {run_count} times in run")
        return StopEvent()