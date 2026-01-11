"""AgentDeveloperAgent: Meta-agent that proxies requests to OpenCode servers."""

import opencode_ai
from aihub_lib.agents.opencode_utils import (
    convert_opencode_response_to_events,
    get_or_create_opencode_session,
)
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import ChunkEvent, StopEvent
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
    ) -> list[ChunkEvent | StopEvent]:
        """
        Main step that proxies user message to OpenCode server.

        Manages session lifecycle:
        - Creates OpenCode session on first message
        - Reuses session for subsequent messages in same thread
        - Sends user message to OpenCode
        - Converts response parts to ChunkEvents
        """
        events: list[ChunkEvent | StopEvent] = []

        try:
            # 1. Create OpenCode client
            client = AsyncOpencode(base_url=agent_config.opencode_server_url, timeout=agent_config.opencode_timeout)

            # 2. Get or create OpenCode session
            session_id = await get_or_create_opencode_session(
                thread_context=thread_context,
                opencode_client=client,
                initialization_prompt=agent_config.initialization_prompt,
            )

            # 3. Send message to OpenCode
            user_message = event.messages[-1].content

            # Emit "thinking" message
            events.append(
                ChunkEvent(content=f"🤖 Forwarding to OpenCode server...\n\n**Your request:** {user_message}\n\n")
            )

            response = await client.session.chat(
                id=session_id,
                parts=[{"type": "text", "text": user_message}],
                model_id=agent_config.model_id,
                provider_id=agent_config.provider_id,
            )

            # 4. Convert response parts to ChunkEvents
            response_events = convert_opencode_response_to_events(
                response=response,
                show_file_changes=agent_config.show_file_changes,
                show_tool_calls=agent_config.show_tool_calls,
                verbose_output=agent_config.verbose_output,
            )
            events.extend(response_events)

        except opencode_ai.APIConnectionError as e:
            # OpenCode server not reachable
            events.append(
                ChunkEvent(
                    content=f"""❌ **Cannot connect to OpenCode server**

Error: {str(e)}

**Troubleshooting:**
1. Check if OpenCode server is running:
   ```bash
   docker ps | grep agent-dev
   ```

2. Verify URL in agent configuration:
   - Current: {agent_config.opencode_server_url}
   - Should be: http://<container-name>:8080

3. Check container logs:
   ```bash
   docker logs agent-1-dev
   ```

4. Restart the agent dev container:
   ```bash
   docker-compose -f docker-compose.agent-dev.yml restart agent-1-dev
   ```
"""
                )
            )

        except opencode_ai.RateLimitError:
            events.append(ChunkEvent(content="⚠️ **Rate limit exceeded**\n\nPlease wait a moment and try again."))

        except opencode_ai.APIStatusError as e:
            events.append(
                ChunkEvent(
                    content=f"""❌ **OpenCode API Error**

Status Code: {e.status_code}
Error: {e.message}

Please check the OpenCode server logs for details.
"""
                )
            )

        except Exception as e:
            events.append(
                ChunkEvent(
                    content=f"""❌ **Unexpected Error**

{type(e).__name__}: {str(e)}

Please report this issue if it persists.
"""
                )
            )

        # 5. Always end with StopEvent
        events.append(StopEvent())

        return events
