from importlib.metadata import entry_points

from swiss_ai_hub.core.persistence.rag.datalake.entities.ingestor import Ingestor
from swiss_ai_hub.core.persistence.rag.datalake.entities.ingestor_type import IngestorType

_ENTRY_POINT_GROUP = "swiss_ai_hub.ingestors"


class IngestorRegistry:
    """Process-wide registry of the ingestion pipelines a user may assign to a knowledge database.

    The platform's own pipeline (``IngestorType.selectable()``) is always available. A customer-specific
    deployment makes its own route-per-run pipeline selectable by contributing an ``Ingestor`` here —
    without forking the ``IngestorType`` enum, the API contract, or the SDK. Two ways to register:

    - **Entry point** (works with the stock API image): declare the pipeline's ``Ingestor`` under the
      ``swiss_ai_hub.ingestors`` group in the deployment package's ``pyproject.toml``; it is auto-discovered
      the first time the registry is queried.
    - **Explicit** ``register()``: for a deployment that builds its own API via the ``packages/api`` SDK, or
      for tests.

    The registry is the single source of truth consulted by ``get_ingestors`` (what to offer) and
    ``create_database`` (what to accept), so a registered ingestor is immediately selectable.
    """

    _custom: dict[str, Ingestor] = {}
    _entry_points_loaded: bool = False

    @classmethod
    def register(cls, ingestor: Ingestor) -> None:
        """Register a custom selectable ingestor. Re-registering the same id with identical metadata is a no-op."""
        if ingestor.id in {ingestor_type.value for ingestor_type in IngestorType}:
            raise ValueError(f"Ingestor id '{ingestor.id}' is reserved by the platform IngestorType enum.")
        existing = cls._custom.get(ingestor.id)
        if existing is not None and existing != ingestor:
            raise ValueError(f"Ingestor id '{ingestor.id}' is already registered with different metadata.")
        cls._custom[ingestor.id] = ingestor

    @classmethod
    def custom(cls) -> list[Ingestor]:
        """Every registered custom ingestor, in registration order."""
        cls._load_entry_points()
        return list(cls._custom.values())

    @classmethod
    def selectable_ids(cls) -> list[str]:
        """Every ingestor id a user may assign to a new knowledge database (platform selectable + custom)."""
        cls._load_entry_points()
        return [ingestor_type.value for ingestor_type in IngestorType.selectable()] + list(cls._custom)

    @classmethod
    def is_selectable(cls, ingestor_id: str) -> bool:
        return ingestor_id in cls.selectable_ids()

    @classmethod
    def _load_entry_points(cls) -> None:
        if cls._entry_points_loaded:
            return
        cls._entry_points_loaded = True
        for entry_point in entry_points(group=_ENTRY_POINT_GROUP):
            cls.register(entry_point.load())
