Feature: Multi Hop RAG Agent
  Testing the RAGAgent steps in sequence with specific configuration

  Scenario: Test MultiHopRAGAgent with valid configuration and valid question
    Given the following guard examples:
      | user                           | success | reason                                          |
      | How many days off do I have?   | false   | This request is personal and not related to AI. |
      | What is the weather in Berlin? | false   | This request is not related to AI.              |
      | What are AI agents?            | true    | This request is related to AI.                  |
    And a MultiHopRAGAgent runner with a valid configuration with "3" hops

    When the start event is sent with a user query "What are AI agents?"

    Then a StartEvent is present with payload "What are AI agents?"
    And a LimitChatHistoryEvent is present
    And "3" DecomposeQueryEvent are present and are not the same
    And "3" FewShotAcceptEvent are present
    And "3" RetrieverEvent are present
    And a ConcatenationEvent is present with concatenated documents
    And an InOrderNodeCombinerEvent is present with ordered context message
    And a LimitChatHistoryWithContextEvent is present with limited history and context
    And an LLMEvent is present with a generated response
    And a StopEvent is present


  Scenario: Test MultiHopRAGAgent with valid configuration and invalid question
    Given the following guard examples:
      | user                           | success | reason                                          |
      | How many days off do I have?   | false   | This request is personal and not related to AI. |
      | What is the weather in Berlin? | false   | This request is not related to AI.              |
      | What are AI agents?            | true    | This request is related to AI.                  |
    And a MultiHopRAGAgent runner with a valid configuration with "3" hops

    When the start event is sent with a user query "How many days off do I have?"

    Then a StartEvent is present with payload "How many days off do I have?"
    And a LimitChatHistoryEvent is present
    And "3" DecomposeQueryEvent are present and are not the same
    And a FewShotRejectEvent is present
    And a ExceptionEvent is present
