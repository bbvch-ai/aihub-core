import pytest

from swiss_ai_hub.core.form.all_form_options import ALL_FORM_OPTIONS  # noqa: F401 — rebuilds Group/Repeater
from swiss_ai_hub.core.form.elements.input_text import InputText
from swiss_ai_hub.core.form.elements.password import Password
from swiss_ai_hub.core.form.elements.select_button import SelectButton
from swiss_ai_hub.core.form.secret_field_walker import SecretFieldWalker
from swiss_ai_hub.core.imap.imap_client_config import ImapClientConfig

_OAUTH2_FIELDS = ["tenant_id", "client_id", "client_secret"]


class TestAuthMethodData:
    def test_a_profile_saved_before_oauth_existed_keeps_password_auth(self):
        config = ImapClientConfig(host="imap.example.com", username="me@example.com", password="secret")

        assert config.auth_method == "password"

    def test_oauth_without_credentials_is_still_a_valid_config(self):
        """A cross-field check here would fail every dispatched event and take the profile down (ADR 2026_08_07)."""
        config = ImapClientConfig(
            host="outlook.office365.com", username="shared@contoso.com", auth_method="oauth2_client_credentials"
        )

        assert (config.tenant_id, config.client_id, config.client_secret) == ("", "", "")

    def test_an_unknown_auth_method_is_rejected(self):
        with pytest.raises(ValueError, match="auth_method"):
            ImapClientConfig(host="imap.example.com", username="me@example.com", auth_method="kerberos")

    def test_the_entra_endpoints_default_to_the_public_cloud(self):
        config = ImapClientConfig(host="outlook.office365.com", username="shared@contoso.com")

        assert config.oauth_authority == "login.microsoftonline.com"
        assert config.oauth_scope == "https://outlook.office365.com/.default"


class TestAuthMethodForm:
    def test_auth_method_is_a_select_button_offering_both_methods(self):
        auth_method = ImapClientConfig.as_form().auth_method

        assert isinstance(auth_method, SelectButton)
        assert [option["value"] for option in auth_method.options] == ["password", "oauth2_client_credentials"]
        assert auth_method.ref == "imap_auth_method"

    def test_password_is_shown_only_for_password_auth(self):
        assert ImapClientConfig.as_form().password.condition_if == "$get(imap_auth_method).value === 'password'"

    @pytest.mark.parametrize("field", _OAUTH2_FIELDS)
    def test_entra_fields_are_shown_only_for_oauth(self, field: str):
        element = getattr(ImapClientConfig.as_form(), field)

        assert element.condition_if == "$get(imap_auth_method).value === 'oauth2_client_credentials'"

    def test_entra_ids_are_text_and_the_secret_is_masked(self):
        form = ImapClientConfig.as_form()

        assert isinstance(form.tenant_id, InputText)
        assert isinstance(form.client_id, InputText)
        assert isinstance(form.client_secret, Password)

    def test_the_client_secret_is_treated_as_a_secret_like_the_password(self):
        paths = SecretFieldWalker.secret_paths(ImapClientConfig.as_form().to_formkit_form())

        assert paths == {"password", "client_secret"}

    def test_the_entra_endpoints_are_not_editable_in_the_form(self):
        configurable = ImapClientConfig.as_form().get_configurable_fields()

        assert "oauth_authority" not in configurable
        assert "oauth_scope" not in configurable

    @pytest.mark.parametrize("field", ["auth_method", *_OAUTH2_FIELDS])
    def test_every_new_field_resolves_its_translations(self, field: str):
        element = getattr(ImapClientConfig.as_form(), field)

        for locale in ("de", "en", "fr", "it"):
            assert not element.label.in_locale(locale).startswith("lib.imap.config.")
            assert not element.help.in_locale(locale).startswith("lib.imap.config.")
