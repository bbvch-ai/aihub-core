import argparse
import asyncio

import time
from nats.aio.client import Client as NATS
from nats.js import api
from nats.js.api import StreamConfig


async def run_performance_test(message_count, payload_size_kb, stream_name="perf-test-3", subject="perf.test.3"):
    # Connect to NATS server
    nc = NATS()
    await nc.connect("nats://localhost:4222")

    # Get JetStream context
    js = nc.jetstream()

    # Create or get the stream
    try:
        # Try to create the stream
        stream_config = StreamConfig(name=stream_name, subjects=[subject], storage=api.StorageType.FILE)
        await js.add_stream(config=stream_config)
    except Exception as e:
        # Stream might already exist
        print(f"Stream already exists or error: {e}")

    # Create payload based on size
    payload = 'a' * 1024 * payload_size_kb

    # Counter and event for tracking received messages
    received_count = 0
    all_received = asyncio.Event()

    # Subscribe to the subject
    async def message_handler(msg):
        nonlocal received_count
        received_count += 1
        if received_count >= message_count:
            all_received.set()

    sub = await js.subscribe(subject, cb=message_handler)

    # Give the subscription a moment to initialize
    await asyncio.sleep(0.1)

    # Start the timer
    start_time = time.time()

    # Publish messages
    for i in range(message_count):
        await js.publish(subject, payload.encode())

    # Wait for all messages to be received
    await asyncio.wait_for(all_received.wait(), timeout=60)

    # Stop the timer
    end_time = time.time()

    # Calculate results
    duration = end_time - start_time
    messages_per_second = message_count / duration
    throughput_mb_per_second = (message_count * len(payload)) / (1024 * 1024) / duration

    # Unsubscribe and disconnect
    await sub.unsubscribe()
    await nc.close()

    # Return results
    return {
        "message_count": message_count,
        "payload_size_kb": payload_size_kb,
        "duration_seconds": duration,
        "messages_per_second": messages_per_second,
        "throughput_mb_per_second": throughput_mb_per_second
    }


async def run_all_tests():
    message_counts = [10, 100, 1000]
    payload_sizes = [0, 1, 10, 100]  # in KB

    # Table header
    print(f"{'Messages':<10} {'Payload':<10} {'Duration':<12} {'Msgs/sec':<12} {'MB/sec':<10}")
    print("-" * 60)

    for count in message_counts:
        for size in payload_sizes:
            try:
                result = await run_performance_test(count, size)
                print(
                    f"{result['message_count']:<10} {result['payload_size_kb']:<10}KB {result['duration_seconds']:<12.4f} {result['messages_per_second']:<12.2f} {result['throughput_mb_per_second']:<10.2f}")
            except Exception as e:
                print(f"Error with {count} messages, {size}KB payload: {e}")

            # Small pause between tests
            await asyncio.sleep(2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='NATS JetStream Performance Test')
    parser.add_argument('--message-count', type=int, help='Run a single test with specified message count')
    parser.add_argument('--payload-size', type=int, help='Run a single test with specified payload size in KB')

    args = parser.parse_args()

    if args.message_count and args.payload_size is not None:
        # Run a single test
        asyncio.run(run_performance_test(args.message_count, args.payload_size))
    else:
        # Run all tests
        asyncio.run(run_all_tests())
