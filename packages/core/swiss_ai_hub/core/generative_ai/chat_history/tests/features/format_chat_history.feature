Feature: Format Chat History

  Scenario: Empty chat history renders as empty string
    Given an empty chat history
    When the chat history is formatted
    Then the result should equal ""

  Scenario: Single user message renders as role prefixed line
    Given a chat history:
      | role | content      |
      | user | Hello agent. |
    When the chat history is formatted
    Then the result should equal "user: Hello agent."

  Scenario: Multiple messages across roles are joined with newlines
    Given a chat history:
      | role      | content                                |
      | system    | You are an HR assistant.               |
      | user      | How many vacation days do I get?       |
      | assistant | 25 per year for full-time employees.   |
    When the chat history is formatted
    Then the result should equal "system: You are an HR assistant.\nuser: How many vacation days do I get?\nassistant: 25 per year for full-time employees."

  Scenario: Messages with empty content are skipped
    Given a chat history:
      | role      | content    |
      | user      | What time? |
      | assistant |            |
      | user      | Hello?     |
    When the chat history is formatted
    Then the result should equal "user: What time?\nuser: Hello?"
