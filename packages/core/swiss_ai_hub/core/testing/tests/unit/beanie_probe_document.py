from beanie import Document


class BeanieProbeDocument(Document):
    """Test-only document that proves the shared-loop Beanie setup before any entity is ported."""

    key: str

    class Settings:
        name = "beanie_probe"
