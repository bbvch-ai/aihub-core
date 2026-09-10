from typing import Annotated, Self

from pydantic import Field

from swiss_ai_hub.core.form.all_form_options import ALL_FORM_OPTIONS  # noqa: F401 — rebuilds Group/Repeater
from swiss_ai_hub.core.form.elements.input_text import InputText
from swiss_ai_hub.core.form.elements.password import Password
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.form.secret_field_walker import SecretFieldWalker
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class _Server(Form):
    url: Annotated[str | InputText, Field(description="URL")] = ""
    api_key: Annotated[str | Password, Field(description="Key")] = ""

    @classmethod
    def as_form(cls) -> Self:
        return cls(url=InputText(label=LocaleString(en="URL")), api_key=Password(label=LocaleString(en="Key")))


class _Connection(Form):
    host: Annotated[str | InputText, Field(description="Host")] = ""
    password: Annotated[str | Password, Field(description="Password")] = ""

    @classmethod
    def as_form(cls) -> Self:
        return cls(host=InputText(label=LocaleString(en="Host")), password=Password(label=LocaleString(en="Pw")))


class _Config(Form):
    name: Annotated[str | InputText, Field(description="Name")] = ""
    token: Annotated[str | Password, Field(description="Token")] = ""
    connection: Annotated[_Connection, Field(description="Connection")] = Field(default_factory=_Connection)
    servers: Annotated[list[_Server], Field(description="Servers")] = Field(default_factory=list)

    @classmethod
    def as_form(cls) -> Self:
        return cls(
            name=InputText(label=LocaleString(en="Name")),
            token=Password(label=LocaleString(en="Token")),
            connection=_Connection.as_form(),
            servers=[_Server.as_form()],
        )


class TestSecretPaths:
    def test_password_fields_are_found_at_the_top_level_in_groups_and_in_repeaters(self):
        paths = SecretFieldWalker.secret_paths(_Config.as_form().to_formkit_form())

        assert paths == {"token", "connection.password", "servers.api_key"}

    def test_a_form_without_passwords_has_no_secret_paths(self):
        assert SecretFieldWalker.secret_paths(_Connection(host=InputText(label="Host")).to_formkit_form()) == set()
