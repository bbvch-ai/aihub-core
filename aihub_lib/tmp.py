import os

from llama_index.core.base.llms.types import ChatMessage

from aihub_lib.generative_ai.resources.models.llm.EmbeddingModelConfig import EmbeddingModelConfig
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig

os.environ["LITE_LLM_PROXY_BASE_URL"] = "http://localhost:4000"
os.environ["LITE_LLM_PROXY_API_KEY"] = "asdfadfasfd"

llm = LLMConfig(model_name="local/llama-3.2-1b")
chat_model, cost_tracker = llm.to_llama_index()

print(chat_model.chat(messages=[ChatMessage(role="user", content="Hello, how are you?")]))
print(cost_tracker.get_total_costs())

emb = EmbeddingModelConfig(model_name="local/text-embedding-gte")
embedding_model, cost_tracker = emb.to_llama_index()

print(embedding_model.get_text_embedding("Hello, how are you?"))
print(cost_tracker.get_total_costs())