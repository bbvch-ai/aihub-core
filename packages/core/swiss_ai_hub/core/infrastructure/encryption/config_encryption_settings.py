from typing import Annotated

from pydantic import Field, SecretStr

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class ConfigEncryptionSettings(EnvironmentSettings):
    """
    Key that encrypts secret configuration fields at rest.

    One symmetric key is shared by every container that stores or reads such fields (the API on write, agent
    runners and pipelines on read), so the value must be identical across those services. Left unset on purpose
    rather than required: the absence is reported at the first encrypt or decrypt with a message naming the
    variable, instead of failing every settings construction in services that never touch a secret.
    """

    model_config = EnvironmentSettings.create_settings_config("AIHUB_CONFIG_")

    ENCRYPTION_KEY: Annotated[
        SecretStr | None,
        Field(
            description="Fernet key (url-safe base64, 32 bytes) used to encrypt secret configuration fields at rest. "
            "Generate one with `python -c 'from cryptography.fernet import Fernet; "
            "print(Fernet.generate_key().decode())'`."
        ),
    ] = None
