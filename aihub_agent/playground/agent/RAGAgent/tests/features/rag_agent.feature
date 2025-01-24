Feature: RAG Agent
  Testing the RAGAgent steps in sequence with specific configuration

  Scenario: Test RAGAgent with valid azure configuration
    Given a RAGAgent runner with a valid azure configuration
    When the start event is sent with a user query "What is AI?"
    Then a StartEvent is present with payload "What is AI?"
    And a LimitChatHistoryEvent is present
    And a StandaloneQuestionCondenserEvent is present with condensed question
    And a RetrieverEvent is present with retrieved documents
    And an InOrderNodeCombinerEvent is present with ordered context message
    And a LimitChatHistoryWithContextEvent is present with limited history and context
    And an LLMEvent is present with a generated response
    And a StopEvent is present


  Scenario: Test RAGAgent with valid self hosted configuration
    Given a RAGAgent runner with a valid self hosted configuration
    When the start event is sent with a user query "What is AI?"
    Then a StartEvent is present with payload "What is AI?"
    And a LimitChatHistoryEvent is present
    And a StandaloneQuestionCondenserEvent is present with condensed question
    And a RetrieverEvent is present with retrieved documents
    And an InOrderNodeCombinerEvent is present with ordered context message
    And a LimitChatHistoryWithContextEvent is present with limited history and context
    And an LLMEvent is present with a generated response
    And a StopEvent is present
