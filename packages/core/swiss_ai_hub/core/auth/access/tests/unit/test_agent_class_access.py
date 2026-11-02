"""Covers ``has_access_to_agent_class`` — "may this subject reach this blueprint at all".

The bare class root is the interesting case: it is what a curated tenant holds, and what *creating* a
profile is guarded on. Probing ``?*`` would answer no for it, because that form demands a rule strictly
below the class — so a tenant able to create profiles but holding none yet would see no blueprints at all.
"""

import pytest

from swiss_ai_hub.core.auth.access.access_checker import AccessChecker


def _checker(tenant_rules: list[str]) -> AccessChecker:
    """Resolves against the broadest role, so whatever is denied is denied by the tenant ceiling alone."""
    return AccessChecker(user_access_rules=["aihub.admin.>"], tenant_access_rules=tenant_rules)


@pytest.mark.parametrize(
    ("tenant_rules", "expected"),
    [
        ([], False),
        # What a curated tenant is seeded with, and the case ``?*`` would have got wrong.
        (["aihub.admin.agent.MyAgent"], True),
        # What tenants seeded before the curated shape still hold.
        (["aihub.admin.agent.MyAgent.>"], True),
        (["aihub.admin.agent.MyAgent.inst1"], True),
        (["aihub.admin.agent.>"], True),
        (["aihub.admin.>"], True),
        # A user-level grant is enough to *reach* the blueprint; creating a profile is guarded separately.
        (["aihub.user.agent.MyAgent"], True),
        (["aihub.admin.agent.OtherAgent"], False),
        (["aihub.admin.knowledge.>"], False),
    ],
)
def test_has_access_to_agent_class(tenant_rules: list[str], expected: bool) -> None:
    assert _checker(tenant_rules).has_access_to_agent_class("MyAgent") is expected


def test_reaching_a_blueprint_does_not_reach_its_profiles() -> None:
    """The distinction the curated ceiling rests on: profiles share one global collection with no tenant
    column, so a tenant that may build on a blueprint must not thereby hold everyone else's profiles."""
    checker = _checker(["aihub.admin.agent.MyAgent"])

    assert checker.has_access_to_agent_class("MyAgent")
    assert not checker.has_access_to_agent("MyAgent", "someone-elses-profile")
