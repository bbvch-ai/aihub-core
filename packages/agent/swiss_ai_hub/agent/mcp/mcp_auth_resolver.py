from swiss_ai_hub.agent.context.run.run_context import RunContext


class McpAuthResolver:
    """Read the user's bearer token out of the X-AIHub-* headers stashed in RunContext.

    Per #948 the API extracts ``X-AIHub-*`` request headers, forwards them on the NATS message
    envelope, and ``AgentDispatcher`` (PR #1258) lifts them into RunContext under
    ``aihub_headers`` (lowercased keys). This resolver is the MCP-side reader of that contract.

    Keep ``AIHUB_HEADERS_KEY`` and ``USER_TOKEN_HEADER`` in lockstep with the dispatcher writer
    (``AgentDispatcher._AIHUB_HEADERS_KEY``) and ``NATSMessageHeaders.extract_aihub_headers``.
    """

    AIHUB_HEADERS_KEY = "aihub_headers"
    USER_TOKEN_HEADER = "x-aihub-user-token"

    @staticmethod
    async def resolve_user_token(run_context: RunContext) -> str | None:
        """Return the requesting user's bearer token if one was forwarded, else None.

        None is the normal case for runs initiated outside an HTTP request (scheduled,
        process-initiated, agent-to-agent) and for entry points that do not yet forward the
        header. Callers that require a token — e.g. ``McpClientConfig`` with
        ``auth_mode='user_token'`` — are responsible for failing loudly when None comes back.
        """
        aihub_headers: dict[str, str] | None = await run_context.get(McpAuthResolver.AIHUB_HEADERS_KEY)
        if not aihub_headers:
            return None
        return aihub_headers.get(McpAuthResolver.USER_TOKEN_HEADER)
