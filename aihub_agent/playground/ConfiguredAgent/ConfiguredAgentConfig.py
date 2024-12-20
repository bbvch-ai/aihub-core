from aihub_lib.generative_ai.agent.AgentConfig import AgentConfig, StepConfig


class StartStepConfig(StepConfig):
    some_step_value: str

class ConfiguredAgentAgentConfig(AgentConfig):
    some_agent_value: str
    start_step_config: StartStepConfig