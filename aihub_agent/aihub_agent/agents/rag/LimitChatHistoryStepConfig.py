from aihub_lib.generative_ai.agent.AgentConfig import StepConfig
from mongoengine import IntField


class LimitChatHistoryStepConfig(StepConfig):
    number_of_input_tokens = IntField(required=True, default=2048)
