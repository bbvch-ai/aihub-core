Feature: RAG Agent
  Testing the RAGAgent steps in sequence with specific configuration

  @azure
  Scenario: Test RAGAgent with valid azure configuration
    Given a RAGAgent runner with a valid azure configuration
    When the start event is sent with a user query "What is AI?"
    Then a StartEvent is present with payload "What is AI?"
    And a LimitChatHistoryEvent is present
    And a StandaloneQuestionCondenserEvent is present with condensed question
    And a RetrieverEvent is present with retrieved nodes
    And an InOrderNodeCombinerEvent is present with ordered context message
    And a LimitChatHistoryWithContextEvent is present with limited history and context
    And an LLMEvent is present with a generated response
    And a StopEvent is present

  @self_hosted
  Scenario: Test RAGAgent with valid self hosted configuration
    Given a RAGAgent runner with a valid self hosted configuration
    When the start event is sent with a user query "What is AI?"
    Then a StartEvent is present with payload "What is AI?"
    And a LimitChatHistoryEvent is present
    And a StandaloneQuestionCondenserEvent is present with condensed question
    And a RetrieverEvent is present with retrieved nodes
    And an InOrderNodeCombinerEvent is present with ordered context message
    And a LimitChatHistoryWithContextEvent is present with limited history and context
    And an LLMEvent is present with a generated response
    And a StopEvent is present

  @azure
  Scenario: Test the RAGAgent with few shot guard examples when sending an invalid user query
    Given a RAGAgent runner with a valid azure configuration
    * with few shot guard examples
      | user                           | success | reason                                          |
      | How many days off do I have?   | false   | This request is personal and not related to AI. |
      | What is the weather in Berlin? | false   | This request is not related to AI.              |
      | What are AI agents?            | true    | This request is related to AI.                  |
    When the start event is sent with a user query "Where can I see my work hours?" and locale en
    Then the few shot guard should reject the user query
    * respond to the user with the reasoning for the rejection

  @azure
  Scenario: Test the RAGAgent with few shot guard examples when sending a valid user query
    Given a RAGAgent runner with a valid azure configuration
    * with few shot guard examples
      | user                           | success | reason                                          |
      | How many days off do I have?   | false   | This request is personal and not related to AI. |
      | What is the weather in Berlin? | false   | This request is not related to AI.              |
      | What are AI agents?            | true    | This request is related to AI.                  |
    When the start event is sent with a user query "What is AI?" and locale en
    Then the few shot guard should accept the user query
    * respond to the user with a generated response

  @azure
  Scenario: Test the RAGAgent with multiple retrieval hops
    Given a RAGAgent runner with a valid azure configuration
    * check_context_sufficiency set to "True" and max_hops to "3"
    When the start event is sent with a user query "What is AI?" and locale en
    Then "6" RetrieverEvent are present
    * an LLMEvent is present with a generated response
    * a StopEvent is present