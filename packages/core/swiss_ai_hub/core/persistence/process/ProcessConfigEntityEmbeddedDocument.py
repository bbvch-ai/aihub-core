from mongoengine import EmbeddedDocument

from swiss_ai_hub.core.persistence.process.ProcessConfigEntity import ProcessConfigEntity


class ProcessConfigEntityEmbeddedDocument(ProcessConfigEntity, EmbeddedDocument):
    """
    This is the specific class for storing process configurations as an embedded document.
    It extends the base `ProcessConfigEntity` class and uses MongoDB's EmbeddedDocument model for persistence
    within other documents, such as `ProcessEntity`.
    This is commonly used to store default configurations defined in the ProcessRunner constructor by the implementer.
    """

    pass
