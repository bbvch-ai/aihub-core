# ruff: noqa: E501
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio  # noqa: E402
import gc  # noqa: E402
import json  # noqa: E402
import random  # noqa: E402
import time  # noqa: E402
import uuid  # noqa: E402
from typing import Any  # noqa: E402

from bson import ObjectId  # noqa: E402
from nats.aio.client import Client as NATS  # noqa: E402
from nats.js.api import StreamConfig  # noqa: E402
from swiss_ai_hub.core.events import BaseEvent  # noqa: E402
from swiss_ai_hub.core.events.agent import StartEvent, StopEvent  # noqa: E402

# For NATS JS benchmarking
from swiss_ai_hub.core.i18n import LocaleString  # noqa: E402
from swiss_ai_hub.core.infrastructure import NatsSettings  # noqa: E402
from swiss_ai_hub.core.publishers import JSPublisher  # noqa: E402
from swiss_ai_hub.core.subscribers import AgentNCSubscriber  # noqa: E402
from swiss_ai_hub.core.topic_managers import AgentInstanceTopicManager, AgentThreadTopicManager  # noqa: E402
from swiss_ai_hub.core.topics import Topic  # noqa: E402
from tabulate import tabulate  # noqa: E402
from tqdm import tqdm  # noqa: E402

from playground.performance.performance_testing_agent.events.parallel_event import ParallelEvent  # noqa: E402
from playground.performance.performance_testing_agent.performance_testing_agent import (  # noqa: E402
    PerformanceTestingAgent,
)
from playground.performance.performance_testing_agent.performance_testing_agent_config import (  # noqa: E402
    PerformanceTestingAgentConfig,
)
from swiss_ai_hub.agent.runners.multiprocess_agent_runner import MultiprocessAgentRunner  # noqa: E402


# ====== NATS JetStream Benchmark ======
async def benchmark_jetstream(n_events: int, payload_kb: int) -> dict[str, Any]:
    """
    Benchmark NATS JetStream performance.
    """
    nc = await NatsSettings.create_client()
    js = nc.jetstream()

    # Create a random stream name
    stream_name = f"benchmark-{uuid.uuid4().hex[:8]}"
    subject = f"{stream_name}.events"

    # Create the stream
    stream_config = StreamConfig(name=stream_name, subjects=[subject])
    await js.add_stream(stream_config)

    # Create payload
    payload = ("a" * 1024 * payload_kb).encode()
    payload_size_bytes = len(payload)
    total_data_bytes = payload_size_bytes * n_events

    # Setup for receiving messages
    received_count = 0
    received_event = asyncio.Event()

    async def message_handler(msg):
        nonlocal received_count
        received_count += 1
        if received_count >= n_events:
            received_event.set()

    # Subscribe to the stream
    sub = await js.subscribe(subject, cb=message_handler)

    # Publish messages and time it
    start_time = time.time()

    for i in range(n_events):
        await js.publish(subject, payload)

    publish_time = time.time() - start_time

    # Wait for all messages to be received
    await asyncio.wait_for(received_event.wait(), timeout=30.0)

    end_time = time.time()
    total_time = end_time - start_time

    # Clean up
    await sub.unsubscribe()
    await js.purge_stream(stream_name)
    await js.delete_stream(stream_name)
    await nc.close()

    # Calculate metrics
    throughput_kb_per_second = (total_data_bytes / 1024) / total_time
    events_per_second = n_events / total_time
    publish_events_per_second = n_events / publish_time if publish_time > 0 else 0

    metrics = {
        "n_events": n_events,
        "payload_kb": payload_kb,
        "total_time_seconds": total_time,
        "publish_time_seconds": publish_time,
        "throughput_kb_per_second": throughput_kb_per_second,
        "events_per_second": events_per_second,
        "publish_events_per_second": publish_events_per_second,
        "total_data_mb": total_data_bytes / (1024 * 1024),
    }

    return metrics


# ====== System Benchmark ======
async def purge_jetstream(nc: NATS):
    """Purge all JetStream data between test runs."""
    js = nc.jetstream()

    try:
        # Get all streams
        streams = await js.streams_info()

        # Delete all streams
        for stream in streams:
            try:
                await js.delete_stream(stream.config.name)
            except Exception as e:
                print(f"Error deleting stream {stream.config.name}: {e}")

    except Exception as e:
        print(f"Error purging JetStream: {e}")


async def run_system_test(process_count: int, n_events: int, payload_kb: int) -> dict[str, any]:
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
            agent_type=agent_type,
            agent_config=agent_config,
            process_count=process_count,
        )
        runner.start()

        # Allow time for processes to initialize
        await asyncio.sleep(2)

        # Set up NATS connection for test coordination
        nc = await NatsSettings.create_client()
        js = nc.jetstream()

        # Generate unique IDs for this test run
        thread_id = str(ObjectId())
        display_id = str(ObjectId())
        run_id = str(ObjectId())

        # Setup event tracking
        _stop_signal = asyncio.Event()

        # Create topic managers
        topic_manager = AgentInstanceTopicManager(agent_class=agent_type.__name__, agent_id=agent_config.agent_id)
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
                _stop_signal.set()

        # Subscribe to events
        event_subscriber = AgentNCSubscriber.for_all_thread_events(
            nc=nc, topic_manager=thread_topic_manager, handler=observe_event, subscriber_name="PerformanceTesting"
        )
        await event_subscriber.start()

        # Create and publish the start event
        start_event = StartEvent()
        publisher = JSPublisher("PerformanceTesting", js)

        subject = thread_topic_manager.get_subject_for_control_event_in_thread(
            start_event.event_name, event_id=start_event.event_id
        )

        await asyncio.sleep(1)

        # Start timing and send the event
        start_time = time.time()
        await publisher.publish_event(start_event, subject)

        # Wait for completion
        timeout_duration = 60 * 60  # 5 minutes
        try:
            await asyncio.wait_for(_stop_signal.wait(), timeout=timeout_duration)
            await asyncio.sleep(1)
        except TimeoutError:
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
                await purge_jetstream(nc)
                try:
                    await nc.close()
                except Exception as e:
                    print(f"Error closing NATS connection: {e}")

            if runner:
                runner.stop()
                # Wait for processes to terminate
                await asyncio.sleep(1)

            # Force garbage collection to release any lingering resources
            gc.collect()
            await asyncio.sleep(1)

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
        "missing_indices": (
            sorted(missing_indices) if len(missing_indices) <= 10 else f"{len(missing_indices)} indices missing"
        ),
        "duplicate_indices": len(duplicate_indices),
        "index_distribution": {
            "min_index": min(event_indices) if event_indices else None,
            "max_index": max(event_indices) if event_indices else None,
            "complete": len(missing_indices) == 0,
        },
        "error": error,
        "success": success,
    }


async def benchmark_theoretical_limits(config_list):
    """Run raw NATS benchmarks to establish theoretical limits."""
    theoretical_results = {}

    print("Benchmarking theoretical limits...")
    for config in tqdm(config_list, desc="Benchmarking limits"):
        n_events, payload_kb = config

        # Create a unique key for this configuration
        config_key = f"{n_events}_{payload_kb}"

        # Run NATS JetStream benchmark
        try:
            print(f"\nRunning NATS benchmark: {n_events} events, {payload_kb} KB")
            nats_results = await benchmark_jetstream(n_events, payload_kb)
            print(
                f"NATS throughput: {nats_results['events_per_second']:.2f} "
                f"evt/s, {nats_results['throughput_kb_per_second']:.2f} KB/s"
            )
        except Exception as e:
            print(f"NATS benchmark failed: {e}")
            nats_results = {"events_per_second": 0, "throughput_kb_per_second": 0}

        # Store both results for this configuration
        theoretical_results[config_key] = {
            "nats": nats_results,
            "n_events": n_events,
            "payload_kb": payload_kb,
            # Calculate the bottleneck (minimum of the two)
            "min_events_per_second": nats_results["events_per_second"],
            "min_throughput_kb_per_second": nats_results["throughput_kb_per_second"],
        }

    return theoretical_results


async def main():
    # Define parameter ranges for test generation
    process_counts = [1, 2, 3, 4, 5, 10]  # Number of processes to run
    event_counts = [100, 1000, 10_000]  # Number of events per test
    payload_sizes = [1, 10, 100]  # Payload size in KB

    # Create a subset of configurations for theoretical limit testing
    # We'll run these tests for both NATS to establish baselines
    limit_configs = [(n, p) for n in event_counts for p in payload_sizes]

    # Get theoretical limits first
    print("Benchmarking theoretical limits of NATS...")
    theoretical_limits = await benchmark_theoretical_limits(limit_configs)

    # Save theoretical limits to a separate file
    with open("results/theoretical_limits.json", "w") as f:
        json.dump(theoretical_limits, f, indent=2)
    print("Theoretical limits saved to theoretical_limits.json")

    # Generate all combinations of test configurations for system tests
    configurations = []
    for process_count in process_counts:
        for event_count in event_counts:
            for payload_size in payload_sizes:
                configurations.append((process_count, event_count, payload_size))

    results = []
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    print("Running system tests...")
    for i, config in tqdm(enumerate(configurations), total=len(configurations), desc="Running tests"):
        processes, events, payload_size = config

        try:
            # Run the test
            result = await run_system_test(processes, events, payload_size)

            # Add theoretical limit comparisons
            config_key = f"{events}_{payload_size}"
            if config_key in theoretical_limits:
                limits = theoretical_limits[config_key]

                # Add the raw limit values
                result["nats_events_per_second"] = limits["nats"]["events_per_second"]
                result["nats_throughput_kb"] = limits["nats"]["throughput_kb_per_second"]

                # Add the bottleneck limits (minimum of NATS)
                result["min_events_per_second"] = limits["min_events_per_second"]
                result["min_throughput_kb"] = limits["min_throughput_kb_per_second"]

                # Calculate percentages of theoretical maximum
                if limits["min_events_per_second"] > 0:
                    result["percent_of_max_events"] = (result["throughput"] / limits["min_events_per_second"]) * 100
                else:
                    result["percent_of_max_events"] = 0

                if limits["min_throughput_kb_per_second"] > 0:
                    result["percent_of_max_throughput"] = (
                        result["throughput_kb"] / limits["min_throughput_kb_per_second"]
                    ) * 100
                else:
                    result["percent_of_max_throughput"] = 0

            results.append(result)

            # Save incremental results after each test to prevent data loss
            with open(f"results/performance_results_{timestamp}_partial.json", "w") as f:
                json.dump(results, f, indent=2)

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
                    # Add default theoretical comparison fields
                    "nats_events_per_second": 0,
                    "nats_throughput_kb": 0,
                    "min_events_per_second": 0,
                    "min_throughput_kb": 0,
                    "percent_of_max_events": 0,
                    "percent_of_max_throughput": 0,
                }
            )

        await asyncio.sleep(1)
        gc.collect()

    # Save final results to JSON file
    with open(f"performance_results_{timestamp}.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to performance_results_{timestamp}.json")

    # Format and display the results table with theoretical limit comparisons
    table_data = []
    headers = [
        "Processes",
        "Events",
        "Payload (KB)",
        "Duration (s)",
        "Throughput (evt/s)",
        "NATS Max (evt/s)",
        "% of Max (evt/s)",
        "Throughput (KB/s)",
        "NATS Max (KB/s)",
        "% of Max (KB/s)",
        "Success",
        "Error",
    ]

    for r in results:
        if r["success"]:
            row_data = [
                r["processes"],
                r["events_requested"],
                r["payload_kb"],
                f"{r['duration']:.2f}",
                f"{r['throughput']:.2f}",
                f"{r.get('nats_events_per_second', 0):.2f}",
                f"{r.get('percent_of_max_events', 0):.2f}%",
                f"{r['throughput_kb']:.2f}",
                f"{r.get('nats_throughput_kb', 0):.2f}",
                f"{r.get('percent_of_max_throughput', 0):.2f}%",
                "✓",
                "",
            ]
            table_data.append(row_data)
        else:
            row_data = [
                r["processes"],
                r["events_requested"],
                r["payload_kb"],
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "✗",
                r["error"],
            ]
            table_data.append(row_data)

    # Sort table by process count, event count, then payload size
    table_data.sort(key=lambda x: (x[0], x[1], x[2]))

    print("\nPerformance Results with Theoretical Limits")
    print("===========================================")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

    # Print summary of theoretical limits
    print("\nTheoretical Limit Summary")
    print("========================")
    limit_table = []
    limit_headers = [
        "Events",
        "Payload (KB)",
        "NATS (evt/s)",
        "Bottleneck (evt/s)",
        "NATS (KB/s)",
        "Bottleneck (KB/s)",
    ]

    for n_events in event_counts:
        for payload_kb in payload_sizes:
            config_key = f"{n_events}_{payload_kb}"
            if config_key in theoretical_limits:
                limits = theoretical_limits[config_key]
                limit_row = [
                    n_events,
                    payload_kb,
                    f"{limits['nats']['events_per_second']:.2f}",
                    f"{limits['min_events_per_second']:.2f}",
                    f"{limits['nats']['throughput_kb_per_second']:.2f}",
                    f"{limits['min_throughput_kb_per_second']:.2f}",
                ]
                limit_table.append(limit_row)

    limit_table.sort(key=lambda x: (x[0], x[1]))
    print(tabulate(limit_table, headers=limit_headers, tablefmt="grid"))

    """
    Date: 07.03.2025
    Performance Results with Theoretical Limits
    ===========================================
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |   Processes |   Events |   Payload (KB) | Duration (s)   | Throughput (evt/s)   | NATS Max (evt/s)   | % of Max (evt/s)   | Throughput (KB/s)   | NATS Max (KB/s)   | % of Max (KB/s)   | Success   |
    +=============+==========+================+================+======================+====================+====================+=====================+===================+===================+===========+
    |           1 |      100 |              1 | 1.06           | 94.36                | 6376.36            | 1.48%              | 94.36               | 6376.36           | 1.48%             | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           1 |      100 |             10 | 1.07           | 93.42                | 5968.08            | 1.57%              | 934.20              | 59680.76          | 1.57%             | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           1 |      100 |            100 | 1.24           | 80.34                | 2396.80            | 3.35%              | 8034.46             | 239679.99         | 3.35%             | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           1 |     1000 |              1 | 1.67           | 599.77               | 7741.11            | 7.75%              | 599.77              | 7741.11           | 7.75%             | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           1 |     1000 |             10 | 1.82           | 550.29               | 6195.69            | 8.88%              | 5502.94             | 61956.92          | 8.88%             | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           1 |     1000 |            100 | 3.36           | 297.70               | 2141.58            | 13.90%             | 29770.34            | 214157.69         | 13.90%            | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           1 |    10000 |              1 | 26.97          | 370.78               | 7048.99            | 5.26%              | 370.78              | 7048.99           | 5.26%             | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           1 |    10000 |             10 | 29.99          | 333.46               | 6941.06            | 4.80%              | 3334.60             | 69410.55          | 4.80%             | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           1 |    10000 |            100 | 46.11          | 216.89               | 2982.53            | 7.27%              | 21689.11            | 298252.86         | 7.27%             | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           1 |   100000 |              1 | 2454.96        | 40.73                | 6516.05            | N/A                | 40.733              | 6516.05           | N/A               | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           1 |   100000 |             10 | 2414.96        | 41.40                | 6516.05            | N/A                | 414.08              | 6516.05           | N/A               | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           1 |   100000 |            100 | N/A            | N/A                  | N/A                | N/A                | N/A                 | N/A               | N/A               | ✗         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           2 |      100 |              1 | 1.05           | 95.32                | 6376.36            | 1.49%              | 95.32               | 6376.36           | 1.49%             | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           2 |      100 |             10 | 1.06           | 94.23                | 5968.08            | 1.58%              | 942.34              | 59680.76          | 1.58%             | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           2 |      100 |            100 | 1.21           | 82.34                | 2396.80            | 3.44%              | 8233.54             | 239679.99         | 3.44%             | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           2 |     1000 |              1 | 1.47           | 678.72               | 7741.11            | 8.77%              | 678.72              | 7741.11           | 8.77%             | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           2 |     1000 |             10 | 1.62           | 617.22               | 6195.69            | 9.96%              | 6172.24             | 61956.92          | 9.96%             | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           2 |     1000 |            100 | 3.12           | 320.54               | 2141.58            | 14.97%             | 32053.80            | 214157.69         | 14.97%            | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           2 |    10000 |              1 | 15.42          | 648.67               | 7048.99            | 9.20%              | 648.67              | 7048.99           | 9.20%             | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           2 |    10000 |             10 | 17.04          | 587.02               | 6941.06            | 8.46%              | 5870.23             | 69410.55          | 8.46%             | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           2 |    10000 |            100 | 31.73          | 315.17               | 2982.53            | 10.57%             | 31516.86            | 298252.86         | 10.57%            | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           2 |   100000 |              1 | 1974.24        | 50.65                | 6516.05            | N/A                | 50.65               | 6516.05           | N/A               | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           2 |   100000 |             10 | N/A            | N/A                  | N/A                | N/A                | N/A                 | N/A               | N/A               | ✗         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           2 |   100000 |            100 | N/A            | N/A                  | N/A                | N/A                | N/A                 | N/A               | N/A               | ✗         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           3 |      100 |              1 | 1.05           | 95.66                | 6376.36            | 1.50%              | 95.66               | 6376.36           | 1.50%             | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           3 |      100 |             10 | 1.07           | 93.71                | 5968.08            | 1.57%              | 937.09              | 59680.76          | 1.57%             | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           3 |      100 |            100 | 1.20           | 83.32                | 2396.80            | 3.48%              | 8332.32             | 239679.99         | 3.48%             | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           3 |     1000 |              1 | 1.46           | 686.19               | 7741.11            | 8.86%              | 686.19              | 7741.11           | 8.86%             | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           3 |     1000 |             10 | 1.60           | 624.08               | 6195.69            | 10.07%             | 6240.84             | 61956.92          | 10.07%            | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           3 |     1000 |            100 | 3.12           | 320.38               | 2141.58            | 14.96%             | 32037.62            | 214157.69         | 14.96%            | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           3 |    10000 |              1 | 12.27          | 814.86               | 7048.99            | 11.56%             | 814.86              | 7048.99           | 11.56%            | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           3 |    10000 |             10 | 14.31          | 698.88               | 6941.06            | 10.07%             | 6988.78             | 69410.55          | 10.07%            | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           3 |    10000 |            100 | 29.06          | 344.06               | 2982.53            | 11.54%             | 34406.30            | 298252.86         | 11.54%            | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           3 |   100000 |              1 | N/A            | N/A                  | N/A                | N/A                | N/A                 | N/A               | N/A               | ✗         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           3 |   100000 |             10 | N/A            | N/A                  | N/A                | N/A                | N/A                 | N/A               | N/A               | ✗         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           3 |   100000 |            100 | N/A            | N/A                  | N/A                | N/A                | N/A                 | N/A               | N/A               | ✗         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           4 |      100 |              1 | 1.05           | 94.80                | 6376.36            | 1.49%              | 94.80               | 6376.36           | 1.49%             | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           4 |      100 |             10 | 1.06           | 94.40                | 5968.08            | 1.58%              | 944.01              | 59680.76          | 1.58%             | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           4 |      100 |            100 | 1.20           | 83.09                | 2396.80            | 3.47%              | 8309.25             | 239679.99         | 3.47%             | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           4 |     1000 |              1 | 1.49           | 670.30               | 7741.11            | 8.66%              | 670.30              | 7741.11           | 8.66%             | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           4 |     1000 |             10 | 1.61           | 622.70               | 6195.69            | 10.05%             | 6227.03             | 61956.92          | 10.05%            | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           4 |     1000 |            100 | 3.18           | 314.00               | 2141.58            | 14.66%             | 31400.24            | 214157.69         | 14.66%            | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           4 |    10000 |              1 | 11.32          | 883.69               | 7048.99            | 12.54%             | 883.69              | 7048.99           | 12.54%            | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           4 |    10000 |             10 | 12.91          | 774.61               | 6941.06            | 11.16%             | 7746.09             | 69410.55          | 11.16%            | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           4 |    10000 |            100 | 27.87          | 358.85               | 2982.53            | 12.03%             | 35885.11            | 298252.86         | 12.03%            | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           4 |   100000 |              1 | N/A            | N/A                  | N/A                | N/A                | N/A                 | N/A               | N/A               | ✗         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           4 |   100000 |             10 | N/A            | N/A                  | N/A                | N/A                | N/A                 | N/A               | N/A               | ✗         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           4 |   100000 |            100 | N/A            | N/A                  | N/A                | N/A                | N/A                 | N/A               | N/A               | ✗         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           5 |      100 |              1 | 1.06           | 94.76                | 6376.36            | 1.49%              | 94.76               | 6376.36           | 1.49%             | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           5 |      100 |             10 | 1.06           | 94.44                | 5968.08            | 1.58%              | 944.36              | 59680.76          | 1.58%             | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           5 |      100 |            100 | 1.22           | 81.93                | 2396.80            | 3.42%              | 8193.45             | 239679.99         | 3.42%             | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           5 |     1000 |              1 | 1.46           | 686.21               | 7741.11            | 8.86%              | 686.21              | 7741.11           | 8.86%             | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           5 |     1000 |             10 | 1.61           | 620.27               | 6195.69            | 10.01%             | 6202.67             | 61956.92          | 10.01%            | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           5 |     1000 |            100 | 3.21           | 311.05               | 2141.58            | 14.52%             | 31105.34            | 214157.69         | 14.52%            | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           5 |    10000 |              1 | 10.38          | 963.38               | 7048.99            | 13.67%             | 963.38              | 7048.99           | 13.67%            | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           5 |    10000 |             10 | 12.01          | 832.85               | 6941.06            | 12.00%             | 8328.51             | 69410.55          | 12.00%            | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           5 |    10000 |            100 | 27.65          | 361.69               | 2982.53            | 12.13%             | 36168.62            | 298252.86         | 12.13%            | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           5 |   100000 |              1 | N/A            | N/A                  | N/A                | N/A                | N/A                 | N/A               | N/A               | ✗         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           5 |   100000 |             10 | N/A            | N/A                  | N/A                | N/A                | N/A                 | N/A               | N/A               | ✗         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |           5 |   100000 |            100 | N/A            | N/A                  | N/A                | N/A                | N/A                 | N/A               | N/A               | ✗         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |          10 |      100 |              1 | 1.05           | 94.89                | 6376.36            | 1.49%              | 94.89               | 6376.36           | 1.49%             | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |          10 |      100 |             10 | 1.07           | 93.51                | 5968.08            | 1.57%              | 935.09              | 59680.76          | 1.57%             | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |          10 |      100 |            100 | 1.24           | 80.72                | 2396.80            | 3.37%              | 8071.91             | 239679.99         | 3.37%             | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |          10 |     1000 |              1 | 1.53           | 654.83               | 7741.11            | 8.46%              | 654.83              | 7741.11           | 8.46%             | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |          10 |     1000 |             10 | 1.71           | 586.32               | 6195.69            | 9.46%              | 5863.20             | 61956.92          | 9.46%             | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |          10 |     1000 |            100 | 3.35           | 298.94               | 2141.58            | 13.96%             | 29893.90            | 214157.69         | 13.96%            | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |          10 |    10000 |              1 | 9.14           | 1094.67              | 7048.99            | 15.53%             | 1094.67             | 7048.99           | 15.53%            | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |          10 |    10000 |             10 | 10.94          | 914.38               | 6941.06            | 13.17%             | 9143.78             | 69410.55          | 13.17%            | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |          10 |    10000 |            100 | 28.39          | 352.23               | 2982.53            | 11.81%             | 35223.24            | 298252.86         | 11.81%            | ✓         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |          10 |   100000 |              1 | N/A            | N/A                  | N/A                | N/A                | N/A                 | N/A               | N/A               | ✗         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |          10 |   100000 |             10 | N/A            | N/A                  | N/A                | N/A                | N/A                 | N/A               | N/A               | ✗         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+
    |          10 |   100000 |            100 | N/A            | N/A                  | N/A                | N/A                | N/A                 | N/A               | N/A               | ✗         |
    +-------------+----------+----------------+----------------+----------------------+--------------------+--------------------+---------------------+-------------------+-------------------+-----------+

    Theoretical Limit Summary
    ========================
    +----------+----------------+----------------+----------------------+---------------+---------------------+
    |   Events |   Payload (KB) |   NATS (evt/s) |   Bottleneck (evt/s) |   NATS (KB/s) |   Bottleneck (KB/s) |
    +==========+================+================+======================+===============+=====================+
    |      100 |              1 |        6376.36 |              6376.36 |       6376.36 |             6376.36 |
    +----------+----------------+----------------+----------------------+---------------+---------------------+
    |      100 |             10 |        5968.08 |              5968.08 |      59680.8  |            59680.8  |
    +----------+----------------+----------------+----------------------+---------------+---------------------+
    |      100 |            100 |        2396.8  |              2396.8  |     239680    |           239680    |
    +----------+----------------+----------------+----------------------+---------------+---------------------+
    |     1000 |              1 |        7741.11 |              7741.11 |       7741.11 |             7741.11 |
    +----------+----------------+----------------+----------------------+---------------+---------------------+
    |     1000 |             10 |        6195.69 |              6195.69 |      61956.9  |            61956.9  |
    +----------+----------------+----------------+----------------------+---------------+---------------------+
    |     1000 |            100 |        2141.58 |              2141.58 |     214158    |           214158    |
    +----------+----------------+----------------+----------------------+---------------+---------------------+
    |    10000 |              1 |        7048.99 |              7048.99 |       7048.99 |             7048.99 |
    +----------+----------------+----------------+----------------------+---------------+---------------------+
    |    10000 |             10 |        6941.06 |              6941.06 |      69410.6  |            69410.6  |
    +----------+----------------+----------------+----------------------+---------------+---------------------+
    |    10000 |            100 |        2982.53 |              2982.53 |     298253    |           298253    |
    +----------+----------------+----------------+----------------------+---------------+---------------------+
    |   100000 |              1 |        8122.19 |              8122.19 |       8122.19 |             8122.19 |
    +----------+----------------+----------------+----------------------+---------------+---------------------+
    |   100000 |             10 |        7074.76 |              7074.76 |      70747.6  |            70747.6  |
    +----------+----------------+----------------+----------------------+---------------+---------------------+
    |   100000 |            100 |        3082.06 |              3082.06 |     308206    |           308206    |
    +----------+----------------+----------------+----------------------+---------------+---------------------+
    """


if __name__ == "__main__":
    asyncio.run(main())
