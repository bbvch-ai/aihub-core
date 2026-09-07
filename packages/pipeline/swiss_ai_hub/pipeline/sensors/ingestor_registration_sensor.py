import logging
from typing import Annotated

from dagster import DefaultSensorStatus, SensorEvaluationContext, SkipReason, sensor
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.persistence import Ingestor, IngestorEntity

from swiss_ai_hub.pipeline.util.bucket_utils import ensure_main_db_connection

logger = logging.getLogger(__name__)

_REGISTRATION_INTERVAL_SECONDS = 300


def ingestor_registration_sensor(
    ingestor: Annotated[str, "Ingestor id this pipeline claims"],
    display_name: Annotated[LocaleString, "Localized name shown in the create-database selector"],
    description: Annotated[LocaleString, "Localized description of what the pipeline does"],
):
    """Advertises this pipeline as a selectable ingestor, so the API can offer it.

    The API and the pipelines are separate containers, so a pipeline cannot hand the API anything
    in-process; it publishes its metadata to the database both already share. Doing that from a sensor
    rather than at import keeps a momentary Mongo outage from taking the whole code location down, and
    re-registers automatically once the database is back.
    """
    registration = Ingestor(id=ingestor, display_name=display_name, description=description)

    @sensor(
        minimum_interval_seconds=_REGISTRATION_INTERVAL_SECONDS,
        default_status=DefaultSensorStatus.RUNNING,
        name=f"IngestorRegistrationSensorFor_{ingestor}",
        description="Keeps this pipeline listed as a selectable ingestor for new knowledge databases.",
    )
    def _sensor(context: SensorEvaluationContext):
        ensure_main_db_connection()
        IngestorEntity.upsert(registration)
        return SkipReason(f"Ingestor '{ingestor}' is registered.")

    return _sensor
