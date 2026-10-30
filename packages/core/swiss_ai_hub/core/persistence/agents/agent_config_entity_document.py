import re
from datetime import UTC, datetime
from typing import Annotated, Any, Self

from beanie import Delete, Document, Insert, Replace, Save, SaveChanges, after_event, before_event
from pydantic import Field
from pymongo import ASCENDING, IndexModel

from swiss_ai_hub.core.agents.agent_config import AgentConfig
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.agents.agent_config_change_hook import AgentConfigChangeHook


class AgentConfigEntityDocument(Document):
    """An agent instance's configuration (a profile), stored in the `agent_configs` collection.

    Written in the shape MongoEngine wrote it, so a previous release can still read every document: only changed
    fields on update (`save_changes`, with a changed field rewritten whole so a key removed from `config_data` is
    removed in storage too), and no `null` for an unset field.
    """

    agent_class: str
    agent_id: Annotated[str, Field(description="Unique, URL-safe ID for the agent instance (e.g., 'agent_123').")]
    name: Annotated[LocaleString, Field(description="Name of the agent, used for display in the UI.")]
    description: Annotated[LocaleString, Field(description="Description of the agent's purpose or functionality.")]
    icon: Annotated[str, Field(description="Icon representing the agent, e.g., 'meteor-icons:robot'.")]
    config_data: Annotated[dict[str, Any], Field(description="The configuration data matching the Pydantic model.")]
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "agent_configs"
        keep_nulls = False
        use_state_management = True
        state_management_replace_objects = True
        indexes = [
            IndexModel([("agent_class", ASCENDING), ("agent_id", ASCENDING)], unique=True),
            IndexModel([("agent_class", ASCENDING)]),
        ]

    @classmethod
    @trace_fn
    def from_agent_config(cls, agent_config: AgentConfig, agent_class: str) -> Self:
        """Create an instance entity from an AgentConfig."""
        return cls(
            agent_class=agent_class,
            agent_id=agent_config.agent_id,
            name=agent_config.name,
            description=agent_config.description,
            icon=agent_config.icon,
            config_data=agent_config.model_dump(),
        )

    @trace_fn
    def update_from_agent_config(self, agent_config: AgentConfig, agent_class: str) -> Self:
        """Update an existing instance entity from an AgentConfig."""
        self.agent_class = agent_class
        self.agent_id = agent_config.agent_id
        self.name = agent_config.name
        self.description = agent_config.description
        self.icon = agent_config.icon
        self.config_data = agent_config.model_dump()
        return self

    @before_event(Insert, Replace, Save, SaveChanges)
    def _touch_updated_at(self) -> None:
        self.updated_at = datetime.now(UTC)

    @after_event(Insert, Replace, Save, SaveChanges, Delete)
    def _resync_openwebui(self) -> None:
        AgentConfigChangeHook.notify()

    @classmethod
    @trace_fn
    async def find_for_classes(cls, agent_classes: list[str]) -> list[Self]:
        return await cls.find({"agent_class": {"$in": agent_classes}}).to_list()

    @classmethod
    @trace_fn
    async def find_with_config_key(cls, config_key: str) -> list[Self]:
        """Every profile carrying `config_key`, whatever class it belongs to.

        Takes the key rather than naming one, so this stays a persistence query: which key matters is the
        caller's business, and the entity has no reason to know what a schedule is.
        """
        return await cls.find({f"config_data.{config_key}": {"$exists": True}}).to_list()

    @classmethod
    @trace_fn
    async def unset_config_key(cls, config_key: str) -> int:
        """Strip `config_key` (a dotted path inside `config_data`) from every profile still carrying it.

        For a field a blueprint has dropped: nothing reads the key any more (a config model ignores extras),
        so this is tidiness rather than correctness. Returns how many profiles were changed.
        """
        key_path = f"config_data.{config_key}"
        result = await cls.find({key_path: {"$exists": True}}).update({"$unset": {key_path: ""}})
        return result.modified_count

    @classmethod
    @trace_fn
    async def list_all(cls) -> list[Self]:
        """Every profile, whatever class it belongs to, including classes that are offline or retired.

        Not named `find_all`: Beanie's own `find_all` returns a query, and `delete_all` relies on it.
        """
        return await cls.find().to_list()

    @classmethod
    @trace_fn
    async def replace_config_data_if_unchanged(
        cls, document_id: Any, expected_config_data: dict[str, Any], config_data: dict[str, Any]
    ) -> bool:
        """Swap in `config_data` only while the stored value still equals `expected_config_data`.

        For startup rewrites: several API replicas boot together, and a profile saved between the read and
        the write must not be overwritten with a rewrite of what it held before.
        """
        matching = cls.find({"_id": document_id, "config_data": expected_config_data})
        result = await matching.update({"$set": {"config_data": config_data}})
        return result.modified_count == 1

    @classmethod
    @trace_fn
    async def find_for_class(cls, agent_class: str) -> list[Self]:
        """Find all configurations for a specific agent class."""
        return await cls.find({"agent_class": agent_class}).to_list()

    @classmethod
    @trace_fn
    async def find_for_name(cls, agent_class: str, name: str | None = None) -> list[Self]:
        if name is None:
            return await cls.find_for_class(agent_class)
        name_pattern = {"$regex": re.escape(name), "$options": "i"}
        name_matches = [{f"name.{locale}": name_pattern} for locale in LocaleHandler.LOCALE_WHITE_LIST]
        return await cls.find({"agent_class": agent_class, "$or": name_matches}).to_list()

    @classmethod
    @trace_fn
    async def find_for_class_and_id(cls, agent_class: str, agent_id: str) -> Self | None:
        """Find a specific configuration by agent class and ID."""
        return await cls.find_one({"agent_class": agent_class, "agent_id": agent_id})

    @classmethod
    @trace_fn
    async def find_for_instances(cls, instances: set[tuple[str, str]]) -> dict[tuple[str, str], Self]:
        """The stored profiles of the given (agent_class, agent_id) pairs, keyed by that pair; missing ones left out.

        For callers that must resolve many profiles from synchronous code: they collect the pairs, load them here
        in one query, and pass the mapping down.
        """
        if not instances:
            return {}
        pairs = [{"agent_class": agent_class, "agent_id": agent_id} for agent_class, agent_id in instances]
        documents = await cls.find({"$or": pairs}).to_list()
        return {(document.agent_class, document.agent_id): document for document in documents}

    @classmethod
    @trace_fn
    async def delete_if_exists_for_class_and_id(cls, agent_class: str, agent_id: str) -> None:
        """Delete a specific configuration by agent class and ID if it exists."""
        existing = await cls.find_for_class_and_id(agent_class, agent_id)
        if existing:
            await existing.delete()
