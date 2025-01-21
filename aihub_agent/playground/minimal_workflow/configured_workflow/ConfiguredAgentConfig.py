from aihub_agent.agents.AgentConfig import StepConfig, AgentConfig


class StartStepConfig(StepConfig):
    some_step_value: str


class ConfiguredAgentConfig(AgentConfig):
    some_agent_value: str
    start_step_config: StartStepConfig
