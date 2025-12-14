Feature: RAG Agent
  Testing the RAGAgent steps in sequence with specific configuration.

  Note: Retrieval logic is now handled by specialized KnowledgeRetrievalAgent
  and InsightRetrievalAgent. RAGAgent invokes them via AgentInTheLoop.

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
    * a CombinedRetrievalEvent is present with context message
    * a LimitChatHistoryWithContextEvent is present with limited history and context
    * an LLMEvent is present with a generated response
    * a StopEvent is present

  Scenario: Test RAGAgent multi-hop retrieval when context is insufficient
    Given a RAGAgent runner with a valid self hosted configuration
    * context sufficiency checking enabled with max_hops 3
    When a multi-hop query is sent with insufficient context on first retrieval
    Then a ContextInsufficientWithQueryEvent is present with a new query
    * two retrieval rounds were executed
    * a ContextSufficientAcceptEvent is present after second retrieval
    * an LLMEvent is present with a generated response
    * a StopEvent is present

