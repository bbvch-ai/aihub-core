Feature: RAG Agent
  Testing the RAGAgent steps in sequence with specific configuration

  Scenario Outline: Test RAGAgent with multi-language system prompt
    Given a RAGAgent runner with a valid self hosted configuration
    * with multi-language system prompt for locale <locale> and prompt "<prompt>"
    When the start event is sent with a user query "<query>" and locale <locale>
    Then an LLMEvent is present with a generated response
    * the LLM received the system prompt "<prompt>"
    * a StopEvent is present

    Examples:
      | locale | prompt                                                                  | query               |
      | en     | You are a helpful AI assistant. Always respond in English.              | What is AI?         |
      | de     | Sie sind ein hilfreicher KI-Assistent. Antworten Sie immer auf Deutsch. | Was ist AI?         |
      | fr     | Vous êtes un assistant IA utile. Répondez toujours en français.         | Qu'est-ce que l'IA? |

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

  Scenario: Test RAGAgent with reranking enabled
    Given a RAGAgent runner with a valid self hosted configuration
    * with reranking enabled and top_n of "2"
    When the start event is sent with a user query "What is AI Hub?"
    Then a RetrieverEvent is present with more than "2" retrieved nodes
    * a RerankerEvent is present with reranked nodes
    * the RerankerEvent model name should be "reranker/bge"
    * the RerankerEvent should limit results to "2" nodes
    * an LLMEvent is present with a generated response
    * a StopEvent is present

  Scenario: Test RAGAgent retrieves organization memory alongside knowledge base documents
    Given a RAGAgent runner with organization memory enabled
    * organization memories are pre-seeded in the system
    When the start event is sent with a user query "What is machine learning?"
    Then a RetrieveOrganizationMemoryEvent is present
    * an AddOrganizationMemoryToChatHistoryEvent is present
    * a RetrieverEvent is present with retrieved nodes
    * an LLMEvent is present with a generated response
    * a StopEvent is present

