import pytest

from swiss_ai_hub.core.auth.access.access_checker import AccessChecker


@pytest.mark.parametrize(
    ("rules", "expected"),
    [
        ([], False),
        (["aihub.admin.agent.MyAgent.inst1"], True),
        (["aihub.admin.agent.MyAgent"], False),
        (["aihub.admin.agent.MyAgent.*"], True),
        (["aihub.admin.agent.>"], True),
        (["aihub.admin.>"], True),
        (["aihub.user.agent.MyAgent.inst1"], False),
        (["aihub.user.agent.>"], False),
        (["aihub.admin.agent.OtherAgent.inst1"], False),
        (["aihub.admin.agent.OtherAgent.*"], False),
        (["not-a-valid-rule", "aihub.admin.agent.MyAgent.inst1"], True),
    ],
)
def test_rules_grant_admin_to_agent_instance(rules: list[str], expected: bool) -> None:
    assert AccessChecker.rules_grant_admin_to_agent_instance(rules, "MyAgent", "inst1") is expected


def test_agent_instance_rule_builders() -> None:
    assert AccessChecker.agent_instance_admin_rule("MyAgent", "inst1") == "aihub.admin.agent.MyAgent.inst1"
    assert AccessChecker.agent_instance_user_rule("MyAgent", "inst1") == "aihub.user.agent.MyAgent.inst1"
