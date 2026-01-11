"""AgentDeveloperAgent: Meta-agent that proxies requests to OpenCode servers."""

import opencode_ai
from aihub_lib.agents.opencode_helpers import (
    chatmessage_to_opencode_parts,
    filepart_to_document_changed_event,
    get_or_create_opencode_session,
    step_finish_to_cost_event,
    step_start_to_thought_event,
    toolpart_to_tool_events,
)
from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import ChunkEvent, ExceptionEvent, StopEvent
from aihub_lib.nats.events.user import UserMessageEvent
from opencode_ai import AsyncOpencode
from opencode_ai.types import FilePart, StepFinishPart, StepStartPart, TextPart, ToolPart

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.AgentDeveloperAgent.configs.AgentDeveloperAgentConfig import AgentDeveloperAgentConfig
from aihub_agent.context.thread.ThreadContext import ThreadContext
from aihub_agent.workflow.decorators.step import step


class AgentDeveloperAgent(Agent):
    """
    Meta-agent that proxies user requests to OpenCode server.

    Allows developers to build AI agents through OpenWebUI chat interface
    without needing local OpenCode installation.

    Workflow:
    1. User sends build request via chat
    2. Agent manages OpenCode session (creates on first message)
    3. Forwards request to OpenCode server
    4. Converts OpenCode response to chat messages
    5. Returns formatted updates to user

    Example:
        User: "Build a legal RAG agent with citations"
        Agent:
            ✅ Created LegalRAGAgent.py
            ✅ Created configs/LegalRAGAgentConfig.py
            ✅ Created events/CitationEvent.py
            ✅ Created tests/test_legal_rag.py
            ✅ Tests passing!

            Your agent is ready at /workspace/agent/LegalRAGAgent/
    """

    @step(
        name=LocaleString(en="Proxy to OpenCode", de="An OpenCode weiterleiten"),
        description=LocaleString(
            en="Forward user request to OpenCode server and stream response",
            de="Benutzeranfrage an OpenCode-Server weiterleiten und Antwort streamen",
        ),
        icon="mdi:robot-outline",
    )
    async def proxy_to_opencode_step(
        self,
        event: UserMessageEvent,
        thread_context: ThreadContext,
        agent_config: AgentDeveloperAgentConfig,
        displayer: EventDisplayer,
    ) -> StopEvent | ExceptionEvent:
        """
        Proxies user message to OpenCode server and streams response events.

        Converts ChatMessage blocks to OpenCode parts, forwards to OpenCode,
        then streams live events back through EventDisplayer using typed helpers.
        """
        try:
            # Create OpenCode client with authentication
            client = AsyncOpencode(
                base_url=agent_config.opencode_server_url,
                timeout=agent_config.opencode_timeout,
                api_key=agent_config.opencode_token.get_secret_value(),
            )

            # Get or create OpenCode session
            session_id = await get_or_create_opencode_session(
                thread_context=thread_context,
                opencode_client=client,
            )

            # Convert last user message to OpenCode parts (handles multimodal content)
            last_message = event.last_user_message
            parts = chatmessage_to_opencode_parts(last_message)

            # Get model name from LLM config
            model_name = agent_config.llm.model_name

            # Send message and start streaming
            await client.session.chat(
                id=session_id,
                parts=parts,
                model_id=model_name,
            )

            # Stream live events from OpenCode
            async for stream_event in await client.event.list():
                # Process message.part.updated (contains the actual content parts)
                if stream_event.type == "message.part.updated":
                    part = stream_event.properties.part

                    # TextPart → ChunkEvent
                    if isinstance(part, TextPart):
                        await displayer.display_event(ChunkEvent(content=part.text))

                    # FilePart → DocumentChangedEvent + ChunkEvent
                    elif isinstance(part, FilePart):
                        doc_event = filepart_to_document_changed_event(part)
                        await displayer.display_event(doc_event)
                        await displayer.display_event(ChunkEvent(content=f"📝 **Changed:** `{doc_event.path}`\n"))

                    # ToolPart → ToolOutputEvent/ToolErrorEvent + ChunkEvent
                    elif isinstance(part, ToolPart):
                        tool_event = toolpart_to_tool_events(part)
                        if tool_event:
                            await displayer.display_event(tool_event)
                            # Add user-friendly chunk
                            if tool_event.__class__.__name__ == "ToolOutputEvent":
                                title = tool_event.title or tool_event.name
                                await displayer.display_event(ChunkEvent(content=f"✅ **Completed:** `{title}`\n"))
                            else:  # ToolErrorEvent
                                title = tool_event.title or tool_event.name
                                await displayer.display_event(ChunkEvent(content=f"❌ **Failed:** `{title}`\n"))

                    # StepStartPart → ThoughtEvent
                    elif isinstance(part, StepStartPart):
                        thought_event = step_start_to_thought_event(part)
                        await displayer.display_event(thought_event)

                    # StepFinishPart → LLMCostEvent
                    elif isinstance(part, StepFinishPart):
                        cost_event = step_finish_to_cost_event(part)
                        await displayer.display_event(cost_event)

                # Handle session.error
                elif stream_event.type == "session.error":
                    error_obj = stream_event.properties.error
                    if error_obj:
                        error_msg = getattr(error_obj, "message", str(error_obj))
                        await displayer.display_event(
                            ChunkEvent(content=f"❌ **OpenCode Error:** {error_msg}\n"),
                        )

            return StopEvent()

        except opencode_ai.APIConnectionError as e:
            return ExceptionEvent(
                exception_type="APIConnectionError",
                exception_message=f"Cannot connect to OpenCode server at {agent_config.opencode_server_url}: {str(e)}",
            )

        except opencode_ai.RateLimitError as e:
            return ExceptionEvent(
                exception_type="RateLimitError",
                exception_message=f"OpenCode rate limit exceeded: {str(e)}",
            )

        except opencode_ai.APIStatusError as e:
            return ExceptionEvent(
                exception_type="APIStatusError",
                exception_message=f"OpenCode API error (status {e.status_code}): {e.message}",
            )

        except Exception as e:
            return ExceptionEvent(
                exception_type=type(e).__name__,
                exception_message=str(e),
            )
