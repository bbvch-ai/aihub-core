Feature: File Processing Agent
  Verify that the FileProcessingAgent processes user messages correctly,
  optionally enriching the context with uploaded file contents.

  Scenario: Process user message without files
    Given a FileProcessingAgent runner with a valid self hosted configuration
    When the start event is sent with a user query "What is Python?"
    Then a StartEvent is present
    And a LimitChatHistoryEvent is present
    And a StopEvent is present
