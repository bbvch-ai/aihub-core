from mongoengine import EmbeddedDocument

from swiss_ai_hub.core.persistence.agents import AgentConfigEntity


class AgentConfigEntityEmbeddedDocument(AgentConfigEntity, EmbeddedDocument):
    """
    This is the specific class for storing agent configurations as an embedded document.
    It extends the base `AgentConfigEntity` class and uses MongoDB's EmbeddedDocument model for persistence
    within other documents, such as `AgentEntity`.
    This is commonly used to store default configurations defined in the AgentRunner constructor by the implementer.
    """

    pass
