"""Both playground blueprints compose the tool loop with a capability tool and a LlamaIndex tool spec: one lets the
loop answer, the other gathers with it and answers in its own step."""

import pytest

from playground.minimal_workflow.tool_loop_workflow.answering_tool_loop_agent import AnsweringToolLoopAgent
from playground.minimal_workflow.tool_loop_workflow.gathering_tool_loop_agent import GatheringToolLoopAgent
from playground.minimal_workflow.tool_loop_workflow.tool_loop_playground_config import ToolLoopPlaygroundConfig
from swiss_ai_hub.agent.capabilities import ToolLoop


@pytest.mark.parametrize("agent", [AnsweringToolLoopAgent, GatheringToolLoopAgent], ids=lambda agent: agent.__name__)
def test_the_blueprint_validates_with_both_tool_kinds(agent):
    agent.validate_workflow(ToolLoopPlaygroundConfig)

    steps = {step.__name__ for step in agent.get_steps()}
    assert {
        "decide_step",
        "gate_step",
        "join_step",
        "run_function_step",
        "search_tool_call_step",
        "search_step",
    } <= steps
    assert agent.tools.names() == ["search_knowledge", "current_time"]


def test_the_published_form_offers_the_blueprints_tools_for_approval():
    form = ToolLoop.published_config(ToolLoopPlaygroundConfig.as_form(), AnsweringToolLoopAgent)

    assert [option["value"] for option in form.tool_loop.approvals[0].tool.options] == [
        "search_knowledge",
        "current_time",
    ]
