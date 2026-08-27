import pytest
from pydantic import ValidationError

from swiss_ai_hub.core.agents.agent_ref import AgentRef
from swiss_ai_hub.core.form.elements.agent_selector import AgentSelector
from swiss_ai_hub.core.i18n.locale_string import LocaleString


def _label() -> LocaleString:
    return LocaleString(de="Agent", en="Agent", fr="Agent", it="Agent")


def test_required_agent_selector_emits_agent_ref_required_rule():
    """FormKit's own `required` passes on any non-empty object, and this element's value is always an
    `{agent_class, agent_id}` object — so picking a class alone would slip through."""
    assert AgentSelector(label=_label(), required=True).validation == "agentRefRequired"


def test_optional_agent_selector_emits_no_rule():
    assert AgentSelector(label=_label(), required=False).validation == ""


def test_additional_rules_are_appended_after_agent_ref_required():
    element = AgentSelector(label=_label(), required=True, additional_validation_rules="length:3")
    assert element.validation == "agentRefRequired|length:3"


class TestAgentRefConstraints:
    """A blank half renders as the NATS wildcard `*` in `PartialAgentTopic.to_subject`, so the
    delegation reaches no instance and the caller waits forever with nothing logged."""

    def test_complete_reference_is_accepted(self):
        reference = AgentRef(agent_class="RAGAgent", agent_id="shared-knowledge-rag")
        assert reference.agent_id == "shared-knowledge-rag"

    @pytest.mark.parametrize(
        ("agent_class", "agent_id"),
        [("RAGAgent", ""), ("", "shared-knowledge-rag"), ("", "")],
    )
    def test_blank_half_is_rejected(self, agent_class: str, agent_id: str):
        with pytest.raises(ValidationError):
            AgentRef(agent_class=agent_class, agent_id=agent_id)

    @pytest.mark.parametrize(
        ("agent_class", "agent_id"),
        [("RAGAgent", "   "), ("   ", "shared-knowledge-rag"), ("\t", "\n")],
    )
    def test_whitespace_only_half_is_rejected(self, agent_class: str, agent_id: str):
        """A whitespace segment reaches NATS just as blank as an empty one, and `min_length` alone lets it through."""
        with pytest.raises(ValidationError):
            AgentRef(agent_class=agent_class, agent_id=agent_id)
