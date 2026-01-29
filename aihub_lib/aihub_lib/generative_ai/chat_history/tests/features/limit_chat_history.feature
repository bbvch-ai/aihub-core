Feature: Limit chat history step behavior

  Scenario: Limit chat history when token count is within limit
    Given a chat history with 3 messages
    And a token limit configuration of 2048 tokens
    When the limit chat history step is executed
    Then the limited chat history should contain all messages

  Scenario: Limit chat history when token count exceeds limit
    Given a chat history with 10 messages
    And a token limit configuration of 10 tokens
    When the limit chat history step is executed
    Then the limited chat history should contain fewer messages
