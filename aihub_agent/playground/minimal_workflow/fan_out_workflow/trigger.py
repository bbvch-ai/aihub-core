import asyncio
import multiprocessing
import os
from multiprocessing import Process

from bson import ObjectId

from aihub_agent.runners.AgentRunner import AgentRunner
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StartEvent
from aihub_lib.nats.redis.RedisConfig import RedisConfig
from aihub_lib.testing.logging.logger import enable_logging
from playground.minimal_workflow.fan_out_workflow.FanOutAgent import FanOutAgent
from playground.minimal_workflow.fan_out_workflow.FanOutAgentConfig import (
    FanOutAgentConfig,
)

# Set up logging
enable_logging(level=30)


# Function to run a single agent in its own process
def run_agent(i, is_primary=False, event_id=None, workflow_id=None, run_id=None):
    async def _run():
        # Configure NATS servers
        servers = os.getenv("NATS_SERVERS", "nats://localhost:4222")
        servers_list = [server.strip() for server in servers.split(",") if server.strip()]

        # Create and configure the agent runner
        runner = AgentRunner(
            servers=servers_list,
            agent_type=FanOutAgent,
            agent_config=FanOutAgentConfig(
                agent_id="fan_out_agent",
                name=LocaleString(en=f"Agent #{i}"),
                description=LocaleString(en="This is an agent that fans out multiple steps"),
                system_prompt=LocaleString(en="You are an agent"),
            ),
            redis_url=RedisConfig().REDIS_URL,
        )

        # Start the runner
        await runner.start()

        # Send start event if this is the primary agent
        if is_primary and event_id and workflow_id and run_id:
            await runner.send_event(StartEvent(), event_id, workflow_id, run_id)
            print(f"Primary agent #{i} sent start event")

        # Keep the agent running for a while (can be adjusted based on your needs)
        try:
            # Run indefinitely or until external termination
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print(f"Agent {i} received shutdown signal")
        finally:
            # Ensure proper cleanup
            await runner.stop()
            print(f"Agent {i} stopped")

    # Run the async function in the process
    asyncio.run(_run())


def main():
    # Generate IDs for the workflow
    event_id = str(ObjectId())
    workflow_id = str(ObjectId())
    run_id = str(ObjectId())

    processes = []

    # Create 100 agent processes
    for i in range(30):
        # The first agent is designated as primary
        is_primary = (i == 0)

        # Create and start process for each agent
        p = Process(
            target=run_agent,
            args=(i, is_primary, event_id, workflow_id, run_id)
        )
        p.start()
        processes.append(p)

    try:
        # Wait for user to terminate the program
        print("All agents started. Press Ctrl+C to terminate.")
        # Join the first process (optional, prevents main process from exiting)
        processes[0].join()
    except KeyboardInterrupt:
        print("Main process received termination signal")
    finally:
        # Clean up all processes
        for i, p in enumerate(processes):
            if p.is_alive():
                print(f"Terminating agent process {i}")
                p.terminate()

        # Wait for all processes to finish
        for i, p in enumerate(processes):
            p.join()
            print(f"Agent process {i} joined")

        print("All agent processes terminated")


if __name__ == "__main__":
    # Set multiprocessing start method
    # 'spawn' is more compatible across platforms than 'fork'
    multiprocessing.set_start_method('fork')
    main()
