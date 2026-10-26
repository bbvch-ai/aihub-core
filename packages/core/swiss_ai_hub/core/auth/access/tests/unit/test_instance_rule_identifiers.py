import pytest

from swiss_ai_hub.core.auth.access.access_checker import AccessChecker

NOT_CONCRETE = [None, "", "None.None", "*", ">", "?>", "?*", "a.b", "a b"]
BROAD_CHECKER = AccessChecker(["aihub.user.>"], tenant_access_rules=["aihub.admin.>"])


@pytest.mark.parametrize("identifier", NOT_CONCRETE)
@pytest.mark.parametrize(
    "builder",
    [
        AccessChecker.process_user_rule,
        AccessChecker.process_admin_rule,
        AccessChecker.agent_instance_user_rule,
        AccessChecker.agent_instance_admin_rule,
    ],
)
def test_instance_rules_reject_an_identifier_that_is_not_one_concrete_token(builder, identifier):
    with pytest.raises(ValueError):
        builder("SomeClass", identifier)
    with pytest.raises(ValueError):
        builder(identifier, "some-id")


def test_process_access_for_a_missing_process_raises_instead_of_matching_a_broad_rule():
    with pytest.raises(ValueError):
        BROAD_CHECKER.has_access_to_process(None, None)


def test_agent_access_for_a_missing_agent_raises_instead_of_matching_a_broad_rule():
    with pytest.raises(ValueError):
        BROAD_CHECKER.has_access_to_agent(None, None)


def test_concrete_identifiers_still_build_the_canonical_rule():
    assert AccessChecker.process_user_rule("InvoiceProcess", "p-1_a") == "aihub.user.process.InvoiceProcess.p-1_a"
    assert AccessChecker.agent_instance_admin_rule("RAGAgent", "64f0c0ffee") == "aihub.admin.agent.RAGAgent.64f0c0ffee"
