from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.nats.events.discovery.ClassDiscoveryRequestEvent import ClassDiscoveryRequestEvent
from aihub_lib.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from aihub_lib.testing.asyncio_utils.bdd import async_test
from bson import ObjectId
from pytest_bdd import given, parsers, scenarios, then, when

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from playground.minimal_workflow.discoverable_workflow.DiscoverableAgent import DiscoverableAgent
from playground.minimal_workflow.discoverable_workflow.DiscoverableAgentConfig import (
    DiscoverableAgentConfig,
)

enable_logging()

scenarios("./features/discoverable_agent.feature")


@given("a DiscoverableAgent runner", target_fixture="agent_runner")
def _():
    return AgentTestRunner(
        agent_type=DiscoverableAgent,
        agent_config=DiscoverableAgentConfig(
            agent_id="discoverable_agent",
            agent_class=DiscoverableAgent.__name__,
            name=LocaleString(en="Discoverable Agent"),
            description=LocaleString(en="This is a very discoverable agent"),
        ),
    )


@when(parsers.parse("a DiscoveryRequestEvent is sent"))
@async_test
async def _(agent_runner: AgentTestRunner):
    async with agent_runner.test_run(delay_before_stop=10):
        call_id = str(ObjectId())
        await agent_runner.nc_publisher.publish_event(
            event=ClassDiscoveryRequestEvent(),
            subject=AgentTopicManager().get_agent_class_discovery_subject_request(call_id=call_id),
        )


@then(parsers.parse("a DiscoveryRequestEvent is present"))
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_discovery_request_event, "Agent did not receive discovery request event"


@then("an AgentDiscoveryResponseEvent with the agent's class and ID is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_own_agent_discovery_response_event, "Agent did not send discovery response event"
