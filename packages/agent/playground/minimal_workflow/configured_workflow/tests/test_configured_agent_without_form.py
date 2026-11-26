"""A config that does not override `as_form()` keeps running now that the dispatcher can decrypt secrets (#1587).

`AgentConfig.secret_field_paths()` builds the form, which `ConfiguredAgentConfig` cannot, so the dispatcher must only
ask for the paths once a config holds ciphertext, never when it is constructed.
"""

import pytest
from swiss_ai_hub.core.events.agent import StartEvent
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing import async_test

from playground.minimal_workflow.configured_workflow.configured_agent import ConfiguredAgent
from playground.minimal_workflow.configured_workflow.configured_agent_config import (
    ConfiguredAgentConfig,
    StartStepConfig,
)
from playground.minimal_workflow.configured_workflow.events.event_configured_b import EventConfiguredB
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner


@async_test
async def test_a_config_without_its_own_form_still_runs(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("AIHUB_CONFIG_ENCRYPTION_KEY", raising=False)
    runner = AgentTestRunner(
        agent_type=ConfiguredAgent,
        agent_config=ConfiguredAgentConfig(
            agent_id="configured_agent",
            name=LocaleString(en="Configured Agent"),
            description=LocaleString(en="This is a very configured agent"),
            some_agent_value="agent-value",
            start_step_config=StartStepConfig(some_step_value="step-value"),
        ),
    )

    async with runner.test_run() as topic:
        await runner.send_event_from_topic(start_event=StartEvent(), topic=topic)

    assert not runner.has_exception_event
    assert runner.get_event_of_class(EventConfiguredB).payload == "agent-value"
    assert runner.has_stop_event
