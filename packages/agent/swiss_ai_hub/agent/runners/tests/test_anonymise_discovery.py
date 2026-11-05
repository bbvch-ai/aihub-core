"""Every blueprint offers the anonymisation toggle, with no code of its own, after its own settings.

Built from the configs the agents' entry points (`app/*/main.py`) publish, so a new blueprint that copies that
shape is covered the day it is added here.
"""

import importlib

import pytest
from swiss_ai_hub.core.agents import ANONYMISE_CONFIG_KEY, CRON_CONFIG_KEY
from swiss_ai_hub.core.form import ConfigSpecs
from swiss_ai_hub.core.form.elements.checkbox import Checkbox

# rag_agent first: rag.preconditions/step_functions only import cleanly in the runtime (rag_agent-first) order.
import swiss_ai_hub.agent.agents.rag_agent  # noqa: F401,E402
from swiss_ai_hub.agent.runners.agent_runner import AgentRunner

BLUEPRINTS = [
    ("email_classification_agent", "EmailClassificationAgent", "EmailClassificationAgentConfig"),
    ("expert_asking_agent", "ExpertAskingAgent", "ExpertAskingAgentConfig"),
    ("expert_rag_agent", "ExpertRAGAgent", "ExpertRAGAgentConfig"),
    ("few_shot_agent", "FewShotAgent", "FewShotAgentConfig"),
    ("imap_agent", "ImapAgent", "ImapAgentConfig"),
    ("llm_wrapping_agent", "LLMWrappingAgent", "LLMWrappingAgentConfig"),
    ("mcp_react_agent", "McpReactAgent", "McpReactAgentConfig"),
    ("namespace_selection_agent", "NamespaceSelectionAgent", "NamespaceSelectionAgentConfig"),
    ("rag_agent", "RAGAgent", "RAGAgentConfig"),
    ("retrieval_agent", "RetrievalAgent", "RetrievalAgentConfig"),
    ("universal_agent", "UniversalAgent", "UniversalAgentConfig"),
]


def _runner(package: str, agent_name: str, config_name: str) -> AgentRunner:
    module = importlib.import_module(f"swiss_ai_hub.agent.agents.{package}")
    config_module = module if hasattr(module, config_name) else importlib.import_module(f"{module.__name__}.configs")
    return AgentRunner(
        agent_type=getattr(module, agent_name), agent_config=getattr(config_module, config_name).as_form()
    )


@pytest.mark.parametrize(("package", "agent_name", "config_name"), BLUEPRINTS, ids=[b[1] for b in BLUEPRINTS])
def test_should_offer_the_toggle_on_every_blueprint(package: str, agent_name: str, config_name: str) -> None:
    runner = _runner(package, agent_name, config_name)

    names = [element.name for element in runner._published_form()]
    platform = [name for name in names if name in (ANONYMISE_CONFIG_KEY, CRON_CONFIG_KEY)]

    assert isinstance(runner.published_config.anonymise, Checkbox)
    assert names[-len(platform) :] == platform
    assert platform[0] == ANONYMISE_CONFIG_KEY
    specs = ConfigSpecs.from_form(runner.published_config, runner.agent_class)
    assert specs.config_schema["properties"][ANONYMISE_CONFIG_KEY]["type"] == "boolean"
