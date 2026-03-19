Feature: Llama Index Agent
  test for LlamaIndexAgent

  Scenario: Test Llama Index Agent
    Given a LlamaIndexAgent is initialized and configured with a language model

    When the user sends a message "Hello"
    Then the agent should call the LLM to process the message "Hello"
    And the agent should stream a partial response
    And the agent should produce a complete response from the LLM
    And the agent should stop after completing the response
