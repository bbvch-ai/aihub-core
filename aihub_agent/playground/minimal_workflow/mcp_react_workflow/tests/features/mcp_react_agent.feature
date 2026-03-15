Feature: MCP React Agent

  Scenario: Agent calls MCP tools via LLM reasoning and completes
    Given a McpReactAgent runner with a mocked MCP server and LLM
    When the start event is sent
    Then a StopEvent is present
    And a McpReasoningEvent was emitted
    And a McpToolCallEvent was emitted
