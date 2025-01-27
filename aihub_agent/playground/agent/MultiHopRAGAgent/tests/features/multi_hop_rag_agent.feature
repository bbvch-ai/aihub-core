Feature: Multi Hop RAG Agent
  Testing the RAGAgent steps in sequence with specific configuration

  Scenario: Test MultiHopRAGAgent with valid configuration
    Given a MultiHopRAGAgent runner with a valid configuration
    When the start event is sent with a user query "What is AI?"
    Then a StartEvent is present with payload "What is AI?"
    And a LimitChatHistoryEvent is present
    And "5" DecomposeQueryEvent are present
    And "10" RetrieverEvent are present
    And a ConcatenationEvent is present with concatenated documents
    And an InOrderNodeCombinerEvent is present with ordered context message
    And a LimitChatHistoryWithContextEvent is present with limited history and context
    And an LLMEvent is present with a generated response
    And a StopEvent is present
