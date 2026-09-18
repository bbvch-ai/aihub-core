from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings

DEFAULT_MAX_ATTACHMENTS = 5
DEFAULT_MAX_ATTACHMENT_BYTES = 5 * 1024 * 1024


class IncidentSettings(EnvironmentSettings):
    """Where incident reports are filed, and with what credentials.

    Unset — the default — the feature is off: no button in the UI, no endpoints
    doing anything. A self-hosted deployment without a support desk should look
    exactly as it did before this existed.
    """

    model_config = EnvironmentSettings.create_settings_config("INCIDENT_")

    GITHUB_REPOSITORY: Annotated[
        str | None,
        Field(
            default=None,
            description="Repository issues are filed in, as 'owner/name'. Must be private — reports carry customer "
            "data, and a public repository would publish it irreversibly.",
        ),
    ]
    GITHUB_APP_ID: Annotated[
        str | None,
        Field(default=None, description="GitHub App id. The App needs Issues: write and Contents: write."),
    ]
    GITHUB_INSTALLATION_ID: Annotated[
        str | None,
        Field(default=None, description="Installation id of the App on the target repository."),
    ]
    GITHUB_PRIVATE_KEY: Annotated[
        str | None,
        Field(
            default=None,
            description="PEM private key of the GitHub App, used to sign the JWT that buys an installation token. "
            "Supply it as a Docker secret or from a vault, never in a committed env file.",
        ),
    ]
    MAX_ATTACHMENTS: Annotated[
        int,
        Field(
            default=DEFAULT_MAX_ATTACHMENTS,
            description="How many files one report may carry. Attachments are committed to the repository and cannot "
            "meaningfully be removed from its history afterwards, which is why this is deliberately small.",
        ),
    ]
    MAX_ATTACHMENT_BYTES: Annotated[
        int,
        Field(default=DEFAULT_MAX_ATTACHMENT_BYTES, description="Largest single attachment accepted, in bytes."),
    ]

    @property
    def enabled(self) -> bool:
        return all((self.GITHUB_REPOSITORY, self.GITHUB_APP_ID, self.GITHUB_INSTALLATION_ID, self.GITHUB_PRIVATE_KEY))
