Feature: RAG Agent
  Testing the RAGAgent steps in sequence with specific configuration

  @azure
  Scenario: Test RAGAgent with valid azure configuration
    Given a RAGAgent runner with a valid azure configuration
    When the start event is sent with a user query "What is AI?"
    Then a StartEvent is present with payload "What is AI?"
    * a LimitChatHistoryEvent is present
    * a StandaloneQuestionCondenserEvent is present with condensed question
    * a RetrieverEvent is present with retrieved nodes
    * an InOrderNodeCombinerEvent is present with ordered context message
    * a LimitChatHistoryWithContextEvent is present with limited history and context
    * an LLMEvent is present with a generated response
    * a StopEvent is present

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

  @self_hosted
  Scenario: Test RAGAgent with multi-language system prompt (English)
    Given a RAGAgent runner with a valid self hosted configuration
    * with multi-language system prompt
      | locale | prompt                                                                          |
      | en     | You are a helpful AI assistant. Always respond in English and be very detailed. |
    When the start event is sent with a user query "What is AI?" and locale en
    Then an LLMEvent is present with a generated response
    * the LLM received the system prompt "You are a helpful AI assistant. Always respond in English and be very detailed."
    * a StopEvent is present

  @self_hosted
  Scenario: Test RAGAgent with multi-language system prompt (German)
    Given a RAGAgent runner with a valid self hosted configuration
    * with multi-language system prompt
      | locale | prompt                                                                                  |
      | de     | Sie sind ein hilfreicher KI-Assistent. Antworten Sie immer auf Deutsch und ausführlich. |
    When the start event is sent with a user query "Was ist AI?" and locale de
    Then an LLMEvent is present with a generated response
    * the LLM received the system prompt "Sie sind ein hilfreicher KI-Assistent. Antworten Sie immer auf Deutsch und ausführlich."
    * a StopEvent is present

  @self_hosted
  Scenario: Test RAGAgent with valid self hosted configuration
    Given a RAGAgent runner with a valid self hosted configuration
    When the start event is sent with a user query "What is AI?"
    Then a StartEvent is present with payload "What is AI?"
    * a LimitChatHistoryEvent is present
    * a StandaloneQuestionCondenserEvent is present with condensed question
    * a RetrieverEvent is present with retrieved nodes
    * an InOrderNodeCombinerEvent is present with ordered context message
    * a LimitChatHistoryWithContextEvent is present with limited history and context
    * an LLMEvent is present with a generated response
    * a StopEvent is present