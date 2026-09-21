"""Pydantic-layer validation of tenant-admin request DTOs.

Locks down the surface that ``tenant_id``, ``name`` and ``description`` accept
before any business logic runs — the ``tenant_id`` in particular flows straight
into a Keycloak group name, a MongoDB ``_id``, and a URL path segment, so a
blindly-accepted value can corrupt several systems at once.
"""

import pytest
from pydantic import ValidationError

from swiss_ai_hub.sysadmin_api.routes.tenant_admin.dto.create_tenant_metadata_request import CreateTenantMetadataRequest
from swiss_ai_hub.sysadmin_api.routes.tenant_admin.dto.update_tenant_metadata_request import UpdateTenantMetadataRequest


def _valid_configure_payload(**overrides) -> dict:
    payload = {"tenant_id": "my-tenant", "name": "My Tenant", "description": "desc", "access_rules": []}
    payload.update(overrides)
    return payload


class TestTenantIdConstraints:
    """``tenant_id`` is not user-chosen — it must match an existing Keycloak group
    whose name Keycloak already blessed. So we only enforce length bounds here;
    imposing a regex would reject names that Keycloak accepted (e.g. ``MyTenant``,
    ``customer.acme``) and make ``configure`` fail on a legitimately-created group.
    """

    @pytest.mark.parametrize(
        "tenant_id",
        [
            "default",
            "my-tenant",
            "MyTenant",  # mixed case, accepted by Keycloak
            "customer.acme",  # dots, accepted by Keycloak
            "Tenant 1",  # space, accepted by Keycloak
            "客户-1",  # non-ASCII, accepted by Keycloak
            "a",  # min length
            "a" * 255,  # max length
        ],
    )
    def test_accepts_any_non_empty_bounded_string(self, tenant_id: str) -> None:
        req = CreateTenantMetadataRequest.model_validate(_valid_configure_payload(tenant_id=tenant_id))
        assert req.tenant_id == tenant_id

    def test_rejects_empty_tenant_id(self) -> None:
        with pytest.raises(ValidationError):
            CreateTenantMetadataRequest.model_validate(_valid_configure_payload(tenant_id=""))

    def test_rejects_tenant_id_exceeding_255_chars(self) -> None:
        with pytest.raises(ValidationError):
            CreateTenantMetadataRequest.model_validate(_valid_configure_payload(tenant_id="a" * 256))


class TestTenantNameConstraints:
    def test_strips_surrounding_whitespace(self) -> None:
        req = CreateTenantMetadataRequest.model_validate(_valid_configure_payload(name="  My Tenant  "))
        assert req.name == "My Tenant"

    @pytest.mark.parametrize("name", ["", "   ", "\t\n"])
    def test_rejects_empty_or_whitespace_only_name(self, name: str) -> None:
        with pytest.raises(ValidationError):
            CreateTenantMetadataRequest.model_validate(_valid_configure_payload(name=name))

    def test_rejects_name_exceeding_120_chars(self) -> None:
        with pytest.raises(ValidationError):
            CreateTenantMetadataRequest.model_validate(_valid_configure_payload(name="x" * 121))

    def test_accepts_name_at_120_chars(self) -> None:
        req = CreateTenantMetadataRequest.model_validate(_valid_configure_payload(name="x" * 120))
        assert len(req.name) == 120


class TestTenantDescriptionConstraints:
    def test_accepts_empty_description(self) -> None:
        req = CreateTenantMetadataRequest.model_validate(_valid_configure_payload(description=""))
        assert req.description == ""

    def test_rejects_description_exceeding_500_chars(self) -> None:
        with pytest.raises(ValidationError):
            CreateTenantMetadataRequest.model_validate(_valid_configure_payload(description="x" * 501))


class TestUpdateTenantMetadataRequest:
    """Constraints on ``UpdateTenantMetadataRequest`` must mirror ``CreateTenantMetadataRequest``
    so a create that passes can't be defeated by an update that slips through."""

    def test_all_fields_optional(self) -> None:
        req = UpdateTenantMetadataRequest()
        assert req.name is None
        assert req.description is None
        assert req.access_rules is None

    def test_rejects_whitespace_only_name(self) -> None:
        with pytest.raises(ValidationError):
            UpdateTenantMetadataRequest.model_validate({"name": "   "})

    def test_strips_whitespace_from_name_when_provided(self) -> None:
        req = UpdateTenantMetadataRequest.model_validate({"name": "  Renamed  "})
        assert req.name == "Renamed"

    def test_rejects_name_exceeding_120_chars(self) -> None:
        with pytest.raises(ValidationError):
            UpdateTenantMetadataRequest.model_validate({"name": "x" * 121})

    def test_rejects_description_exceeding_500_chars(self) -> None:
        with pytest.raises(ValidationError):
            UpdateTenantMetadataRequest.model_validate({"description": "x" * 501})

    def test_accepts_none_for_all_fields(self) -> None:
        req = UpdateTenantMetadataRequest.model_validate({"name": None, "description": None, "access_rules": None})
        assert req.name is None
