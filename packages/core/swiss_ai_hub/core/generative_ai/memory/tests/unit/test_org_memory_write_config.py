import pytest
from pydantic import ValidationError

from swiss_ai_hub.core.form import ChipsInput, InputText
from swiss_ai_hub.core.generative_ai.memory.org_memory_write_config import OrgMemoryWriteConfig


class TestDefaultInAllowedValidator:
    def test_valid_default_in_allowed(self):
        config = OrgMemoryWriteConfig(
            tenant_id="t1",
            default_tenant_namespace="hr",
            allowed_tenant_namespaces=["hr", "legal"],
        )
        assert config.default_tenant_namespace == "hr"

    def test_invalid_default_not_in_allowed(self):
        with pytest.raises(ValidationError):
            OrgMemoryWriteConfig(
                tenant_id="t1",
                default_tenant_namespace="other",
                allowed_tenant_namespaces=["hr", "legal"],
            )

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

    def test_form_mode_skips_validation(self):
        """When fields hold FormkitElements (form mode), the validator must not fire."""
        config = OrgMemoryWriteConfig.as_form()
        assert isinstance(config.allowed_tenant_namespaces, ChipsInput)
        assert isinstance(config.default_tenant_namespace, InputText)
