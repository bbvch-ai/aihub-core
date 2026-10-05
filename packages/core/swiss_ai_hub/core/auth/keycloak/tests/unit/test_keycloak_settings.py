import pytest
from pydantic import ValidationError

from swiss_ai_hub.core.auth.keycloak.keycloak_settings import KeycloakSettings


@pytest.fixture(autouse=True)
def keycloak_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KEYCLOAK_URL", "http://keycloak:8080")


class TestTenantIdpAliasesParsing:
    def test_unset_yields_no_mapping(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("KEYCLOAK_TENANT_IDP_ALIASES", raising=False)
        assert KeycloakSettings().TENANT_IDP_ALIASES == {}

    def test_empty_string_yields_no_mapping(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("KEYCLOAK_TENANT_IDP_ALIASES", "")
        assert KeycloakSettings().TENANT_IDP_ALIASES == {}

    def test_pairs_are_parsed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("KEYCLOAK_TENANT_IDP_ALIASES", "acme=acme-entra,beta=shared-idp")
        assert KeycloakSettings().TENANT_IDP_ALIASES == {"acme": "acme-entra", "beta": "shared-idp"}

    def test_tenants_may_share_an_alias(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("KEYCLOAK_TENANT_IDP_ALIASES", "beta=shared-idp,gamma=shared-idp")
        assert KeycloakSettings().TENANT_IDP_ALIASES == {"beta": "shared-idp", "gamma": "shared-idp"}

    def test_whitespace_and_empty_segments_are_ignored(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("KEYCLOAK_TENANT_IDP_ALIASES", " acme = acme-entra ,, beta=shared-idp , ")
        assert KeycloakSettings().TENANT_IDP_ALIASES == {"acme": "acme-entra", "beta": "shared-idp"}

    @pytest.mark.parametrize("malformed", ["acme", "acme=", "=acme-entra", "acme=a=b"])
    def test_malformed_pair_fails(self, monkeypatch: pytest.MonkeyPatch, malformed: str) -> None:
        monkeypatch.setenv("KEYCLOAK_TENANT_IDP_ALIASES", f"beta=shared-idp,{malformed}")
        with pytest.raises(ValidationError, match="Expected tenant_id=idp_alias"):
            KeycloakSettings()

    def test_tenant_mapped_twice_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("KEYCLOAK_TENANT_IDP_ALIASES", "acme=acme-entra,acme=shared-idp")
        with pytest.raises(ValidationError, match="mapped more than once"):
            KeycloakSettings()
