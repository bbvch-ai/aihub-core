from typing import List

from lib_core.entities.ConversationStarter import (
    ConversationStarter,
    ConversationStarterMessage,
)


class ConversationStarterHandler:
    @staticmethod
    def start_conversation(
        source_user_email: str,
        target_user_email: str,
        source_agent_id: str,
        target_agent_id: str,
        title: str,
        messages: List[ConversationStarterMessage],
        organization: str,
        source_conversation_id: str = None,
        target_conversation_id: str = None,
    ) -> ConversationStarter:
        task = ConversationStarter(
            source_user_email=source_user_email,
            target_user_email=target_user_email,
            source_agent_id=source_agent_id,
            target_agent_id=target_agent_id,
            source_conversation_id=source_conversation_id,
            target_conversation_id=target_conversation_id,
            title=title,
            messages=messages,
        )
        task.switch_db(organization)
        task.save()
        return task
