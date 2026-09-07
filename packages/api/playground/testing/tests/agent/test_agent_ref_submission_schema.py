"""Guards the constraints on the path that actually runs when a config is saved.

`AgentRef`'s constraints only protect a real save if they survive being emitted as JSON Schema and
rebuilt by jambo — which is what `AgentService` validates a submission against. A future jambo change
that dropped `minLength` or `pattern` would silently reopen the hole, and no Pydantic-level test would
notice.

The form below stands in for any config that delegates to an agent; it is declared here rather than
imported from `packages/agent` so this scope keeps to its declared dependencies.
"""

from typing import Annotated, Self

import pytest
from pydantic import Field
from swiss_ai_hub.core.agents import AgentRef
from swiss_ai_hub.core.form import AgentSelector, Form
from swiss_ai_hub.jambo import SchemaConverter


class DelegationForm(Form):
    rag_agent: Annotated[AgentRef | AgentSelector, Field(description="The target agent to delegate queries to.")]

    @classmethod
    def as_form(cls) -> Self:
        return cls(rag_agent=AgentSelector(label="Agent"))


@pytest.fixture(scope="module")
def emitted_schema() -> dict:
    return DelegationForm.as_form().to_configurable_submission_model().model_json_schema()


@pytest.fixture(scope="module")
def submission_model(emitted_schema: dict) -> type:
    return SchemaConverter.build(emitted_schema)


def test_min_length_survives_into_the_emitted_json_schema(emitted_schema: dict):
    agent_ref_properties = emitted_schema["$defs"]["AgentRef"]["properties"]

    assert agent_ref_properties["agent_class"]["minLength"] == 1
    assert agent_ref_properties["agent_id"]["minLength"] == 1


def test_pattern_survives_into_the_emitted_json_schema(emitted_schema: dict):
    """`minLength` alone accepts a single space, which renders as a blank NATS segment just as `""` does.

    The pattern is deliberately the same character class `AccessChecker.validate_permission_template`
    accepts, so a reference that passes this save path can never make the access check raise instead of
    answering. It must also stay anchored: pydantic-core treats `pattern` as a search.
    """
    agent_ref_properties = emitted_schema["$defs"]["AgentRef"]["properties"]

    assert agent_ref_properties["agent_class"]["pattern"] == r"^[A-Za-z0-9_-]+$"
    assert agent_ref_properties["agent_id"]["pattern"] == r"^[A-Za-z0-9_-]+$"


def test_complete_reference_is_accepted(submission_model: type):
    submission_model(rag_agent={"agent_class": "RAGAgent", "agent_id": "shared-knowledge-rag"})


@pytest.mark.parametrize(
    ("agent_class", "agent_id"),
    [("RAGAgent", ""), ("", "shared-knowledge-rag")],
)
def test_blank_half_is_rejected_on_the_save_path(submission_model: type, agent_class: str, agent_id: str):
    with pytest.raises(Exception, match="at least 1 character"):
        submission_model(rag_agent={"agent_class": agent_class, "agent_id": agent_id})


@pytest.mark.parametrize(
    ("agent_class", "agent_id"),
    [("RAGAgent", "   "), ("   ", "shared-knowledge-rag")],
)
def test_whitespace_only_half_is_rejected_on_the_save_path(
    submission_model: type, agent_class: str, agent_id: str
) -> None:
    with pytest.raises(Exception, match="pattern"):
        submission_model(rag_agent={"agent_class": agent_class, "agent_id": agent_id})


@pytest.mark.parametrize(
    ("agent_class", "agent_id"),
    [("  RAGAgent  ", "shared-knowledge-rag"), ("RAGAgent", " shared-knowledge-rag ")],
)
def test_padded_half_is_rejected_on_the_save_path(submission_model: type, agent_class: str, agent_id: str) -> None:
    """The unanchored pattern this replaced accepted a padded half, which reaches `to_subject` verbatim."""
    with pytest.raises(Exception, match="pattern"):
        submission_model(rag_agent={"agent_class": agent_class, "agent_id": agent_id})


@pytest.mark.parametrize(
    ("agent_class", "agent_id"),
    [("RAG.Agent", "shared-knowledge-rag"), ("RAGAgent", "a.b"), ("RAGAgent", "*")],
)
def test_subject_separator_is_rejected_on_the_save_path(
    submission_model: type, agent_class: str, agent_id: str
) -> None:
    """A `.` splits the segment into two NATS tokens and a `*` fans the delegation out to every instance."""
    with pytest.raises(Exception, match="pattern"):
        submission_model(rag_agent={"agent_class": agent_class, "agent_id": agent_id})


@pytest.mark.parametrize(
    ("agent_class", "agent_id"),
    [
        ("RAGAgent", "shared-knowledge-rag"),
        ("ExpertAskingAgent", "engineering-expert"),
        ("LLMWrappingAgent", "dev_agent"),
    ],
)
def test_the_shipped_references_are_accepted_on_the_save_path(
    submission_model: type, agent_class: str, agent_id: str
) -> None:
    """So the pattern cannot be tightened past the references the app templates ship without failing here."""
    submission_model(rag_agent={"agent_class": agent_class, "agent_id": agent_id})
