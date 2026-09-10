from swiss_ai_hub.core.form import ChipsInput, InputText
from swiss_ai_hub.core.generative_ai.memory.org_memory_write_config import OrgMemoryWriteConfig


class TestDefaultOutsideAllowList:
    """A default outside the allow-list must stay a *valid* config — see the class docstring for why."""

    def test_valid_default_in_allowed(self):
        config = OrgMemoryWriteConfig(
            tenant_id="t1",
            default_tenant_namespace="hr",
            allowed_tenant_namespaces=["hr", "legal"],
        )
        assert config.default_tenant_namespace == "hr"

    def test_default_not_in_allowed_is_accepted(self):
        """Rejecting this here would abort AgentConfig.model_validate on every event and brick the agent."""
        config = OrgMemoryWriteConfig(
            tenant_id="t1",
            default_tenant_namespace="other",
            allowed_tenant_namespaces=["hr", "legal"],
        )
        assert config.default_tenant_namespace == "other"
        assert config.allowed_tenant_namespaces == ["hr", "legal"]

    def test_valid_empty_allowed_means_unrestricted(self):
        config = OrgMemoryWriteConfig(
            tenant_id="t1",
            default_tenant_namespace="anything",
            allowed_tenant_namespaces=[],
        )
        assert config.default_tenant_namespace == "anything"

    def test_valid_default_none_with_non_empty_allowed(self):
        config = OrgMemoryWriteConfig(
            tenant_id="t1",
            default_tenant_namespace=None,
            allowed_tenant_namespaces=["hr"],
        )
        assert config.default_tenant_namespace is None


class TestForm:
    def test_form_mode_builds_elements(self):
        config = OrgMemoryWriteConfig.as_form()
        assert isinstance(config.allowed_tenant_namespaces, ChipsInput)
        assert isinstance(config.default_tenant_namespace, InputText)

    def test_default_namespace_carries_the_allow_list_form_rule(self):
        """The admin gets the feedback in the form that the model deliberately no longer raises."""
        default_namespace = OrgMemoryWriteConfig.as_form().default_tenant_namespace
        assert default_namespace.validation == "memberOf:allowed_tenant_namespaces"
