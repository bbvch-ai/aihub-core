Feature: Format Chat History

  Scenario: Empty chat history renders as empty string
    Given an empty chat history
    When the chat history is formatted
    Then the result should equal ""

  Scenario: Single user message renders with role header on its own line
    Given a chat history:
      | role | content      |
      | user | Hello agent. |
    When the chat history is formatted
    Then the result should equal "user:\nHello agent."

  Scenario: Multiple messages across roles are joined with newlines
    Given a chat history:
      | role      | content                              |
      | system    | You are an HR assistant.             |
      | user      | How many vacation days do I get?     |
      | assistant | 25 per year for full-time employees. |
    When the chat history is formatted
    Then the result should equal "system:\nYou are an HR assistant.\nuser:\nHow many vacation days do I get?\nassistant:\n25 per year for full-time employees."

  Scenario: Messages with empty content are skipped
    Given a chat history:
      | role      | content    |
      | user      | What time? |
      | assistant |            |
      | user      | Hello?     |
    When the chat history is formatted
    Then the result should equal "user:\nWhat time?\nuser:\nHello?"

  Scenario: Multi-line content keeps structure but drops blank lines and indentation
    Given a chat history with a multi-line system message containing blank lines and indentation
    When the chat history is formatted
    Then the result has no blank lines
    And the result has no leading whitespace on any line
    And every non-empty content line from the input appears in the output
