from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, field_validator
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.i18n import LocaleString


class UpdateTenantMetadataRequest(BaseModel):
    """Request model for updating a tenant. All fields are optional.

    Name and description constraints mirror ``CreateTenantMetadataRequest`` — an update
    must not be able to slip a value past a constraint that create enforced.
    """

    name: (
        Annotated[
            str,
            StringConstraints(strip_whitespace=True, min_length=1, max_length=120),
            Field(description="The unique display name of the tenant."),
        ]
        | None
    ) = None
    description: (
        Annotated[
            str,
            StringConstraints(max_length=500),
            Field(description="A short description of the tenant."),
        ]
        | None
    ) = None
    access_rules: Annotated[list[str] | None, Field(description="Access rules granted to this tenant.")] = None
    chat_disclaimer: Annotated[
        LocaleString | None,
        Field(
            description="Plain text below the chat input, up to 100 characters per language. "
            "At least one translation is required."
        ),
    ] = None

    @field_validator("chat_disclaimer")
    @classmethod
    def normalize_disclaimer(cls, text: LocaleString | None) -> LocaleString | None:
        if text is None:
            return None
        if not text.has_content():
            raise ValueError("At least one disclaimer translation is required.")
        values = {locale: (value or "").strip() or None for locale, value in text.model_dump().items()}
        if any(len(value) > 100 for value in values.values() if value):
            raise ValueError("The disclaimer must be at most 100 characters per language.")
        return LocaleString(**values)

    @field_validator("access_rules")
    @classmethod
    def validate_access_rules(cls, value: list[str] | None) -> list[str] | None:
        for rule in value or []:
            if not AccessChecker.validate_user_access_rule(rule):
                raise ValueError(f"Invalid access rule: {rule!r}")
        return value
