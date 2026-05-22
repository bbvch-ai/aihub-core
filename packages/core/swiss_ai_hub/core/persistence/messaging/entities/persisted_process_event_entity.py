from typing import TYPE_CHECKING, Self

from bson import ObjectId
from mongoengine import DictField, Document, ListField, StringField

from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn

if TYPE_CHECKING:
    from swiss_ai_hub.core.events.base_event import BaseEvent
    from swiss_ai_hub.core.topics import ProcessInstanceTopic

# MongoDB aggregation pipeline syntax constants. Field references ($-prefixed
# strings used as VALUES point to document fields; operators ($-prefixed strings
# used as KEYS introduce a stage or expression).
_PROCESS_WALKTHROUGH_ID_REF = "$process_walkthrough_id"
_PROCESS_CLASS_REF = "$process_class"
_PROCESS_ID_REF = "$process_id"

_OP_MATCH = "$match"
_OP_EQ = "$eq"


class PersistedProcessEventEntity(Document):
    meta = {
        "collection": "process_events",
        "strict": False,
        "indexes": [
            {"fields": ["process_class", "process_id", "process_walkthrough_id", "event_parents"]},
            {"fields": ["process_class", "process_id"]},
            {"fields": ["event_data.forms._event_name"]},
        ],
    }
    process_class = StringField(required=True)
    process_id = StringField(required=True)
    process_walkthrough_id = StringField(required=True)
    event_id = StringField(required=True)
    event_type = StringField(required=True)
    event_name = StringField(required=True)
    event_data = DictField(required=True)
    event_parents = ListField(StringField(), required=True)

    @classmethod
    @trace_fn
    def persist_event(cls, event: "BaseEvent", topic: "ProcessInstanceTopic", db: str) -> None:
        persisted_entity = cls(
            id=ObjectId(),
            process_class=topic.process_class,
            process_id=topic.process_id,
            process_walkthrough_id=topic.process_walkthrough_id,
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
    def get_open_human_work_requests(
        cls, process_class: str, process_id: str, process_walkthrough_id: str
    ) -> list[Self]:
        """
        Finds unanswered human work requests for a given process walkthrough.

        This method uses a MongoDB aggregation pipeline to identify work requests
        where no corresponding 'work' event has been fulfilled. A work request is
        considered "unanswered" or "open" if for all the event names listed in its
        `event_data.forms`, no matching 'work' event exists in the same
        process walkthrough.
        """
        pipeline = [
            # Stage 1: Filter for all documents that are human work requests
            # within the specified process walkthrough.
            {
                _OP_MATCH: {
                    "process_class": process_class,
                    "process_id": process_id,
                    "process_walkthrough_id": process_walkthrough_id,
                    "event_parents": "HumanWorkRequestEvent",
                }
            },
            # Stage 2: Use a sub-query ($lookup) to find any 'work' events that have been
            # persisted for the same walkthrough and match the event names required by the request's forms.
            {
                "$lookup": {
                    "from": cls._get_collection_name(),
                    "let": {
                        "form_event_names": "$event_data.forms._event_name",
                        "form_process_class": _PROCESS_CLASS_REF,
                        "form_process_id": _PROCESS_ID_REF,
                        "form_process_walkthrough_id": _PROCESS_WALKTHROUGH_ID_REF,
                    },
                    "pipeline": [
                        {
                            _OP_MATCH: {
                                "$expr": {
                                    "$and": [
                                        {_OP_EQ: [_PROCESS_WALKTHROUGH_ID_REF, "$$form_process_walkthrough_id"]},
                                        {_OP_EQ: [_PROCESS_CLASS_REF, "$$form_process_class"]},
                                        {_OP_EQ: [_PROCESS_ID_REF, "$$form_process_id"]},
                                        {_OP_EQ: ["$event_type", "work"]},
                                        {"$in": ["$event_name", "$$form_event_names"]},
                                    ]
                                }
                            }
                        }
                    ],
                    "as": "corresponding_work_events",
                }
            },
            # Stage 3: Filter the results to only include work requests where the $lookup
            # found no corresponding work events. An empty 'corresponding_work_events'
            # array signifies an unanswered request.
            {_OP_MATCH: {"corresponding_work_events": {"$size": 0}}},
        ]

        unanswered_requests_data = list(cls.objects.aggregate(pipeline))

        if not unanswered_requests_data:
            return []

        unanswered_ids = [data["_id"] for data in unanswered_requests_data]

        # Perform a final query to retrieve the full MongoEngine Document objects.
        # This is a robust way to convert aggregation results back into hydrated objects.
        return list(cls.objects(id__in=unanswered_ids))

    @classmethod
    @trace_fn
    def find_request_for_work_event(
        cls, process_class: str, process_id: str, process_walkthrough_id: str, event_name: str
    ) -> Self | None:
        """
        Finds the specific HumanWorkRequestEvent that corresponds to a given work event name
        within a process walkthrough.

        This is useful for linking a completed 'work' event back to the original request
        that prompted it by matching the event name against the `_event_name` field
        within the request's forms.
        """
        return cls.objects(
            # These fields are defined in the schema and are queried normally.
            process_class=process_class,
            process_id=process_id,
            process_walkthrough_id=process_walkthrough_id,
            event_parents="HumanWorkRequestEvent",
            # Use __raw__ to pass the nested query directly to MongoDB.
            # This bypasses MongoEngine's schema validation for this part of the query.
            __raw__={"event_data.forms._event_name": event_name},
        ).first()

    @classmethod
    def get_paginated_walkthrough_events(
        cls, process_class: str, process_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[int, list[dict]]:
        """
        Gets paginated process walkthroughs with all their events.

        Returns a tuple of (total_count, walkthrough_data) where walkthrough_data contains
        aggregated information about each walkthrough including all its events.
        """
        # First, get the total count of unique walkthroughs
        pipeline_count = [
            {
                _OP_MATCH: {
                    "process_class": process_class,
                    "process_id": process_id,
                }
            },
            {
                "$group": {
                    "_id": _PROCESS_WALKTHROUGH_ID_REF,
                }
            },
            {"$count": "total"},
        ]

        count_result = list(cls.objects.aggregate(pipeline_count))
        total_count = count_result[0]["total"] if count_result else 0

        # Calculate pagination
        skip = (page - 1) * page_size

        # Main pipeline to get walkthrough data with events
        pipeline = [
            {
                _OP_MATCH: {
                    "process_class": process_class,
                    "process_id": process_id,
                }
            },
            {"$sort": {"event_data.created_at": 1}},  # Sort events by creation time
            {
                "$group": {
                    "_id": _PROCESS_WALKTHROUGH_ID_REF,
                    "process_class": {"$first": _PROCESS_CLASS_REF},
                    "process_id": {"$first": _PROCESS_ID_REF},
                    "events": {
                        "$push": {
                            "event_id": "$event_id",
                            "event_type": "$event_type",
                            "event_name": "$event_name",
                            "event_data": "$event_data",
                            "event_parents": "$event_parents",
                            "process_class": _PROCESS_CLASS_REF,
                            "process_id": _PROCESS_ID_REF,
                            "process_walkthrough_id": _PROCESS_WALKTHROUGH_ID_REF,
                        }
                    },
                    "first_event_timestamp": {"$min": "$event_data.created_at"},
                    "last_event_timestamp": {"$max": "$event_data.created_at"},
                    "event_count": {"$sum": 1},
                }
            },
            {"$sort": {"last_event_timestamp": -1}},  # Sort walkthroughs by most recent activity
            {"$skip": skip},
            {"$limit": page_size},
            {
                "$project": {
                    "process_walkthrough_id": "$_id",
                    "process_class": 1,
                    "process_id": 1,
                    "events": 1,
                    "first_event_timestamp": 1,
                    "last_event_timestamp": 1,
                    "event_count": 1,
                    "_id": 0,
                }
            },
        ]

        walkthrough_data = list(cls.objects.aggregate(pipeline))

        return total_count, walkthrough_data
