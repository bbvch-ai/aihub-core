"""AgentDeveloperAgent: Meta-agent that proxies requests to OpenCode servers."""

from typing import Any

import opencode_ai
from aihub_lib.agents.opencode_utils import get_or_create_opencode_session
from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import (
    ChunkEvent,
    DocumentChangedEvent,
    ExceptionEvent,
    LLMCostEvent,
    StopEvent,
    ThoughtEvent,
    ToolErrorEvent,
    ToolOutputEvent,
)
from aihub_lib.nats.events.user import UserMessageEvent
from opencode_ai import AsyncOpencode

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
        Main step that proxies user message to OpenCode server.

        Streams events live using EventDisplayer as OpenCode processes the request.
        """
        try:
            # Create OpenCode client
            client = AsyncOpencode(base_url=agent_config.opencode_server_url, timeout=agent_config.opencode_timeout)

            # Get or create OpenCode session
            session_id = await get_or_create_opencode_session(
                thread_context=thread_context,
                opencode_client=client,
                initialization_prompt=agent_config.initialization_prompt,
            )

            # Send message and stream events
            user_message = event.messages[-1].content
            await client.session.chat(
                id=session_id,
                parts=[{"type": "text", "text": user_message}],
                model_id=agent_config.model_id,
                provider_id=agent_config.provider_id,
            )

            # Stream live events from OpenCode
            async for stream_event in await client.event.list():
                await self._process_opencode_event(stream_event, displayer, agent_config)

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

    async def _process_opencode_event(
        self,
        stream_event: Any,
        displayer: EventDisplayer,
        agent_config: AgentDeveloperAgentConfig,
    ) -> None:
        """Process a single OpenCode stream event and emit to Swiss AI-Hub protocol."""
        # Handle message.part.updated (contains the actual content parts)
        if stream_event.type == "message.part.updated":
            part = stream_event.properties.part
            await self._process_part(part, displayer, agent_config)

        # Handle session.error
        elif stream_event.type == "session.error":
            error_obj = stream_event.properties.error
            if error_obj:
                error_msg = getattr(error_obj, "message", str(error_obj))
                await displayer.display_event(
                    ChunkEvent(content=f"❌ **OpenCode Error:** {error_msg}\n"),
                )

    async def _process_part(
        self,
        part: Any,
        displayer: EventDisplayer,
        agent_config: AgentDeveloperAgentConfig,
    ) -> None:
        """Process a Part (TextPart, FilePart, ToolPart, etc.) and emit corresponding events."""
        # 1. TextPart → ChunkEvent
        if part.type == "text":
            await displayer.display_event(ChunkEvent(content=part.text))

        # 2. FilePart → DocumentChangedEvent + ChunkEvent
        elif part.type == "file" and agent_config.show_file_changes:
            await self._process_file_part(part, displayer, agent_config.verbose_output)

        # 3. ToolPart → ToolOutputEvent/ToolErrorEvent + ChunkEvent
        elif part.type == "tool" and agent_config.show_tool_calls:
            await self._process_tool_part(part, displayer, agent_config.verbose_output)

        # 4. StepStartPart → ThoughtEvent
        elif part.type == "step-start":
            await displayer.display_event(ThoughtEvent(content="🧠 Thinking...\n"))

        # 5. StepFinishPart → LLMCostEvent
        elif part.type == "step-finish":
            await self._process_step_finish(part, displayer, agent_config.verbose_output)

    async def _process_file_part(self, file_part: Any, displayer: EventDisplayer, verbose: bool) -> None:
        """Process FilePart and emit DocumentChangedEvent + ChunkEvent."""
        import hashlib
        from datetime import UTC, datetime

        path = file_part.source.path if hasattr(file_part, "source") and file_part.source else "unknown"
        mime_type = getattr(file_part, "mime", None)

        # Extract content
        content = None
        if hasattr(file_part, "source") and file_part.source and hasattr(file_part.source, "text"):
            text_obj = file_part.source.text
            if hasattr(text_obj, "value"):
                content = text_obj.value

        # Emit DocumentChangedEvent
        await displayer.display_event(
            DocumentChangedEvent(
                document_id=hashlib.sha256(path.encode()).hexdigest()[:16],
                path=path,
                content=content,
                mime_type=mime_type,
                content_preview=content[:200] if content else None,
                operation="changed",
                namespace="opencode",
            )
        )

        # Emit ChunkEvent
        await displayer.display_event(ChunkEvent(content=f"📝 **Changed:** `{path}`\n"))

    async def _process_tool_part(self, tool_part: Any, displayer: EventDisplayer, verbose: bool) -> None:
        """Process ToolPart and emit ToolOutputEvent/ToolErrorEvent + ChunkEvent."""
        tool_name = tool_part.tool if hasattr(tool_part, "tool") else "unknown"
        state = tool_part.state if hasattr(tool_part, "state") else None

        if not state or not hasattr(state, "status"):
            return

        # Skip pending/running states
        if state.status in ["pending", "running"]:
            return

        title = getattr(state, "title", None)
        input_params = getattr(state, "input", None)

        # Calculate duration
        duration = None
        if hasattr(state, "time") and state.time:
            if hasattr(state.time, "start") and hasattr(state.time, "end"):
                duration = state.time.end - state.time.start

        # Handle completed state
        if state.status == "completed":
            output = getattr(state, "output", "")
            await displayer.display_event(
                ToolOutputEvent(name=tool_name, title=title, output=output, input=input_params, duration=duration)
            )
            await displayer.display_event(ChunkEvent(content=f"✅ **Completed:** `{title or tool_name}`\n"))

        # Handle error state
        elif state.status == "error":
            error = getattr(state, "error", "Unknown error")
            await displayer.display_event(
                ToolErrorEvent(name=tool_name, title=title, error=error, input=input_params, duration=duration)
            )
            await displayer.display_event(ChunkEvent(content=f"❌ **Failed:** `{title or tool_name}`\n"))

    async def _process_step_finish(self, step_finish_part: Any, displayer: EventDisplayer, verbose: bool) -> None:
        """Process StepFinishPart and emit LLMCostEvent."""
        cost = getattr(step_finish_part, "cost", 0.0)
        tokens = getattr(step_finish_part, "tokens", None)

        if not tokens:
            return

        input_tokens = int(getattr(tokens, "input", 0))
        output_tokens = int(getattr(tokens, "output", 0))
        reasoning_tokens = int(getattr(tokens, "reasoning", 0))

        cache_read = 0
        cache_write = 0
        if hasattr(tokens, "cache"):
            cache_read = int(getattr(tokens.cache, "read", 0))
            cache_write = int(getattr(tokens.cache, "write", 0))

        # Map to Swiss AI-Hub cost structure
        prompt_token_count = input_tokens + cache_read
        completion_token_count = output_tokens + reasoning_tokens

        # Split cost proportionally
        total_tokens = prompt_token_count + completion_token_count
        if total_tokens > 0:
            prompt_costs = cost * (prompt_token_count / total_tokens)
            completion_costs = cost * (completion_token_count / total_tokens)
        else:
            prompt_costs = 0.0
            completion_costs = 0.0

        await displayer.display_event(
            LLMCostEvent(
                llm_name="opencode",
                prompt_token_count=prompt_token_count,
                completion_token_count=completion_token_count,
                embedding_token_count=0,
                prompt_tokens_costs=prompt_costs,
                completion_tokens_costs=completion_costs,
                embedding_tokens_costs=0.0,
            )
        )
