import asyncio

from llama_index.core.base.llms.types import ChatMessage

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.generative_ai.memory.AgentMemory import AgentMemory
from aihub_lib.generative_ai.memory.UserMemory import UserMemory
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString

rag_agent_config = AgentConfig(
    agent_class="WikiAgent",
    agent_id="bbv_wiki",
    name=LocaleString(en="bbv Wiki Agent", de="bbv Wiki Agent", fr="bbv Wiki Agent", it="bbv Wiki Agent"),
    description=LocaleString(
        en="This is the default RAG Agent",
        de="Dies ist der Standard RAG Agent",
        fr="Ceci est l'agent RAG par défaut",
        it="Questo è l'agente RAG predefinito",
    ),
)


async def main():
    agent_memory = AgentMemory(agent_config=rag_agent_config, t=LocaleHandler(locale="en"))

    # print("RESETTING MEMORY")
    # await agent_memory.delete_all(user_id="cc4af21b-981a-4a76-826d-e722715082e0")

    conversation = [
        ChatMessage(
            role="user",
            content="Ich arbeite mit Stefan zusammen, "
            "er ist ein Mitarbeiter von swiss ai hub. Wie heist er zum Nachnamen?",
        ),
        ChatMessage(role="assistant", content="Er heisst Stefan Häberling."),
    ]
    created_memory = await agent_memory.add_user_memory(
        conversation,
        thread_id="thread-1",
        display_id="display-1",
        run_id="run-1",
        user_id="cc4af21b-981a-4a76-826d-e722715082e0",
    )
    print("created_memory", created_memory)

    search_result = await agent_memory.search(
        query="Wo arbeitet Stefan Häberling?",
        user_id="cc4af21b-981a-4a76-826d-e722715082e0",
        # thread_id="thread-1",
    )

    print("search_result", search_result)

    user_memory = UserMemory(
        user=UserIdentity(
            id="cc4af21b-981a-4a76-826d-e722715082e0", name="Joel", email="joel.barmettler@bbv.ch", roles=[]
        ),
        t=LocaleHandler(locale="en"),
    )
    print(await user_memory.get_all())


if __name__ == "__main__":
    asyncio.run(main())
