from llama_index.core.base.llms.types import ChatMessage


def format_chat_history(chat_history: list[ChatMessage]) -> str:
    entries = []
    for message in chat_history:
        content = message.content
        if not content or content.strip() == "":
            continue
        entries.append(f"{message.role.value}:\n{content}")
    return "\n".join(entries)
