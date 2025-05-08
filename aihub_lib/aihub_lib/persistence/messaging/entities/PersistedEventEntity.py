import logging
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Dict, List, Literal, Optional, Tuple, Any

from bson import ObjectId
from llama_index.core.base.llms.types import MessageRole
from mongoengine import DictField, Document, ListField, StringField

from aihub_lib.nats.events.control import AssistantChatMessage, UserChatMessage
from aihub_lib.nats.topic_managers.TopicManager import TopicManager
from aihub_lib.persistence.messaging.entities.types.EventBucket import EventBucket

if TYPE_CHECKING:
    from aihub_lib.nats.events import BaseEvent
    from aihub_lib.nats.topics import AgentTopic

logger = logging.getLogger(__name__)


EVENT_TIMESERIES_TIME_RANGE = Literal["1h", "24h", "30d", "365d"]
EVENT_TIMESERIES_RESOLUTION = Literal["1m", "1h", "1d", "1w"]

class PersistedEventEntity(Document):
    meta = {
        "collection": "events",
        "strict": False,
        "indexes": [
            {"fields": ["thread_id", "event_type"]},
            {"fields": ["agent_id", "event_type"]},
            {"fields": ["thread_id", "event_parents"]},
            {"fields": ["run_id"]},
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
    def persist_event(cls, event: "BaseEvent", topic: "AgentTopic", db: str):
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
        cls, thread_id: str, display_id: Optional[str] = None, event_name: Optional[str] = None
    ) -> List["PersistedEventEntity"]:
        query = cls.objects().filter(thread_id=thread_id, event_type=TopicManager.DISPLAY_EVENT)

        if display_id is not None:
            query = query.filter(display_id=display_id)

        if event_name is not None:
            query = query.filter(event_parents__contains=event_name)

        return query.order_by("event_data__created_at")

    @classmethod
    def display_events_for_threads(
        cls, thread_ids: List[str], event_name: Optional[str] = None
    ) -> List["PersistedEventEntity"]:
        query = cls.objects().filter(thread_id__in=thread_ids, event_type=TopicManager.DISPLAY_EVENT)

        if event_name is not None:
            query = query.filter(event_parents__contains=event_name)

        return query.order_by("event_data__created_at")

    @classmethod
    def display_events_for_agent(cls, agent_id: str) -> List["PersistedEventEntity"]:
        return (
            cls.objects()
            .filter(agent_id=agent_id, event_type=TopicManager.DISPLAY_EVENT)
            .order_by("event_data__created_at")
        )

    @classmethod
    def human_in_the_loop_request_events_for_thread(cls, thread_id: str) -> List["PersistedEventEntity"]:
        return list(
            cls.objects()
            .filter(thread_id=thread_id, event_parents__contains="HumanInTheLoopRequestEvent")
            .order_by("event_data__created_at")
        )

    @classmethod
    def human_in_the_loop_response_events_for_thread(cls, thread_id: str) -> List["PersistedEventEntity"]:
        return list(
            cls.objects()
            .filter(
                thread_id=thread_id,
                event_parents__contains="HumanInTheLoopResponseEvent",
                event_type=TopicManager.CONTROL_EVENT,
            )
            .order_by("event_data__created_at")
        )

    @classmethod
    def all_events_for_thread(cls, thread_id: str) -> List["PersistedEventEntity"]:
        """
        Retrieves all events (both display and control) for a thread.
        """
        return list(cls.objects().filter(thread_id=thread_id).order_by("event_data__created_at"))

    # Inside ThreadService or potentially PersistedEventEntity as a class method

    @classmethod
    def get_aggregated_run_statistics(cls, thread_id: str) -> List[dict]:
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
            # 4. Group events by run_id to calculate run-level stats
            {
                "$group": {
                    "_id": "$run_id",
                    "display_id": {"$first": "$display_id"},
                    "first_event_time": {"$min": "$event_time"},
                    "latest_event_time": {"$max": "$event_time"},
                    "n_events": {"$sum": 1},
                    # --- Count specific event types ---
                    "start_events": {"$sum": {"$cond": [{"$in": ["StartEvent", "$event_parents"]}, 1, 0]}},
                    "stop_events": {
                        "$sum": {"$cond": [{"$in": ["StopEvent", "$event_parents"]}, 1, 0]}
                    },  # Added stop count
                    "exception_events": {
                        "$sum": {"$cond": [{"$in": ["ExceptionEvent", "$event_parents"]}, 1, 0]}
                    },  # Simplified
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
                    # --- Calculate LLM Cost (Simplified) ---
                    "llm_cost": {
                        "$sum": {
                            "$cond": {
                                "if": {"$in": ["LLMCostEvent", "$event_parents"]},  # Simplified
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
                        }
                    },
                }
            },
            # 5. Project/AddFields to calculate derived stats for each run and format output
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
                    "has_pending": {
                        "$gt": ["$start_events", {"$add": ["$stop_events", "$exception_events"]}]
                    },  # Uses stop_events
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
                                "cond": {"$and": ["$$event.is_start", "$$event.is_not_user"]},
                            }
                        }
                    },
                }
            },
            # 6. Final projection to shape the output document for each run
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
                    "exception_events": 1,  # Added stop_events
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
    def to_message_history(cls, thread_id: str) -> List[UserChatMessage | AssistantChatMessage]:
        # Retrieve and filter events from the database
        events = (
            cls.objects()
            .filter(
                thread_id=thread_id,
                event_type=TopicManager.DISPLAY_EVENT,
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

        message_history: List[UserChatMessage | AssistantChatMessage] = []
        assistant_content_buffer = ""
        current_run_id = None
        current_agent_id = None
        current_agent_class = None

        for event in events:
            if event.event_name in ["UserMessageEvent", "HumanInTheLoopResponseEvent"]:
                # Finalize any ongoing assistant message
                if assistant_content_buffer:
                    message_history.append(
                        AssistantChatMessage(
                            role=MessageRole.ASSISTANT,
                            content=assistant_content_buffer,
                            agent_id=current_agent_id,
                            agent_class=current_agent_class,
                        )
                    )
                    assistant_content_buffer = ""
                    current_run_id = None
                    current_agent_id = None
                    current_agent_class = None

                # Create and append user message
                content = event.event_data.get("content", "") or event.event_data.get("response", "")
                message_history.append(
                    UserChatMessage(
                        role=MessageRole.USER,
                        content=content,
                        user_id=event.agent_id,
                    )
                )

            elif event.event_name in ["ChunkEvent", "HumanInTheLoopRequestEvent"]:
                # Check if we are continuing the same assistant message
                if current_run_id == event.run_id and current_agent_id == event.agent_id:
                    assistant_content_buffer = event.event_data.get("content", "") or event.event_data.get(
                        "question", ""
                    )
                else:
                    # Finalize previous assistant message if it exists
                    if assistant_content_buffer:
                        message_history.append(
                            AssistantChatMessage(
                                role=MessageRole.ASSISTANT,
                                content=assistant_content_buffer,
                                agent_id=current_agent_id,
                                agent_class=current_agent_class,
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
                AssistantChatMessage(
                    role=MessageRole.ASSISTANT,
                    content=assistant_content_buffer,
                    agent_id=current_agent_id,
                    agent_class=current_agent_class,
                )
            )

        return message_history

    @classmethod
    def get_event_timeseries(
        cls,
        time_range: Literal["1h", "24h", "30d", "365d"],
        thread_id: Optional[ObjectId] = None,
        agent_id: Optional[ObjectId] = None,
        agent_class: Optional[str] = None,
        event_name: Optional[str] = None,
    ) -> Tuple[List[EventBucket], datetime, datetime, Literal["1m", "1h", "1d", "1w"]]:
        """
        Uses MongoDB aggregation to calculate time-based statistics for a thread or agent.
        Counts total events, optionally filtered by a specific event_name.
        If event_name is NOT provided, it aggregates over all events of type display_event.
        Requires either thread_id OR both agent_class and agent_id.
        Returns a list of EventBucket instances (start_time, end_time, total_events),
        the overall start time, end time, and resolution of the analysis.
        """
        resolution_val: Literal["1m", "1h", "1d", "1w"]
        interval_seconds: int

        if time_range == "1h":
            now = datetime.now(timezone.utc)
            start_time = now - timedelta(hours=1)
            resolution_val = "1m"
            interval_seconds = 60
        else:
            now = datetime.now(timezone.utc).replace(hour=23, minute=59, second=59, microsecond=999999)
            if time_range == "24h":
                start_time = now - timedelta(hours=24)
                resolution_val = "1h"
                interval_seconds = 60 * 60
            elif time_range == "30d":
                start_time = now - timedelta(days=30)
                resolution_val = "1d"
                interval_seconds = 60 * 60 * 24
            elif time_range == "365d":
                start_time = now - timedelta(days=365)
                resolution_val = "1w"
                interval_seconds = 60 * 60 * 24 * 7
            else:
                raise ValueError(f"Invalid time range: {time_range}")

        match_filter: Dict[str, Any] = {
            "event_type": "display_event",
            "event_data.created_at": {
                "$gte": int(start_time.timestamp() * 1e9),
                "$lte": int(now.timestamp() * 1e9),
            },
        }

        if thread_id:
            match_filter["thread_id"] = thread_id

        if agent_class and agent_id:
            match_filter["agent_class"] = agent_class
            match_filter["agent_id"] = agent_id

        if event_name:
            match_filter["event_parents"] = event_name

        pipeline: List[Dict[str, Any]] = [
            # 1. Match events based on primary criteria and optionally event_name
            {"$match": match_filter},

            # 2. Add a standardized BSON date field
            {"$addFields": {"event_time": {"$toDate": {"$divide": ["$event_data.created_at", 1e6]}}}},

            # 3. Create time buckets (timestamp in milliseconds)
            {
                "$addFields": {
                    "time_bucket": {
                        "$subtract": [
                            {"$toLong": "$event_time"},
                            {"$mod": [{"$toLong": "$event_time"}, interval_seconds * 1000]},
                        ]
                    }
                }
            },

            # 4. Group events by time bucket and count them
            {
                "$group": {
                    "_id": "$time_bucket", # Group by the millisecond timestamp of the bucket start
                    "start_time": {"$first": {"$toDate": "$time_bucket"}}, # Convert bucket start ms to Date
                    "total_events": {"$sum": 1} # Count documents in each bucket
                }
            },

            # 5. Add end_time field (derived from bucket start + interval)
            {
                "$addFields": {
                    "end_time": {"$toDate": {"$add": ["$_id", interval_seconds * 1000]}} # $_id is time_bucket (ms)
                }
            },

            # 6. Project the final simplified fields
            {
                "$project": {
                    "_id": 0,
                    "start_time": 1,
                    "end_time": 1,
                    "total_events": 1,
                }
            },

            # 7. Sort by start_time
            {"$sort": {"start_time": 1}},
        ]

        results = list(cls.objects.aggregate(pipeline))

        for result in results:
            if result["start_time"].tzinfo is None:
                result["start_time"] = result["start_time"].replace(tzinfo=timezone.utc)
            if result["end_time"].tzinfo is None:
                result["end_time"] = result["end_time"].replace(tzinfo=timezone.utc)

        filled_results: List[EventBucket] = []
        current_loop_time = start_time

        # Align current_loop_time for consistent bucket iteration start
        if interval_seconds >= 3600: # Hourly or more
            current_loop_time = current_loop_time.replace(minute=0, second=0, microsecond=0)
        if interval_seconds >= 86400: # Daily or more
            current_loop_time = current_loop_time.replace(hour=0)

        idx = 0
        while current_loop_time < now:
            current_bucket_end_time = current_loop_time + timedelta(seconds=interval_seconds)
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
                actual_end_time = min(current_bucket_end_time, now)
                # Only add bucket if its start time is less than the overall 'now'
                if current_loop_time < now:
                    filled_results.append(
                        EventBucket(
                            start_time=current_loop_time,
                            end_time=actual_end_time,
                            total_events=0,
                        )
                    )

            current_loop_time = current_bucket_end_time
            # Safety break for the unlikely event that 'now' isn't reached due to floating point issues with many small intervals
            if len(filled_results) > ( (now - start_time).total_seconds() / interval_seconds ) + 10 and interval_seconds > 0 :
                # This condition suggests we've created significantly more buckets than expected
                logger.warning(f"Exiting fill loop early due to excessive bucket count. Current loop time: {current_loop_time}, Now: {now}")
                break


        return filled_results, start_time, now, resolution_val