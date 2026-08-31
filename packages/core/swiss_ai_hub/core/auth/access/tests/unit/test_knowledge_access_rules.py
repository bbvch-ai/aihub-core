import pytest

from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.auth.access.access_level import AccessLevel

DATABASE = "researchdocs"
NAMESPACE = "reports"


class TestRuleBuilders:
    def test_database_rules_name_the_database(self):
        assert AccessChecker.knowledge_database_admin_rule(DATABASE) == f"aihub.admin.knowledge.{DATABASE}"
        assert AccessChecker.knowledge_database_user_rule(DATABASE) == f"aihub.user.knowledge.{DATABASE}"

    def test_namespace_rules_nest_under_their_database(self):
        assert (
            AccessChecker.knowledge_namespace_admin_rule(DATABASE, NAMESPACE)
            == f"aihub.admin.knowledge.{DATABASE}.{NAMESPACE}"
        )
        assert (
            AccessChecker.knowledge_namespace_user_rule(DATABASE, NAMESPACE)
            == f"aihub.user.knowledge.{DATABASE}.{NAMESPACE}"
        )


class TestRulesGrantAdmin:
    @pytest.mark.parametrize("rule", ["aihub.admin.>", "aihub.admin.knowledge.>", f"aihub.admin.knowledge.{DATABASE}"])
    def test_a_covering_rule_makes_a_per_database_grant_redundant(self, rule):
        assert AccessChecker.rules_grant_admin([rule], AccessChecker.knowledge_database_admin_rule(DATABASE))

    @pytest.mark.parametrize(
        "rule",
        [
            "aihub.admin.knowledge.otherdb",
            f"aihub.user.knowledge.{DATABASE}",
            "aihub.admin.agent.>",
        ],
    )
    def test_an_unrelated_or_weaker_rule_does_not_cover_it(self, rule):
        assert not AccessChecker.rules_grant_admin([rule], AccessChecker.knowledge_database_admin_rule(DATABASE))


class TestCreateGuardLevel:
    def test_a_per_database_admin_may_not_create_a_sibling_database(self):
        """Creating is guarded on the knowledge root, so admin of one database no longer mints others."""
        checker = AccessChecker(
            user_access_rules=[f"aihub.admin.knowledge.{DATABASE}"],
            tenant_access_rules=["aihub.admin.>"],
        )

        assert checker.access_level("aihub.admin.knowledge") != AccessLevel.ACCESS_ADMIN

    def test_a_knowledge_root_admin_may_create(self):
        checker = AccessChecker(
            user_access_rules=["aihub.admin.knowledge"],
            tenant_access_rules=["aihub.admin.>"],
        )

        assert checker.access_level("aihub.admin.knowledge") == AccessLevel.ACCESS_ADMIN

    def test_the_wildcard_form_alone_does_not_satisfy_the_root_create_guard(self):
        """Deployments whose ceiling is only ``aihub.admin.knowledge.>`` need the root rule adding."""
        checker = AccessChecker(
            user_access_rules=["aihub.admin.knowledge.>"],
            tenant_access_rules=["aihub.admin.>"],
        )

        assert checker.access_level("aihub.admin.knowledge") != AccessLevel.ACCESS_ADMIN
