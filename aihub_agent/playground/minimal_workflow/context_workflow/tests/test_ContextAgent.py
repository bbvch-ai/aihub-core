import pytest
from pytest_bdd import scenarios, given, when, then, parsers

# Example imports — update as needed for your actual project structure:
from aihub_lib.nats.topics.agents.PartialAgentTopic import PartialAgentTopic
from aihub_lib.testing.asyncio_utils.bdd import async_test
from bson import ObjectId

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from playground.minimal_workflow.context_workflow.ContextAgent import ContextAgent
from playground.minimal_workflow.context_workflow.ContextAgentConfig import ContextAgentConfig
from playground.minimal_workflow.context_workflow.events.CustomStartEvent import CustomStartEvent

from aihub_lib.i18n.LocaleString import LocaleString

# Tell pytest-bdd to look for the scenario(s) in this feature file:
scenarios("features/context_agent.feature")

# We will store each run's run_id + thread_id here, so we can re-check context later:
RUN_DATA = []


@given("a ContextAgent test runner", target_fixture="test_runner")
def context_agent_test_runner() -> AgentTestRunner:
    """
    Instantiates the AgentTestRunner with a ContextAgentConfig.
    """
    return AgentTestRunner(
        agent_type=ContextAgent,
        agent_config=ContextAgentConfig(
            agent_id="context_agent",
            name=LocaleString(en="Context Agent"),
            description=LocaleString(en="This is an agent that accesses the run and thread context"),
            system_prompt=LocaleString(en="You are an agent"),
        ),
    )


@when(parsers.parse("'{number_of_runs:d}' runs are executed with distinct RunContexts"))
@async_test
async def execute_multiple_runs_same_thread(test_runner: AgentTestRunner, number_of_runs: int):
    """
    Executes N runs in the SAME thread (one test_run context) but with different run_id each time.
    """
    async with test_runner.test_run() as base_topic:
        # We'll reuse the same thread_id & display_id from base_topic
        thread_id = base_topic.thread_id
        display_id = base_topic.display_id

        # Create a NEW run_id for each run (distinct RunContext)
        new_run_id = str(ObjectId())
        new_topic = PartialAgentTopic(
            agent_class=base_topic.agent_class,
            agent_id=base_topic.agent_id,
            run_id=new_run_id,
            thread_id=thread_id,
            display_id=display_id,
        )
        # Send the CustomStartEvent to kick off that run
        start_event = CustomStartEvent(payload=f"Run {0 + 1}")
        await test_runner.send_event_from_topic(start_event, new_topic)
        events = await test_runner.dispatcher.event_store.get_all_events(new_run_id)
        # Record the run/thread so we can later inspect run_context + thread_context
        RUN_DATA.append({"run_id": new_run_id, "thread_id": thread_id})

    print("test")


@then(parsers.parse("the thread context count should increment to '{expected_count:d}'"))
@async_test
async def verify_thread_context_count(test_runner: AgentTestRunner, expected_count: int):
    """
    Since we used the same thread, the agent increments a 'count' in ThreadContext each run.
    So after N runs, we expect the thread count to be N.
    """
    # All runs used the same thread_id, so just grab from the first one
    thread_id = RUN_DATA[0]["thread_id"]
    thread_context = await test_runner.get_thread_context(thread_id)
    actual = await thread_context.get("count", 0)
    assert actual == expected_count, f"Expected thread context count = {expected_count}, got {actual}"


@then(parsers.parse("each RunContext count should be '{expected_count:d}'"))
@async_test
async def verify_run_context_count(test_runner: AgentTestRunner, expected_count: int):
    """
    Each run's RunContext has its own 'count' that starts at 0 and gets incremented once,
    so we expect each to be exactly 1, showing they don't interfere.
    """
    for i, data in enumerate(RUN_DATA, start=1):
        run_id = data["run_id"]
        thread_id = data["thread_id"]

        run_context = await test_runner.get_run_context(run_id, thread_id)
        actual = await run_context.get("count", 0)
        assert actual == expected_count, f"Run {i}: expected RunContext.count = {expected_count}, got {actual}"


@then("RunContext values should remain isolated across runs")
@async_test
async def verify_run_context_isolation(test_runner: AgentTestRunner):
    """
    Confirms that increments in one RunContext do not spill over into another.
    For example, each run saw 'count=1' rather than a cumulative total across runs.
    """
    counts = []
    for data in RUN_DATA:
        run_context = await test_runner.get_run_context(data["run_id"], data["thread_id"])
        counts.append(await run_context.get("count", 0))

    # In this scenario, each run has count=1 if they are truly isolated (no carry-over).
    # If there was cross-run interference, we'd see something like [1,2,3].
    assert len(set(counts)) == 1, "RunContext values appear to overlap; counts differ!"
    assert counts[0] == 1, "Expected each run's context count to be 1, but found something else."
