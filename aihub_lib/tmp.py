from mem0 import Memory

from aihub_lib.infrastructure.mem0.Mem0Settings import Mem0Settings

mem0 = Mem0Settings()

print(mem0.config)

memory = Memory.from_config(mem0.config)

conversation = [
    {"role": "user", "content": "Stefan Häberling ist ein Freund von mir. Wo arbeitet er?"},
    {
        "role": "assistant",
        "content": "Er arbeitet bei swiss ai hub.",
    },
]

memory.add(conversation, user_id="joel", run_id="1", metadata={"thread_id": "12"})

results = memory.search(
    "What are known ai projects?",
    user_id="joel",
    # agent_id="MyAgent",
    # run_id="1",
    limit=100,
    rerank=False,
    threshold=0,
    filters={"thread_id": "12"},
)

print(results)
