from typing import Any

import pytest
from pydantic import ValidationError

from swiss_ai_hub.core.agents.agent_ref import AgentRef
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.form.base.config_authorization_violation import ConfigAuthorizationViolation
from swiss_ai_hub.core.form.elements.agent_selector import AgentSelector
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString


def _label() -> LocaleString:
    return LocaleString(de="Agent", en="Agent", fr="Agent", it="Agent")


def _checker(*allowed: str) -> AccessChecker:
    """A real checker, not a mock: the blank-segment behaviour under test lives in `AccessChecker` itself."""
    return AccessChecker(
        user_access_rules=[AccessChecker.agent_instance_user_rule(*reference.split("/")) for reference in allowed],
        tenant_access_rules=["aihub.admin.>"],
    )


def _violations(value: Any, checker: AccessChecker) -> list[ConfigAuthorizationViolation]:
    element = AgentSelector(label=_label(), name="target_agent")
    return element.validate_authorization("target_agent", value, checker, set(), LocaleHandler(locale="en"))


def test_required_agent_selector_emits_agent_ref_required_rule():
    """FormKit's own `required` passes on any non-empty object, and this element's value is always an
    `{agent_class, agent_id}` object — so picking a class alone would slip through."""
    assert AgentSelector(label=_label(), required=True).validation == "agentRefRequired"


def test_optional_agent_selector_emits_no_rule():
    assert AgentSelector(label=_label(), required=False).validation == ""


def test_additional_rules_are_appended_after_agent_ref_required():
    element = AgentSelector(label=_label(), required=True, additional_validation_rules="length:3")
    assert element.validation == "agentRefRequired|length:3"

    cross_field = AgentSelector(label=_label(), required=True, additional_validation_rules="memberOf:allowed_agents")
    assert cross_field.validation == "agentRefRequired|memberOf:allowed_agents"


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

    @pytest.mark.parametrize(
        ("agent_class", "agent_id"),
        [("  RAGAgent  ", "shared-knowledge-rag"), ("RAGAgent", " shared-knowledge-rag ")],
    )
    def test_padded_half_is_rejected(self, agent_class: str, agent_id: str):
        """pydantic-core treats `pattern` as a *search*, so the unanchored `\\S` this replaced accepted these.

        A padded half is not blank, so no other guard catches it: it reaches `to_subject` verbatim and
        renders a subject with spaces in it, which addresses no instance.
        """
        with pytest.raises(ValidationError):
            AgentRef(agent_class=agent_class, agent_id=agent_id)

    @pytest.mark.parametrize(
        ("agent_class", "agent_id"),
        [("RAG Agent", "shared-knowledge-rag"), ("RAGAgent", "shared rag")],
    )
    def test_interior_whitespace_is_rejected(self, agent_class: str, agent_id: str):
        """A space inside the segment splits it into two NATS tokens, shifting every later segment."""
        with pytest.raises(ValidationError):
            AgentRef(agent_class=agent_class, agent_id=agent_id)

    @pytest.mark.parametrize(
        ("agent_class", "agent_id"),
        [("RAG.Agent", "shared-knowledge-rag"), ("RAGAgent", "a.b"), ("RAGAgent", "*"), ("RAGAgent", ">")],
    )
    def test_subject_separator_or_wildcard_half_is_rejected(self, agent_class: str, agent_id: str):
        """Each of these is a NATS token separator or wildcard, so the delegation fans out or misses.

        Each also makes `AccessChecker.validate_permission_template` *raise* rather than deny, which would
        turn the intended 403 in `validate_authorization` into a 500.
        """
        with pytest.raises(ValidationError):
            AgentRef(agent_class=agent_class, agent_id=agent_id)

    @pytest.mark.parametrize(
        ("agent_class", "agent_id"),
        [
            ("RAGAgent", "shared-knowledge-rag"),
            ("ExpertAskingAgent", "engineering-expert"),
            ("ExpertRAGAgent", "engineering-expert-rag"),
            ("LLMWrappingAgent", "dev_agent"),
        ],
    )
    def test_every_shipped_reference_is_accepted(self, agent_class: str, agent_id: str):
        """The counterweight to the rejections above: these are the references the app templates ship.

        Tightening the pattern further than the class `validate_permission_template` accepts would start
        rejecting configs that work today, so this pins the accepted side too.
        """
        assert AgentRef(agent_class=agent_class, agent_id=agent_id).agent_id == agent_id


class TestPartialReferenceAuthorization:
    """Exercised against a real `AccessChecker`, because a mock cannot show the failure this guards.

    `has_access_to_agent` builds the permission template `aihub.user.agent.{class}.{id}`, and
    `validate_permission_template` raises `ValueError` on a blank segment instead of returning False.
    Asking it about a half-filled reference therefore turns an intended 403 into an unhandled 500 —
    so the element must deny such a reference on its own, without consulting the checker.
    """

    @pytest.mark.parametrize(
        ("value", "expected_resource"),
        [
            ({"agent_class": "MyAgent"}, "MyAgent/"),
            ({"agent_class": "MyAgent", "agent_id": ""}, "MyAgent/"),
            ({"agent_class": "MyAgent", "agent_id": "   "}, "MyAgent/"),
            ({"agent_id": "inst_1"}, "/inst_1"),
            ({"agent_class": "  ", "agent_id": "inst_1"}, "/inst_1"),
        ],
    )
    def test_half_filled_reference_is_denied_without_raising(self, value: dict, expected_resource: str):
        violations = _violations(value, _checker("MyAgent/inst_1"))

        assert len(violations) == 1
        assert violations[0].resource_type == "agent"
        assert violations[0].resource == expected_resource

    @pytest.mark.parametrize("value", [{}, {"agent_class": "", "agent_id": ""}, {"agent_class": " ", "agent_id": "\t"}])
    def test_fully_unset_reference_is_skipped(self, value: dict):
        """An untouched field is the `required` rule's job, not the authorization checker's."""
        assert _violations(value, _checker("MyAgent/inst_1")) == []

    def test_complete_reference_the_user_may_access_is_allowed(self):
        assert _violations({"agent_class": "MyAgent", "agent_id": "inst_1"}, _checker("MyAgent/inst_1")) == []

    def test_complete_reference_the_user_may_not_access_is_denied(self):
        violations = _violations({"agent_class": "SecretAgent", "agent_id": "inst_1"}, _checker("MyAgent/inst_1"))

        assert len(violations) == 1
        assert violations[0].resource == "SecretAgent/inst_1"

    def test_non_dict_value_is_skipped(self):
        assert _violations("not-a-reference", _checker("MyAgent/inst_1")) == []

    @pytest.mark.parametrize("half", [123, {"a": 1}, ["MyAgent"]])
    def test_non_string_half_is_denied_without_raising(self, half: Any):
        """`validate_config_for_*` normally rejects these first, but it runs off a persisted schema that
        can be stale, so this must not be the layer that turns odd input into a 500."""
        violations = _violations({"agent_class": half, "agent_id": "inst_1"}, _checker("MyAgent/inst_1"))

        assert len(violations) == 1
        assert violations[0].resource == "/inst_1"
