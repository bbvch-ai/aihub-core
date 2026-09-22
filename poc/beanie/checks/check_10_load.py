"""Check 10 — the load measurement that decides the ADR.

Beanie is NOT faster (check 08: 524 ms vs 447 ms for 200 sequential reads), so the
question is not throughput. It is:

    At what concurrency does `asyncio.to_thread` stop holding the line, and is that
    above or below our real load?

`to_thread` does not remove blocking, it relocates it into a bounded pool
(`min(32, cpu_count + 4)`; nothing in this repo configures it). Past the pool width,
work queues again and the 5 s `NCRequester` budget comes back into play.

WHAT THE SATURATOR MODELS -- and why the first version of this harness was wrong.
The first attempt saturated the loop with ~400 small writes/second, standing in for
EventPersister. It starved nothing and every variant passed, which is the
pre-registered "the harness is not reproducing the symptom" outcome. The source
comment at persisted_agent_event_entity.py:584 says what the real incident was:

    "It is not what took the event loop down, though -- that was a 123s cold read
     of 30 days off disk, which no pipeline shape avoids and only the threadpool
     hand-off contains."

So the starver is ONE SLOW READ, not many fast writes. The saturator here runs the
real spend-aggregation shape over a seeded corpus, back to back. It is a stand-in
for whichever unfixed blocking call site happens to be running -- not a claim about
EventPersister specifically.

FOUR variants, because the shipped fix is partial and the comparison must be honest:

  raw             responder blocks + saturator blocks   -- BEFORE the interim fix
  to_thread_part  responder off-loop, saturator blocks  -- TODAY: the fix touched two
                                                           call sites; ~137 others still block
  to_thread_full  both off-loop                         -- the "keep patching" end state
  beanie          both natively async                   -- the migration end state

`to_thread_full` vs `beanie` is the decision. `raw` is the CONTROL: if it does not
show timeouts, nothing else here can be believed.

Client requests run on their own loop in a separate thread with their own NATS
connection, so the caller is never starved by the server's loop -- as an agent in
its own process would not be.
"""

import argparse
import asyncio
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any

from beanie import Document, init_beanie
from mongoengine import DictField, Document as MEDocument, StringField, connect, disconnect
from nats.aio.client import Client as NATS
from pymongo import AsyncMongoClient, MongoClient

from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.infrastructure.nats.nats_settings import NatsSettings
from swiss_ai_hub.core.requester.nc_requester import NCRequester
from swiss_ai_hub.core.responder.nc_responder import NCResponder
from swiss_ai_hub.core.rpc.models import FetchAgentConfigRequest, FetchAgentConfigResponse

SPIKE_DB_NAME = "aihub_beanie_spike"
CONFIG_COLLECTION = "load_configs"
EVENT_COLLECTION = "load_events"
SUBJECT = "aihub.rpc.load.agent.RAGAgent.default"

CONNECTION_STRING = MongoSettings().CONNECTION_STRING.get_secret_value()
VARIANTS = ["raw", "to_thread_part", "to_thread_full", "beanie"]

# The spend-aggregation shape from persisted_agent_event_entity.py:578.
SPEND_PIPELINE: list[dict[str, Any]] = [
    {"$match": {"event_parents": "LLMCostEvent"}},
    {
        "$project": {
            "_id": 0,
            "event_id": 1,
            "user_id": "$event_data.user_id",
            "tenant_id": "$event_data.tenant_id",
            "prompt_tokens_costs": "$event_data.prompt_tokens_costs",
        }
    },
    {
        "$group": {
            "_id": "$event_id",
            "user_id": {"$first": "$user_id"},
            "tenant_id": {"$first": "$tenant_id"},
            "prompt_tokens_costs": {"$first": "$prompt_tokens_costs"},
        }
    },
    {
        "$group": {
            "_id": {"user_id": "$user_id", "tenant_id": "$tenant_id"},
            "calls": {"$sum": 1},
            "prompt_tokens_costs": {"$sum": {"$ifNull": ["$prompt_tokens_costs", 0]}},
        }
    },
    {"$sort": {"_id": 1}},
]


class MEConfig(MEDocument):
    meta = {"collection": CONFIG_COLLECTION, "strict": False}
    agent_class = StringField()
    agent_id = StringField()
    config_data = DictField()


class BeanieConfig(Document):
    agent_class: str
    agent_id: str
    config_data: dict[str, Any]

    class Settings:
        name = CONFIG_COLLECTION


class BeanieEvent(Document):
    event_id: str
    event_parents: list[str]
    event_data: dict[str, Any]

    class Settings:
        name = EVENT_COLLECTION


class Server:
    """Responder + saturator on ONE event loop, as the API runs them."""

    def __init__(self, variant: str, pool_width: int | None, gap: float) -> None:
        self.variant = variant
        self.pool_width = pool_width
        self.gap = gap
        self.saturator_passes = 0
        self._stop = False
        self._nc: NATS | None = None
        self._responder: NCResponder | None = None
        self._async_client: AsyncMongoClient | None = None
        self._sync_client: MongoClient | None = None

    async def handler(self, request: FetchAgentConfigRequest, subject: str) -> FetchAgentConfigResponse:
        if self.variant == "raw":
            entity = MEConfig.objects(agent_class="RAGAgent", agent_id="default").first()
            config = entity.config_data if entity else {}
        elif self.variant in ("to_thread_part", "to_thread_full"):
            entity = await asyncio.to_thread(
                lambda: MEConfig.objects(agent_class="RAGAgent", agent_id="default").first()
            )
            config = entity.config_data if entity else {}
        else:
            entity = await BeanieConfig.find_one(BeanieConfig.agent_id == "default")
            config = entity.config_data if entity else {}
        return FetchAgentConfigResponse(
            agent_class=request.agent_class, agent_id=request.agent_id, config=config, found=True
        )

    def _blocking_aggregate(self) -> int:
        assert self._sync_client is not None
        return len(list(self._sync_client[SPIKE_DB_NAME][EVENT_COLLECTION].aggregate(SPEND_PIPELINE, allowDiskUse=True)))

    async def _saturate(self) -> None:
        """A stand-in for whichever unfixed blocking call site is running: one slow read, repeatedly.

        `gap` is the idle time between passes and is the contention dial. gap=0 is a 100%
        blocking duty cycle, which no real API sustains; larger gaps model a loop that has
        room to breathe between expensive calls.
        """
        while not self._stop:
            if self.variant in ("raw", "to_thread_part"):
                self._blocking_aggregate()
            elif self.variant == "to_thread_full":
                await asyncio.to_thread(self._blocking_aggregate)
            else:
                await BeanieEvent.aggregate(SPEND_PIPELINE, allowDiskUse=True).to_list()
            self.saturator_passes += 1
            await asyncio.sleep(self.gap)

    async def run(self, ready: threading.Event, stop: threading.Event) -> None:
        if self.pool_width is not None:
            asyncio.get_running_loop().set_default_executor(ThreadPoolExecutor(max_workers=self.pool_width))

        self._sync_client = MongoClient(CONNECTION_STRING)
        if self.variant == "beanie":
            self._async_client = AsyncMongoClient(CONNECTION_STRING)
            await init_beanie(
                database=self._async_client[SPIKE_DB_NAME], document_models=[BeanieConfig, BeanieEvent]
            )
        else:
            disconnect()
            connect(db=SPIKE_DB_NAME, host=CONNECTION_STRING, alias="default")

        self._nc = NATS()
        await self._nc.connect(servers=[NatsSettings().ENDPOINT], token=NatsSettings().TOKEN.get_secret_value())
        self._responder = NCResponder(
            name="LoadConfig",
            nc=self._nc,
            subject=SUBJECT,
            request_cls=FetchAgentConfigRequest,
            handler=self.handler,
        )
        await self._responder.start()

        saturator = asyncio.create_task(self._saturate())
        ready.set()
        while not stop.is_set():
            await asyncio.sleep(0.02)

        self._stop = True
        await asyncio.gather(saturator, return_exceptions=True)
        await self._responder.stop()
        await self._nc.close()
        if self._async_client:
            await self._async_client.close()
        self._sync_client.close()
        if self.variant != "beanie":
            disconnect()


async def drive(concurrency: int) -> tuple[list[float], int, int]:
    """One burst of concurrent config RPCs through the real NCRequester and its 5 s budget."""
    nc = NATS()
    await nc.connect(servers=[NatsSettings().ENDPOINT], token=NatsSettings().TOKEN.get_secret_value())
    requester: NCRequester = NCRequester(
        name="LoadConfig", nc=nc, response_cls=FetchAgentConfigResponse, default_timeout_ms=5000
    )

    latencies: list[float] = []
    timeouts = 0
    errors = 0

    async def one() -> None:
        nonlocal timeouts, errors
        started = time.perf_counter()
        try:
            await requester.request(
                FetchAgentConfigRequest(agent_class="RAGAgent", agent_id="default"), subject=SUBJECT
            )
            latencies.append(time.perf_counter() - started)
        except TimeoutError:
            timeouts += 1
        except Exception:
            errors += 1

    await asyncio.gather(*[one() for _ in range(concurrency)])
    await nc.close()
    return latencies, timeouts, errors


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    return ordered[min(int(fraction * len(ordered)), len(ordered) - 1)]


def run_scenario(variant: str, concurrency: int, pool_width: int | None, gap: float) -> dict[str, Any]:
    server = Server(variant, pool_width, gap)
    ready, stop = threading.Event(), threading.Event()

    thread = threading.Thread(target=lambda: asyncio.run(server.run(ready, stop)), daemon=True)
    thread.start()
    ready.wait(timeout=60)
    time.sleep(1.5)  # let the saturator reach steady state

    latencies, timeouts, errors = asyncio.run(drive(concurrency))

    stop.set()
    thread.join(timeout=60)

    return {
        "ok": len(latencies),
        "timeouts": timeouts,
        "errors": errors,
        "p50": percentile(latencies, 0.50),
        "p95": percentile(latencies, 0.95),
        "p99": percentile(latencies, 0.99),
        "passes": server.saturator_passes,
    }


def seed(event_count: int) -> float:
    """Seed the corpus and report how long one aggregation pass over it takes."""
    client: MongoClient = MongoClient(CONNECTION_STRING)
    configs = client[SPIKE_DB_NAME][CONFIG_COLLECTION]
    events = client[SPIKE_DB_NAME][EVENT_COLLECTION]

    configs.delete_many({})
    configs.insert_one({"agent_class": "RAGAgent", "agent_id": "default", "config_data": {"temperature": 0.7}})

    if events.count_documents({}) != event_count:
        events.drop()
        stamp = int(datetime.now(UTC).timestamp() * 1e9)
        batch = [
            {
                "event_id": f"evt-{index}",
                "event_parents": ["LLMCostEvent", "CostEvent"],
                "event_data": {
                    "created_at": stamp,
                    "user_id": f"user-{index % 50}",
                    "tenant_id": f"tenant-{index % 5}",
                    "prompt_tokens_costs": 1.0,
                    "completion_tokens_costs": 2.0,
                    "payload": "x" * 400,
                },
            }
            for index in range(event_count)
        ]
        for offset in range(0, len(batch), 20_000):  # FerretDB caps a write batch at 25000
            events.insert_many(batch[offset : offset + 20_000])

    started = time.perf_counter()
    list(events.aggregate(SPEND_PIPELINE, allowDiskUse=True))
    duration = time.perf_counter() - started
    client.close()
    return duration


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--concurrency", type=int, nargs="+", default=[1, 5, 10, 25, 50])
    parser.add_argument("--pool", type=int, default=None, help="pin the default executor width")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--events", type=int, default=50_000)
    parser.add_argument("--variants", nargs="+", default=VARIANTS)
    parser.add_argument(
        "--gap",
        type=float,
        nargs="+",
        default=[0.0],
        help="idle seconds between saturator passes; the loop-contention dial (0 = 100%% duty cycle)",
    )
    args = parser.parse_args()

    blocking_duration = seed(args.events)
    print(
        f"corpus={args.events} docs | one saturator pass blocks for {blocking_duration * 1000:.0f} ms | "
        f"pool={args.pool or 'default'} | runs={args.runs} | RPC budget=5000 ms"
    )
    header = (
        f"{'variant':<16}{'gap s':>7}{'conc':>5}{'ok':>6}{'t/out':>7}{'err':>5}"
        f"{'p50 ms':>9}{'p95 ms':>9}{'p99 ms':>9}{'passes':>8}"
    )
    print(header)
    print("-" * len(header))

    for gap in args.gap:
        for variant in args.variants:
            for concurrency in args.concurrency:
                results = [run_scenario(variant, concurrency, args.pool, gap) for _ in range(args.runs)]

                def median(key: str, rows: list[dict[str, Any]] = results) -> float:
                    return statistics.median(row[key] for row in rows)

                print(
                    f"{variant:<16}{gap:>7.2f}{concurrency:>5}{median('ok'):>6.0f}{median('timeouts'):>7.0f}"
                    f"{median('errors'):>5.0f}{median('p50') * 1000:>9.0f}{median('p95') * 1000:>9.0f}"
                    f"{median('p99') * 1000:>9.0f}{median('passes'):>8.0f}"
                )
        print("-" * len(header))


if __name__ == "__main__":
    main()
