from unittest.mock import Mock

import pytest
from swiss_ai_hub.core.form import (
    AgentSelector,
    Group,
    InputNumber,
    InputText,
    KnowledgeDatabaseSelector,
    ModelSelect,
    Repeater,
    TenantSelect,
    VectorStoreInput,
)
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler

from swiss_ai_hub.api.util.config_authorization_service import ConfigAuthorizationService

ORG_MEMORY_RULE = "aihub.user.memory.organization.?>"
ORG_MEMORY_MESSAGE_PATH = "lib.common.authorization.no_access_organization_memory"


def _make_access_checker(
    knowledge_dbs: set[str] | None = None,
    knowledge_namespaces: set[str] | None = None,
    agents: set[str] | None = None,
    org_memory: bool = False,
    is_sys_admin: bool = False,
) -> Mock:
    """Create a mock AccessChecker that grants access to specified resources.

    ``knowledge_dbs`` are databases the user may read as a whole; ``knowledge_namespaces`` are
    ``"db/namespace"`` pairs the user may read individually.
    """
    allowed_knowledge_dbs = knowledge_dbs or set()
    allowed_knowledge_namespaces = knowledge_namespaces or set()
    allowed_agents = agents or set()

    checker = Mock()

    def has_access(permission_template: str) -> bool:
        return org_memory and permission_template.startswith("aihub.user.memory.organization")

    def has_access_to_all_knowledge_namespaces(database: str) -> bool:
        return database in allowed_knowledge_dbs

    def has_access_to_knowledge_namespace(database: str, namespace: str) -> bool:
        return database in allowed_knowledge_dbs or f"{database}/{namespace}" in allowed_knowledge_namespaces

    def has_access_to_agent(agent_class: str, agent_id: str) -> bool:
        return f"{agent_class}/{agent_id}" in allowed_agents

    checker.has_access = Mock(side_effect=has_access)
    checker.has_access_to_all_knowledge_namespaces = Mock(side_effect=has_access_to_all_knowledge_namespaces)
    checker.has_access_to_knowledge_namespace = Mock(side_effect=has_access_to_knowledge_namespace)
    checker.has_access_to_agent = Mock(side_effect=has_access_to_agent)
    checker.is_sys_admin = is_sys_admin
    return checker


def _validate(form: list[dict], config: dict, checker: Mock, t: LocaleHandler, tenants: set[str] | None = None) -> None:
    ConfigAuthorizationService.validate_config_authorization_or_raise(form, config, checker, tenants or set(), t)


def _to_dicts(elements: list) -> list[dict]:
    """Serialize typed form elements to dicts, matching how AgentClassEntity stores them."""
    return [e.model_dump() for e in elements]


@pytest.fixture
def t() -> LocaleHandler:
    return LocaleHandler(locale="en")


class TestKnowledgeDatabaseValidation:
    def test_access_granted(self, t: LocaleHandler):
        form = _to_dicts([KnowledgeDatabaseSelector(label="DBs", name="knowledge_databases")])
        config = {"knowledge_databases": ["db_a", "db_b"]}
        checker = _make_access_checker(knowledge_dbs={"db_a", "db_b"})

        _validate(form, config, checker, t)

    def test_access_denied(self, t: LocaleHandler):
        form = _to_dicts([KnowledgeDatabaseSelector(label="DBs", name="knowledge_databases")])
        config = {"knowledge_databases": ["db_a", "db_secret"]}
        checker = _make_access_checker(knowledge_dbs={"db_a"})

        with pytest.raises(Exception) as exc_info:
            _validate(form, config, checker, t)

        assert exc_info.value.status_code == 403
        violations = exc_info.value.detail["violations"]
        assert len(violations) == 1
        assert violations[0]["resource_type"] == "knowledge_database"
        assert violations[0]["resource"] == "db_secret"
        assert violations[0]["field"] == "knowledge_databases"

    def test_access_denied_message_is_localized(self):
        form = _to_dicts([KnowledgeDatabaseSelector(label="DBs", name="dbs")])
        config = {"dbs": ["secret_db"]}
        checker = _make_access_checker()

        with pytest.raises(Exception) as exc_info:
            _validate(form, config, checker, LocaleHandler(locale="de"))

        violations = exc_info.value.detail["violations"]
        assert "Wissensdatenbank" in violations[0]["message"]

    def test_empty_list(self, t: LocaleHandler):
        form = _to_dicts([KnowledgeDatabaseSelector(label="DBs", name="dbs")])
        config = {"dbs": []}
        checker = _make_access_checker()

        _validate(form, config, checker, t)

    def test_none_value_skipped(self, t: LocaleHandler):
        form = _to_dicts([KnowledgeDatabaseSelector(label="DBs", name="dbs")])
        config = {"dbs": None}
        checker = _make_access_checker()

        _validate(form, config, checker, t)

    def test_missing_field_skipped(self, t: LocaleHandler):
        form = _to_dicts([KnowledgeDatabaseSelector(label="DBs", name="dbs")])
        config = {}
        checker = _make_access_checker()

        _validate(form, config, checker, t)


class TestAgentSelectorValidation:
    def test_access_granted(self, t: LocaleHandler):
        form = _to_dicts([AgentSelector(label="Agent", name="target_agent")])
        config = {"target_agent": {"agent_class": "MyAgent", "agent_id": "inst_1"}}
        checker = _make_access_checker(agents={"MyAgent/inst_1"})

        _validate(form, config, checker, t)

    def test_access_denied(self, t: LocaleHandler):
        form = _to_dicts([AgentSelector(label="Agent", name="target_agent")])
        config = {"target_agent": {"agent_class": "SecretAgent", "agent_id": "inst_1"}}
        checker = _make_access_checker(agents=set())

        with pytest.raises(Exception) as exc_info:
            _validate(form, config, checker, t)

        assert exc_info.value.status_code == 403
        violations = exc_info.value.detail["violations"]
        assert len(violations) == 1
        assert violations[0]["resource_type"] == "agent"
        assert violations[0]["resource"] == "SecretAgent/inst_1"

    def test_incomplete_value_skipped(self, t: LocaleHandler):
        form = _to_dicts([AgentSelector(label="Agent", name="target_agent")])
        config = {"target_agent": {"agent_class": "MyAgent"}}
        checker = _make_access_checker()

        _validate(form, config, checker, t)


class TestModelSelectSkipped:
    def test_model_select_not_checked(self, t: LocaleHandler):
        form = _to_dicts([ModelSelect(label="Model", name="llm_model")])
        config = {"llm_model": "gpt-4"}
        checker = _make_access_checker()

        _validate(form, config, checker, t)


class TestTenantSelectValidation:
    def test_member_access_granted(self, t: LocaleHandler):
        form = _to_dicts([TenantSelect(label="Tenant", name="tenant_id")])
        config = {"tenant_id": "tenant_a"}
        checker = _make_access_checker()

        _validate(form, config, checker, t, tenants={"tenant_a", "tenant_b"})

    def test_non_member_access_denied(self, t: LocaleHandler):
        form = _to_dicts([TenantSelect(label="Tenant", name="tenant_id")])
        config = {"tenant_id": "tenant_secret"}
        checker = _make_access_checker()

        with pytest.raises(Exception) as exc_info:
            _validate(form, config, checker, t, tenants={"tenant_a"})

        assert exc_info.value.status_code == 403
        violations = exc_info.value.detail["violations"]
        assert len(violations) == 1
        assert violations[0]["resource_type"] == "tenant"
        assert violations[0]["resource"] == "tenant_secret"
        assert violations[0]["field"] == "tenant_id"

    def test_sysadmin_bypasses_membership(self, t: LocaleHandler):
        form = _to_dicts([TenantSelect(label="Tenant", name="tenant_id")])
        config = {"tenant_id": "any_tenant"}
        checker = _make_access_checker(is_sys_admin=True)

        _validate(form, config, checker, t, tenants=set())

    def test_none_value_skipped(self, t: LocaleHandler):
        form = _to_dicts([TenantSelect(label="Tenant", name="tenant_id")])
        config = {"tenant_id": None}
        checker = _make_access_checker()

        _validate(form, config, checker, t, tenants=set())

    def test_denied_message_is_localized(self):
        form = _to_dicts([TenantSelect(label="Tenant", name="tenant_id")])
        config = {"tenant_id": "tenant_secret"}
        checker = _make_access_checker()

        with pytest.raises(Exception) as exc_info:
            _validate(form, config, checker, LocaleHandler(locale="de"), tenants=set())

        violations = exc_info.value.detail["violations"]
        assert "Mandanten" in violations[0]["message"]


class TestNestedForms:
    def test_group_validation(self, t: LocaleHandler):
        form = _to_dicts(
            [
                Group(
                    name="rag_config",
                    label="RAG Config",
                    children=[
                        KnowledgeDatabaseSelector(label="DBs", name="knowledge_databases"),
                        InputText(label="Prompt", name="prompt"),
                    ],
                )
            ]
        )
        config = {"rag_config": {"knowledge_databases": ["forbidden_db"], "prompt": "hello"}}
        checker = _make_access_checker(knowledge_dbs=set())

        with pytest.raises(Exception) as exc_info:
            _validate(form, config, checker, t)

        violations = exc_info.value.detail["violations"]
        assert len(violations) == 1
        assert violations[0]["field"] == "rag_config.knowledge_databases"
        assert violations[0]["resource"] == "forbidden_db"

    def test_repeater_validates_all_items(self, t: LocaleHandler):
        form = _to_dicts(
            [
                Repeater(
                    name="steps",
                    label="Steps",
                    children=[AgentSelector(label="Agent", name="agent")],
                )
            ]
        )
        config = {
            "steps": [
                {"agent": {"agent_class": "A", "agent_id": "ok"}},
                {"agent": {"agent_class": "B", "agent_id": "denied"}},
                {"agent": {"agent_class": "C", "agent_id": "also_ok"}},
            ]
        }
        checker = _make_access_checker(agents={"A/ok", "C/also_ok"})

        with pytest.raises(Exception) as exc_info:
            _validate(form, config, checker, t)

        violations = exc_info.value.detail["violations"]
        assert len(violations) == 1
        assert violations[0]["resource"] == "B/denied"
        assert "steps.1" in violations[0]["field"]

    def test_deeply_nested_group(self, t: LocaleHandler):
        form = _to_dicts(
            [
                Group(
                    name="outer",
                    label="Outer",
                    children=[
                        Group(
                            name="inner",
                            label="Inner",
                            children=[AgentSelector(label="Delegate", name="delegate")],
                        )
                    ],
                )
            ]
        )
        config = {"outer": {"inner": {"delegate": {"agent_class": "X", "agent_id": "y"}}}}
        checker = _make_access_checker(agents=set())

        with pytest.raises(Exception) as exc_info:
            _validate(form, config, checker, t)

        violations = exc_info.value.detail["violations"]
        assert violations[0]["field"] == "outer.inner.delegate"


class TestGatedSectionValidation:
    """A Group carrying `access_rule` gates the whole section (e.g. organization memory)."""

    def _org_memory_form(self) -> list[dict]:
        return _to_dicts(
            [
                Group(
                    name="org_memory",
                    label="Org Memory",
                    access_rule=ORG_MEMORY_RULE,
                    access_denied_message_path=ORG_MEMORY_MESSAGE_PATH,
                    children=[TenantSelect(label="Tenant", name="tenant_id")],
                )
            ]
        )

    def test_access_granted(self, t: LocaleHandler):
        config = {"org_memory": {"tenant_id": "tenant_a"}}
        checker = _make_access_checker(org_memory=True)

        _validate(self._org_memory_form(), config, checker, t, tenants={"tenant_a"})

    def test_access_denied(self, t: LocaleHandler):
        config = {"org_memory": {"tenant_id": "tenant_a"}}
        checker = _make_access_checker()

        with pytest.raises(Exception) as exc_info:
            _validate(self._org_memory_form(), config, checker, t, tenants={"tenant_a"})

        assert exc_info.value.status_code == 403
        violations = exc_info.value.detail["violations"]
        assert any(v["resource_type"] == "section" and v["field"] == "org_memory" for v in violations)

    def test_denied_message_uses_section_message_path(self, t: LocaleHandler):
        config = {"org_memory": {"tenant_id": "tenant_a"}}
        checker = _make_access_checker()

        with pytest.raises(Exception) as exc_info:
            _validate(self._org_memory_form(), config, checker, t, tenants={"tenant_a"})

        section_violation = next(v for v in exc_info.value.detail["violations"] if v["resource_type"] == "section")
        assert "organization memory" in section_violation["message"]

    def test_section_null_skipped(self, t: LocaleHandler):
        config = {"org_memory": None}
        checker = _make_access_checker()

        _validate(self._org_memory_form(), config, checker, t)

    def test_section_missing_skipped(self, t: LocaleHandler):
        config: dict = {}
        checker = _make_access_checker()

        _validate(self._org_memory_form(), config, checker, t)


class TestMixedForms:
    def test_no_resource_selectors(self, t: LocaleHandler):
        form = _to_dicts(
            [
                InputText(label="Prompt", name="prompt"),
                InputNumber(label="Max Tokens", name="max_tokens"),
            ]
        )
        config = {"prompt": "Hello", "max_tokens": 100}
        checker = _make_access_checker()

        _validate(form, config, checker, t)

    def test_multiple_violations_across_types(self, t: LocaleHandler):
        form = _to_dicts(
            [
                KnowledgeDatabaseSelector(label="DBs", name="dbs"),
                AgentSelector(label="Agent", name="agent"),
            ]
        )
        config = {
            "dbs": ["secret_db"],
            "agent": {"agent_class": "SecretAgent", "agent_id": "x"},
        }
        checker = _make_access_checker()

        with pytest.raises(Exception) as exc_info:
            _validate(form, config, checker, t)

        violations = exc_info.value.detail["violations"]
        assert len(violations) == 2
        resource_types = {v["resource_type"] for v in violations}
        assert resource_types == {"knowledge_database", "agent"}

    def test_no_raise_when_all_authorized(self, t: LocaleHandler):
        form = _to_dicts(
            [
                KnowledgeDatabaseSelector(label="DBs", name="dbs"),
                AgentSelector(label="Agent", name="agent"),
            ]
        )
        config = {
            "dbs": ["allowed_db"],
            "agent": {"agent_class": "MyAgent", "agent_id": "inst_1"},
        }
        checker = _make_access_checker(knowledge_dbs={"allowed_db"}, agents={"MyAgent/inst_1"})

        _validate(form, config, checker, t)


class TestVectorStoreInputAuthorization:
    """The RAG retriever's database + namespaces selection is what most agents read from."""

    @staticmethod
    def _form() -> list[dict]:
        return _to_dicts([VectorStoreInput(label="Store", name="vector_store")])

    @staticmethod
    def _config(namespaces: list[str] | None = None, all_namespaces: bool = False) -> dict:
        return {
            "vector_store": {
                "collection_name": "db_a",
                "index_namespaces": namespaces or [],
                "all_namespaces": all_namespaces,
            }
        }

    def test_named_namespaces_the_user_may_read_pass(self, t: LocaleHandler):
        checker = _make_access_checker(knowledge_namespaces={"db_a/reports", "db_a/policies"})
        _validate(self._form(), self._config(["reports", "policies"]), checker, t)

    def test_a_named_namespace_the_user_may_not_read_is_rejected_individually(self, t: LocaleHandler):
        checker = _make_access_checker(knowledge_namespaces={"db_a/reports"})
        with pytest.raises(Exception) as exc_info:
            _validate(self._form(), self._config(["reports", "secret"]), checker, t)
        violations = exc_info.value.detail["violations"]
        assert len(violations) == 1
        assert violations[0]["resource_type"] == "knowledge_namespace"
        assert violations[0]["resource"] == "db_a/secret"
        assert violations[0]["field"] == "vector_store"

    def test_all_namespaces_needs_access_to_the_whole_database(self, t: LocaleHandler):
        checker = _make_access_checker(knowledge_namespaces={"db_a/reports"})
        with pytest.raises(Exception) as exc_info:
            _validate(self._form(), self._config(all_namespaces=True), checker, t)
        violations = exc_info.value.detail["violations"]
        assert violations[0]["resource_type"] == "knowledge_database"
        assert violations[0]["resource"] == "db_a"

    def test_all_namespaces_passes_with_whole_database_access(self, t: LocaleHandler):
        _validate(self._form(), self._config(all_namespaces=True), _make_access_checker(knowledge_dbs={"db_a"}), t)

    def test_an_empty_scope_is_not_an_authorization_matter(self, t: LocaleHandler):
        """Nothing is read, so nothing is refused here; the config model rejects the empty scope itself."""
        _validate(self._form(), self._config([]), _make_access_checker(), t)

    def test_incomplete_value_skipped(self, t: LocaleHandler):
        _validate(self._form(), {"vector_store": {"index_namespaces": ["x"]}}, _make_access_checker(), t)


class TestKnowledgeDatabaseSelectorNeedsWholeDatabase:
    def test_partial_namespace_access_does_not_allow_selecting_the_database(self, t: LocaleHandler):
        form = _to_dicts([KnowledgeDatabaseSelector(label="DBs", name="knowledge_databases")])
        checker = _make_access_checker(knowledge_namespaces={"db_a/reports"})
        with pytest.raises(Exception) as exc_info:
            _validate(form, {"knowledge_databases": ["db_a"]}, checker, t)
        assert exc_info.value.detail["violations"][0]["resource"] == "db_a"
