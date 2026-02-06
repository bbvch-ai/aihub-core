import asyncio
import logging
import multiprocessing
import os
import signal
from multiprocessing import Process

from aihub_lib.agents.AgentConfig import AgentConfig

from aihub_agent.agents.Agent import Agent
from aihub_agent.runners.AgentRunner import AgentRunner

logger = logging.getLogger(__name__)


class MultiprocessAgentRunner:
    """
    Manages multiple AgentRunners across separate processes.

    This class enables horizontal scaling of agents by running multiple instances
    of the same agent type across different processes. It handles process creation,
    management, and cleanup.

    ### Key Features
    - **Process-based Parallelism**: Runs agents in separate processes for true parallelism
    - **Configurable Instance Count**: Allows specifying the number of agent instances to run
    - **Primary Instance Control**: Optionally designates one instance as primary for sending initial events
    - **Uniform Configuration**: Applies the same agent configuration across all instances
    - **Graceful Shutdown**: Properly terminates all agent processes on shutdown

    ### Usage Example
    ```python
    runner = MultiprocessAgentRunner(
        agent_type=MyAgent,
        agent_config=my_config,
        process_count=5
    )

    runner.run_forever()
    ```
    """

    def __init__(
        self,
        agent_type: type[Agent],
        agent_config: AgentConfig,
        locale_paths: list[str] | None = None,
        process_count: int = 10,
    ):
        self.agent_type = agent_type
        self.agent_config = agent_config
        self.process_count = process_count
        self.locale_paths = locale_paths

        self.processes: list[Process] = []

        if not multiprocessing.get_start_method(allow_none=True):
            multiprocessing.set_start_method("fork")

    @staticmethod
    def _process_runner(
        process_index: int,
        agent_type: type[Agent],
        agent_config: AgentConfig,
        locale_paths: list[str] | None,
    ):
        """Static method that runs in each process to initialize and run an agent."""

        runner = None
        stop_loop = asyncio.Event()
        shutdown_task: asyncio.Task | None = None

        def signal_handler(sig, frame):
            nonlocal shutdown_task
            if asyncio.get_event_loop().is_running():
                shutdown_task = asyncio.create_task(shutdown_runner())
            else:
                # If no event loop is running, just set the event
                stop_loop.set()

        async def shutdown_runner():
            """Gracefully shutdown the runner"""
            logger.info(f"Process {process_index}: Received shutdown signal, stopping runner...")
            if runner and hasattr(runner, "stop"):
                await runner.stop()
            stop_loop.set()

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        async def _run_agent():
            nonlocal runner
            process_id = os.getpid()
            logger.info(f"Agent process {process_index} running with PID: {process_id}")

            runner = AgentRunner(
                agent_type=agent_type,
                agent_config=agent_config.model_copy(deep=True),
                locale_paths=locale_paths,
            )

            # Start the runner
            await runner.start()

            try:
                # Wait until we're signaled to stop
                await stop_loop.wait()
            except KeyboardInterrupt:
                logger.info(f"Process {process_index}: Received KeyboardInterrupt")
            except Exception as e:
                logger.exception(f"Process {process_index}: Error while running: {e}")
            finally:
                # Ensure proper cleanup
                if shutdown_task is not None:
                    logger.info(f"Process {process_index}: Waiting for shutdown task to complete")
                    await shutdown_task
                if runner and hasattr(runner, "stop") and not stop_loop.is_set():
                    logger.info(f"Process {process_index}: Stopping runner in finally block")
                    await runner.stop()

        try:
            asyncio.run(_run_agent())
        except Exception as e:
            logger.exception(f"Error in agent process {process_index}: {e}")

    def start(self):
        """
        Start all agent processes.
        """
        logger.info(f"Starting {self.process_count} agent processes")
        self.processes = []

        for i in range(self.process_count):
            process = Process(
                target=self._process_runner,
                args=(
                    i,
                    self.agent_type,
                    self.agent_config,
                    self.locale_paths,
                ),
            )
            process.daemon = True  # Ensure processes exit when main program exits
            process.start()
            self.processes.append(process)

        logger.info(f"Started {len(self.processes)} agent processes")

    def stop(self):
        """
        Stop all agent processes.
        """
        logger.info("Stopping all agent processes")

        # Terminate all processes
        for i, process in enumerate(self.processes):
            if process.is_alive():
                logger.info(f"Terminating agent process {i}")
                process.terminate()

        # Wait for all processes to finish
        for i, process in enumerate(self.processes):
            process.join()
            logger.info(f"Agent process {i} joined")

        self.processes = []
        logger.info("All agent processes stopped")

    def run_forever(self):
        """
        Start the runner if not already running and block until all processes complete.
        """
        self.start()
        try:
            # Wait for all processes to complete (which they won't unless terminated)
            for process in self.processes:
                process.join()
        except KeyboardInterrupt:
            logger.info("Caught keyboard interrupt, stopping all processes")
            self.stop()
