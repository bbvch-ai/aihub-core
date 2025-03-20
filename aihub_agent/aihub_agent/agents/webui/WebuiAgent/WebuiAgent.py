from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.agents.webui.WebuiAgent.WebuiAgentConfig import WebuiAgentConfig
from aihub_agent.workflow.decorators.step import step
from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.nats.events import UserMessageEvent, LLMEvent, LLMStopEvent
from aihub_lib.nats.events.semantic import Message
import httpx
import json


class WebuiAgent(Agent):

    @step()
    async def start_step(
            self,
            agent_config: WebuiAgentConfig,
            event: UserMessageEvent,
            displayer: EventDisplayer,
    ) -> LLMEvent:
        aggregate = ""
        buffer = ""
        max_buffer_length = 500

        messages = event.messages

        # Iterate over streamed chunks from the LLM
        url = f"{agent_config.webui_base_url}/api/chat/completions"
        token = agent_config.webui_bearer_token
        body = {
            "stream": True,
            "model": agent_config.assistant_name,
            "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
            "features": {
                "image_generation": False,
                "code_interpreter": False,
                "web_search": agent_config.features.web_search,
            },
            "model_item": {
                "id": agent_config.assistant_name
            }
        }

        async with httpx.AsyncClient() as client:
            async with client.stream(
                    "POST",
                    url,
                    json=body,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=60.0
            ) as response:
                response.raise_for_status()

                # Process the streaming response
                async for line in response.aiter_lines():
                    # Skip empty lines
                    if not line.strip():
                        continue

                    # Check for SSE format (data: prefix)
                    if line.startswith("data: "):
                        # Remove the "data: " prefix
                        data = line[6:]

                        # Check for end of stream marker
                        if data == "[DONE]":
                            break

                        try:
                            # Parse the JSON data
                            chunk_data = json.loads(data)

                            # Extract content from the chunk
                            content = ""
                            if "choices" in chunk_data and chunk_data["choices"]:
                                delta = chunk_data["choices"][0].get("delta", {})
                                content = delta.get("content", "")

                            if content:
                                aggregate += content
                                buffer += content

                                # Flush buffer at newline boundaries
                                while "\n" in buffer:
                                    section, buffer = buffer.split("\n", 1)
                                    await displayer.display_chunk(section + "\n", model_name=agent_config.assistant_name)

                                # If no newline but buffer large, flush to avoid delays
                                if len(buffer) > max_buffer_length:
                                    await displayer.display_chunk(buffer, model_name=agent_config.assistant_name)
                                    buffer = ""

                        except json.JSONDecodeError:
                            # Handle malformed JSON
                            continue

        # Flush remaining buffer after streaming finishes
        if buffer:
            await displayer.display_chunk(buffer, model_name=agent_config.assistant_name)

        return LLMStopEvent(
            input_messages=[Message(role=msg.role, content=msg.content) for msg in messages],
            output_messages=[Message(role="assistant", content=aggregate)],
            invocation_parameters=body,
            chat_model_name=agent_config.assistant_name,
            provider="open-webui",
        )