from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import NoDecode

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class NotificationSettings(EnvironmentSettings):
    """Settings for pipeline run-failure notifications dispatched via Apprise.

    When ``URLS`` is empty, no sensor is attached and nothing is sent.
    """

    model_config = EnvironmentSettings.create_settings_config("NOTIFICATION_")

    URLS: Annotated[
        list[str],
        NoDecode,
        Field(
            default_factory=list,
            description=(
                "Apprise notification URIs (comma-separated). "
                "Examples: 'slack://TokenA/TokenB/TokenC/#alerts', 'mailto://user:pw@smtp.example.com', "
                "'msteams://TokenA/TokenB/TokenC/'. See https://github.com/caronc/apprise for the full list."
            ),
        ),
    ]
    DAGSTER_UI_BASE_URL: Annotated[
        str | None,
        Field(
            default=None,
            description="Base URL of the Dagster UI used to build deep links in notification bodies (e.g. 'https://dagster.example.com').",
        ),
    ]
    TITLE_PREFIX: Annotated[
        str,
        Field(
            default="Swiss AI Hub Pipeline",
            description="Prefix prepended to the notification title.",
        ),
    ]
    MIN_INTERVAL_SECONDS: Annotated[
        int,
        Field(
            default=30,
            description="Minimum interval between sensor ticks in seconds.",
        ),
    ]

    @field_validator("URLS", mode="before")
    @classmethod
    def _split_comma_separated(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def enabled(self) -> bool:
        return bool(self.URLS)
