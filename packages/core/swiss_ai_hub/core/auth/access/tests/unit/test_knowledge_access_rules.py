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


class TestVisibilityTemplates:
    """The controller lists a database when the caller holds any rule at or below it, and gates the whole
    listing on any knowledge rule at all — so the creator-only ``aihub.admin.knowledge`` root rule and a bare
    ``aihub.user.knowledge.{db}`` rule must both get through."""

    @staticmethod
    def _checker(*rules: str) -> AccessChecker:
        return AccessChecker(user_access_rules=list(rules), tenant_access_rules=["aihub.admin.>"])

    @pytest.mark.parametrize(
        ("rule", "expected"),
        [
            ("aihub.admin.knowledge", AccessLevel.ACCESS_ADMIN),
            (f"aihub.admin.knowledge.{DATABASE}", AccessLevel.ACCESS_ADMIN),
            ("aihub.admin.knowledge.>", AccessLevel.ACCESS_ADMIN),
            (f"aihub.user.knowledge.{DATABASE}", AccessLevel.ACCESS_USER),
            (f"aihub.user.knowledge.{DATABASE}.{NAMESPACE}", AccessLevel.ACCESS_USER),
            ("aihub.user.knowledge.>", AccessLevel.ACCESS_USER),
            ("aihub.user.agent.>", AccessLevel.ACCESS_DENIED),
        ],
    )
    def test_listing_gate_admits_every_knowledge_rule_including_the_root(self, rule, expected):
        assert self._checker(rule).access_level("aihub.user.knowledge.?>") == expected

    @pytest.mark.parametrize(
        ("rule", "expected"),
        [
            (f"aihub.user.knowledge.{DATABASE}", AccessLevel.ACCESS_USER),
            (f"aihub.admin.knowledge.{DATABASE}", AccessLevel.ACCESS_ADMIN),
            (f"aihub.user.knowledge.{DATABASE}.{NAMESPACE}", AccessLevel.ACCESS_USER),
            (f"aihub.user.knowledge.{DATABASE}.*", AccessLevel.ACCESS_USER),
            (f"aihub.user.knowledge.{DATABASE}.>", AccessLevel.ACCESS_USER),
            ("aihub.user.knowledge.>", AccessLevel.ACCESS_USER),
            ("aihub.admin.knowledge", AccessLevel.ACCESS_DENIED),
            ("aihub.user.knowledge.otherdb", AccessLevel.ACCESS_DENIED),
        ],
    )
    def test_a_database_is_visible_with_any_rule_at_or_below_it(self, rule, expected):
        assert self._checker(rule).access_level(f"aihub.user.knowledge.{DATABASE}.?>") == expected

    @pytest.mark.parametrize(
        "rule",
        [f"aihub.user.knowledge.{DATABASE}", f"aihub.admin.knowledge.{DATABASE}", "aihub.admin.knowledge"],
    )
    def test_a_database_level_rule_alone_reveals_no_namespace(self, rule):
        namespace_rule = AccessChecker.knowledge_namespace_user_rule(DATABASE, NAMESPACE)
        assert self._checker(rule).access_level(namespace_rule) == AccessLevel.ACCESS_DENIED

    def test_a_database_admin_creates_namespaces_but_does_not_manage_unseen_ones(self):
        checker = self._checker(f"aihub.admin.knowledge.{DATABASE}")
        assert checker.access_level(AccessChecker.knowledge_database_admin_rule(DATABASE)) == AccessLevel.ACCESS_ADMIN
        namespace_admin = AccessChecker.knowledge_namespace_admin_rule(DATABASE, NAMESPACE)
        assert checker.access_level(namespace_admin) == AccessLevel.ACCESS_DENIED


class TestAgentConfigChecks:
    """What an agent may be configured to read: one named namespace, or a whole database."""

    @staticmethod
    def _checker(*rules: str) -> AccessChecker:
        return AccessChecker(user_access_rules=list(rules), tenant_access_rules=["aihub.admin.>"])

    @pytest.mark.parametrize(
        "rule",
        [
            f"aihub.user.knowledge.{DATABASE}.{NAMESPACE}",
            f"aihub.user.knowledge.{DATABASE}.>",
            "aihub.user.knowledge.>",
        ],
    )
    def test_a_named_namespace_is_readable_with_a_rule_that_reaches_it(self, rule):
        assert self._checker(rule).has_access_to_knowledge_namespace(DATABASE, NAMESPACE)

    @pytest.mark.parametrize("rule", [f"aihub.user.knowledge.{DATABASE}", f"aihub.user.knowledge.{DATABASE}.other"])
    def test_a_named_namespace_is_not_readable_from_the_database_or_a_sibling(self, rule):
        assert not self._checker(rule).has_access_to_knowledge_namespace(DATABASE, NAMESPACE)

    @pytest.mark.parametrize(
        "rule",
        [
            f"aihub.user.knowledge.{DATABASE}.*",
            f"aihub.user.knowledge.{DATABASE}.>",
            "aihub.user.knowledge.>",
            f"aihub.admin.knowledge.{DATABASE}.>",
        ],
    )
    def test_a_whole_database_needs_a_rule_covering_every_namespace(self, rule):
        assert self._checker(rule).has_access_to_all_knowledge_namespaces(DATABASE)

    @pytest.mark.parametrize(
        "rule",
        [
            f"aihub.user.knowledge.{DATABASE}",
            f"aihub.user.knowledge.{DATABASE}.{NAMESPACE}",
            f"aihub.admin.knowledge.{DATABASE}",
            "aihub.user.knowledge.otherdb.>",
        ],
    )
    def test_partial_or_database_level_access_does_not_open_the_whole_database(self, rule):
        assert not self._checker(rule).has_access_to_all_knowledge_namespaces(DATABASE)
