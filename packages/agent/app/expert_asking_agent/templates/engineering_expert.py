from swiss_ai_hub.core.events.agent import TeamsConfig
from swiss_ai_hub.core.generative_ai import LLMConfig, LLMParameter, OrgMemoryWriteConfig
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.agents.expert_asking_agent import ExpertAskingAgentConfig
from swiss_ai_hub.agent.agents.expert_asking_agent.expert_asking_agent_config import ChannelConfig


def build() -> ExpertAskingAgentConfig:
    return ExpertAskingAgentConfig(
        agent_id="engineering-expert",
        name=LocaleString(
            en="Engineering Expert",
            de="Engineering-Experte",
            fr="Expert en ingénierie",
            it="Esperto di ingegneria",
        ),
        description=LocaleString(
            en="Escalates engineering questions to a Microsoft Teams channel of human experts.",
            de="Eskaliert technische Fragen an einen Microsoft Teams-Kanal von menschlichen Experten.",
            fr="Escalade les questions techniques vers un canal Microsoft Teams d'experts humains.",
            it="Inoltra le domande tecniche a un canale Microsoft Teams di esperti umani.",
        ),
        icon="mage:hard-hat",
        llm=LLMConfig(
            model_name="text-generation/gpt-oss-120b",
            default_parameter=LLMParameter(temperature=0.2, timeout=60.0),
        ),
        loop_max=3,
        org_memory=OrgMemoryWriteConfig(
            default_tenant_namespace="engineering",
            allowed_tenant_namespaces=["engineering"],
        ),
        org_memory_format=LocaleString(
            en="Question: {question}\n\nExpert Answer: {answer}",
            de="Frage: {question}\n\nAntwort des Experten: {answer}",
            fr="Question : {question}\n\nRéponse de l'expert : {answer}",
            it="Domanda: {question}\n\nRisposta dell'esperto: {answer}",
        ),
        channel_config=ChannelConfig(
            channel_type="teams",
            teams_config=TeamsConfig(
                channel_id="19:placeholder-channel-id@thread.tacv2",
                tenant_id="00000000-0000-0000-0000-000000000000",
                bot_id="00000000-0000-0000-0000-000000000000",
            ),
        ),
    )
