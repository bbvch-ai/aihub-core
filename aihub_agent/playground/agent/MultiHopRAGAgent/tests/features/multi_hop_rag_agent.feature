Feature: Multi Hop RAG Agent
  Testing the RAGAgent steps in sequence with specific configuration

  Scenario: Test MultiHopRAGAgent with valid configuration
    Given a MultiHopRAGAgent runner with a valid configuration with "3" hops
    When the start event is sent with a user query ""Hello my Name is Joe. What can we discuss?"
    Then a StartEvent is present with payload ""Hello my Name is Joe. What can we discuss?"
    And a LimitChatHistoryEvent is present
    And "3" DecomposeQueryEvent are present and are not the same
    And "3" RetrieverEvent are present
    And a ConcatenationEvent is present with concatenated documents
    And an InOrderNodeCombinerEvent is present with ordered context message
    And a LimitChatHistoryWithContextEvent is present with limited history and context
    And an LLMEvent is present with a generated response
    And a StopEvent is present
