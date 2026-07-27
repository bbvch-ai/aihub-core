import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from bson import ObjectId
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from mongoengine import DictField, Document, ListField, StringField

from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.messaging.entities.types.event_bucket import EventBucket
from swiss_ai_hub.core.topic_managers.agents.agent_topic_manager import AgentTopicManager

if TYPE_CHECKING:
    from swiss_ai_hub.core.events.base_event import BaseEvent
    from swiss_ai_hub.core.topics import AgentInstanceTopic

logger = logging.getLogger(__name__)


class TimeRange(StrEnum):
    ONE_HOUR = "1h"
    TWENTY_FOUR_HOURS = "24h"
    THIRTY_DAYS = "30d"
    THREE_SIXTY_FIVE_DAYS = "365d"


class Resolution(StrEnum):
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
    @trace_fn
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
    @trace_fn
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
    @trace_fn
    def thread_id_for_display(cls, display_id: str) -> str | None:
        """Resolve the thread that owns a display. Every event sharing a display_id shares one thread_id (AITL
        delegation preserves both), so any match yields the same answer."""
        event = cls.objects(display_id=display_id).only("thread_id").first()
        return event.thread_id if event else None

    @classmethod
    @trace_fn
    def display_events_for_threads(
        cls, thread_ids: list[str], event_name: str | None = None
    ) -> list["PersistedAgentEventEntity"]:
        query = cls.objects().filter(thread_id__in=thread_ids, event_type=AgentTopicManager.DISPLAY_EVENT)

        if event_name is not None:
            query = query.filter(event_parents__contains=event_name)

        return query.order_by("event_data__created_at")

    @classmethod
    @trace_fn
    def display_events_for_agent(cls, agent_id: str) -> list["PersistedAgentEventEntity"]:
        return (
            cls.objects()
            .filter(agent_id=agent_id, event_type=AgentTopicManager.DISPLAY_EVENT)
            .order_by("event_data__created_at")
        )

    @classmethod
    @trace_fn
    def thread_ids_by_status(cls, status: str, thread_ids: list[str] | None = None) -> list[str]:
        """
        Classify each thread by run status from its events and return the thread_ids
        matching the requested status ("active" | "completed" | "failed").

        Precedence: failed (any ExceptionEvent) > active (more StartEvents than
        StopEvent + ExceptionEvent) > completed. Mirrors the has_errors / has_pending
        logic in ThreadService._calculate_overall_thread_stats.
        """
        pipeline = [
            *([{"$match": {"thread_id": {"$in": thread_ids}}}] if thread_ids is not None else []),
            # De-duplicate events by id (an event may be persisted more than once),
            # same as get_aggregated_run_statistics.
            {
                "$group": {
                    "_id": {"thread_id": "$thread_id", "event_id": "$event_id"},
                    "thread_id_val": {"$first": "$thread_id"},
                    "event_parents": {"$first": "$event_parents"},
                    "event_type": {"$first": "$event_type"},
                }
            },
            # Count terminal/start events per thread.
            {
                "$group": {
                    "_id": "$thread_id_val",
                    "start_events": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$and": [
                                        {"$in": ["StartEvent", "$event_parents"]},
                                        {"$eq": ["$event_type", AgentTopicManager.CONTROL_EVENT]},
                                    ]
                                },
                                1,
                                0,
                            ]
                        }
                    },
                    "stop_events": {"$sum": {"$cond": [{"$in": ["StopEvent", "$event_parents"]}, 1, 0]}},
                    "exception_events": {"$sum": {"$cond": [{"$in": ["ExceptionEvent", "$event_parents"]}, 1, 0]}},
                }
            },
            # Classify each thread.
            {
                "$addFields": {
                    "status": {
                        "$switch": {
                            "branches": [
                                {"case": {"$gt": ["$exception_events", 0]}, "then": "failed"},
                                {
                                    "case": {"$gt": ["$start_events", {"$add": ["$stop_events", "$exception_events"]}]},
                                    "then": "active",
                                },
                            ],
                            "default": "completed",
                        }
                    }
                }
            },
            {"$match": {"status": status}},
        ]
        return [doc["_id"] for doc in cls.objects.aggregate(pipeline)]

    @classmethod
    @trace_fn
    def human_in_the_loop_request_events_for_thread(cls, thread_id: str) -> list["PersistedAgentEventEntity"]:
        return list(
            cls.objects()
            .filter(thread_id=thread_id, event_parents__contains="HumanInTheLoopRequestEvent")
            .order_by("event_data__created_at")
        )

    @classmethod
    @trace_fn
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
    @trace_fn
    def all_events_for_thread(cls, thread_id: str) -> list["PersistedAgentEventEntity"]:
        """
        Retrieves all events (both display and control) for a thread.
        """
        return list(cls.objects().filter(thread_id=thread_id).order_by("event_data__created_at"))

    # Inside ThreadService or potentially PersistedAgentEventEntity as a class method

    @classmethod
    @trace_fn
    def get_aggregated_run_statistics(cls, thread_id: str) -> list[dict]:
        """
        Uses MongoDB aggregation to calculate statistics for each run within a thread.
        Returns a list of dictionaries, each summarizing a run.
        """
        pipeline = [
            # 1. Match events for the given thread
            {"$match": {"thread_id": thread_id}},
            # 2. Add a standardized BSON date field (simplified)
            {"$addFields": {"event_time": {"$toDate": {"$divide": ["$event_data.created_at", 1e6]}}}},
            # 3. Sort events within the thread by time
            {"$sort": {"event_time": 1}},
            # 4. Group by run_id and event_id to de-duplicate events
            # We take the first occurrence of each event_id within a run.
            # All fields needed for the subsequent $group stage must be preserved here.
            {
                "$group": {
                    "_id": {"run_id": "$run_id", "event_id": "$event_id"},
                    "run_id_val": {"$first": "$run_id"},  # Keep run_id for next stage
                    "display_id": {"$first": "$display_id"},
                    "event_time": {"$first": "$event_time"},
                    "event_parents": {"$first": "$event_parents"},
                    "agent_class": {"$first": "$agent_class"},
                    "agent_id": {"$first": "$agent_id"},
                    "event_data": {"$first": "$event_data"},  # For LLM cost calculation
                    "event_type": {"$first": "$event_type"},
                }
            },
            # 5. Group events by run_id to calculate run-level stats
            # This stage now operates on the de-duplicated events from the previous stage.
            {
                "$group": {
                    "_id": "$run_id_val",
                    "display_id": {"$first": "$display_id"},
                    "first_event_time": {"$min": "$event_time"},
                    "latest_event_time": {"$max": "$event_time"},
                    "n_events": {"$sum": 1},
                    "start_events": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$and": [
                                        {"$in": ["StartEvent", "$event_parents"]},
                                        {"$eq": ["$event_type", AgentTopicManager.CONTROL_EVENT]},
                                    ]
                                },
                                1,
                                0,
                            ]
                        }
                    },
                    "stop_events": {"$sum": {"$cond": [{"$in": ["StopEvent", "$event_parents"]}, 1, 0]}},
                    "exception_events": {"$sum": {"$cond": [{"$in": ["ExceptionEvent", "$event_parents"]}, 1, 0]}},
                    "hitl_request_events": {
                        "$sum": {"$cond": [{"$in": ["HumanInTheLoopRequestEvent", "$event_parents"]}, 1, 0]}
                    },
                    "hitl_response_events": {
                        "$sum": {"$cond": [{"$in": ["HumanInTheLoopResponseEvent", "$event_parents"]}, 1, 0]}
                    },
                    "bitl_request_events": {
                        "$sum": {"$cond": [{"$in": ["BotInTheLoopRequestEvent", "$event_parents"]}, 1, 0]}
                    },
                    "bitl_response_events": {
                        "$sum": {"$cond": [{"$in": ["BotInTheLoopResponseEvent", "$event_parents"]}, 1, 0]}
                    },
                    "aitl_request_events": {
                        "$sum": {"$cond": [{"$in": ["AgentInTheLoopRequestEvent", "$event_parents"]}, 1, 0]}
                    },
                    "aitl_response_events": {
                        "$sum": {"$cond": [{"$in": ["AgentInTheLoopResponseEvent", "$event_parents"]}, 1, 0]}
                    },
                    # --- Calculate LLM Cost ---
                    "llm_cost": {
                        "$sum": {
                            "$cond": {
                                "if": {"$in": ["LLMCostEvent", "$event_parents"]},
                                "then": {
                                    "$add": [
                                        {"$ifNull": ["$event_data.prompt_tokens_costs", 0]},
                                        {"$ifNull": ["$event_data.completion_tokens_costs", 0]},
                                        {"$ifNull": ["$event_data.embedding_tokens_costs", 0]},
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
                            "is_start": {"$in": ["StartEvent", "$event_parents"]},
                            "is_not_user": {"$ne": ["$agent_class", "UserAgent"]},
                            "is_control": {"$eq": ["$event_type", AgentTopicManager.CONTROL_EVENT]},
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
                        "$cond": {
                            "if": {"$and": ["$first_event_time", "$latest_event_time"]},
                            "then": {"$divide": [{"$subtract": ["$latest_event_time", "$first_event_time"]}, 1000]},
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
                        "$first": {
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
    @trace_fn
    def to_message_history(cls, thread_id: str) -> list[ChatMessage]:
        # Retrieve and filter events from the database
        events = (
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

        message_history: list[ChatMessage] = []
        assistant_content_buffer = ""
        current_run_id = None
        current_agent_id = None
        current_agent_class = None

        for event in events:
            if event.event_name in ["UserMessageEvent", "HumanInTheLoopResponseEvent"]:
                # Finalize any ongoing assistant message
                if assistant_content_buffer:
                    message_history.append(
                        ChatMessage(
                            role=MessageRole.ASSISTANT,
                            content=assistant_content_buffer,
                            additional_kwargs={
                                "agent_id": current_agent_id,
                                "agent_class": current_agent_class,
                            },
                        )
                    )
                    assistant_content_buffer = ""
                    current_run_id = None
                    current_agent_id = None
                    current_agent_class = None

                content = event.event_data.get("content", "") or event.event_data.get("response", "")
                message_history.append(
                    ChatMessage(
                        role=MessageRole.USER,
                        content=content,
                    )
                )

            elif event.event_name in ["ChunkEvent", "HumanInTheLoopRequestEvent"]:
                if current_run_id == event.run_id and current_agent_id == event.agent_id:
                    assistant_content_buffer = event.event_data.get("content", "") or event.event_data.get(
                        "question", ""
                    )
                else:
                    # Finalize previous assistant message if it exists
                    if assistant_content_buffer:
                        message_history.append(
                            ChatMessage(
                                role=MessageRole.ASSISTANT,
                                content=assistant_content_buffer,
                                additional_kwargs={
                                    "agent_id": current_agent_id,
                                    "agent_class": current_agent_class,
                                },
                            )
                        )
                    # Start a new assistant message
                    assistant_content_buffer = event.event_data.get("content", "") or event.event_data.get(
                        "question", ""
                    )
                    current_run_id = event.run_id
                    current_agent_id = event.agent_id
                    current_agent_class = event.agent_class
            else:
                continue  # Skip other event types

        # Finalize any remaining assistant message
        if assistant_content_buffer:
            message_history.append(
                ChatMessage(
                    role=MessageRole.ASSISTANT,
                    content=assistant_content_buffer,
                    additional_kwargs={
                        "agent_id": current_agent_id,
                        "agent_class": current_agent_class,
                    },
                )
            )

        return message_history

    @classmethod
    @trace_fn
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

        current_utc_time = datetime.now(UTC)
        if config.align_to_end_of_day:
            end_time_boundary = current_utc_time.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            end_time_boundary = current_utc_time

        start_time = end_time_boundary - config.delta
        if time_range == TimeRange.ONE_HOUR:  # Compare with Enum member
            start_time = current_utc_time - config.delta
            end_time_boundary = current_utc_time

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

        pipeline: list[dict[str, Any]] = [
            # 1. Match events based on primary criteria
            {"$match": match_filter},
            # 2. Add a standardized BSON date field
            {"$addFields": {"event_time": {"$toDate": {"$divide": ["$event_data.created_at", 1e6]}}}},
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
                "$group": {
                    "_id": {"time_bucket": "$time_bucket", "event_id": "$event_id"},
                    "time_bucket_val": {"$first": "$time_bucket"},
                }
            },
            # 5. Group events by time bucket and count them
            {
                "$group": {
                    "_id": "$time_bucket_val",  #
                    "start_time": {"$first": {"$toDate": "$time_bucket_val"}},
                    "total_events": {"$sum": 1},
                }
            },
            # 6. Add end_time field (derived from bucket start + interval)
            {
                "$addFields": {
                    "end_time": {
                        "$toDate": {"$add": ["$_id", config.interval_seconds * 1000]}
                    }  # $_id is time_bucket (ms)
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

        results = list(cls.objects.aggregate(pipeline))

        for result in results:
            if result["start_time"].tzinfo is None:
                result["start_time"] = result["start_time"].replace(tzinfo=UTC)
            if result["end_time"].tzinfo is None:
                result["end_time"] = result["end_time"].replace(tzinfo=UTC)

        filled_results: list[EventBucket] = []
        current_loop_time = start_time

        if config.interval_seconds >= 3600:
            current_loop_time = current_loop_time.replace(minute=0, second=0, microsecond=0)
        if config.interval_seconds >= 86400:
            current_loop_time = current_loop_time.replace(hour=0)

        idx = 0
        while current_loop_time < end_time_boundary:
            current_bucket_end_time = current_loop_time + timedelta(seconds=config.interval_seconds)
            bucket_data = None

            if idx < len(results):
                res_start_time = results[idx]["start_time"]
                if res_start_time >= current_loop_time and res_start_time < current_bucket_end_time:
                    bucket_data = results[idx]
                    idx += 1

            if bucket_data:
                filled_results.append(
                    EventBucket(
                        start_time=bucket_data["start_time"],
                        end_time=bucket_data["end_time"],
                        total_events=bucket_data["total_events"],
                    )
                )
            else:
                actual_end_time = min(current_bucket_end_time, end_time_boundary)
                if current_loop_time < end_time_boundary:
                    filled_results.append(
                        EventBucket(
                            start_time=current_loop_time,
                            end_time=actual_end_time,
                            total_events=0,
                        )
                    )

            current_loop_time = current_bucket_end_time
            # Safety break for the unlikely event that 'end_time_boundary' isn't reached
            # due to floating point issues with many small intervals
            if (
                len(filled_results) > ((end_time_boundary - start_time).total_seconds() / config.interval_seconds) + 10
                and config.interval_seconds > 0
            ):
                # This condition suggests we've created significantly more buckets than expected
                logger.warning(
                    f"Exiting fill loop early due to excessive bucket count. Current loop time: "
                    f"{current_loop_time}, end_time_boundary: {end_time_boundary}"
                )
                break

        return filled_results, start_time, end_time_boundary, config.resolution
