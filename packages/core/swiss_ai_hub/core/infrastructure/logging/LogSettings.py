import logging
from typing import Annotated, Literal

from pydantic import Field

from swiss_ai_hub.core.settings.EnvironmentSettings import EnvironmentSettings


class LogSettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("LOG_")

    LEVEL: Annotated[
        Literal["CRITICAL", "FATAL", "ERROR", "WARNING", "WARN", "INFO", "DEBUG", "NOTSET"],
        Field(description="Logging level"),
    ] = "WARNING"

    @property
    def level_number(self) -> int:
        return {
            "CRITICAL": logging.CRITICAL,
            "FATAL": logging.FATAL,
            "ERROR": logging.ERROR,
            "WARNING": logging.WARNING,
            "WARN": logging.WARN,
            "INFO": logging.INFO,
            "DEBUG": logging.DEBUG,
            "NOTSET": logging.NOTSET,
        }[self.LEVEL]
