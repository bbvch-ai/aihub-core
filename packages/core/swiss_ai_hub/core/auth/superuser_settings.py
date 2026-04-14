from typing import Annotated

from pydantic import Field, SecretStr, field_validator

from swiss_ai_hub.core.persistence.access.entities.bearer_token import TOKEN_PREFIX
from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class SuperuserSettings(EnvironmentSettings):
    """
    Configuration for the platform superuser.

    The superuser is an ordinary Keycloak-seeded user (``SUPERUSER_USERNAME`` /
    ``SUPERUSER_EMAIL``) whose realm roles — including ``AIHubSysAdmin`` — grant
    sysadmin access through the normal OAuth2 flow. No special auth handler is
    involved; there is no synthetic identity or "virtual tenant".

    ``SUPERUSER_TOKEN`` is a static bearer token that internal services
    (OpenWebUI, RAG, images, audio, the external document loader, the Langfuse
    provisioner) use to call the API as this user. It is materialized in the
    ``bearer_tokens`` collection at API startup, bound to the Keycloak user
    found by ``SUPERUSER_EMAIL`` — ``TokenAuthHandler`` validates it and
    ``is_sys_admin`` is derived from the user's Keycloak realm roles, just like
    a regular login.
    """

    model_config = EnvironmentSettings.create_settings_config("SUPERUSER_")

    USERNAME: Annotated[str, Field(description="Keycloak username of the seeded superuser.")]
    EMAIL: Annotated[str, Field(description="Keycloak email used to look up the superuser.")]
    ROLES: Annotated[
        str,
        Field(
            description="Comma-separated realm roles assigned to the superuser. Must include AIHubSysAdmin.",
        ),
    ]
    TOKEN: Annotated[
        SecretStr,
        Field(description=f"Static bearer token for machine-to-machine API calls. Must start with '{TOKEN_PREFIX}'."),
    ]

    @field_validator("TOKEN")
    @classmethod
    def _token_must_have_prefix(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().startswith(TOKEN_PREFIX):
            raise ValueError(f"SUPERUSER_TOKEN must start with '{TOKEN_PREFIX}'")
        return value

    @property
    def roles_list(self) -> list[str]:
        return [r.strip() for r in self.ROLES.split(",") if r.strip()]
