from datetime import timedelta
from typing import Annotated, Self

from pydantic import Field, model_validator

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class DiscoverySettings(EnvironmentSettings):
    """Pacing of the API's class discovery rounds and how many of them a class may miss.

    Online status is judged against completed rounds rather than the clock, so these knobs decide how
    quickly a class that really went away reads offline — and nothing else: a round that fails or never
    finishes changes no class's status however long it lasts.
    """

    model_config = EnvironmentSettings.create_settings_config("DISCOVERY_")

    INTERVAL_SECONDS: Annotated[
        int,
        Field(ge=1, description="Pause between the end of one discovery round and the start of the next."),
    ] = 60
    RESPONSE_WAIT_SECONDS: Annotated[
        int,
        Field(ge=1, description="How long a round collects answers after broadcasting its request."),
    ] = 10
    ROUND_TIMEOUT_SECONDS: Annotated[
        int,
        Field(
            ge=1,
            description="Longest a round may take before it is abandoned as stalled and logged as an error. "
            "Covers the response wait plus stamping every class that answered.",
        ),
    ] = 60
    MISSED_ROUNDS_BEFORE_OFFLINE: Annotated[
        int,
        Field(
            ge=1,
            description="Completed rounds in a row a class may fail to answer and still count as online. "
            "The same rule decides when its REST endpoints are removed.",
        ),
    ] = 3
    MAX_SILENCE_SECONDS: Annotated[
        int,
        Field(
            ge=1,
            description="However the rounds went, a class that has not answered for this long reads offline. "
            "Bounds how long dead classes keep reading online while every round fails, and how old the rounds "
            "left over from before an API restart may be.",
        ),
    ] = 900

    @model_validator(mode="after")
    def max_silence_exceeds_the_missed_rounds(self) -> Self:
        """A limit inside the missed-rounds span would take healthy classes offline between two rounds."""
        if self.MAX_SILENCE_SECONDS <= self.cold_start_window.total_seconds():
            msg = (
                f"DISCOVERY_MAX_SILENCE_SECONDS ({self.MAX_SILENCE_SECONDS}) must exceed the "
                f"{self.cold_start_window.total_seconds():.0f}s that "
                "DISCOVERY_MISSED_ROUNDS_BEFORE_OFFLINE rounds span."
            )
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def round_timeout_exceeds_response_wait(self) -> Self:
        """A timeout at or below the wait would abandon every round before it could stamp anything."""
        if self.ROUND_TIMEOUT_SECONDS <= self.RESPONSE_WAIT_SECONDS:
            msg = (
                f"DISCOVERY_ROUND_TIMEOUT_SECONDS ({self.ROUND_TIMEOUT_SECONDS}) must exceed "
                f"DISCOVERY_RESPONSE_WAIT_SECONDS ({self.RESPONSE_WAIT_SECONDS})."
            )
            raise ValueError(msg)
        return self

    @property
    def cold_start_window(self) -> timedelta:
        """The wall-clock stand-in for the missed-rounds rule until that many rounds have completed."""
        round_period = self.INTERVAL_SECONDS + self.RESPONSE_WAIT_SECONDS
        return timedelta(seconds=round_period * self.MISSED_ROUNDS_BEFORE_OFFLINE)

    @property
    def max_silence(self) -> timedelta:
        return timedelta(seconds=self.MAX_SILENCE_SECONDS)

    @property
    def recorder_lease_ttl(self) -> int:
        """Two of the slowest rounds, so the recording process keeps its lease across a stalled round."""
        return 2 * (self.INTERVAL_SECONDS + self.ROUND_TIMEOUT_SECONDS)
