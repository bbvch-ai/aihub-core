Feature: Knowledge Retrieval Agent
  Testing the KnowledgeRetrievalAgent for vector store retrieval

  Scenario: Test KnowledgeRetrievalAgent retrieves relevant documents
    Given a KnowledgeRetrievalAgent and a vector store with 3 documents about AI
    When the user asks "What is AI?"
    Then the agent should retrieve "3" nodes
    * the nodes should be combined into a single message
    * the agent returns an event with this context message and stops

  Scenario: Test KnowledgeRetrievalAgent with reranking enabled
    Given a KnowledgeRetrievalAgent with reranking enabled and top_n of "2"
    When the user asks "What is AI?"
    Then a RetrieverEvent is present with more than "2" retrieved nodes
    * a RerankerEvent is present with reranked nodes
    * the RerankerEvent model name should be "reranker"
    * the RerankerEvent should limit results to "2" nodes
    * the agent returns an event with this context message and stops
