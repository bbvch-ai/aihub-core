import asyncio
import gc
import random
import time
from typing import Dict

from bson import ObjectId
from tabulate import tabulate
from tqdm import tqdm

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.RedisConfig import RedisConfig
from nats.aio.client import Client as NATS

from aihub_agent.runners.MultiprocessAgentRunner import MultiprocessAgentRunner
from aihub_lib.nats.NatsConfig import NatsConfig
from aihub_lib.nats.events import BaseEvent, StopEvent, StartEvent
from aihub_lib.nats.publishers.JSPublisher import JSPublisher
from aihub_lib.nats.subscribers.NCSubscriber import NCSubscriber
from aihub_lib.nats.topic_managers.agents.AgentInstanceTopicManager import AgentInstanceTopicManager
from aihub_lib.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager
from aihub_lib.nats.topics import Topic
from playground.performance.PerformanceTestingAgent.PerformanceTestingAgent import PerformanceTestingAgent
from playground.performance.PerformanceTestingAgent.PerformanceTestingAgentConfig import PerformanceTestingAgentConfig
from playground.performance.PerformanceTestingAgent.events.ParallelEvent import ParallelEvent

async def run_test(process_count: int, n_events: int, payload_kb: int) -> Dict[str, any]:
    """
    Run a performance test with the specified parameters.

    Returns a dictionary with test results, including index distribution analysis.
    """
    agent_id = f"performance_testing_agent_{random.randint(0, 1000)}"
    agent_type = PerformanceTestingAgent
    agent_config = PerformanceTestingAgentConfig(
        agent_id=agent_id,
        name=LocaleString(en="Performance Testing Agent"),
        description=LocaleString(en=""),
        system_prompt=LocaleString(en=""),
        number_of_events=n_events,
        payload_kb=payload_kb,
    )

    # Variables to track resources that need cleanup
    runner = None
    nc = None
    event_subscriber = None
    timed_out = False
    duration = 0
    parallel_events = []

    try:
        # Start the multiprocess runner
        runner = MultiprocessAgentRunner(
            servers=[NatsConfig().NATS_ENDPOINT],
            redis_url=RedisConfig().REDIS_URL,
            agent_type=agent_type,
            agent_config=agent_config,
            process_count=process_count,
        )
        runner.start()

        # Allow time for processes to initialize
        await asyncio.sleep(2)

        # Set up NATS connection for test coordination
        nc = NATS()
        await nc.connect(servers=[NatsConfig().NATS_ENDPOINT])
        js = nc.jetstream()

        # Generate unique IDs for this test run
        thread_id = str(ObjectId())
        display_id = str(ObjectId())
        run_id = str(ObjectId())

        # Setup event tracking
        _stop_event = asyncio.Event()

        # Create topic managers
        topic_manager = AgentInstanceTopicManager(agent_type.__name__, agent_config.agent_id)
        thread_topic_manager = AgentThreadTopicManager.from_agent_instance_topic_manager(
            topic_manager,
            thread_id=thread_id,
            display_id=display_id,
            run_id=run_id,
        )

        # Define event observer
        async def observe_event(event: BaseEvent, topic: Topic):
            if isinstance(event, ParallelEvent):
                parallel_events.append(event)

            if isinstance(event, StopEvent):
                _stop_event.set()

        # Subscribe to events
        event_subscriber = NCSubscriber.for_all_thread_events(
            nc=nc,
            topic_manager=thread_topic_manager,
            handler=observe_event,
        )
        await event_subscriber.start()

        # Create and publish the start event
        start_event = StartEvent()
        publisher = JSPublisher(js)

        subject = thread_topic_manager.get_subject_for_control_event_in_thread(
            start_event.__class__.__name__, event_id=start_event.event_id
        )

        # Start timing and send the event
        start_time = time.time()
        await publisher.publish_event(start_event, subject)

        # Wait for completion
        timeout_duration = 60*5  # 5 minutes
        try:
            await asyncio.wait_for(_stop_event.wait(), timeout=timeout_duration)
        except asyncio.TimeoutError:
            timed_out = True

        # Record timing
        stop_time = time.time()
        duration = stop_time - start_time

    except Exception as e:
        print(f"Error during test execution: {e}")
        # Return minimal results in case of error
        return {
            "processes": process_count,
            "events_requested": n_events,
            "payload_kb": payload_kb,
            "events_processed": 0,
            "unique_events": 0,
            "duration": 0,
            "throughput": 0,
            "throughput_kb": 0,
            "completion": 0,
            "timed_out": True,
            "error": str(e),
            "missing_indices": list(range(n_events)),
            "duplicate_indices": 0,
            "index_distribution": {"min_index": None, "max_index": None, "complete": False},
            "success": False,
        }
    finally:
        # Ensure all resources are properly cleaned up
        try:
            if event_subscriber:
                await event_subscriber.stop()

            if nc:
                try:
                    await nc.drain()
                    await nc.close()
                except Exception as e:
                    print(f"Error closing NATS connection: {e}")

            if runner:
                runner.stop()
                # Wait for processes to terminate
                await asyncio.sleep(1)

            # Force garbage collection to release any lingering resources
            gc.collect()

        except Exception as cleanup_error:
            print(f"Error during cleanup: {cleanup_error}")

    # Analyze the distribution of event indices
    event_indices = [event.index for event in parallel_events]
    unique_indices = set(event_indices)

    # Find missing and duplicate indices
    expected_indices = set(range(n_events))
    missing_indices = expected_indices - unique_indices

    # Count occurrences of each index
    index_counts = {}
    for idx in event_indices:
        index_counts[idx] = index_counts.get(idx, 0) + 1

    duplicate_indices = {idx: count for idx, count in index_counts.items() if count > 1}

    # Return results as a dictionary
    events_processed = len(parallel_events)
    unique_events = len(unique_indices)

    # Calculate throughput in kb/s
    throughput_kb = (events_processed * payload_kb) / duration if duration > 0 else 0

    # Determine if the run was successful (100% coverage, no duplicates, no missing)
    success = True
    error = ""

    if len(missing_indices) != 0:
        success = False
        error += f"Missing indices: {missing_indices}. "

    if len(duplicate_indices) != 0:
        success = False
        error += f"Duplicate indices: {duplicate_indices}. "

    if unique_events != n_events:
        success = False
        error += f"Unique events: {unique_events} != {n_events}. "

    return {
        "processes": process_count,
        "events_requested": n_events,
        "payload_kb": payload_kb,
        "events_processed": events_processed,
        "unique_events": unique_events,
        "duration": duration,
        "throughput": events_processed / duration if duration > 0 else 0,
        "throughput_kb": throughput_kb,
        "completion": unique_events / n_events * 100 if n_events > 0 else 0,
        "timed_out": timed_out,
        "missing_indices": sorted(missing_indices)
        if len(missing_indices) <= 10
        else f"{len(missing_indices)} indices missing",
        "duplicate_indices": len(duplicate_indices),
        "index_distribution": {
            "min_index": min(event_indices) if event_indices else None,
            "max_index": max(event_indices) if event_indices else None,
            "complete": len(missing_indices) == 0,
        },
        "error": error,
        "success": success,
    }


async def main():
    # Define parameter ranges for test generation
    process_counts = [1]  # Number of processes to run
    event_counts = [100, 1_000, 10_000]  # Number of events per test
    payload_sizes = [1, 10, 100]  # Payload size in KB

    # Generate all combinations of test configurations
    configurations = []
    for process_count in process_counts:
        for event_count in event_counts:
            for payload_size in payload_sizes:
                configurations.append((process_count, event_count, payload_size))

    results = []

    for i, config in tqdm(enumerate(configurations), total=len(configurations), desc="Running tests"):
        processes, events, payload_size = config

        try:
            # Run the test
            result = await run_test(processes, events, payload_size)
            results.append(result)

        except Exception as e:
            print(f"Test failed with error: {e}")
            # Add a placeholder result for the failed test
            results.append(
                {
                    "processes": processes,
                    "events_requested": events,
                    "payload_kb": payload_size,
                    "events_processed": 0,
                    "unique_events": 0,
                    "duration": 0,
                    "throughput": 0,
                    "throughput_kb": 0,
                    "completion": 0,
                    "timed_out": True,
                    "error": str(e),
                    "missing_indices": [],
                    "duplicate_indices": 0,
                    "index_distribution": {"min_index": None, "max_index": None, "complete": False},
                    "success": False,
                }
            )

    await asyncio.sleep(3)
    gc.collect()

    # Format and display the results table with simplified metrics
    table_data = []
    headers = [
        "Processes",
        "Events",
        "Payload (KB)",
        "Duration (s)",
        "Throughput (evt/s)",
        "Throughput (KB/s)",
        "Success",
        "Error",
    ]

    for r in results:
        row_data = [
            r["processes"],
            r["events_requested"],
            r["payload_kb"],
            f"{r['duration']:.2f}",
            f"{r['throughput']:.2f}",
            f"{r['throughput_kb']:.2f}",
            "✓" if r["success"] else "✗",
            r["error"] if "error" in r else "",
        ]
        table_data.append(row_data)

    print(tabulate(table_data, headers=headers, tablefmt="grid"))


if __name__ == "__main__":
    asyncio.run(main())
