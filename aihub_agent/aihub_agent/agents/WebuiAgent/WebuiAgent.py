import httpx
from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.nats.events import LLMEvent, LLMStopEvent, UserMessageEvent
from aihub_lib.nats.events.semantic import Message
from aihub_lib.nats.workflow.decorators.step import step

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.WebuiAgent.utils import _display_streamed_content, _parse_sse_chunk
from aihub_agent.agents.WebuiAgent.WebuiAgentConfig import WebuiAgentConfig


class WebuiAgent(Agent):
    @step()
    async def start_step(
        self,
        agent_config: WebuiAgentConfig,
        event: UserMessageEvent,
        displayer: EventDisplayer,
    ) -> LLMEvent:
        # Initialize response tracking
        aggregate = ""
        buffer = ""
        max_buffer_length = 500

        # Prepare request data
        url = f"{agent_config.webui_base_url}/api/chat/completions"
        headers = {"Authorization": f"Bearer {agent_config.webui_bearer_token}"}

        # Format messages for the API
        formatted_messages = [{"role": msg.role, "content": msg.content} for msg in event.messages]

        # Prepare request body
        request_body = {
            "stream": True,
            "model": agent_config.assistant_name,
            "messages": formatted_messages,
            "features": {
                "image_generation": False,
                "code_interpreter": False,
                "web_search": agent_config.features.web_search,
            },
            "model_item": {"id": agent_config.assistant_name},
        }

        usage = {"completion_tokens": -1, "prompt_tokens": -1, "total_tokens": -1}

        # Stream response from API
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", url, json=request_body, headers=headers, timeout=60.0) as response:
                response.raise_for_status()

                # Process each line of the streaming response
                async for line in response.aiter_lines():
                    content_or_usage = await _parse_sse_chunk(line)

                    if type(content_or_usage) is str:
                        aggregate += content_or_usage
                        buffer = await _display_streamed_content(
                            content_or_usage, buffer, max_buffer_length, displayer, agent_config.assistant_name
                        )

                    if type(content_or_usage) is dict:
                        usage = content_or_usage

        # Flush any remaining content in buffer
        if buffer:
            await displayer.display_chunk(buffer, model_name=agent_config.assistant_name)

        # Create and return the stop event
        return LLMStopEvent(
            input_messages=[Message.from_llama_index(msg) for msg in event.messages],
            output_messages=[Message.from_string(role="assistant", content=aggregate)],
            invocation_parameters=request_body,
            chat_model_name=agent_config.assistant_name,
            provider="open-webui",
            token_count_prompt=usage["prompt_tokens"],
            token_count_completion=usage["completion_tokens"],
            token_count_total=usage["total_tokens"],
        )
