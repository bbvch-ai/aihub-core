import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING, Any

from bson import ObjectId
from llama_index.core.base.llms.types import MessageRole
from mongoengine import DictField, Document, ListField, StringField

from aihub_lib.nats.events.control import AssistantChatMessage, UserChatMessage
from aihub_lib.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from aihub_lib.persistence.messaging.entities.types.EventBucket import EventBucket

if TYPE_CHECKING:
    from aihub_lib.nats.events import BaseEvent
    from aihub_lib.nats.topics import AgentInstanceTopic

logger = logging.getLogger(__name__)


class TimeRange(Enum):
    ONE_HOUR = "1h"
    TWENTY_FOUR_HOURS = "24h"
    THIRTY_DAYS = "30d"
    THREE_SIXTY_FIVE_DAYS = "365d"


class Resolution(Enum):
    ONE_MINUTE = "1m"
    ONE_HOUR = "1h"
    ONE_DAY = "1d"
    ONE_WEEK = "1w"


@dataclass(frozen=True)
class TimeRangeDetailConfig:
    resolution: Resolution
    interval_seconds: int
    delta: timedelta
    align_to_end_of_day: bool


TIME_RANGE_CONFIG: dict[TimeRange, TimeRangeDetailConfig] = {
    TimeRange.ONE_HOUR: TimeRangeDetailConfig(
        resolution=Resolution.ONE_MINUTE,
        interval_seconds=60,
        delta=timedelta(hours=1),
        align_to_end_of_day=False,
    ),
    TimeRange.TWENTY_FOUR_HOURS: TimeRangeDetailConfig(
        resolution=Resolution.ONE_HOUR,
        interval_seconds=60 * 60,
        delta=timedelta(hours=24),
        align_to_end_of_day=True,
    ),
    TimeRange.THIRTY_DAYS: TimeRangeDetailConfig(
        resolution=Resolution.ONE_DAY,
        interval_seconds=60 * 60 * 24,
        delta=timedelta(days=30),
        align_to_end_of_day=True,
    ),
    TimeRange.THREE_SIXTY_FIVE_DAYS: TimeRangeDetailConfig(
        resolution=Resolution.ONE_WEEK,
        interval_seconds=60 * 60 * 24 * 7,
        delta=timedelta(days=365),
        align_to_end_of_day=True,
    ),
}


# MongoDB query operator constants
MONGODB_ADD_FIELDS = "$addFields"
MONGODB_AGENT_CLASS = "$agent_class"
MONGODB_AGENT_ID = "$agent_id"
MONGODB_COND = "$cond"
MONGODB_DISPLAY_ID = "$display_id"
MONGODB_DIVIDE = "$divide"
MONGODB_EVENT_DATA = "$event_data"
MONGODB_EVENT_ID = "$event_id"
MONGODB_EVENT_PARENTS = "$event_parents"
MONGODB_EVENT_TIME = "$event_time"
MONGODB_EVENT_TYPE = "$event_type"
MONGODB_FIRST = "$first"
MONGODB_FIRST_EVENT_TIME = "$first_event_time"
MONGODB_GROUP = "$group"
MONGODB_IF_NULL = "$ifNull"
MONGODB_LATEST_EVENT_TIME = "$latest_event_time"
MONGODB_MATCH = "$match"
MONGODB_RUN_ID = "$run_id"
MONGODB_SORT = "$sort"
MONGODB_TO_DATE = "$toDate"


class PersistedAgentEventEntity(Document):
    meta = {
        "collection": "agent_events",
        "strict": False,
        "indexes": [
            {"fields": ["thread_id", "event_type"]},
            {"fields": ["agent_id", "event_type"]},
            {"fields": ["thread_id", "event_parents"]},
            {"fields": ["run_id"]},
            {"fields": ["event_data.created_at"]},
            {"fields": ["display_id"]},
            {"fields": ["thread_id", "event_type", "event_parents"]},
        ],
    }
    agent_class = StringField(required=True)
    agent_id = StringField(required=True)
    thread_id = StringField(required=True)
    display_id = StringField(required=True)
    run_id = StringField(required=True)
    event_id = StringField(required=True)
    event_type = StringField(required=True)
    event_name = StringField(required=True)
    event_data = DictField(required=True)
    event_parents = ListField(StringField(), required=True)

    @classmethod
    def persist_event(cls, event: "BaseEvent", topic: "AgentInstanceTopic", db: str):
        persisted_entity = cls(
            id=ObjectId(),
            agent_class=topic.agent_class,
            agent_id=topic.agent_id,
            thread_id=topic.thread_id,
            display_id=topic.display_id,
            run_id=topic.run_id,
            event_id=event.event_id,
            event_type=topic.event_type,
            event_name=topic.event_name,
            event_data=event.model_dump(),
            event_parents=event._parent_event_names,
        )
        persisted_entity.switch_db(db)
        persisted_entity.save()

    @classmethod
    def display_events_for_thread(
        cls, thread_id: str, display_id: str | None = None, event_name: str | None = None
    ) -> list["PersistedAgentEventEntity"]:
        query = cls.objects().filter(thread_id=thread_id, event_type=AgentTopicManager.DISPLAY_EVENT)

        if display_id is not None:
            query = query.filter(display_id=display_id)

        if event_name is not None:
            query = query.filter(event_parents__contains=event_name)

        return query.order_by("event_data__created_at")

    @classmethod
    def display_events_for_threads(
        cls, thread_ids: list[str], event_name: str | None = None
    ) -> list["PersistedAgentEventEntity"]:
        query = cls.objects().filter(thread_id__in=thread_ids, event_type=AgentTopicManager.DISPLAY_EVENT)

        if event_name is not None:
            query = query.filter(event_parents__contains=event_name)

        return query.order_by("event_data__created_at")

    @classmethod
    def display_events_for_agent(cls, agent_id: str) -> list["PersistedAgentEventEntity"]:
        return (
            cls.objects()
            .filter(agent_id=agent_id, event_type=AgentTopicManager.DISPLAY_EVENT)
            .order_by("event_data__created_at")
        )

    @classmethod
    def human_in_the_loop_request_events_for_thread(cls, thread_id: str) -> list["PersistedAgentEventEntity"]:
        return list(
            cls.objects()
            .filter(thread_id=thread_id, event_parents__contains="HumanInTheLoopRequestEvent")
            .order_by("event_data__created_at")
        )

    @classmethod
    def human_in_the_loop_response_events_for_thread(cls, thread_id: str) -> list["PersistedAgentEventEntity"]:
        return list(
            cls.objects()
            .filter(
                thread_id=thread_id,
                event_parents__contains="HumanInTheLoopResponseEvent",
                event_type=AgentTopicManager.CONTROL_EVENT,
            )
            .order_by("event_data__created_at")
        )

    @classmethod
    def all_events_for_thread(cls, thread_id: str) -> list["PersistedAgentEventEntity"]:
        """
        Retrieves all events (both display and control) for a thread.
        """
        return list(cls.objects().filter(thread_id=thread_id).order_by("event_data__created_at"))

    # Inside ThreadService or potentially PersistedAgentEventEntity as a class method

    @classmethod
    def get_aggregated_run_statistics(cls, thread_id: str) -> list[dict]:
        """
        Uses MongoDB aggregation to calculate statistics for each run within a thread.
        Returns a list of dictionaries, each summarizing a run.
        """
        pipeline = [
            # 1. Match events for the given thread
            {MONGODB_MATCH: {"thread_id": thread_id}},
            # 2. Add a standardized BSON date field (simplified)
            {MONGODB_ADD_FIELDS: {"event_time": {MONGODB_TO_DATE: {MONGODB_DIVIDE: [f"{MONGODB_EVENT_DATA}.created_at", 1e6]}}}},
            # 3. Sort events within the thread by time
            {MONGODB_SORT: {"event_time": 1}},
            # 4. Group by run_id and event_id to de-duplicate events
            # We take the first occurrence of each event_id within a run.
            # All fields needed for the subsequent $group stage must be preserved here.
            {
                MONGODB_GROUP: {
                    "_id": {"run_id": MONGODB_RUN_ID, "event_id": MONGODB_EVENT_ID},
                    "run_id_val": {MONGODB_FIRST: MONGODB_RUN_ID},  # Keep run_id for next stage
                    "display_id": {MONGODB_FIRST: MONGODB_DISPLAY_ID},
                    "event_time": {MONGODB_FIRST: MONGODB_EVENT_TIME},
                    "event_parents": {MONGODB_FIRST: MONGODB_EVENT_PARENTS},
                    "agent_class": {MONGODB_FIRST: MONGODB_AGENT_CLASS},
                    "agent_id": {MONGODB_FIRST: MONGODB_AGENT_ID},
                    "event_data": {MONGODB_FIRST: MONGODB_EVENT_DATA},  # For LLM cost calculation
                    "event_type": {MONGODB_FIRST: MONGODB_EVENT_TYPE},
                }
            },
            # 5. Group events by run_id to calculate run-level stats
            # This stage now operates on the de-duplicated events from the previous stage.
            {
                MONGODB_GROUP: {
                    "_id": "$run_id_val",
                    "display_id": {MONGODB_FIRST: "$display_id"},
                    "first_event_time": {"$min": "$event_time"},
                    "latest_event_time": {"$max": "$event_time"},
                    "n_events": {"$sum": 1},
                    "start_events": {
                        "$sum": {
                            MONGODB_COND: [
                                {
                                    "$and": [
                                        {"$in": ["StartEvent", MONGODB_EVENT_PARENTS]},
                                        {"$eq": [MONGODB_EVENT_TYPE, AgentTopicManager.CONTROL_EVENT]},
                                    ]
                                },
                                1,
                                0,
                            ]
                        }
                    },
                    "stop_events": {"$sum": {MONGODB_COND: [{"$in": ["StopEvent", MONGODB_EVENT_PARENTS]}, 1, 0]}},
                    "exception_events": {"$sum": {MONGODB_COND: [{"$in": ["ExceptionEvent", MONGODB_EVENT_PARENTS]}, 1, 0]}},
                    "hitl_request_events": {
                        "$sum": {MONGODB_COND: [{"$in": ["HumanInTheLoopRequestEvent", MONGODB_EVENT_PARENTS]}, 1, 0]}
                    },
                    "hitl_response_events": {
                        "$sum": {MONGODB_COND: [{"$in": ["HumanInTheLoopResponseEvent", MONGODB_EVENT_PARENTS]}, 1, 0]}
                    },
                    "bitl_request_events": {
                        "$sum": {MONGODB_COND: [{"$in": ["BotInTheLoopRequestEvent", MONGODB_EVENT_PARENTS]}, 1, 0]}
                    },
                    "bitl_response_events": {
                        "$sum": {MONGODB_COND: [{"$in": ["BotInTheLoopResponseEvent", MONGODB_EVENT_PARENTS]}, 1, 0]}
                    },
                    "aitl_request_events": {
                        "$sum": {MONGODB_COND: [{"$in": ["AgentInTheLoopRequestEvent", MONGODB_EVENT_PARENTS]}, 1, 0]}
                    },
                    "aitl_response_events": {
                        "$sum": {MONGODB_COND: [{"$in": ["AgentInTheLoopResponseEvent", MONGODB_EVENT_PARENTS]}, 1, 0]}
                    },
                    # --- Calculate LLM Cost ---
                    "llm_cost": {
                        "$sum": {
                            MONGODB_COND: {
                                "if": {"$in": ["LLMCostEvent", MONGODB_EVENT_PARENTS]},
                                "then": {
                                    "$add": [
                                        {MONGODB_IF_NULL: ["$event_data.prompt_tokens_costs", 0]},
                                        {MONGODB_IF_NULL: ["$event_data.completion_tokens_costs", 0]},
                                        {MONGODB_IF_NULL: ["$event_data.embedding_tokens_costs", 0]},
                                    ]
                                },
                                "else": 0,
                            }
                        }
                    },
                    # --- Collect Agent Info ---
                    "participating_agents_in_run": {
                        "$addToSet": {"agent_class": "$agent_class", "agent_id": "$agent_id"}
                    },
                    "potential_start_events": {
                        "$push": {
                            "agent_class": "$agent_class",
                            "agent_id": "$agent_id",
                            "event_time": "$event_time",
                            "is_start": {"$in": ["StartEvent", MONGODB_EVENT_PARENTS]},
                            "is_not_user": {"$ne": ["$agent_class", "UserAgent"]},
                            "is_control": {"$eq": [MONGODB_EVENT_TYPE, AgentTopicManager.CONTROL_EVENT]},
                        }
                    },
                }
            },
            # 6. Project/AddFields to calculate derived stats for each run and format output
            {
                "$addFields": {
                    "run_id": "$_id",
                    "started_at": "$first_event_time",
                    "ended_at": "$latest_event_time",
                    "duration": {
                        MONGODB_COND: {
                            "if": {"$and": [MONGODB_FIRST_EVENT_TIME, MONGODB_LATEST_EVENT_TIME]},
                            "then": {MONGODB_DIVIDE: [{"$subtract": [MONGODB_LATEST_EVENT_TIME, MONGODB_FIRST_EVENT_TIME]}, 1000]},
                            "else": None,
                        }
                    },
                    "has_pending": {"$gt": ["$start_events", {"$add": ["$stop_events", "$exception_events"]}]},
                    "has_errors": {"$gt": ["$exception_events", 0]},
                    "is_hitl": {"$gt": ["$hitl_request_events", 0]},
                    "open_hitl": {"$gt": ["$hitl_request_events", "$hitl_response_events"]},
                    "is_bitl": {"$gt": ["$bitl_request_events", 0]},
                    "open_bitl": {"$gt": ["$bitl_request_events", "$bitl_response_events"]},
                    "is_aitl": {"$gt": ["$aitl_request_events", 0]},
                    "open_aitl": {"$gt": ["$aitl_request_events", "$aitl_response_events"]},
                    "start_event_info": {
                        MONGODB_FIRST: {
                            "$filter": {
                                "input": "$potential_start_events",
                                "as": "event",
                                "cond": {"$and": ["$$event.is_start", "$$event.is_not_user", "$$event.is_control"]},
                            }
                        }
                    },
                }
            },
            # 7. Final projection to shape the output document for each run
            {
                "$project": {
                    "_id": 0,
                    "run_id": 1,
                    "display_id": 1,
                    "started_at": 1,
                    "ended_at": 1,
                    "duration": 1,
                    "n_events": 1,
                    "has_errors": 1,
                    "has_pending": 1,
                    "is_hitl": 1,
                    "open_hitl": 1,
                    "is_bitl": 1,
                    "open_bitl": 1,
                    "is_aitl": 1,
                    "open_aitl": 1,
                    "llm_cost": 1,
                    "participating_agents_in_run": 1,
                    "start_agent_class": "$start_event_info.agent_class",
                    "start_agent_id": "$start_event_info.agent_id",
                    # Include raw counts needed for aggregation
                    "start_events": 1,
                    "stop_events": 1,
                    "exception_events": 1,
                    "hitl_request_events": 1,
                    "hitl_response_events": 1,
                    "bitl_request_events": 1,
                    "bitl_response_events": 1,
                    "aitl_request_events": 1,
                    "aitl_response_events": 1,
                }
            },
        ]

        results = list(cls.objects.aggregate(pipeline))
        return results

    @classmethod
    def to_message_history(cls, thread_id: str) -> list[UserChatMessage | AssistantChatMessage]:
        events = cls._get_message_events(thread_id)
        context = cls._MessageContext()
        message_history: list[UserChatMessage | AssistantChatMessage] = []

        for event in events:
            cls._process_event(event, context, message_history)

        cls._finalize_assistant_message(context, message_history)
        return message_history

    @classmethod
    def _get_message_events(cls, thread_id: str):
        """Retrieve and filter message events from the database."""
        return (
            cls.objects()
            .filter(
                thread_id=thread_id,
                event_type=AgentTopicManager.DISPLAY_EVENT,
                event_parents__in=[
                    "ChunkEvent",
                    "UserMessageEvent",
                    "HumanInTheLoopRequestEvent",
                    "HumanInTheLoopResponseEvent",
                ],
            )
            .order_by("event_data__created_at")
            .only("event_name", "event_data", "agent_id", "agent_class", "run_id")
        )

    @classmethod
    def _process_event(cls, event, context: "_MessageContext", message_history: list):
        """Process a single event and update message history."""
        if cls._is_user_event(event):
            cls._handle_user_event(event, context, message_history)
        elif cls._is_assistant_event(event):
            cls._handle_assistant_event(event, context, message_history)

    @classmethod
    def _is_user_event(cls, event) -> bool:
        """Check if event is a user message event."""
        return event.event_name in ["UserMessageEvent", "HumanInTheLoopResponseEvent"]

    @classmethod
    def _is_assistant_event(cls, event) -> bool:
        """Check if event is an assistant message event."""
        return event.event_name in ["ChunkEvent", "HumanInTheLoopRequestEvent"]

    @classmethod
    def _handle_user_event(cls, event, context: "_MessageContext", message_history: list):
        """Handle user message events."""
        cls._finalize_assistant_message(context, message_history)
        content = event.event_data.get("content", "") or event.event_data.get("response", "")
        message_history.append(
            UserChatMessage(role=MessageRole.USER, content=content, user_id=event.agent_id)
        )

    @classmethod
    def _handle_assistant_event(cls, event, context: "_MessageContext", message_history: list):
        """Handle assistant message events."""
        if context.is_same_assistant(event.run_id, event.agent_id):
            context.update_content(event)
        else:
            cls._finalize_assistant_message(context, message_history)
            context.start_new_message(event)

    @classmethod
    def _finalize_assistant_message(cls, context: "_MessageContext", message_history: list):
        """Add buffered assistant message to history if exists."""
        if context.assistant_content_buffer:
            message_history.append(
                AssistantChatMessage(
                    role=MessageRole.ASSISTANT,
                    content=context.assistant_content_buffer,
                    agent_id=context.current_agent_id,
                    agent_class=context.current_agent_class,
                )
            )
            context.reset()

    class _MessageContext:
        """Context for tracking assistant message state during processing."""
        def __init__(self):
            self.assistant_content_buffer = ""
            self.current_run_id = None
            self.current_agent_id = None
            self.current_agent_class = None

        def is_same_assistant(self, run_id: str, agent_id: str) -> bool:
            """Check if event belongs to current assistant message."""
            return self.current_run_id == run_id and self.current_agent_id == agent_id

        def update_content(self, event):
            """Update content for current assistant message."""
            self.assistant_content_buffer = event.event_data.get("content", "") or event.event_data.get("question", "")

        def start_new_message(self, event):
            """Start a new assistant message."""
            self.assistant_content_buffer = event.event_data.get("content", "") or event.event_data.get("question", "")
            self.current_run_id = event.run_id
            self.current_agent_id = event.agent_id
            self.current_agent_class = event.agent_class

        def reset(self):
            """Reset context state."""
            self.assistant_content_buffer = ""
            self.current_run_id = None
            self.current_agent_id = None
            self.current_agent_class = None

    @classmethod
    def get_event_timeseries(
        cls,
        time_range: TimeRange,
        thread_id: ObjectId | None = None,
        agent_id: ObjectId | None = None,
        agent_class: str | None = None,
        event_name: str | None = None,
    ) -> tuple[list[EventBucket], datetime, datetime, Resolution]:
        """
        Uses MongoDB aggregation to calculate time-based statistics for a thread or agent.
        Counts total events, optionally filtered by a specific event_name.
        If event_name is NOT provided, it aggregates over all events of type display_event.
        Returns a list of EventBucket instances (start_time, end_time, total_events),
        the overall start time, end time, and resolution of the analysis.
        """
        config = TIME_RANGE_CONFIG.get(time_range)
        start_time, end_time_boundary = cls._calculate_time_boundaries(config, time_range)
        match_filter = cls._build_match_filter(start_time, end_time_boundary, thread_id, agent_id, agent_class, event_name)
        pipeline = cls._build_aggregation_pipeline(config, match_filter)
        
        results = list(cls.objects.aggregate(pipeline))
        cls._normalize_timezone_info(results)
        
        filled_results = cls._fill_time_buckets(results, start_time, end_time_boundary, config)
        
        return filled_results, start_time, end_time_boundary, config.resolution

    @classmethod
    def _calculate_time_boundaries(cls, config, time_range: TimeRange) -> tuple[datetime, datetime]:
        """Calculate start and end time boundaries for the time range."""
        current_utc_time = datetime.now(UTC)
        if config.align_to_end_of_day:
            end_time_boundary = current_utc_time.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            end_time_boundary = current_utc_time

        start_time = end_time_boundary - config.delta
        if time_range == TimeRange.ONE_HOUR:
            start_time = current_utc_time - config.delta
            end_time_boundary = current_utc_time
            
        return start_time, end_time_boundary

    @classmethod
    def _build_match_filter(
        cls, 
        start_time: datetime, 
        end_time_boundary: datetime,
        thread_id: ObjectId | None,
        agent_id: ObjectId | None,
        agent_class: str | None,
        event_name: str | None
    ) -> dict[str, Any]:
        """Build the MongoDB match filter for the aggregation pipeline."""
        match_filter: dict[str, Any] = {
            "event_data.created_at": {
                "$gte": int(start_time.timestamp() * 1e9),
                "$lte": int(end_time_boundary.timestamp() * 1e9),
            },
        }

        if thread_id:
            match_filter["thread_id"] = thread_id

        if agent_class and agent_id:
            match_filter["agent_class"] = agent_class
            match_filter["agent_id"] = agent_id

        if event_name:
            match_filter["event_parents"] = event_name
            
        return match_filter

    @classmethod
    def _build_aggregation_pipeline(cls, config, match_filter: dict[str, Any]) -> list[dict[str, Any]]:
        """Build the MongoDB aggregation pipeline for event timeseries."""
        return [
            # 1. Match events based on primary criteria
            {MONGODB_MATCH: match_filter},
            # 2. Add a standardized BSON date field
            {MONGODB_ADD_FIELDS: {"event_time": {MONGODB_TO_DATE: {MONGODB_DIVIDE: [f"{MONGODB_EVENT_DATA}.created_at", 1e6]}}}},
            # 3. Create time buckets (timestamp in milliseconds)
            {
                "$addFields": {
                    "time_bucket": {
                        "$subtract": [
                            {"$toLong": "$event_time"},
                            {"$mod": [{"$toLong": "$event_time"}, config.interval_seconds * 1000]},
                        ]
                    }
                }
            },
            # 4. Group by time_bucket and event_id to de-duplicate events
            {
                MONGODB_GROUP: {
                    "_id": {"time_bucket": "$time_bucket", "event_id": "$event_id"},
                    "time_bucket_val": {MONGODB_FIRST: "$time_bucket"},
                }
            },
            # 5. Group events by time bucket and count them
            {
                MONGODB_GROUP: {
                    "_id": "$time_bucket_val",
                    "start_time": {MONGODB_FIRST: {"$toDate": "$time_bucket_val"}},
                    "total_events": {"$sum": 1},
                }
            },
            # 6. Add end_time field (derived from bucket start + interval)
            {
                "$addFields": {
                    "end_time": {
                        "$toDate": {"$add": ["$_id", config.interval_seconds * 1000]}
                    }
                }
            },
            # 7. Project the final simplified fields
            {
                "$project": {
                    "_id": 0,
                    "start_time": 1,
                    "end_time": 1,
                    "total_events": 1,
                }
            },
            # 8. Sort by start_time
            {"$sort": {"start_time": 1}},
        ]

    @classmethod
    def _normalize_timezone_info(cls, results: list[dict[str, Any]]) -> None:
        """Normalize timezone information in the results."""
        for result in results:
            if result["start_time"].tzinfo is None:
                result["start_time"] = result["start_time"].replace(tzinfo=UTC)
            if result["end_time"].tzinfo is None:
                result["end_time"] = result["end_time"].replace(tzinfo=UTC)

    @classmethod
    def _fill_time_buckets(
        cls, 
        results: list[dict[str, Any]], 
        start_time: datetime, 
        end_time_boundary: datetime, 
        config
    ) -> list[EventBucket]:
        """Fill time buckets with data, creating empty buckets where needed."""
        filled_results: list[EventBucket] = []
        current_loop_time = cls._align_start_time(start_time, config)
        
        idx = 0
        while current_loop_time < end_time_boundary:
            current_bucket_end_time = current_loop_time + timedelta(seconds=config.interval_seconds)
            bucket_data = cls._find_matching_bucket(results, idx, current_loop_time, current_bucket_end_time)
            
            if bucket_data:
                filled_results.append(
                    EventBucket(
                        start_time=bucket_data["start_time"],
                        end_time=bucket_data["end_time"],
                        total_events=bucket_data["total_events"],
                    )
                )
                idx += 1
            else:
                cls._add_empty_bucket(filled_results, current_loop_time, current_bucket_end_time, end_time_boundary)

            current_loop_time = current_bucket_end_time
            
            if cls._should_break_loop(filled_results, start_time, end_time_boundary, config):
                break
                
        return filled_results

    @classmethod
    def _align_start_time(cls, start_time: datetime, config) -> datetime:
        """Align start time to appropriate boundaries based on interval."""
        current_loop_time = start_time
        if config.interval_seconds >= 3600:
            current_loop_time = current_loop_time.replace(minute=0, second=0, microsecond=0)
        if config.interval_seconds >= 86400:
            current_loop_time = current_loop_time.replace(hour=0)
        return current_loop_time

    @classmethod
    def _find_matching_bucket(cls, results: list[dict[str, Any]], idx: int, current_loop_time: datetime, current_bucket_end_time: datetime) -> dict[str, Any] | None:
        """Find a matching bucket in results for the current time range."""
        if idx < len(results):
            res_start_time = results[idx]["start_time"]
            if res_start_time >= current_loop_time and res_start_time < current_bucket_end_time:
                return results[idx]
        return None

    @classmethod
    def _add_empty_bucket(cls, filled_results: list[EventBucket], current_loop_time: datetime, current_bucket_end_time: datetime, end_time_boundary: datetime) -> None:
        """Add an empty bucket to the results."""
        actual_end_time = min(current_bucket_end_time, end_time_boundary)
        if current_loop_time < end_time_boundary:
            filled_results.append(
                EventBucket(
                    start_time=current_loop_time,
                    end_time=actual_end_time,
                    total_events=0,
                )
            )

    @classmethod
    def _should_break_loop(cls, filled_results: list[EventBucket], start_time: datetime, end_time_boundary: datetime, config) -> bool:
        """Check if the loop should be broken due to excessive bucket count."""
        if (
            len(filled_results) > ((end_time_boundary - start_time).total_seconds() / config.interval_seconds) + 10
            and config.interval_seconds > 0
        ):
            logger.warning(
                f"Exiting fill loop early due to excessive bucket count. "
                f"Expected max buckets: {((end_time_boundary - start_time).total_seconds() / config.interval_seconds) + 10}, "
                f"Current count: {len(filled_results)}"
            )
            return True
        return False
