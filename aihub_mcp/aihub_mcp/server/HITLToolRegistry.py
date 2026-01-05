import logging

from fastmcp import Context

from aihub_mcp.server.MCPServer import MCPServer
from aihub_mcp.translation.EventTranslator import EventTranslator

logger = logging.getLogger(__name__)


class HITLToolRegistry:
    """
    Registers MCP tools for Human-in-the-Loop fallback flow.

    When MCP elicitation is not supported by the client, HITL requests return a pending
    status with a request_id. The submit_hitl_response tool allows the AI assistant to
    submit the user's response and resume agent execution.
    """

    def __init__(
        self,
        mcp_server: MCPServer,
        event_translator: EventTranslator,
    ) -> None:
        self._mcp_server = mcp_server
        self._event_translator = event_translator

    def register_tools(self) -> None:
        """Register HITL-related MCP tools."""
        mcp = self._mcp_server.mcp
        event_translator = self._event_translator

        @mcp.tool(
            name="submit_hitl_response",
            description=(
                "Submit a human response to a pending Human-in-the-Loop request. "
                "Use this tool after an agent tool returns a hitl_pending status. "
                "For confirmation requests (hitl_type='confirmation'), respond with "
                "'yes', 'true', or 'y' for confirmation, any other value for rejection. "
                "For input requests (hitl_type='input'), provide the user's text response."
            ),
        )
        async def submit_hitl_response(
            request_id: str,
            response: str,
            ctx: Context,
        ) -> str:
            """Submit a human response to resume agent execution after HITL pending status."""
            logger.info(f"submit_hitl_response called: request_id={request_id}")

            try:
                await ctx.info(f"Submitting HITL response for request: {request_id}")

                result = await event_translator.resume_after_hitl(
                    request_id=request_id,
                    response=response,
                    ctx=ctx,
                )

                return result

            except ValueError as e:
                # Invalid or expired request_id
                error_msg = str(e)
                logger.warning(f"HITL submission failed: {error_msg}")
                await ctx.error(error_msg)
                return f"Error: {error_msg}"

            except RuntimeError as e:
                # Configuration error (no store)
                error_msg = str(e)
                logger.error(f"HITL configuration error: {error_msg}")
                await ctx.error(error_msg)
                return f"Error: {error_msg}"

            except Exception as e:
                error_msg = f"HITL submission failed: {e}"
                logger.exception(error_msg)
                await ctx.error(error_msg)
                raise

        logger.info("Registered submit_hitl_response tool")
