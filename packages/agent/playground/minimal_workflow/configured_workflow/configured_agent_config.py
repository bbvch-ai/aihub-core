from swiss_ai_hub.core.agents import AgentConfig, StepConfig


class StartStepConfig(StepConfig):
    some_step_value: str


class ConfiguredAgentConfig(AgentConfig):
    some_agent_value: str
    start_step_config: StartStepConfig
