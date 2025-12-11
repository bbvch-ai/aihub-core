Feature: Retrieval Agent
  Testing the RetrievalAgent shared retrieval pipeline

  Scenario: Test RetrievalAgent to ensure it retrieves relevant documents and combines them
    Given a RetrievalAgent and a vector store with 3 documents about AI
    When the user asks "What is AI?"
    Then the agent should retrieve "3" nodes
    * the nodes should be combined into a single message
    * the agent returns an event with this context message and stops

  Scenario: Test RetrievalAgent with reranking enabled
    Given a RetrievalAgent with reranking enabled and top_n of "2"
    When the user asks "What is AI?"
    Then a RetrieverEvent is present with more than "2" retrieved nodes
    * a RerankerEvent is present with reranked nodes
    * the RerankerEvent model name should be "reranker"
    * the RerankerEvent should limit results to "2" nodes
    * the agent returns an event with this context message and stops

  Scenario: Test RetrievalAgent retrieves insights alongside knowledge base documents
    Given a RetrievalAgent with insight retriever enabled
    * test insights are pre-seeded in the database
    When the user asks "What is machine learning?"
    Then a RetrieverEvent is present with retrieved nodes
    * the agent returns an event with this context message and stops
