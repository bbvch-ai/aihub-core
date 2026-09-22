"""Check 04 — are our real aggregation pipelines reachable and correct through Beanie?

The pipelines are raw stage dictionaries, so FerretDB either supports them or not,
independently of the ODM. What this tests is whether Beanie passes them through
unchanged -- options included -- and returns the same rows.

Two real pipelines are reproduced verbatim in shape:

1. LLM spend  -- persisted_agent_event_entity.py:578
   $match -> $project -> $group (dedup by event_id) -> $group (sum) -> $sort,
   executed with allowDiskUse=True.

2. Unanswered work requests -- persisted_process_event_entity.py:63
   a CORRELATED $lookup with `let` + `$expr` + `$in` over the same collection,
   then a $size: 0 filter. The hardest $lookup form there is.

Every result is compared against the identical pipeline run through a plain
synchronous PyMongo client, so a Beanie-side transformation cannot hide.
"""

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

from beanie import Document, init_beanie
from pymongo import AsyncMongoClient, MongoClient

from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings

SPIKE_DB_NAME = "aihub_beanie_spike"
SPEND_COLLECTION = "agent_events_spend"
PROCESS_COLLECTION = "process_events_lookup"

COST_FIELDS = ["prompt_tokens_costs", "completion_tokens_costs", "embedding_tokens_costs"]
GROUP_FIELDS = ["user_id", "tenant_id"]


class AgentEventDoc(Document):
    event_id: str
    event_parents: list[str]
    event_data: dict[str, Any]

    class Settings:
        name = SPEND_COLLECTION


class ProcessEventDoc(Document):
    process_class: str
    process_id: str
    process_walkthrough_id: str
    event_type: str
    event_name: str
    event_parents: list[str]
    event_data: dict[str, Any]

    class Settings:
        name = PROCESS_COLLECTION


def spend_pipeline(cutoff: datetime) -> list[dict[str, Any]]:
    """Verbatim shape of _aggregate_llm_spend (persisted_agent_event_entity.py:578)."""
    carried = [*GROUP_FIELDS, *COST_FIELDS]
    return [
        {
            "$match": {
                "event_parents": "LLMCostEvent",
                "event_data.created_at": {"$gte": int(cutoff.timestamp() * 1e9)},
            }
        },
        {"$project": {"_id": 0, "event_id": 1, **{f: f"$event_data.{f}" for f in carried}}},
        {"$group": {"_id": "$event_id", **{f: {"$first": f"${f}"} for f in carried}}},
        {
            "$group": {
                "_id": {f: f"${f}" for f in GROUP_FIELDS},
                "calls": {"$sum": 1},
                **{f: {"$sum": {"$ifNull": [f"${f}", 0]}} for f in COST_FIELDS},
            }
        },
        {"$sort": {"_id": 1}},
    ]


def lookup_pipeline() -> list[dict[str, Any]]:
    """Verbatim shape of get_unanswered_work_requests (persisted_process_event_entity.py:63)."""
    return [
        {
            "$match": {
                "process_class": "OnboardingProcess",
                "process_id": "hr",
                "process_walkthrough_id": "wt-1",
                "event_parents": "HumanWorkRequestEvent",
            }
        },
        {
            "$lookup": {
                "from": PROCESS_COLLECTION,
                "let": {
                    "form_event_names": "$event_data.forms._event_name",
                    "form_process_class": "$process_class",
                    "form_process_id": "$process_id",
                    "form_process_walkthrough_id": "$process_walkthrough_id",
                },
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {"$eq": ["$process_walkthrough_id", "$$form_process_walkthrough_id"]},
                                    {"$eq": ["$process_class", "$$form_process_class"]},
                                    {"$eq": ["$process_id", "$$form_process_id"]},
                                    {"$eq": ["$event_type", "work"]},
                                    {"$in": ["$event_name", "$$form_event_names"]},
                                ]
                            }
                        }
                    }
                ],
                "as": "corresponding_work_events",
            }
        },
        {"$match": {"corresponding_work_events": {"$size": 0}}},
    ]


async def seed_spend(now: datetime) -> None:
    stamp = int(now.timestamp() * 1e9)
    docs = []
    for user, tenant, prompt, completion in [
        ("alice", "t1", 1.0, 2.0),
        ("alice", "t1", 0.5, 0.5),
        ("bob", "t1", 3.0, 1.0),
        ("alice", "t2", 10.0, 0.0),
    ]:
        docs.append(
            AgentEventDoc(
                event_id=f"evt-{user}-{tenant}-{prompt}",
                event_parents=["LLMCostEvent", "CostEvent"],
                event_data={
                    "created_at": stamp,
                    "user_id": user,
                    "tenant_id": tenant,
                    "prompt_tokens_costs": prompt,
                    "completion_tokens_costs": completion,
                    # embedding_tokens_costs deliberately ABSENT on chat-only events --
                    # this is what the $ifNull in the real pipeline exists for.
                },
            )
        )
    # A redelivered duplicate: same event_id, must be collapsed by the dedup $group.
    docs.append(
        AgentEventDoc(
            event_id="evt-alice-t1-1.0",
            event_parents=["LLMCostEvent", "CostEvent"],
            event_data={
                "created_at": stamp,
                "user_id": "alice",
                "tenant_id": "t1",
                "prompt_tokens_costs": 1.0,
                "completion_tokens_costs": 2.0,
            },
        )
    )
    # Outside the time window -- must be excluded by the $match.
    docs.append(
        AgentEventDoc(
            event_id="evt-old",
            event_parents=["LLMCostEvent", "CostEvent"],
            event_data={
                "created_at": int((now - timedelta(days=400)).timestamp() * 1e9),
                "user_id": "alice",
                "tenant_id": "t1",
                "prompt_tokens_costs": 999.0,
                "completion_tokens_costs": 999.0,
            },
        )
    )
    await AgentEventDoc.insert_many(docs)


async def seed_process() -> None:
    await ProcessEventDoc.insert_many(
        [
            ProcessEventDoc(
                process_class="OnboardingProcess",
                process_id="hr",
                process_walkthrough_id="wt-1",
                event_type="work_request",
                event_name="AnsweredRequest",
                event_parents=["HumanWorkRequestEvent"],
                event_data={"forms": [{"_event_name": "FormA"}]},
            ),
            ProcessEventDoc(
                process_class="OnboardingProcess",
                process_id="hr",
                process_walkthrough_id="wt-1",
                event_type="work_request",
                event_name="UnansweredRequest",
                event_parents=["HumanWorkRequestEvent"],
                event_data={"forms": [{"_event_name": "FormB"}]},
            ),
            # The answer to FormA only. FormB stays unanswered.
            ProcessEventDoc(
                process_class="OnboardingProcess",
                process_id="hr",
                process_walkthrough_id="wt-1",
                event_type="work",
                event_name="FormA",
                event_parents=["HumanWorkEvent"],
                event_data={},
            ),
        ]
    )


async def main() -> None:
    connection_string = MongoSettings().CONNECTION_STRING.get_secret_value()
    client: AsyncMongoClient = AsyncMongoClient(connection_string)
    db = client[SPIKE_DB_NAME]

    print("== 0. clean slate ==")
    await db.drop_collection(SPEND_COLLECTION)
    await db.drop_collection(PROCESS_COLLECTION)
    await init_beanie(database=db, document_models=[AgentEventDoc, ProcessEventDoc])
    now = datetime.now(UTC)
    await seed_spend(now)
    await seed_process()
    print(f"seeded {await AgentEventDoc.count()} spend events, {await ProcessEventDoc.count()} process events")

    cutoff = now - timedelta(days=30)

    print("\n== 1. spend pipeline through Beanie, allowDiskUse=True ==")
    beanie_rows = await AgentEventDoc.aggregate(spend_pipeline(cutoff), allowDiskUse=True).to_list()
    for row in beanie_rows:
        print(f"  {row}")

    print("\n== 2. same pipeline, plain PyMongo, allowDiskUse=True ==")
    sync_client: MongoClient = MongoClient(connection_string)
    raw_rows = list(
        sync_client[SPIKE_DB_NAME][SPEND_COLLECTION].aggregate(spend_pipeline(cutoff), allowDiskUse=True)
    )
    for row in raw_rows:
        print(f"  {row}")

    print("\n== 3. do they agree? ==")
    print(f"  identical: {beanie_rows == raw_rows}")

    print("\n== 4. assertions on the spend result ==")
    by_key = {(r["_id"]["user_id"], r["_id"]["tenant_id"]): r for r in beanie_rows}
    alice_t1 = by_key[("alice", "t1")]
    print(f"  alice/t1 calls={alice_t1['calls']} (expect 2: duplicate event_id collapsed)")
    print(f"  alice/t1 prompt={alice_t1['prompt_tokens_costs']} (expect 1.5)")
    print(f"  alice/t1 embedding={alice_t1['embedding_tokens_costs']} (expect 0.0 via $ifNull, not null)")
    print(f"  400-day-old event excluded: {all(r['prompt_tokens_costs'] < 900 for r in beanie_rows)}")

    print("\n== 5. allowDiskUse rejected outright? ==")
    try:
        await AgentEventDoc.aggregate(spend_pipeline(cutoff), allowDiskUse=True).to_list()
        print("  accepted (no error)")
    except Exception as refused:  # noqa: BLE001 - the exception type is the finding
        print(f"  REJECTED: {type(refused).__name__}: {refused}")

    print("\n== 6. correlated $lookup through Beanie ==")
    lookup_beanie = await ProcessEventDoc.aggregate(lookup_pipeline()).to_list()
    for row in lookup_beanie:
        print(f"  unanswered: {row['event_name']} forms={row['event_data']['forms']}")

    print("\n== 7. same $lookup, plain PyMongo ==")
    lookup_raw = list(sync_client[SPIKE_DB_NAME][PROCESS_COLLECTION].aggregate(lookup_pipeline()))
    for row in lookup_raw:
        print(f"  unanswered: {row['event_name']}")
    print(f"  identical: {lookup_beanie == lookup_raw}")
    print(f"  expected exactly 1 unanswered (FormB): {len(lookup_beanie) == 1}")

    sync_client.close()
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
