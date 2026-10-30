import logging
from datetime import datetime
from typing import TYPE_CHECKING, Annotated, Any, Self

from beanie import Document, PydanticObjectId
from pydantic import ConfigDict, Field, TypeAdapter
from pymongo import ASCENDING, IndexModel

from swiss_ai_hub.core.discovery.discovery_kind import DiscoveryKind
from swiss_ai_hub.core.events.agent.discovery.agent_class_discovery_response_event import (
    AgentClassDiscoveryResponseEvent,
)
from swiss_ai_hub.core.form import ALL_FORM_OPTIONS
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.agents.event_spec import EventSpec
from swiss_ai_hub.core.persistence.discovery.discovery_round_entity import DiscoveryRoundEntity
from swiss_ai_hub.core.persistence.form.stored_config_specs import StoredConfigSpecs

if TYPE_CHECKING:
    from swiss_ai_hub.core.form.base.formkit_element import FormkitElement

logger = logging.getLogger(__name__)


class AgentClassEntity(Document):
    """
    Represents a registered agent CLASS in the system.

    Stores the class-level metadata (name, description, icon), form schema for
    creating agent instances, and the validation specs.
    Online status compares the last_discovered timestamp with the completed discovery rounds.

    NOTE: This entity stores CLASS information only (one record per agent_class).
    Instance/configuration data is stored in AgentConfigEntityDocument.

    Unknown fields are kept (`extra="allow"`): the MongoEngine document ran `strict: False`, so stored rows may
    carry fields this model does not declare, and a full rewrite must not drop them. `first_discovered` and
    `last_discovered` stay naive local time, the clock the discovery rounds use (see #1968).
    """

    model_config = ConfigDict(extra="allow")

    agent_class: str
    name: Annotated[LocaleString | None, Field(description="Display name for this agent class.")] = None
    description: Annotated[LocaleString | None, Field(description="Description of this agent class.")] = None
    icon: Annotated[str, Field(description="Icon for this agent class.")] = "mage:robot"
    form: Annotated[
        list[dict[str, Any]], Field(description="FormKit elements defining the agent configuration form.")
    ] = Field(default_factory=list)
    agent_config_specs: StoredConfigSpecs | None = None
    is_conversational: bool
    # Defaulted, unlike is_conversational: classes discovered before this field existed have no stored
    # value, and reads must not yield None into the non-optional DTO field. Self-heals on next discovery.
    is_schedulable: bool = False
    supported_features: list[str] = Field(default_factory=list)
    start_events: list[EventSpec]
    stop_events: list[EventSpec]
    hitl_request_events: list[EventSpec] = Field(default_factory=list)
    hitl_response_events: list[EventSpec] = Field(default_factory=list)
    network_graph: dict[str, Any]
    templates: list[dict[str, Any]] = Field(default_factory=list)
    first_discovered: datetime = Field(default_factory=datetime.now)
    last_discovered: datetime | None = Field(default_factory=datetime.now)

    class Settings:
        name = "agent_classes"
        keep_nulls = False
        use_state_management = True
        state_management_replace_objects = True
        indexes = [IndexModel([("agent_class", ASCENDING)], unique=True)]

    def is_online_since(self, threshold: datetime) -> bool:
        """Whether the class answered a discovery round at or after `threshold`, from `online_threshold()`.

        `last_discovered` is nominally required, but stored rows predate any schema, and a row missing it
        would otherwise raise inside a caller's loop — the scheduler's snapshot would abort every tick.
        """
        return self.last_discovered is not None and self.last_discovered >= threshold

    @property
    def form_elements(self) -> list["FormkitElement"]:
        """Deserialize the stored form dicts back to typed form element Pydantic models."""
        if not self.form:
            return []
        adapter = TypeAdapter(list[ALL_FORM_OPTIONS])
        return adapter.validate_python(self.form)

    @classmethod
    @trace_fn
    async def create_or_update(cls, discovery: AgentClassDiscoveryResponseEvent) -> Self:
        """
        Creates a new AgentClassEntity or updates an existing one if an agent
        with the same agent_class already exists.

        Takes the discovery response wholesale rather than its fields one by one: registering a class
        means recording exactly what the agent reported, so every field arrives from the same event.
        """
        reported = cls._fields_from_discovery(discovery)
        existing_agent = await cls.find_one({"agent_class": discovery.agent_class})
        if existing_agent:
            for field, value in reported.items():
                setattr(existing_agent, field, value)
            existing_agent.last_discovered = datetime.now()
            await existing_agent.save_changes()
            return existing_agent
        now = datetime.now()
        return await cls(
            agent_class=discovery.agent_class, first_discovered=now, last_discovered=now, **reported
        ).insert()

    @staticmethod
    def _fields_from_discovery(discovery: AgentClassDiscoveryResponseEvent) -> dict[str, Any]:
        """Every stored field a discovery response sets, in its stored form.

        The form is stored WITHOUT aliases, since MongoDB doesn't allow keys starting with '$'; alias conversion
        happens in the API layer when serving to the frontend.
        """
        return {
            "name": discovery.name,
            "description": discovery.description,
            "icon": discovery.icon,
            "form": [element.model_dump() for element in discovery.form],
            "agent_config_specs": StoredConfigSpecs.from_specs(discovery.agent_config_specs),
            "is_conversational": discovery.is_conversational,
            "is_schedulable": discovery.is_schedulable,
            "supported_features": [str(feature) for feature in discovery.supported_features],
            "start_events": [EventSpec.from_specs(event) for event in discovery.start_events],
            "stop_events": [EventSpec.from_specs(event) for event in discovery.stop_events],
            "hitl_request_events": [EventSpec.from_specs(event) for event in discovery.hitl_request_events],
            "hitl_response_events": [EventSpec.from_specs(event) for event in discovery.hitl_response_events],
            "network_graph": discovery.network_graph.model_dump(),
            "templates": [template.model_dump() for template in discovery.templates],
        }

    @classmethod
    @trace_fn
    async def get_all(cls) -> list[Self]:
        """Get all registered agent classes."""
        return await cls.find().to_list()

    @classmethod
    @trace_fn
    async def get_online_conversational(cls) -> list[Self]:
        threshold = await cls.online_threshold()
        return await cls.find({"is_conversational": True, "last_discovered": {"$gte": threshold}}).to_list()

    @classmethod
    @trace_fn
    async def get_online_class_names(cls) -> set[str]:
        threshold = await cls.online_threshold()
        online = await cls.find({"last_discovered": {"$gte": threshold}}).to_list()
        return {entity.agent_class for entity in online}

    @classmethod
    async def online_threshold(cls) -> datetime:
        """Read once per request or tick and passed to `is_online_since`, so a listing costs one lookup."""
        return await DiscoveryRoundEntity.online_threshold(DiscoveryKind.AGENT)

    @classmethod
    @trace_fn
    async def get_all_schedulable(cls) -> list[Self]:
        """Every schedulable class, online or not, for a caller that needs both halves.

        The scheduler needs online and offline classes on the same tick — one set to fire, the other to
        report what it dropped. Fetching them together and splitting in Python with `is_online_since` costs
        one round-trip instead of two, on a query that runs inside the API process every tick. That is
        why there is no online-only or offline-only query to reach for here.
        """
        return await cls.find({"is_schedulable": True}).to_list()

    @classmethod
    @trace_fn
    async def get_by_id(cls, agent_class_entity_id: str) -> Self | None:
        """Get an agent class by its MongoDB document ID."""
        return await cls.get(PydanticObjectId(agent_class_entity_id))

    @classmethod
    @trace_fn
    async def get_by_agent_class(cls, agent_class: str) -> Self | None:
        """Get an agent class by its class name."""
        return await cls.find_one({"agent_class": agent_class})
