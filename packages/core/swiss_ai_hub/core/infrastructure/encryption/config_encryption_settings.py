from typing import Annotated

from pydantic import Field, SecretStr

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class ConfigEncryptionSettings(EnvironmentSettings):
    """
    Key that encrypts secret configuration fields at rest.

    One symmetric key is shared by every container that stores or reads such fields (the API on write, agent
    runners and pipelines on read), so the value must be identical across those services. The API's scheduler also
    keys the ids of scheduled-run threads with it. Left unset on purpose rather than required: the absence is
    reported at first use (an encrypt, a decrypt or a scheduled run) with a message naming the variable, instead of
    failing every settings construction in services that never need it.
    """

    model_config = EnvironmentSettings.create_settings_config("AIHUB_CONFIG_")

    ENCRYPTION_KEY: Annotated[
        SecretStr | None,
        Field(
            description=(
                "Fernet key (url-safe base64, 32 bytes) encrypting secret configuration fields at rest. The API also "
                "derives the ids of scheduled-run threads from it, so changing it moves every scheduled profile to a "
                "new thread."
            )
        ),
    ] = None
