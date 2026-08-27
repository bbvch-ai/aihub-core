"""Guards the constraint on the path that actually runs when a config is saved.

`AgentRef`'s `min_length` only protects a real save if it survives being emitted as JSON Schema and
rebuilt by jambo — which is what `AgentService` validates a submission against. A future jambo change
that dropped `minLength` would silently reopen the hole, and no Pydantic-level test would notice.
"""

import pytest
from swiss_ai_hub.agent.agents.namespace_selection_agent.configs import RAGDelegationConfig
from swiss_ai_hub.jambo import SchemaConverter


@pytest.fixture(scope="module")
def submission_model() -> type:
    schema = RAGDelegationConfig.as_form().to_configurable_submission_model().model_json_schema()
    return SchemaConverter.build(schema)


def test_min_length_survives_into_the_emitted_json_schema():
    schema = RAGDelegationConfig.as_form().to_configurable_submission_model().model_json_schema()
    agent_ref_properties = schema["$defs"]["AgentRef"]["properties"]

    assert agent_ref_properties["agent_class"]["minLength"] == 1
    assert agent_ref_properties["agent_id"]["minLength"] == 1


def test_complete_reference_is_accepted(submission_model: type):
    submission_model(rag_agent={"agent_class": "RAGAgent", "agent_id": "shared-knowledge-rag"})


@pytest.mark.parametrize(
    ("agent_class", "agent_id"),
    [("RAGAgent", ""), ("", "shared-knowledge-rag")],
)
def test_blank_half_is_rejected_on_the_save_path(submission_model: type, agent_class: str, agent_id: str):
    with pytest.raises(Exception, match="at least 1 character"):
        submission_model(rag_agent={"agent_class": agent_class, "agent_id": agent_id})
